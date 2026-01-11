import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import io
from datetime import datetime
import pytz
import traceback

class LaunchingProcessor:
    """Launching Data Processor"""
    
    def __init__(self, credentials_dict, sheet_id):
        self.credentials_dict = credentials_dict
        self.sheet_id = sheet_id
        self.worksheet_name = "Launching"
        
        # Định nghĩa thứ tự cột chuẩn từ A đến P
        self.standard_columns = [
            'Launching', 'Ads', 'Idea', 'Qty', 'Start', 'End', 'Progress',
            'Link Idea', 'Link', 'Quy Trình', 'Đánh giá', 'Parent items',
            'Item', 'ASIN', 'ASIN (Item)', 'ID'
        ]
        
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
    
    def _standardize_columns(self, df):
        """Standardize and map columns to standard column order"""
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        
        # Create mapping from uploaded columns to standard columns
        column_mapping = {}
        for std_col in self.standard_columns:
            std_col_lower = std_col.lower()
            for df_col in df.columns:
                df_col_lower = df_col.lower()
                
                # Exact match
                if std_col_lower == df_col_lower:
                    column_mapping[df_col] = std_col
                    break
                # Handle common variations
                elif 'parent' in std_col_lower and 'item' in std_col_lower and 'parent' in df_col_lower and 'item' in df_col_lower:
                    column_mapping[df_col] = std_col
                    break
                elif 'asin' in std_col_lower and 'item' in std_col_lower and 'asin' in df_col_lower and 'item' in df_col_lower:
                    column_mapping[df_col] = std_col
                    break
        
        # Rename columns based on mapping
        df = df.rename(columns=column_mapping)
        
        # Create result dataframe with standard columns
        result_df = pd.DataFrame()
        for col in self.standard_columns:
            if col in df.columns:
                result_df[col] = df[col]
            else:
                result_df[col] = pd.NA
        
        return result_df
    
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
            
            # Standardize columns to A-P format
            df = self._standardize_columns(df)
            
            return df
        except Exception as e:
            st.error(f"⚠️ Error processing {filename}: {e}")
            return pd.DataFrame()
    
    def clear_and_upload_to_sheets(self, df):
        """Clear columns A to P and upload new DataFrame to Google Sheets"""
        if df.empty:
            return False
            
        try:
            self._init_google_sheets()
            
            # Clear only columns A to P (16 columns)
            # Get current row count to clear all data in these columns
            all_values = self.worksheet.get_all_values()
            total_rows = len(all_values) if all_values else 1000
            
            # Clear range A1:P{total_rows}
            clear_range = f"A1:P{total_rows}"
            self.worksheet.batch_clear([clear_range])
            
            # Update header (A1:P1)
            self.worksheet.update(values=[self.standard_columns], range_name='A1:P1')
            
            # Prepare data
            values_to_append = []
            for _, row in df.iterrows():
                row_values = []
                for col in self.standard_columns:
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
            
            # Upload data starting from row 2 (A2:P{end_row})
            if values_to_append:
                end_row = len(values_to_append) + 1
                range_name = f"A2:P{end_row}"
                
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


