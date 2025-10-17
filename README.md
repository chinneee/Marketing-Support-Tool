# Marketing Data Upload Tool

🚀 A comprehensive Streamlit app for uploading marketing data to Google Sheets.

## Features

- **Sellerboard**: Upload and process Sellerboard data for US, CA, UK markets
- **PPC XNurta**: Coming soon
- **DSP XNurta**: Coming soon
- **FBA Inventory**: Coming soon
- **ASIN - Dimension**: Coming soon
- **Launching - Dimension**: Coming soon

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure Google Sheets credentials in Streamlit secrets
4. Run: `streamlit run app.py`

## Deployment on Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Add secrets in the Streamlit Cloud dashboard
5. Deploy!

## File Format

Excel files must have date in filename format: `DD_MM_YYYY`
Example: `report_15_10_2025.xlsx`
