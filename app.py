import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import base64

st.set_page_config(page_title="Master Invoice Processor", layout="wide")
st.title("🖨️ Two-Way Master Invoice Generator")

# --- SIDEBAR CONTROL PANEL LAYOUT ---
st.sidebar.header("⚙️ Invoix Control Panel")
st.sidebar.caption("👉 *Complete Steps 1 & 2 below to see your live document preview on the right & in Step 3 💡 you can download pdf invoice below.*")

st.sidebar.markdown("### 🛠️ Step 1: Customize Style & Currency")
theme_choice = st.sidebar.selectbox("🎨 Choose Invoice Theme Color:", ["Corporate Navy", "Emerald Modern", "Charcoal Minimalist"])
theme_colors = {
    "Corporate Navy": (30, 58, 138),
    "Emerald Modern": (6, 95, 70),
    "Charcoal Minimalist": (55, 65, 81)
}
PRIMARY_RGB = theme_colors[theme_choice]

PRIMARY_HEX = {
    "Corporate Navy": "#1E3A8A",
    "Emerald Modern": "#065F46",
    "Charcoal Minimalist": "#374151"
}[theme_choice]

currency_choice = st.sidebar.selectbox("💰 Select Currency Symbol:", ["₹", "$", "€", "£", "¥"])
CURRENCY_SYM = currency_choice

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 Step 2: Choose Entry Method")
entry_method = st.sidebar.radio("Select Processing Mode:", ["Upload Master CSV File", "Manual Form Entry"], horizontal=False)

# Initialize global fallback default values
vendor_name, vendor_addr, vendor_phone, vendor_web = "My Business Ltd", "Address Line", "N/A", "N/A"
client_name, client_addr = "Client Name", "Client Address"
inv_number, tax_rate = "INV-000", 0.0
inv_date = datetime.today().strftime('%Y-%m-%d') 
final_items = []

if entry_method == "Upload Master CSV File":
    uploaded_file = st.sidebar.file_uploader("Upload your comprehensive items.csv", type=["csv"])
    if uploaded_file is not None:
        try:
            raw_bytes = uploaded_file.read()
            raw_text = raw_bytes.decode("utf-8").splitlines()
            metadata_lines, items_lines = [], []
            current_section = None
            
            for line in raw_text:
                if "[METADATA]" in line:
                    current_section = "metadata"
                    continue
                elif "[ITEMS]" in line:
                    current_section = "items"
                    continue
                
                if current_section == "metadata" and line.strip():
                    metadata_lines.append(line)
                elif current_section == "items" and line.strip():
                    items_lines.append(line)
                    
            from io import StringIO
            if metadata_lines:
                df_meta = pd.read_csv(StringIO("\n".join(metadata_lines)))
                meta_dict = dict(zip(df_meta.iloc[:, 0].str.strip(), df_meta.iloc[:, 1].str.strip()))
                vendor_name = meta_dict.get("Company Name", vendor_name)
                vendor_addr = meta_dict.get("Company Address", vendor_addr)
                vendor_phone = meta_dict.get("Mobile No", vendor_phone)
                vendor_web = meta_dict.get("Website", vendor_web)
                client_name = meta_dict.get("Client Name", client_name)
                client_addr = meta_dict.get("Client Address", client_addr)
                inv_number = meta_dict.get("Invoice Number", inv_number)
                tax_rate = float(meta_dict.get("Tax Rate (%)", tax_rate))
                if "Invoice Date" in meta_dict and meta_dict["Invoice Date"].strip():
                    inv_date = meta_dict["Invoice Date"].strip()

            if items_lines:
                df_items = pd.read_csv(StringIO("\n".join(items_lines)))
                df_items.columns = [c.strip().title() for c in df_items.columns]
                df_items["Quantity"] = pd.to_numeric(df_items["Quantity"]).fillna(1).astype(int)
                df_items["Unit Price"] = pd.to_numeric(df_items["Unit Price"]).fillna(0.0).astype(float)
                df_items["Total"] = df_items["Quantity"] * df_items["Unit Price"]
                final_items = df_items.to_dict(orient="records")
                st.sidebar.success(f"Parsed {len(final_items)} rows from CSV!")
        except Exception as e:
            st.sidebar.error(f"CSV Parse Error: {e}")