def launching_dimension_page():
    """Launching data upload page"""
    
    st.title("🚀 Launching Manager")
    st.markdown("Upload and manage product launching data")
    
    # Step 1: Upload credentials
    st.subheader("🔐 Step 1: Upload Google Credentials")
    
    credentials_file = st.file_uploader(
        "Upload your credential.json file",
        type=['json'],
        key="launching_credentials_uploader",
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
        value="1b9gXvoAaoPqY4HGxAmnOpyv1pujnT9enYpshz90PyJs",
        help="Find this in your Google Sheet URL: docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
    )
    
    if not sheet_id:
        st.warning("⚠️ Please enter Google Sheet ID to continue")
        return
    
    st.markdown("---")
    
    # Step 3: Upload Launching File
    st.subheader("📂 Step 3: Upload Launching File")
    
    uploaded_file = st.file_uploader(
        "Upload Launching file",
        type=['xlsx', 'xls', 'csv', 'txt'],
        key="launching_uploader",
        help="Upload launching data file (Excel, CSV, or Text)"
    )
    
    if uploaded_file:
        # Check if file changed
        if 'launching_filename' not in st.session_state or st.session_state.launching_filename != uploaded_file.name:
            st.session_state.launching_filename = uploaded_file.name
            
            # Process file
            with st.spinner("⚙️ Processing file..."):
                try:
                    processor = LaunchingProcessor(credentials_dict, sheet_id)
                    file_content = uploaded_file.read()
                    df = processor.process_single_file(file_content, uploaded_file.name)
                    
                    if not df.empty:
                        st.session_state.launching_df = df
                        st.session_state.launching_processor = processor
                        st.success("✅ Processing complete!")
                    else:
                        st.error("❌ No data found in uploaded file")
                        if 'launching_df' in st.session_state:
                            del st.session_state.launching_df
                            del st.session_state.launching_processor
                        
                except Exception as e:
                    st.error(f"❌ Error processing file: {str(e)}")
                    with st.expander("🔍 Error Details"):
                        st.code(traceback.format_exc())
                    if 'launching_df' in st.session_state:
                        del st.session_state.launching_df
                        del st.session_state.launching_processor
        
        # Display processed data
        if 'launching_df' in st.session_state:
            df = st.session_state.launching_df
            
            st.markdown("---")
            
            # Metrics
            st.subheader("📊 Data Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📦 Total Products", f"{len(df):,}")
            with col2:
                st.metric("📋 Columns (A-P)", "16")
            with col3:
                if 'ASIN' in df.columns:
                    unique_asins = df['ASIN'].nunique() if pd.notna(df['ASIN']).any() else 0
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
                    key="launching_preview_slider"
                )
            with col2:
                show_all = st.checkbox("All columns", value=True, key="launching_show_all")
            
            display_df = df if show_all else df.iloc[:, :8]
            st.dataframe(display_df.head(preview_rows), use_container_width=True, height=300)
            
            if not show_all:
                st.caption(f"Showing 8 of 16 columns. Enable 'All columns' to see more.")
            
            # Show column mapping info
            with st.expander("📋 Column Structure (A to P)", expanded=False):
                st.markdown("""
                **Standard Column Order:**
                
                | Col | Name | Col | Name |
                |-----|------|-----|------|
                | A | Launching | I | Link |
                | B | Ads | J | Quy Trình |
                | C | Idea | K | Đánh giá |
                | D | Qty | L | Parent items |
                | E | Start | M | Item |
                | F | End | N | ASIN |
                | G | Progress | O | ASIN (Item) |
                | H | Link Idea | P | ID |
                """)
            
            st.markdown("---")
            
            # Export Options
            st.subheader("📤 Export & Upload Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📥 Download Locally")
                
                # Excel download
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Launching')
                output.seek(0)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"Launching_{timestamp}.xlsx"
                
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
                
                st.info(f"**Target Sheet:** `Launching`\n\n**Rows:** {len(df):,}\n\n**Columns:** A to P (16 columns)\n\n⚠️ **Note:** Only columns A-P will be cleared and updated")
                
                if st.button("🚀 Push to Google Sheets", 
                            type="primary", 
                            use_container_width=True,
                            key="push_launching_btn"):
                    
                    try:
                        with st.spinner("☁️ Uploading to Google Sheets..."):
                            processor = st.session_state.launching_processor
                            success = processor.clear_and_upload_to_sheets(df)
                        
                        if success:
                            st.success(f"✅ Successfully uploaded {len(df):,} rows to `Launching` (columns A-P)!")
                            
                            with st.expander("📊 Upload Summary", expanded=True):
                                st.markdown(f"""
                                **Upload Details:**
                                - **Sheet:** `Launching`
                                - **Range:** A1:P{len(df) + 1}
                                - **Rows uploaded:** {len(df):,}
                                - **Columns:** 16 (A to P)
                                - **File:** {uploaded_file.name}
                                - **Timestamp:** {datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')}
                                
                                **Note:** Other columns (Q onwards) remain unchanged.
                                """)
                        else:
                            st.error("❌ Upload failed")
                            
                    except Exception as e:
                        st.error(f"❌ Upload failed: {str(e)}")
                        with st.expander("🔍 Error Details"):
                            st.code(traceback.format_exc())
    
    else:
        st.info("👆 **Upload Launching file to get started**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **📌 File Requirements:**
            - Format: `.xlsx`, `.xls`, `.csv`, or `.txt`
            - Must contain launching data
            - Text files can be tab or comma separated
            - Columns will be mapped to A-P structure
            """)
        
        with col2:
            st.markdown("""
            **⚡ How it works:**
            1. Upload your launching file
            2. Data is mapped to columns A-P
            3. Preview standardized data
            4. Download locally or push to Google Sheets
            
            **Note:** Only columns A-P will be cleared and updated. Other columns (Q onwards) remain unchanged.
            """)


# Main execution
if __name__ == "__main__":
    launching_dimension_page()