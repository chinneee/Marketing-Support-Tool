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
            merged_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
            
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


def load_credentials():
    """Load Google Sheets credentials from Streamlit secrets"""
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        return credentials_dict
    except Exception as e:
        st.error(f"❌ Error loading credentials: {e}")
        return None


def sellerboard_page():
    """Sellerboard data upload page"""
    st.header("📊 Sellerboard Data Upload")
    
    # Market selection
    col1, col2, col3 = st.columns(3)
    with col1:
        market_us = st.button("🇺🇸 US Market", use_container_width=True, type="primary")
    with col2:
        market_ca = st.button("🇨🇦 CA Market", use_container_width=True)
    with col3:
        market_uk = st.button("🇬🇧 UK Market", use_container_width=True)
    
    # Determine selected market
    if market_ca:
        selected_market = "CA"
    elif market_uk:
        selected_market = "UK"
    else:
        selected_market = "US"
    
    st.info(f"📍 Selected Market: **{selected_market}**")
    
    # File upload
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
        
        # Process button
        if st.button("🔄 Process Files", type="primary", use_container_width=True):
            with st.spinner("Processing files..."):
                # Load credentials
                credentials = load_credentials()
                if not credentials:
                    st.error("❌ Failed to load credentials")
                    return
                
                # Get sheet ID from secrets
                sheet_id = st.secrets.get("sheet_id", "")
                
                # Initialize processor
                processor = SBProcessor(credentials, sheet_id, selected_market)
                
                # Process files
                result_df, processed_files = processor.process_files(uploaded_files)
                
                if not result_df.empty:
                    st.success(f"✅ Successfully processed {len(processed_files)} files")
                    st.info(f"📊 Total rows: {len(result_df)}")
                    
                    # Preview data
                    with st.expander("👁️ Preview Data (First 10 rows)"):
                        st.dataframe(result_df.head(10))
                    
                    # Action selection
                    st.subheader("📤 Select Action")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📥 Export to Excel", use_container_width=True):
                            # Create Excel file
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                result_df.to_excel(writer, index=False, sheet_name='Data')
                            output.seek(0)
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            st.download_button(
                                label="⬇️ Download Excel",
                                data=output,
                                file_name=f"SB_{selected_market}_{timestamp}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    
                    with col2:
                        if st.button("☁️ Push to Google Sheets", use_container_width=True):
                            with st.spinner("Uploading to Google Sheets..."):
                                success = processor.append_to_sheets(result_df)
                                if success:
                                    st.success(f"✅ Successfully uploaded {len(result_df)} rows!")
                                else:
                                    st.error("❌ Upload failed")
                    
                    with col3:
                        if st.button("📤 Both Excel & Sheets", use_container_width=True):
                            # Excel download
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                result_df.to_excel(writer, index=False, sheet_name='Data')
                            output.seek(0)
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            st.download_button(
                                label="⬇️ Download Excel",
                                data=output,
                                file_name=f"SB_{selected_market}_{timestamp}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            
                            # Google Sheets upload
                            with st.spinner("Uploading to Google Sheets..."):
                                success = processor.append_to_sheets(result_df)
                                if success:
                                    st.success(f"✅ Successfully uploaded {len(result_df)} rows!")
                                else:
                                    st.error("❌ Upload failed")
                else:
                    st.error("❌ No data to process")


def main():
    st.set_page_config(
        page_title="Marketing Data Upload Tool",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🚀 Marketing Data Upload Tool")
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("📋 Navigation")
    
    page = st.sidebar.radio(
        "Select Tool:",
        [
            "📊 Sellerboard",
            "💰 PPC XNurta",
            "📺 DSP XNurta",
            "📦 FBA Inventory",
            "🔍 ASIN - Dimension",
            "🚀 Launching - Dimension"
        ]
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
        "1. Select a tool from the menu\n"
        "2. Choose market (for SB/PPC/DSP)\n"
        "3. Upload your Excel files\n"
        "4. Process and choose action\n\n"
        "💡 Files must have DD_MM_YYYY format in filename"
    )


if __name__ == "__main__":
    main()