else:
    # --- MANUAL FORM ENTRY MODE ON SIDEBAR ---
    st.sidebar.markdown("#### 🏢 Vendor Details")
    vendor_name = st.sidebar.text_input("Company Name", "My Business Ltd")
    vendor_addr = st.sidebar.text_input("Company Address", "123 Business Rd, NY")
    vendor_phone = st.sidebar.text_input("Mobile No", "+1 (555) 019-2834")
    vendor_web = st.sidebar.text_input("Website", "://mybusiness.com")
    
    st.sidebar.markdown("#### 👤 Client Details")
    client_name = st.sidebar.text_input("Client Name", "John Doe")
    client_addr = st.sidebar.text_input("Client Address", "456 Customer Ave, CA")
    
    st.sidebar.markdown("#### 🔢 Meta Info")
    inv_number = st.sidebar.text_input("Invoice Number", "INV-2026-001")
    inv_date = st.sidebar.text_input("Invoice Date (YYYY-MM-DD)", datetime.today().strftime('%Y-%m-%d'))
    tax_rate = st.sidebar.number_input("Tax Rate (%)", min_value=0.0, value=5.0, step=0.5)
    
    st.sidebar.markdown("#### 🛒 Item Lines Builder")
    if "manual_rows" not in st.session_state:
        st.session_state.manual_rows = [{"Description": "Service Fee", "Quantity": 1, "Unit Price": 100.0}]
        
    col_b1, col_b2 = st.sidebar.columns(2)
    if col_b1.button("➕ Add Row"):
        st.session_state.manual_rows.append({"Description": "", "Quantity": 1, "Unit Price": 0.0})
    if col_b2.button("❌ Remove"):
        if len(st.session_state.manual_rows) > 1:
            st.session_state.manual_rows.pop()
            
    for i, item in enumerate(st.session_state.manual_rows):
        st.sidebar.markdown(f"**Item Row #{i+1}**")
        desc = st.sidebar.text_input(f"Description #{i+1}", item["Description"], key=f"d_f_{i}")
        qty = st.sidebar.number_input(f"Quantity #{i+1}", min_value=1, value=int(item["Quantity"]), key=f"q_f_{i}")
        price = st.sidebar.number_input(f"Unit Price #{i+1}", min_value=0.0, value=float(item["Unit Price"]), key=f"p_f_{i}")
        final_items.append({"Description": desc, "Quantity": qty, "Unit Price": price, "Total": qty * price})
