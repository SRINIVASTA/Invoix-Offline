import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Master CSV Invoice Processor", layout="wide")
st.title("🖨️ Master CSV to PDF Invoice Generator")

# --- USER OPTIONS SECTION ---
st.markdown("### 🛠️ Step 1: Customize Invoice Style & Currency")
col_opt1, col_opt2 = st.columns(2)

with col_opt1:
    theme_choice = st.selectbox("🎨 Choose Invoice Theme Color:", ["Corporate Navy", "Emerald Modern", "Charcoal Minimalist"])
    theme_colors = {
        "Corporate Navy": "#1E3A8A",
        "Emerald Modern": "#065F46",
        "Charcoal Minimalist": "#374151"
    }
    PRIMARY_COLOR = theme_colors[theme_choice]

with col_opt2:
    currency_choice = st.selectbox("💰 Select Currency Symbol:", ["$ (USD)", "₹ (INR)", "€ (EUR)", "£ (GBP)", "¥ (JPY)"])
    CURRENCY_SYM = currency_choice.split()[0]

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
# Build HTML Print Layout and Financial calculations
if final_items:
    df_totals = pd.DataFrame(final_items)
    subtotal = df_totals["Total"].sum()
    tax_amount = subtotal * (tax_rate / 100)
    grand_total = subtotal + tax_amount

    st.markdown("### 🖨️ Step 3: Print Layout Visualizer")
    
    table_rows_html = ""
    for item in final_items:
        table_rows_html += f"""
        <tr>
            <td style='padding: 12px; border-bottom: 1px solid #E5E7EB; text-align: left;'>{item['Description']}</td>
            <td style='padding: 12px; border-bottom: 1px solid #E5E7EB; text-align: center;'>{item['Quantity']}</td>
            <td style='padding: 12px; border-bottom: 1px solid #E5E7EB; text-align: right;'>{CURRENCY_SYM}{item['Unit Price']:,.2f}</td>
            <td style='padding: 12px; border-bottom: 1px solid #E5E7EB; text-align: right; font-weight: bold;'>{CURRENCY_SYM}{item['Total']:,.2f}</td>
        </tr>
        """

    # Combined HTML Layout with embedded automated html2pdf engine
    html_invoice = f"""
    <html>
    <head>
        <script src="https://cloudflare.com"></script>
        <script>
            function generatePDF() {{
                const element = document.getElementById('invoice-card');
                const opt = {{
                    margin:       0.4,
                    filename:     'invoice_{inv_number}.pdf',
                    image:        {{ type: 'jpeg', quality: 0.98 }},
                    html2canvas:  {{ scale: 2, useCORS: true }},
                    jsPDF:        {{ unit: 'in', format: 'letter', orientation: 'portrait' }}
                }};
                html2pdf().set(opt).from(element).save();
            }}
        </script>
    </head>
    <body style="margin:0; padding:10px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color:#f4f4f4;">
        
        <!-- Interactive PDF Trigger Button -->
        <div style="max-width: 850px; margin: 0 auto 15px auto;">
            <button onclick="generatePDF()" style="width:100%; background-color:{PRIMARY_COLOR}; color:white; padding:15px; border:none; border-radius:6px; font-weight:bold; font-size:16px; cursor:pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                📥 Click to Download Instant PDF File
            </button>
        </div>

        <!-- The Target Printable Layout Card Container -->
        <div id="invoice-card" style="padding: 40px; border: 1px solid #E5E7EB; border-radius: 8px; max-width: 850px; margin: auto; background-color: #fff; color: #1F2937; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                <tr>
                    <td style="vertical-align: top; text-align: left;">
                        <span style="font-size: 24px; font-weight: 800; color: {PRIMARY_COLOR}; letter-spacing: -0.5px;">{vendor_name}</span><br>
                        <span style="font-size: 13px; color: #4B5563; line-height: 1.5;">
                            {vendor_addr}<br>
                            📱 Phone: {vendor_phone} | 🌐 Web: {vendor_web}
                        </span>
                    </td>
                    <td style="vertical-align: top; text-align: right;">
                        <span style="font-size: 30px; font-weight: 300; color: #9CA3AF; letter-spacing: 1px;">INVOICE</span><br>
                        <span style="font-size: 14px; color: #1F2937; line-height: 1.6;">
                            <b>Invoice No:</b> <span style="color: {PRIMARY_COLOR}; font-weight: 600;">{inv_number}</span><br>
                            <b>Date:</b> {inv_date}
                        </span>
                    </td>
                </tr>
            </table>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 40px; background-color: #F9FAFB;">
                <tr>
                    <td style="padding: 15px; border: 1px solid #F3F4F6; vertical-align: top;">
                        <span style="font-size: 11px; text-transform: uppercase; font-weight: 700; color: #6B7280;">Billed To:</span><br>
                        <span style="font-size: 15px; font-weight: 700; color: #111827; display:block; margin-top:4px; margin-bottom:4px;">{client_name}</span>
                        <span style="font-size: 13px; color: #4B5563; line-height: 1.4;">{client_addr}</span>
                    </td>
                </tr>
            </table>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                <thead>
                    <tr style="background-color: {PRIMARY_COLOR}; color: white;">
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
                <tr style="border-top: 2px solid {PRIMARY_COLOR};">
                    <td style="padding: 15px 0 0 0; font-size: 16px; font-weight: 700;">Amount Due:</td>
                    <td style="padding: 15px 0 0 0; text-align: right; font-size: 20px; font-weight: 800; color: {PRIMARY_COLOR};">{CURRENCY_SYM}{grand_total:,.2f}</td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """

    st.components.v1.html(html_invoice, height=650, scrolling=True)
else:
    st.info("Please upload your structural `items.csv` file into the box above to generate your invoice template.")
