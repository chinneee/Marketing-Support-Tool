import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import io
from datetime import datetime
import pytz
import traceback

class ASINProcessor:
    """ASIN Dimension Data Processor"""
    
    def __init__(self, credentials_dict, sheet_id):
        self.credentials_dict = credentials_dict
        self.sheet_id = sheet_id
        self.worksheet_name = "Dim_ASIN"
        
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        
    def _init_google_sheets(self):
        """Initialize Google Sheets connection"""
        try:
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
                
                # Try to get worksheet, if not exists, create it
                try:
                    self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
                except gspread.exceptions.WorksheetNotFound:
                    self.worksheet = self.spreadsheet.add_worksheet(
                        title=self.worksheet_name,
                        rows="1000",
                        cols="30"
                    )
                    
        except Exception as e:
            raise Exception(f"Error initializing Google Sheets: {e}")
    
    def process_single_file(self, file_content, filename):
        """Process a single file and return DataFrame"""
        try:
            # Try different file formats
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                df = pd.read_excel(io.BytesIO(file_content))
            elif filename.endswith('.csv'):
                # Try different encodings for CSV
                try:
                    df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv(io.BytesIO(file_content), encoding='latin-1')
                    except:
                        df = pd.read_csv(io.BytesIO(file_content), encoding='iso-8859-1')
            elif filename.endswith('.txt'):
                # Try tab-separated first, then comma-separated
                try:
                    df = pd.read_csv(io.BytesIO(file_content), sep='\t', encoding='utf-8')
                except:
                    try:
                        df = pd.read_csv(io.BytesIO(file_content), sep=',', encoding='utf-8')
                    except:
                        df = pd.read_csv(io.BytesIO(file_content), sep='\t', encoding='latin-1')
            else:
                raise ValueError(f"Unsupported file format: {filename}")
            
            df = df.dropna(axis=1, how="all").copy()
            
            # Add Last Updated timestamp
            df["Last Updated"] = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')
            
            return df
        except Exception as e:
            st.error(f"⚠️ Error processing {filename}: {e}")
            return pd.DataFrame()
    
    def clear_and_upload_to_sheets(self, df):
        """Clear existing data and upload new DataFrame to Google Sheets"""
        if df.empty:
            return False
            
        try:
            self._init_google_sheets()
            
            # Clear all data
            self.worksheet.clear()
            
            # Get column names from DataFrame
            columns = df.columns.tolist()
            
            # Update header
            self.worksheet.update(values=[columns], range_name='A1')
            
            # Prepare data
            values_to_append = []
            for _, row in df.iterrows():
                row_values = []
                for col in columns:
                    val = row[col]
                    if pd.isna(val):
                        row_values.append("")
                    elif isinstance(val, (pd.Timestamp, datetime)):
                        row_values.append(f"{val.month}/{val.day}/{val.year}")
                    elif isinstance(val, (float, int)):
                        row_values.append(val)
                    else:
                        row_values.append(str(val))
                values_to_append.append(row_values)
            
            # Upload data starting from row 2
            if values_to_append:
                end_row = len(values_to_append) + 1
                end_col_index = len(columns)
                end_col_letter = gspread.utils.rowcol_to_a1(1, end_col_index).split('1')[0].strip()
                range_name = f"A2:{end_col_letter}{end_row}"
                
                self.worksheet.update(
                    values=values_to_append,
                    range_name=range_name,
                    value_input_option="USER_ENTERED"
                )
            
            return True
            
        except Exception as e:
            raise Exception(f"Error uploading to Google Sheets: {e}")


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


