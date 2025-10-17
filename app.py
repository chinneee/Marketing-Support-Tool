import streamlit as st
import os
import re
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import io
import json
from typing import List, Tuple


class SBProcessor:
    """Sellerboard Data Processor"""
    
    def __init__(self, credentials_dict, sheet_id, market):
        self.credentials_dict = credentials_dict
        self.sheet_id = sheet_id
        self.market = market
        self.worksheet_name = f"Raw_SB_H2_2025_{market}"
        
        # Định nghĩa thứ tự cột chuẩn
        self.standard_columns = [
            'Product', 'ASIN', 'Date', 'SKU', 'Units', 'Refunds', 'Sales', 
            'Promo', 'Ads', 'Sponsored products (PPC)', '% Refunds', 
            'Refund сost', 'Amazon fees', 'Cost of Goods', 'Gross profit', 
            'Net profit', 'Estimated payout', 'Real ACOS', 'Sessions', 
            'VAT', 'Shipping'
        ]
        
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        
    def _init_google_sheets(self):
        """Initialize Google Sheets connection"""
        if self.client is None:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            creds = Credentials.from_service_account_info(
                self.credentials_dict, scopes=scopes
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.sheet_id)
            self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)

    def extract_date_from_filename(self, filename):
        """Extract first DD_MM_YYYY pattern from filename"""
        match = re.search(r"(\d{2}_\d{2}_\d{4})", filename)
        if match:
            return datetime.strptime(match.group(1), "%d_%m_%Y").date()
        return None

    def _standardize_columns(self, df):
        """Standardize and select only required columns"""
        df.columns = [str(c).strip() for c in df.columns]
        
        column_mapping = {}
        for std_col in self.standard_columns:
            std_col_lower = std_col.lower()
            for df_col in df.columns:
                df_col_lower = df_col.lower()
                if std_col_lower == df_col_lower:
                    column_mapping[df_col] = std_col
                    break
                elif 'sponsored' in std_col_lower and 'sponsored' in df_col_lower and 'ppc' in df_col_lower:
                    column_mapping[df_col] = std_col
                    break
                elif 'refund' in std_col_lower and 'cost' in std_col_lower and 'refund' in df_col_lower and ('cost' in df_col_lower or 'сost' in df_col_lower):
                    column_mapping[df_col] = std_col
                    break
        
        df = df.rename(columns=column_mapping)
        available_columns = [col for col in self.standard_columns if col in df.columns]
        df_filtered = df[available_columns].copy()
        
        # Thêm các cột thiếu
        for col in self.standard_columns:
            if col not in df_filtered.columns:
                df_filtered[col] = pd.NA
        
        # Sắp xếp đúng thứ tự chuẩn
        df_filtered = df_filtered[self.standard_columns]
        return df_filtered

    def process_single_excel(self, file_content, filename):
        """Process a single Excel file and return DataFrame with Date column"""
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            df = df.dropna(axis=1, how="all")
            
            # Extract date from filename
            date_val = self.extract_date_from_filename(filename)
            if date_val:
                df["Date"] = pd.to_datetime(date_val)
            
            # Standardize columns
            df = self._standardize_columns(df)
            return df
        except Exception as e:
            st.error(f"⚠️ Error processing {filename}: {e}")
            return pd.DataFrame()

    def process_files(self, uploaded_files):
        """Process multiple uploaded files"""
        all_dataframes = []
        processed_files = []
        
        for uploaded_file in uploaded_files:
            file_content = uploaded_file.read()
            df = self.process_single_excel(file_content, uploaded_file.name)
            if not df.empty:
                all_dataframes.append(df)
                processed_files.append(uploaded_file.name)
        
        if all_dataframes:
            # ⚙️ Bỏ qua các DataFrame trống hoặc toàn giá trị NA
            valid_dataframes = [df for df in all_dataframes if not df.empty and not df.isna().all().all()]
            
            if valid_dataframes:
                merged_df = pd.concat(valid_dataframes, ignore_index=True, sort=False)
            else:
                st.warning("⚠️ All uploaded files are empty or invalid.")
                return pd.DataFrame(), []
            
            # Sort by Date then Sales
            if "Date" in merged_df.columns and "Sales" in merged_df.columns:
                merged_df = merged_df.sort_values(
                    ["Date", "Sales"], ascending=[True, False]
                )
            elif "Date" in merged_df.columns:
                merged_df = merged_df.sort_values("Date")
            
            # Đảm bảo cột theo đúng thứ tự chuẩn
            merged_df = merged_df[self.standard_columns]
            
            return merged_df, processed_files
        else:
            return pd.DataFrame(), []

    def get_existing_sheet_data_count(self):
        """Get current number of rows in the sheet"""
        try:
            all_values = self.worksheet.col_values(1)
            data_rows = len([val for val in all_values if val.strip()]) - 1 if all_values else 0
            return data_rows
        except Exception as e:
            st.error(f"⚠️ Error getting sheet data count: {e}")
            return 0

    def append_to_sheets(self, df):
        """Append DataFrame to Google Sheets"""
        if df.empty:
            st.warning("⚠️ No data to upload")
            return False
        
        try:
            self._init_google_sheets()
            existing_rows = self.get_existing_sheet_data_count()
            
            start_row = existing_rows + 2
            
            values_to_append = []
            for _, row in df.iterrows():
                row_values = []
                for col in self.standard_columns:
                    val = row[col]
                    if pd.isna(val):
                        row_values.append("")
                    elif isinstance(val, (pd.Timestamp, datetime)):
                        row_values.append(val.strftime("%Y-%m-%d"))
                    else:
                        row_values.append(val)
                values_to_append.append(row_values)
            
            end_col = chr(ord('A') + len(self.standard_columns) - 1)
            end_row = start_row + len(df) - 1
            range_name = f"A{start_row}:{end_col}{end_row}"
            
            self.worksheet.update(range_name, values_to_append)
            return True
        except Exception as e:
            st.error(f"❌ Error uploading to Google Sheets: {e}")
            return False


