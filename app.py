import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import base64

st.set_page_config(page_title="Master CSV Invoice Processor", layout="wide")
st.title("🖨️ Master CSV to PDF Invoice Generator")

# --- USER OPTIONS SECTION ---
st.markdown("### 🛠️ Step 1: Customize Invoice Style & Currency")
col_opt1, col_opt2 = st.columns(2)

with col_opt1:
    theme_choice = st.selectbox("🎨 Choose Invoice Theme Color:", ["Corporate Navy", "Emerald Modern", "Charcoal Minimalist"])
    theme_colors = {
        "Corporate Navy": (30, 58, 138),
        "Emerald Modern": (6, 95, 70),
        "Charcoal Minimalist": (55, 65, 81)
    }
    PRIMARY_RGB = theme_colors[theme_choice]
    # Hex version for HTML embedding previews
    PRIMARY_HEX = {
        "Corporate Navy": "#1E3A8A",
        "Emerald Modern": "#065F46",
        "Charcoal Minimalist": "#374151"
    }[theme_choice]

with col_opt2:
    currency_choice = st.selectbox("💰 Select Currency Symbol:", ["$", "Rs.", "€", "£", "¥"])
    CURRENCY_SYM = currency_choice

# --- FILE UPLOADER ---
st.markdown("---")
st.markdown("### 📥 Step 2: Upload Your Master Invoice CSV")
uploaded_file = st.file_uploader("Upload your comprehensive items.csv", type=["csv"])

# Default fallback values if no file is uploaded
vendor_name, vendor_addr, vendor_phone, vendor_web = "My Business Ltd", "Address", "N/A", "N/A"
client_name, client_addr = "Client Name", "Client Address"
inv_number, tax_rate = "INV-000", 0.0
inv_date = datetime.today().strftime('%Y-%m-%d') 
final_items = []

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
                
        # Parse Metadata Section
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

        # Parse Line Items Section
        if items_lines:
            df_items = pd.read_csv(StringIO("\n".join(items_lines)))
            df_items.columns = [c.strip().title() for c in df_items.columns]
            df_items["Quantity"] = pd.to_numeric(df_items["Quantity"]).fillna(1).astype(int)
            df_items["Unit Price"] = pd.to_numeric(df_items["Unit Price"]).fillna(0.0).astype(float)
            df_items["Total"] = df_items["Quantity"] * df_items["Unit Price"]
            final_items = df_items.to_dict(orient="records")
            
            st.success(f"Successfully loaded invoice structure with {len(final_items)} itemized rows!")
    except Exception as e:
        st.error(f"Error reading file layout: {e}. Please double check your formatting.")
# Function to generate a real PDF binary in-memory using FPDF2
def generate_true_pdf(vendor, addr, phone, web, client, c_addr, inv_num, date, tax, items, rgb_color, currency):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Header styling
    pdf.set_text_color(rgb_color[0], rgb_color[1], rgb_color[2])
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
    pdf.set_fill_color(rgb_color[0], rgb_color[1], rgb_color[2])
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
        pdf.cell(35, 9, txt=f"{currency} {row['Unit Price']:,.2f}", border="B", ln=0, align="R")
        pdf.cell(35, 9, txt=f"{currency} {row['Total']:,.2f} ", border="B", ln=1, align="R")
        
    # Financial Row block
    tax_amount = subtotal * (tax / 100)
    grand_total = subtotal + tax_amount
    
    pdf.ln(5)
    pdf.cell(120, 6, txt="", ln=0)
    pdf.cell(35, 6, txt="Subtotal:", ln=0)
    pdf.cell(35, 6, txt=f"{currency} {subtotal:,.2f} ", ln=1, align="R")
    
    pdf.cell(120, 6, txt="", ln=0)
    pdf.cell(35, 6, txt=f"Tax ({tax}%):", ln=0)
    pdf.cell(35, 6, txt=f"{currency} {tax_amount:,.2f} ", ln=1, align="R")
    
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.set_text_color(rgb_color[0], rgb_color[1], rgb_color[2])
    pdf.cell(120, 10, txt="", ln=0)
    pdf.cell(35, 10, txt="Total Due:", border="T", ln=0)
    pdf.cell(35, 10, txt=f"{currency} {grand_total:,.2f} ", border="T", ln=1, align="R")
    
    return pdf.output()

# --- DUAL ACTION VIEWER ENGINE ---
if final_items:
    st.markdown("### 🖨️ Step 3: Preview & Download Live Document")
    
    # 1. Compile backend PDF data channel bytes
    pdf_bytes = generate_true_pdf(
        vendor_name, vendor_addr, vendor_phone, vendor_web,
        client_name, client_addr, inv_number, inv_date, 
        tax_rate, final_items, PRIMARY_RGB, CURRENCY_SYM
    )
    
    # 2. Render direct download layout trigger
    st.download_button(
        label="📥 Click here to download this file as a real PDF",
        data=bytes(pdf_bytes),
        file_name=f"invoice_{inv_number}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    # 3. Create desktop layout split views
    col_v1, col_v2 = st.columns([1, 1])
    
    with col_v1:
        st.markdown("#### 👁️ Screen Visual Preview")
        # Generates a dynamic clean layout template inside the dashboard wrapper
        table_rows_html = "".join([
            f"<tr><td style='padding:10px; border-bottom:1px solid #eee;'>{r['Description']}</td>"
            f"<td style='text-align:center;'>{r['Quantity']}</td>"
            f"<td style='text-align:right;'>{CURRENCY_SYM}{r['Unit Price']:,.2f}</td>"
            f"<td style='text-align:right; font-weight:bold;'>{CURRENCY_SYM}{r['Total']:,.2f}</td></tr>"
            for r in final_items
        ])
        subtotal = sum([r['Total'] for r in final_items])
        tax_amount = subtotal * (tax_rate / 100)
        grand_total = subtotal + tax_amount
        
        html_preview = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 6px; background: white; color: #333;">
            <h3 style="color:{PRIMARY_HEX}; margin-top:0;">{vendor_name}</h3>
            <p style="font-size:12px; color:#666; margin-bottom:20px;">Invoice #: <b>{inv_number}</b> | Date: {inv_date}</p>
            <div style="background:#f9f9f9; padding:10px; font-size:13px; margin-bottom:20px;"><b>Billed To:</b> {client_name}</div>
            <table style="width:100%; font-size:13px; border-collapse:collapse;">
                <tr style="background:{PRIMARY_HEX}; color:white;"><th style="padding:8px; text-align:left;">Item</th><th style="text-align:center;">Qty</th><th style="text-align:right;">Price</th><th style="text-align:right;">Total</th></tr>
                {table_rows_html}
            </table>
            <div style="text-align:right; margin-top:15px; font-size:14px;">
                <p>Subtotal: {CURRENCY_SYM}{subtotal:,.2f}</p>
                <p style="font-size:16px; font-weight:bold; color:{PRIMARY_HEX};">Total Due: {CURRENCY_SYM}{grand_total:,.2f}</p>
            </div>
        </div>
        """
        st.components.v1.html(html_preview, height=450, scrolling=True)

    with col_v2:
        st.markdown("#### 📄 Embedded Raw PDF Preview Pane")
        # Encodes the backend PDF byte block directly into standard data iframe layers
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="450px" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
else:
    st.info("Please upload your structural `items.csv` file into the box above to generate your desktop preview panels.")