def asin_dimension_page():
    """ASIN Dimension data upload page"""
    
    st.title("🏷️ ASIN Dimension Manager")
    st.markdown("Upload and manage ASIN dimension data")
    
    # Step 1: Upload credentials
    st.subheader("🔐 Step 1: Upload Google Credentials")
    
    credentials_file = st.file_uploader(
        "Upload your credential.json file",
        type=['json'],
        key="asin_credentials_uploader",
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
        return
    
    st.markdown("---")
    
    # Step 2: Enter Sheet ID
    st.subheader("📝 Step 2: Enter Google Sheet ID")
    
    sheet_id = st.text_input(
        "Google Sheet ID",
        value="1GpPsWt_fWCfHnEdFQJIsNBebhqFnIiExsHA8SjNUhFk",
        help="Find this in your Google Sheet URL: docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
    )
    
    if not sheet_id:
        st.warning("⚠️ Please enter Google Sheet ID to continue")
        return
    
    st.markdown("---")
    
    # Step 3: Upload ASIN File
    st.subheader("📂 Step 3: Upload ASIN Dimension File")
    
    uploaded_file = st.file_uploader(
        "Upload ASIN Dimension file",
        type=['xlsx', 'xls', 'csv', 'txt'],
        key="asin_uploader",
        help="Upload ASIN dimension file (Excel, CSV, or Text)"
    )
    
    if uploaded_file:
        # Check if file changed
        if 'asin_filename' not in st.session_state or st.session_state.asin_filename != uploaded_file.name:
            st.session_state.asin_filename = uploaded_file.name
            
            # Process file
            with st.spinner("⚙️ Processing file..."):
                try:
                    processor = ASINProcessor(credentials_dict, sheet_id)
                    file_content = uploaded_file.read()
                    df = processor.process_single_file(file_content, uploaded_file.name)
                    
                    if not df.empty:
                        st.session_state.asin_df = df
                        st.session_state.asin_processor = processor
                        st.success("✅ Processing complete!")
                    else:
                        st.error("❌ No data found in uploaded file")
                        if 'asin_df' in st.session_state:
                            del st.session_state.asin_df
                            del st.session_state.asin_processor
                        
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
                    with st.expander("🔍 Error Details"):
                        st.code(traceback.format_exc())
                    if 'asin_df' in st.session_state:
                        del st.session_state.asin_df
                        del st.session_state.asin_processor
        
        # Display processed data
        if 'asin_df' in st.session_state:
            df = st.session_state.asin_df
            
            st.markdown("---")
            
            # Metrics
            st.subheader("📊 Data Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📦 Total Rows", f"{len(df):,}")
            with col2:
                st.metric("📋 Columns", len(df.columns))
            with col3:
                if 'ASIN' in df.columns:
                    unique_asins = df['ASIN'].nunique() if 'ASIN' in df.columns else len(df)
                    st.metric("🏷️ Unique ASINs", f"{unique_asins:,}")
                else:
                    st.metric("🏷️ Records", f"{len(df):,}")
            with col4:
                completeness = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
                st.metric("✓ Completeness", f"{completeness:.1f}%")
            
            st.markdown("---")
            
            # Preview
            st.subheader("👁️ Data Preview")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                preview_rows = st.slider(
                    "Preview rows",
                    min_value=5,
                    max_value=min(50, len(df)),
                    value=10,
                    step=5,
                    key="asin_preview_slider"
                )
            with col2:
                show_all = st.checkbox("All columns", value=False, key="asin_show_all")
            
            display_df = df if show_all else (df.iloc[:, :8] if len(df.columns) > 8 else df)
            st.dataframe(display_df.head(preview_rows), use_container_width=True, height=300)
            
            if not show_all and len(df.columns) > 8:
                st.caption(f"Showing 8 of {len(df.columns)} columns. Enable 'All columns' to see more.")
            
            st.markdown("---")
            
            # Export Options
            st.subheader("📤 Export & Upload Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📥 Download Locally")
                
                # Excel download
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='ASIN_Dimension')
                output.seek(0)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ASIN_Dimension_{timestamp}.xlsx"
                
                st.download_button(
                    label="💾 Download Excel",
                    data=output,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                # CSV download
                csv = df.to_csv(index=False).encode('utf-8')
                csv_filename = filename.replace('.xlsx', '.csv')
                st.download_button(
                    label="📄 Download CSV",
                    data=csv,
                    file_name=csv_filename,
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                st.markdown("#### ☁️ Upload to Google Sheets")
                
                st.info(f"**Target Sheet:** `Dim_ASIN`\n\n**Rows:** {len(df):,}\n\n**Columns:** {len(df.columns)}")
                
                if st.button("🚀 Push to Google Sheets", 
                            type="primary", 
                            use_container_width=True,
                            key="push_asin_btn"):
                    
                    try:
                        with st.spinner("☁️ Uploading to Google Sheets..."):
                            processor = st.session_state.asin_processor
                            success = processor.clear_and_upload_to_sheets(df)
                        
                        if success:
                            st.success(f"✅ Successfully uploaded {len(df):,} rows to `Dim_ASIN`!")
                            
                            with st.expander("📊 Upload Summary", expanded=True):
                                st.markdown(f"""
                                **Upload Details:**
                                - **Sheet:** `Dim_ASIN`
                                - **Rows uploaded:** {len(df):,}
                                - **Columns:** {len(df.columns)}
                                - **File:** {uploaded_file.name}
                                - **Timestamp:** {datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')}
                                """)
                        else:
                            st.error("❌ Upload failed")
                            
                    except Exception as e:
                        st.error(f"❌ Upload failed: {str(e)}")
                        with st.expander("🔍 Error Details"):
                            st.code(traceback.format_exc())
    
    else:
        st.info("👆 **Upload ASIN Dimension file to get started**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **📌 File Requirements:**
            - Format: `.xlsx`, `.xls`, `.csv`, or `.txt`
            - Must contain ASIN dimension data
            - Text files can be tab or comma separated
            """)
        
        with col2:
            st.markdown("""
            **⚡ How it works:**
            1. Upload your ASIN dimension file
            2. Data is automatically validated
            3. Preview processed data
            4. Download locally or push to Google Sheets
            
            **Note:** Data will be uploaded to sheet `Dim_ASIN`
            """)


# Main execution
if __name__ == "__main__":
    asin_dimension_page()