def load_credentials_from_file(uploaded_file):
    """Load Google Sheets credentials from uploaded JSON file"""
    try:
        credentials_dict = json.load(uploaded_file)
        
        # Validate required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in credentials_dict:
                st.error(f"❌ Missing required field: {field}")
                return None
        
        return credentials_dict
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON file format")
        return None
    except Exception as e:
        st.error(f"❌ Error loading credentials: {e}")
        return None


def sellerboard_page():
    """Sellerboard data upload page"""
    st.header("📊 Sellerboard Data Upload")
    
    # Step 1: Upload credentials
    st.subheader("🔐 Step 1: Upload Google Credentials")
    
    credentials_file = st.file_uploader(
        "Upload your credential.json file",
        type=['json'],
        key="credentials_uploader",
        help="Upload your Google Service Account credentials JSON file"
    )
    
    credentials_dict = None
    if credentials_file:
        credentials_dict = load_credentials_from_file(credentials_file)
        if credentials_dict:
            st.success("✅ Credentials loaded successfully!")
            with st.expander("📋 Credential Info"):
                st.write(f"**Project ID:** {credentials_dict.get('project_id', 'N/A')}")
                st.write(f"**Client Email:** {credentials_dict.get('client_email', 'N/A')}")
        else:
            st.error("❌ Failed to load credentials. Please check your JSON file.")
            return
    else:
        st.warning("⚠️ Please upload credential.json file to continue")
        st.info("💡 You need Google Service Account credentials to push data to Google Sheets")
        return
    
    st.markdown("---")
    
    # Step 2: Enter Sheet ID
    st.subheader("📝 Step 2: Enter Google Sheet ID")
    
    sheet_id = st.text_input(
        "Google Sheet ID",
        placeholder="1rqH3SePVbpwcj1oD4Bqaa40IbkyKUi7aRBThlBdnEu4",
        help="Find this in your Google Sheet URL: docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
    )
    
    if not sheet_id:
        st.warning("⚠️ Please enter Google Sheet ID to continue")
        return
    
    st.markdown("---")
    
    # Step 3: Select Market
    st.subheader("🌍 Step 3: Select Market")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        market_us = st.button("🇺🇸 US Market", width="stretch", type="primary")
    with col2:
        market_ca = st.button("🇨🇦 CA Market", width="stretch")
    with col3:
        market_uk = st.button("🇬🇧 UK Market", width="stretch")
    
    # Determine selected market
    if market_ca:
        selected_market = "CA"
    elif market_uk:
        selected_market = "UK"
    else:
        selected_market = "US"
    
    st.info(f"📍 Selected Market: **{selected_market}**")
    
    st.markdown("---")
    
    # Step 4: Upload data files
    st.subheader("📂 Step 4: Upload Data Files")
    
    uploaded_files = st.file_uploader(
        "Upload Excel files (DD_MM_YYYY format in filename)",
        type=['xlsx'],
        accept_multiple_files=True,
        key="sb_uploader"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
        
        # Show uploaded files
        with st.expander("📁 Uploaded Files"):
            for file in uploaded_files:
                st.text(f"• {file.name}")
        
        st.markdown("---")
        
    # Step 5: Process Files
    st.subheader("⚙️ Step 5: Process Files")

    if st.button("🔄 Process Files", type="primary", width="stretch"):
        with st.spinner("Processing files..."):
            # Initialize processor
            processor = SBProcessor(credentials_dict, sheet_id, selected_market)
            result_df, processed_files = processor.process_files(uploaded_files)
            
            if not result_df.empty:
                st.success(f"✅ Successfully processed {len(processed_files)} files")
                st.info(f"📊 Total rows: {len(result_df)}")

                # Preview data
                with st.expander("👁️ Preview Data (First 10 rows)"):
                    st.dataframe(result_df.head(10), width='stretch')

                st.markdown("---")

                # Step 6: Action selection
                st.subheader("📤 Step 6: Select Action")
                st.caption("Choose how to export your processed data")

                # --- Helper function ---
                def export_to_excel(df, market):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Data')
                    output.seek(0)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    return output, f"SB_{market}_{timestamp}.xlsx"

                # --- Buttons layout ---
                col1, col2, col3 = st.columns(3)
                # Replace the export Excel button section with this:
                with col1:
                    excel_data, filename = export_to_excel(result_df, selected_market)
                    st.download_button(
                        label="📥 Export to Excel",
                        data=excel_data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width='stretch'
                    )
                with col2:
                    push_to_sheets = st.button("☁️ Push to Google Sheets", width="stretch", key="push_sheets_btn")
                    if push_to_sheets:
                        try:
                            with st.spinner("Uploading to Google Sheets..."):
                                if processor and result_df is not None:
                                    success = processor.append_to_sheets(result_df)
                                    if success:
                                        st.success(f"✅ Uploaded {len(result_df)} rows to Google Sheets!")
                                        st.balloons()
                                    else:
                                        st.error("❌ Upload failed - Check your credentials and Sheet ID")
                                else:
                                    st.error("❌ Please process files first")
                        except Exception as e:
                            st.error(f"❌ Upload failed: {str(e)}")

                with col3:
                    export_both = st.button("📤 Export Both", width="stretch", key="export_both_btn")
                    if export_both:
                        try:
                            # First handle Excel export
                            excel_data, filename = export_to_excel(result_df, selected_market)
                            
                            # Then try Google Sheets upload
                            with st.spinner("Uploading to Google Sheets..."):
                                if processor and result_df is not None:
                                    success = processor.append_to_sheets(result_df)
                                    if success:
                                        st.success(f"✅ Uploaded {len(result_df)} rows to Google Sheets!")
                                        # Show Excel download button after successful upload
                                        st.download_button(
                                            label="⬇️ Download Excel",
                                            data=excel_data,
                                            file_name=filename,
                                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                            width='stretch'
                                        )
                                        st.balloons()
                                    else:
                                        st.error("❌ Google Sheets upload failed")
                                else:
                                    st.error("❌ Please process files first")
                        except Exception as e:
                            st.error(f"❌ Export failed: {str(e)}")
            else:
                st.error("❌ No data to process")

    else:
        st.info("📁 Please upload Excel files to continue")


def main():
    st.set_page_config(
        page_title="Marketing Data Upload Tool",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main {
            padding-top: 2rem;
        }
        .stButton>button {
            height: 3rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🚀 Marketing Data Upload Tool")
    st.markdown("### Upload and manage your marketing data efficiently")
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("📋 Navigation")
    st.sidebar.markdown("Select the tool you want to use:")
    
    page = st.sidebar.radio(
        label="Select a page",  # ⚠️ thêm label hợp lệ
        options=[
            "📊 Sellerboard",
            "💰 PPC XNurta",
            "📺 DSP XNurta",
            "📦 FBA Inventory",
            "🔍 ASIN - Dimension",
            "🚀 Launching - Dimension"
        ],
        label_visibility="collapsed"  # vẫn ẩn label đi
    )
    
    # Route to appropriate page
    if page == "📊 Sellerboard":
        sellerboard_page()
    elif page == "💰 PPC XNurta":
        st.info("🚧 PPC XNurta module - Coming soon...")
        st.write("This module will be implemented next.")
    elif page == "📺 DSP XNurta":
        st.info("🚧 DSP XNurta module - Coming soon...")
        st.write("This module will be implemented next.")
    elif page == "📦 FBA Inventory":
        st.info("🚧 FBA Inventory module - Coming soon...")
        st.write("This module will be implemented next.")
    elif page == "🔍 ASIN - Dimension":
        st.info("🚧 ASIN - Dimension module - Coming soon...")
        st.write("This module will be implemented next.")
    elif page == "🚀 Launching - Dimension":
        st.info("🚧 Launching - Dimension module - Coming soon...")
        st.write("This module will be implemented next.")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "📝 **How to use:**\n\n"
        "1. Upload credential.json file\n"
        "2. Enter Google Sheet ID\n"
        "3. Select market (US/CA/UK)\n"
        "4. Upload your Excel files\n"
        "5. Process and choose action\n\n"
        "💡 **File Format:**\n"
        "Files must have DD_MM_YYYY in filename\n"
        "Example: report_15_10_2025.xlsx"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.success(
        "🔒 **Security:**\n\n"
        "Your credentials are only stored\n"
        "in memory during the session\n"
        "and never saved to disk."
    )


if __name__ == "__main__":
    main()