# Function to generate a real PDF binary in-memory using FPDF2
def generate_true_pdf(vendor, addr, phone, web, client, c_addr, inv_num, date, tax, items, rgb_color, currency):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf_currency = "Rs." if currency == "₹" else currency
    
    # Header styling
    pdf.set_text_color(rgb_color, rgb_color, rgb_color)
    pdf.set_font("Helvetica", style="B", size=24)
    pdf.cell(100, 10, txt=vendor, ln=0, align="L")
    
    pdf.set_text_color(120, 120, 120)
    pdf.set_font("Helvetica", style="B", size=28)
    pdf.cell(90, 10, txt="INVOICE", ln=1, align="R")
    pdf.ln(5)
    
    # Vendor & Meta block info
    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", size=10)
    pdf.cell(100, 5, txt=f"Address: {addr[:50]}", ln=0)
    pdf.cell(90, 5, txt=f"Invoice No: {inv_num}", ln=1, align="R")
    pdf.cell(100, 5, txt=f"Phone: {phone} | Web: {web}", ln=0)
    pdf.cell(90, 5, txt=f"Date: {date}", ln=1, align="R")
    pdf.ln(10)
    
    # Client Billing Box
    pdf.set_fill_color(245, 247, 250)
    pdf.cell(190, 22, txt="", border=1, ln=0, fill=True)
    pdf.set_x(15) 
    pdf.ln(2)
    pdf.set_font("Helvetica", style="B", size=9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(190, 4, txt="BILLED TO:", ln=1)
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.set_text_color(17, 24, 39)
    pdf.cell(190, 5, txt=client, ln=1)
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(75, 85, 99)
    pdf.cell(190, 5, txt=c_addr[:90], ln=1)
    pdf.ln(8)
    
    # Table Header
    pdf.set_fill_color(rgb_color, rgb_color, rgb_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", style="B", size=10)
    pdf.cell(100, 10, txt=" Line Item Description", border=0, ln=0, fill=True)
    pdf.cell(20, 10, txt="Qty", border=0, ln=0, align="C", fill=True)
    pdf.cell(35, 10, txt="Unit Price", border=0, ln=0, align="R", fill=True)
    pdf.cell(35, 10, txt="Total ", border=0, ln=1, align="R", fill=True)
    
    # Table Rows
    pdf.set_text_color(31, 41, 55)
    pdf.set_font("Helvetica", size=10)
    subtotal = 0.0
    
    for row in items:
        subtotal += row['Total']
        pdf.cell(100, 9, txt=f" {row['Description']}", border="B", ln=0)
        pdf.cell(20, 9, txt=str(row['Quantity']), border="B", ln=0, align="C")
        pdf.cell(35, 9, txt=f"{pdf_currency} {row['Unit Price']:,.2f}", border="B", ln=0, align="R")
        pdf.cell(35, 9, txt=f"{pdf_currency} {row['Total']:,.2f} ", border="B", ln=1, align="R")
        
    # Financial calculations block
    tax_amount = subtotal * (tax / 100)
    grand_total = subtotal + tax_amount
    
    pdf.ln(5)
    pdf.cell(120, 6, txt="", ln=0)
    pdf.cell(35, 6, txt="Subtotal:", ln=0)
    pdf.cell(35, 6, txt=f"{pdf_currency} {subtotal:,.2f} ", ln=1, align="R")
    
    pdf.cell(120, 6, txt="", ln=0)
    pdf.cell(35, 6, txt=f"Tax ({tax}%):", ln=0)
    pdf.cell(35, 6, txt=f"{pdf_currency} {tax_amount:,.2f} ", ln=1, align="R")
    
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.set_text_color(rgb_color, rgb_color, rgb_color)
    pdf.cell(120, 10, txt="", ln=0)
    pdf.cell(35, 10, txt="Total Due:", border="T", ln=0)
    pdf.cell(35, 10, txt=f"{pdf_currency} {grand_total:,.2f} ", border="T", ln=1, align="R")
    
    return pdf.output()

# --- MAIN ENGINE RENDERING PIPELINE ---
if final_items and any(item['Description'] for item in final_items):
    pdf_bytes = generate_true_pdf(
        vendor_name, vendor_addr, vendor_phone, vendor_web,
        client_name, client_addr, inv_number, inv_date, 
        tax_rate, final_items, PRIMARY_RGB, CURRENCY_SYM
    )
    
    # Updated Step 3 layout block with explicitly mapped user text layout
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🖨 Step 3: Download Invoice")
    
    st.sidebar.download_button(
        label="📥 Click to Download True PDF",
        data=bytes(pdf_bytes),
        file_name=f"invoice_{inv_number}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    st.markdown("### 👁️ Live Invoice Document Preview")
    
    table_rows_html = ""
    subtotal = 0.0
    for item in final_items:
        subtotal += item['Total']
        table_rows_html += f"""
        <tr>
            <td style='padding: 12px; border-bottom: 1px solid #E5E7EB; text-align: left;'>{item['Description']}</td>
            <td style='padding: 12px; border-bottom: 1px solid #E5E7EB; text-align: center;'>{item['Quantity']}</td>
            <td style='padding: 12px; border-bottom: 1px solid #E5E7EB; text-align: right;'>{CURRENCY_SYM}{item['Unit Price']:,.2f}</td>
            <td style='padding: 12px; border-bottom: 1px solid #E5E7EB; text-align: right; font-weight: bold;'>{CURRENCY_SYM}{item['Total']:,.2f}</td>
        </tr>
        """
    tax_amount = subtotal * (tax_rate / 100)
    grand_total = subtotal + tax_amount

    html_invoice = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 40px; border: 1px solid #E5E7EB; border-radius: 8px; max-width: 850px; margin: auto; background-color: #fff; color: #1F2937; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <tr>
                <td style="vertical-align: top; text-align: left;">
                    <span style="font-size: 26px; font-weight: 800; color: {PRIMARY_HEX}; letter-spacing: -0.5px;">{vendor_name}</span><br>
                    <span style="font-size: 13px; color: #4B5563; line-height: 1.5;">
                        {vendor_addr}<br>
                        📱 Phone: {vendor_phone} | 🌐 Web: {vendor_web}
                    </span>
                </td>
                <td style="vertical-align: top; text-align: right;">
                    <span style="font-size: 32px; font-weight: 300; color: #9CA3AF; letter-spacing: 1px;">INVOICE</span><br>
                    <span style="font-size: 14px; color: #1F2937; line-height: 1.6;">
                        <b>Invoice No:</b> <span style="color: {PRIMARY_HEX}; font-weight: 600;">{inv_number}</span><br>
                        <b>Date:</b> {inv_date}
                    </span>
                </td>
            </tr>
        </table>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 40px; background-color: #F9FAFB;">
            <tr>
                <td style="padding: 20px; border: 1px solid #F3F4F6; vertical-align: top;">
                    <span style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #6B7280;">Billed To:</span><br>
                    <span style="font-size: 16px; font-weight: 700; color: #111827; display:block; margin-top:4px; margin-bottom:4px;">{client_name}</span>
                    <span style="font-size: 13px; color: #4B5563; line-height: 1.4;">{client_addr}</span>
                </td>
            </tr>
        </table>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <thead>
                <tr style="background-color: {PRIMARY_HEX}; color: white;">
                    <th style="padding: 12px; text-align: left; font-size: 13px;">Line Item Description</th>
                    <th style="padding: 12px; text-align: center; font-size: 13px;">Qty</th>
                    <th style="padding: 12px; text-align: right; font-size: 13px;">Unit Price</th>
                    <th style="padding: 12px; text-align: right; font-size: 13px;">Total</th>
                </tr>
            </thead>
            <tbody>{table_rows_html}</tbody>
        </table>
        
        <table style="width: 45%; margin-left: 55%; border-collapse: collapse; font-size: 14px;">
            <tr>
                <td style="padding: 8px 0; color: #4B5563;">Subtotal:</td>
                <td style="padding: 8px 0; text-align: right;">{CURRENCY_SYM}{subtotal:,.2f}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #4B5563;">Tax ({tax_rate}%):</td>
                <td style="padding: 8px 0; text-align: right;">{CURRENCY_SYM}{tax_amount:,.2f}</td>
            </tr>
            <tr style="border-top: 2px solid {PRIMARY_HEX};">
                <td style="padding: 15px 0 0 0; font-size: 18px; font-weight: 700; color: #111827;">Amount Due:</td>
                <td style="padding: 15px 0 0 0; text-align: right; font-size: 22px; font-weight: 800; color: {PRIMARY_HEX};">{CURRENCY_SYM}{grand_total:,.2f}</td>
            </tr>
        </table>
    </div>
    """
    st.components.v1.html(html_invoice, height=650, scrolling=True)
else:
    st.info("💡 **Welcome to the Invoix Studio!** Please choose your flow inside the left sidebar control panel. Upload your master template file or enter parameters manually to build your document canvas view here.")
