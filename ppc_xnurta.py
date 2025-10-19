import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import io
import json
import re
import traceback
import warnings

# Suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)

class PPCProcessor:
    """PPC XNurta Data Processor"""
    
    def __init__(self, credentials_dict, sheet_id, market):
        self.credentials_dict = credentials_dict
        self.sheet_id = sheet_id
        self.market = market
        self.worksheet_name = f"Raw_XN_Q4_2025_{market}"
        
        # Define standard columns (from your original code)
        self.required_columns = [
            'ASIN', 'Date', 'Campaign type', 'Campaign', 'Status', 'Country', 'Portfolio',
            'Daily Budget', 'Bidding Strategy', 'Top-of-search IS', 'Avg.time in Budget',
            'Impressions', 'Clicks', 'CTR', 'Spend', 'CPC', 'Orders', 'Sales', 'Units', 'CVR'
        ]
        
        # Columns to drop
        self.columns_to_drop = [
            'Profile', 'Labels', 'Budget group', 'ACOS', 'ROAS', 'CPA', 
            'Sales Same SKU', 'Sales Other SKU', 'Orders Same SKU', 'Orders Other SKU', 
            'Units Same SKU', 'Units Other SKU', 'Target type', 'Current Budget', 
            'SP Off-site Ads Strategy'
        ]
        
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
    
    def _init_google_sheets(self):
        """Initialize Google Sheets connection"""
        try:
            if self.client is None:
                st.info(f"🔄 Connecting to Google Sheets: {self.sheet_id}")
                st.info(f"📋 Looking for worksheet: {self.worksheet_name}")
                
                scopes = [
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive"
                ]
                creds = Credentials.from_service_account_info(
                    self.credentials_dict, scopes=scopes
                )
                self.client = gspread.authorize(creds)
                self.spreadsheet = self.client.open_by_key(self.sheet_id)
                
                try:
                    self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
                    st.success(f"✅ Found worksheet: {self.worksheet_name}")
                except gspread.exceptions.WorksheetNotFound:
                    st.warning(f"⚠️ Worksheet '{self.worksheet_name}' not found. Creating new one...")
                    self.worksheet = self.spreadsheet.add_worksheet(
                        title=self.worksheet_name,
                        rows="1000",
                        cols="30"
                    )
                    self.worksheet.update(values=[self.required_columns], range_name='A1')
                    st.success(f"✅ Created new worksheet: {self.worksheet_name}")
                    
        except Exception as e:
            st.error(f"❌ Error initializing Google Sheets: {e}")
            st.text(traceback.format_exc())
            raise
    
    def extract_date_from_filename(self, filename):
        """Extract date from filename with multiple patterns"""
        patterns = [
            r'SA_Campaign_List_(\d{8})_\d{8}_.*\.xlsx',
            r'(\d{8})',
            r'(\d{2}_\d{2}_\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                try:
                    if '_' in date_str:
                        return pd.to_datetime(date_str, format='%d_%m_%Y')
                    elif '-' in date_str:
                        return pd.to_datetime(date_str, format='%Y-%m-%d')
                    else:
                        return pd.to_datetime(date_str, format='%Y%m%d')
                except:
                    continue
        
        # Fallback: use current date
        return pd.to_datetime(datetime.now().date())
    
    def safe_extract_asin_from_portfolio(self, portfolio_str):
        """Extract ASIN from Portfolio string"""
        if pd.isna(portfolio_str) or portfolio_str == '':
            return portfolio_str
        
        try:
            portfolio_str = str(portfolio_str).strip()
            
            # Pattern 1: B + 9 alphanumeric
            pattern1 = r'B[A-Z0-9]{9}'
            match1 = re.search(pattern1, portfolio_str.upper())
            if match1:
                return match1.group()
            
            # Pattern 2: Any 10 consecutive alphanumeric
            pattern2 = r'[A-Z0-9]{10}'
            match2 = re.search(pattern2, portfolio_str.upper())
            if match2:
                return match2.group()
            
            # Pattern 3: Extract first 10 alphanumeric
            clean_str = re.sub(r'[^A-Za-z0-9]', '', portfolio_str)
            if len(clean_str) >= 10:
                return clean_str[:10].upper()
            
            return portfolio_str
        except Exception as e:
            return portfolio_str
    
    def safe_normalize_campaign_types(self, text):
        """Normalize campaign type keywords"""
        if pd.isna(text) or text == '':
            return text
        
        try:
            text = str(text)
            normalizations = {
                'sponsoredBrands': 'SB',
                'sponsoredDisplay': 'SD', 
                'sponsoredProducts': 'SP',
                'sponsoredbrands': 'SB',
                'sponsoreddisplay': 'SD',
                'sponsoredproducts': 'SP',
                'Sponsored Brands': 'SB',
                'Sponsored Display': 'SD',
                'Sponsored Products': 'SP'
            }
            
            for original, normalized in normalizations.items():
                text = text.replace(original, normalized)
            
            return text
        except Exception as e:
            return text
    
    def safe_clean_currency_column(self, column):
        """Remove $ symbol and convert to float"""
        if column.dtype == 'object':
            try:
                cleaned = column.astype(str).str.replace(r'[C$,]', '', regex=True)
                cleaned = cleaned.replace(['', 'nan', 'NaN', '--', 'N/A'], np.nan)
                result = pd.to_numeric(cleaned, errors='coerce')
                return result
            except:
                return column
        return column
    
    def safe_convert_to_float(self, column):
        """Convert to float"""
        if column.dtype == 'object':
            try:
                cleaned = column.astype(str).str.replace(r'[%,]', '', regex=True)
                cleaned = cleaned.replace(['', 'nan', 'NaN', '--', 'N/A'], np.nan)
                result = pd.to_numeric(cleaned, errors='coerce')
                return result
            except:
                return column
        return column
    
    def safe_convert_to_int(self, column):
        """Convert to int"""
        if column.dtype == 'object':
            try:
                cleaned = column.astype(str).str.replace(r'[,]', '', regex=True)
                cleaned = cleaned.replace(['', 'nan', 'NaN', '--', 'N/A'], np.nan)
                float_col = pd.to_numeric(cleaned, errors='coerce')
                return float_col.astype('Int64')
            except:
                return column
        return column
    
    def process_single_excel(self, file_content, filename):
        """Process a single Excel file"""
        try:
            df = pd.read_excel(io.BytesIO(file_content))
            df = df.dropna(axis=0, how='all').dropna(axis=1, how='all').copy()
            
            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Extract date
            date_extracted = self.extract_date_from_filename(filename)
            
            # Drop unwanted columns
            existing_columns_to_drop = [col for col in self.columns_to_drop if col in df.columns]
            if existing_columns_to_drop:
                df = df.drop(columns=existing_columns_to_drop)
            
            # Create ASIN column
            if 'Portfolio' in df.columns:
                asin_values = df['Portfolio'].apply(self.safe_extract_asin_from_portfolio)
            else:
                asin_values = [None] * len(df)
            
            # Normalize campaign types
            if 'Campaign type' in df.columns:
                df['Campaign type'] = df['Campaign type'].apply(self.safe_normalize_campaign_types)
            
            # Clean currency columns
            currency_columns = ['Daily Budget', 'Spend', 'Sales']
            for col in currency_columns:
                if col in df.columns:
                    df[col] = self.safe_clean_currency_column(df[col])
            
            # Convert float columns
            float_columns = ['Avg.time in Budget', 'Top-of-search IS', 'CPC', 'CVR', 'CTR']
            for col in float_columns:
                if col in df.columns:
                    df[col] = self.safe_convert_to_float(df[col])
            
            # Convert int columns
            int_columns = ['Impressions', 'Clicks', 'Orders', 'Units']
            for col in int_columns:
                if col in df.columns:
                    df[col] = self.safe_convert_to_int(df[col])
            
            # Create ordered DataFrame
            ordered_df = pd.DataFrame()
            ordered_df['ASIN'] = asin_values
            ordered_df['Date'] = [date_extracted] * len(df)
            
            # Add required columns
            for col in self.required_columns[2:]:
                if col in df.columns:
                    ordered_df[col] = df[col]
                else:
                    ordered_df[col] = np.nan
            
            return ordered_df
            
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
            non_empty_dataframes = [df for df in all_dataframes if not df.empty and len(df) > 0]
            
            if non_empty_dataframes:
                merged_df = pd.concat(non_empty_dataframes, ignore_index=True, sort=False)
                
                # Remove duplicates
                if 'ASIN' in merged_df.columns and 'Campaign' in merged_df.columns and 'Date' in merged_df.columns:
                    original_rows = len(merged_df)
                    merged_df = merged_df.drop_duplicates(subset=['ASIN', 'Date', 'Campaign'], keep='last')
                    removed = original_rows - len(merged_df)
                    if removed > 0:
                        st.info(f"🔄 Removed {removed} duplicate rows")
                
                # Sort by Date and Sales
                try:
                    if 'Date' in merged_df.columns and 'Sales' in merged_df.columns:
                        merged_df = merged_df.sort_values(['Date', 'Sales'], ascending=[True, False])
                    elif 'Date' in merged_df.columns:
                        merged_df = merged_df.sort_values('Date')
                except:
                    pass
                
                return merged_df, processed_files
            else:
                st.warning("⚠️ All uploaded files are empty or invalid.")
                return pd.DataFrame(), []
        else:
            return pd.DataFrame(), []
    
    def get_existing_sheet_data_count(self):
        """Get current number of rows in the sheet"""
        try:
            all_values = self.worksheet.col_values(1)
            data_rows = len([val for val in all_values if val.strip()]) - 1 if all_values else 0
            st.info(f"📊 Existing rows in sheet: {data_rows}")
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
            st.info(f"📤 Starting upload of {len(df)} rows...")
            
            self._init_google_sheets()
            existing_rows = self.get_existing_sheet_data_count()
            start_row = max(existing_rows + 2, 2)
            
            st.info(f"📍 Will upload to row {start_row}")
            
            # Prepare values
            safe_df = df.copy()
            
            # Format datetime columns
            datetime_cols = safe_df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns
            for col in datetime_cols:
                safe_df[col] = safe_df[col].apply(lambda x: f"{x.month}/{x.day}/{x.year}" if pd.notna(x) else "")
            
            # Replace NaN with empty string
            safe_df = safe_df.fillna("")
            
            # Convert to list of lists
            values_to_append = safe_df.values.tolist()
            
            # Ensure sheet has enough rows
            needed_rows = start_row + len(values_to_append) - 1
            if needed_rows > self.worksheet.row_count:
                add_count = needed_rows - self.worksheet.row_count
                st.info(f"📈 Adding {add_count} new rows to sheet...")
                self.worksheet.add_rows(add_count)
            
            # Calculate range
            end_col_index = len(self.required_columns)
            end_col_letter = gspread.utils.rowcol_to_a1(1, end_col_index).split('1')[0].strip()
            end_row = start_row + len(df) - 1
            range_name = f"A{start_row}:{end_col_letter}{end_row}"
            
            st.info(f"📊 Uploading to range: {range_name}")
            
            # Upload with USER_ENTERED to auto-detect data types
            self.worksheet.update(
                values=values_to_append, 
                range_name=range_name,
                value_input_option='USER_ENTERED'
            )
            
            st.success(f"✅ Successfully uploaded {len(df)} rows!")
            return True
            
        except Exception as e:
            st.error(f"❌ Error uploading to Google Sheets: {e}")
            st.text(traceback.format_exc())
            return False

def load_credentials_from_file(uploaded_file):
    """Load Google Sheets credentials from uploaded JSON file"""
    try:
        credentials_dict = json.load(uploaded_file)
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

def ppc_xnurta_page():
    """PPC XNurta data upload page"""
    
    # Step 1: Upload credentials
    st.subheader("🔐 Step 1: Upload Google Credentials")
    
    credentials_file = st.file_uploader(
        "Upload your credential.json file",
        type=['json'],
        key="ppc_credentials_uploader",
        help="Upload your Google Service Account credentials JSON file"
    )
    
    credentials_dict = None
    if credentials_file:
        credentials_dict = load_credentials_from_file(credentials_file)
        if credentials_dict:
            st.success("✅ Credentials loaded successfully!")
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
        value="1rqH3SePVbpwcj1oD4Bqaa40IbkyKUi7aRBThlBdnEu4",
        help="Find this in your Google Sheet URL"
    )
    
    if not sheet_id:
        st.warning("⚠️ Please enter Google Sheet ID to continue")
        return
    
    st.markdown("---")
    
    # Step 3: Select Market
    st.subheader("🌍 Step 3: Select Market")
    
    if 'ppc_selected_market' not in st.session_state:
        st.session_state.ppc_selected_market = "US"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🇺🇸 US Market", width="stretch", key="ppc_us",
                    type="primary" if st.session_state.ppc_selected_market == "US" else "secondary"):
            st.session_state.ppc_selected_market = "US"
    with col2:
        if st.button("🇨🇦 CA Market", width="stretch", key="ppc_ca",
                    type="primary" if st.session_state.ppc_selected_market == "CA" else "secondary"):
            st.session_state.ppc_selected_market = "CA"
    with col3:
        if st.button("🇬🇧 UK Market", width="stretch", key="ppc_uk",
                    type="primary" if st.session_state.ppc_selected_market == "UK" else "secondary"):
            st.session_state.ppc_selected_market = "UK"
    
    selected_market = st.session_state.ppc_selected_market
    st.info(f"📍 Selected Market: **{selected_market}**")
    
    st.markdown("---")
    
   # Combined Step: Upload, Process & Export Data Files
    st.subheader("📂 Step 4: Upload, Process & Export Data")
    
    uploaded_files = st.file_uploader(
        "Upload Excel files (DD_MM_YYYY format in filename)",
        type=['xlsx'],
        accept_multiple_files=True,
        key="ppc_uploader",
        help="Files are processed automatically upon upload"
    )
    
    if uploaded_files:
        # File upload success indicator
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully")
        with col2:
            total_size = sum(f.size for f in uploaded_files) / (1024 * 1024)  # Convert to MB
            st.metric("Total Size", f"{total_size:.2f} MB")

        # Auto-process files
        current_file_names = [f.name for f in uploaded_files]
        
        # Initialize session state
        if 'last_processed_files' not in st.session_state:
            st.session_state.last_processed_files = []
        
        # Process if files changed
        if current_file_names != st.session_state.last_processed_files:
            # Processing section
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            with status_placeholder.container():
                st.markdown("### ⚙️ Processing Files...")
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            try:
                # Simulate progress steps
                status_text.text("Initializing processor...")
                progress_bar.progress(20)
                
                processor = PPCProcessor(credentials_dict, sheet_id, selected_market)
                
                status_text.text("Reading and validating files...")
                progress_bar.progress(40)
                
                result_df, processed_files = processor.process_files(uploaded_files)
                
                status_text.text("Finalizing data...")
                progress_bar.progress(80)
                
                # Store in session state
                st.session_state.result_df = result_df
                st.session_state.processor = processor
                st.session_state.processed_files = processed_files
                st.session_state.last_processed_files = current_file_names
                
                progress_bar.progress(100)
                status_text.text("✅ Processing complete!")
                
                # Clear progress indicators after a moment
                import time
                time.sleep(0.5)
                status_placeholder.empty()
                
                if not result_df.empty:
                    # Success message with metrics
                    st.success(f"✅ Successfully processed {len(processed_files)} file(s)")
                    
                    # Key metrics in cards
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📊 Total Rows", f"{len(result_df):,}")
                    with col2:
                        st.metric("📝 Columns", len(result_df.columns))
                    with col3:
                        st.metric("📁 Files", len(processed_files))
                    with col4:
                        # Calculate data completeness
                        completeness = (1 - result_df.isnull().sum().sum() / (len(result_df) * len(result_df.columns))) * 100
                        st.metric("✓ Completeness", f"{completeness:.1f}%")
                    
                else:
                    st.error("❌ No data found in uploaded files")
                    st.warning("Please verify your files contain data in the expected format.")
                    
            except Exception as e:
                status_placeholder.empty()
                st.error(f"❌ Error processing files: {str(e)}")
                st.exception(e)
                # Clear session state on error
                for key in ['result_df', 'processor', 'processed_files', 'last_processed_files']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.session_state.last_processed_files = []
        
        # Display processed data and export options
        if 'result_df' in st.session_state and not st.session_state.result_df.empty:
            result_df = st.session_state.result_df
            processed_files = st.session_state.processed_files
            
            # Preview controls in one row
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                preview_rows = st.slider(
                    "Preview rows",
                    min_value=5,
                    max_value=min(50, len(result_df)),
                    value=10,
                    step=5
                )
            with col2:
                show_all = st.checkbox("All columns", value=False)

            
            # Display dataframe
            display_df = result_df if show_all else (result_df.iloc[:, :8] if len(result_df.columns) > 8 else result_df)
            st.dataframe(
                display_df.head(preview_rows),
                use_container_width=True,
                height=300
            )
            
            if not show_all and len(result_df.columns) > 8:
                st.caption(f"Showing 8 of {len(result_df.columns)} columns. Enable 'All columns' to see more.")
            
            st.markdown("---")
            
            # Export section - Simplified and prominent
            st.markdown("### 📤 Export Options")
            st.caption("Choose how to save or upload your processed data")
            
            # Helper function for Excel export
            def export_to_excel(df, market):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Data')
                output.seek(0)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                return output, f"XN_{market}_{timestamp}.xlsx"
            
            # Export buttons in a clean layout
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📥 Download Locally")
                st.caption("Save processed data to your computer")
                
                # Excel download
                excel_data, filename = export_to_excel(result_df, selected_market)
                st.download_button(
                    label="💾 Download Excel",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help="Download as Excel file (.xlsx)"
                )
                
                # CSV download
                csv = result_df.to_csv(index=False).encode('utf-8')
                csv_filename = filename.replace('.xlsx', '.csv')
                st.download_button(
                    label="📄 Download CSV",
                    data=csv,
                    file_name=csv_filename,
                    mime="text/csv",
                    use_container_width=True,
                    help="Download as CSV file (lighter format)"
                )
            
            with col2:
                st.markdown("#### ☁️ Upload to Cloud")
                st.caption("Push data directly to Google Sheets")
                
                # Info box
                st.info(f"**Target:** {selected_market} market sheet\n\n**Rows:** {len(result_df):,}")
                
                # Upload button - prominent and clear
                if st.button(
                    "🚀 Push to Google Sheets",
                    type="primary",
                    use_container_width=True,
                    help="Upload data to your Google Sheets"
                ):
                    upload_placeholder = st.empty()
                    
                    with upload_placeholder.container():
                        st.markdown("---")
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        try:
                            status_text.text("Connecting to Google Sheets...")
                            progress_bar.progress(25)
                            
                            status_text.text("Uploading data...")
                            progress_bar.progress(50)
                            
                            success = st.session_state.processor.append_to_sheets(result_df)
                            
                            status_text.text("Verifying upload...")
                            progress_bar.progress(90)
                            
                            if success:
                                progress_bar.progress(100)
                                status_text.text("✅ Upload complete!")
                                time.sleep(0.5)
                                upload_placeholder.empty()
                                
                                st.success(f"✅ Successfully uploaded {len(result_df):,} rows to Google Sheets!")
                                st.balloons()
                                
                                # Show success details
                                with st.expander("📊 Upload Summary", expanded=True):
                                    st.markdown(f"""
                                    - **Market:** {selected_market}
                                    - **Rows uploaded:** {len(result_df):,}
                                    - **Columns:** {len(result_df.columns)}
                                    - **Files processed:** {len(processed_files)}
                                    - **Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                                    """)
                            else:
                                upload_placeholder.empty()
                                st.error("❌ Upload failed - Please check the error messages above")
                                
                        except Exception as e:
                            upload_placeholder.empty()
                            st.error(f"❌ Upload failed: {str(e)}")
                            with st.expander("🔍 Error Details"):
                                st.code(traceback.format_exc())
            
    else:
        # Empty state with helpful instructions
        st.info("👆 **Upload Excel files to get started**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **📌 File Requirements:**
            - Format: `.xlsx` (Excel 2007+)
            - Filename must contain: `DD_MM_YYYY`
            - Example: `sales_report_15_10_2025.xlsx`
            """)
        
        with col2:
            st.markdown("""
            **⚡ What happens next:**
            1. Files are validated
            2. Data is automatically processed
            3. Preview & export options appear
            4. Choose download or upload to Sheets
            """)
        