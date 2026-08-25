# 🖨️ Invoix Offline - Master CSV to PDF Invoice Generator

A lightweight, high-performance, and **100% offline-first invoice processor** built with Python and Streamlit. This app allows you to upload a single comprehensive `items.csv` containing both your business profile details and product lines, instantly generating a beautiful on-screen HTML preview and a native, downloadable PDF document.

---

## ✨ Features
- **Zero Heavy Cloud Overhead:** Operates pure-play processing in-memory with lightweight components (`fpdf2` and `pandas`).
- **Dynamic Theming:** Instant dropdown switches between Corporate Navy, Emerald Modern, and Charcoal styles.
- **Universal Currency Matrix:** Supports localized signs including **₹ (Rupee)**, `$ (USD)`, `€ (EUR)`, `£ (GBP)`, and `¥ (JPY)`.
- **Sandbox Bypassing Engine:** Bypasses browser iframe download blockades to drop native `.pdf` streams directly to your desktop.

---

## 📁 Repository Structure
```text
📁 master-csv-invoice-app/
│
├── 📄 app.py               # Main application source code logic
├── 📄 requirements.txt     # Python server package dependencies
└── 📄 items.csv            # Structural metadata and itemized ledger template
```

---

## 📋 The Unified CSV Template Structure (`items.csv`)
Your source data file must be divided into a strict `[METADATA]` block and an `[ITEMS]` block. Copy this text into your template file:

```csv
[METADATA]
Key,Value
Company Name,WebTech Solutions Ltd
Company Address,"123 Innovation Way, Tech District, NY 10001"
Mobile No,+1 (555) 019-2834
Website,://webtechsolutions.com
Client Name,John Doe Enterprises
Client Address,"456 Commerce Avenue, Suite B, CA 94016"
Invoice Number,INV-2026-889
Invoice Date,2026-08-25
Tax Rate (%),18.0

[ITEMS]
Description,Quantity,Unit Price
Web Design Services,1,1200.00
Cloud Server Hosting,12,15.50
SSL Security Certificate,2,49.99
```

---

## 🚀 How to Run locally (100% Offline)
You can download this codebase to run it locally on your computer without an internet connection:

1. **Clone or download** this repository tree folder to your workstation machine.
2. Open your system **terminal or command prompt** inside the directory workspace.
3. Install package tools via pip:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the web engine dashboard script:
   ```bash
   streamlit run app.py
   ```
5. A local web portal view will automatically pop open inside your default browser window.

---

## 🌐 How to Deploy to the Web for Free
1. Push these exact codebase files into a **Public GitHub Repository**.
2. Log into the free hosting tier platform at [Streamlit Community Cloud](https://streamlit.io).
3. Click **"New App"**, choose your repository path link branch, select `app.py`, and press **"Deploy"**. Your system link goes live instantly!
