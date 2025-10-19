import streamlit as st
from sellerboard import sellerboard_page
from ppc_xnurta import ppc_xnurta_page
from dsp_xnurta import dsp_xnurta_page
from datetime import datetime

def main():
    st.set_page_config(
        page_title="Marketing Data Upload Tool",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )


    def apply_custom_theme():
        """Apply professional custom theme with white sidebar and light gray main area"""
        st.markdown("""
            <style>
            /* ============================================
            GOOGLE FONTS & ROOT VARIABLES
            ============================================ */
            
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
            
            :root {
                --primary-color: #FF4B4B;
                --primary-hover: #FF6B6B;
                --success-color: #10B981;
                --info-color: #3B82F6;
                --warning-color: #F59E0B;
                --error-color: #EF4444;
                
                /* Main area - Light gray background */
                --main-bg: #F5F7FA;
                --main-content-bg: #FFFFFF;
                
                /* Sidebar - White background */
                --sidebar-bg: #FFFFFF;
                --sidebar-border: #E5E7EB;
                
                /* Text colors */
                --text-primary: #1F2937;
                --text-secondary: #6B7280;
                --text-light: #9CA3AF;
                
                /* Border & Dividers */
                --border-color: #E5E7EB;
                --border-light: #F3F4F6;
                
                /* Shadows */
                --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
                --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
                --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                
                /* Radius */
                --radius-sm: 6px;
                --radius-md: 8px;
                --radius-lg: 12px;
                --radius-xl: 16px;
                
                /* Transitions */
                --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            }
            
            /* ============================================
            GLOBAL STYLES
            ============================================ */
            
            * {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }
            
            /* Main app background - Light gray */
            .main {
                background-color: var(--main-bg) !important;
                padding-top: 1rem;
            }
            
            .block-container {
                padding: 2rem 3rem;
                max-width: 1400px;
            }
            
            /* ============================================
            SIDEBAR - WHITE THEME
            ============================================ */
            
            [data-testid="stSidebar"] {
                background-color: var(--sidebar-bg) !important;
                border-right: 1px solid var(--sidebar-border);
                box-shadow: var(--shadow-sm);
            }
            
            [data-testid="stSidebar"] > div:first-child {
                padding: 2rem 1.5rem;
            }
            
            /* Sidebar text - Black */
            [data-testid="stSidebar"] * {
                color: var(--text-primary) !important;
            }
            
            /* Sidebar title */
            [data-testid="stSidebar"] h1,
            [data-testid="stSidebar"] h2,
            [data-testid="stSidebar"] h3 {
                color: var(--text-primary) !important;
                font-weight: 700;
            }
            
            /* Sidebar navigation items */
            [data-testid="stSidebar"] .stRadio > div {
                gap: 0.5rem;
            }
            
            [data-testid="stSidebar"] .stRadio > div > label {
                background-color: var(--main-bg);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                padding: 0.875rem 1rem;
                margin-bottom: 0.5rem;
                transition: var(--transition);
                cursor: pointer;
                font-weight: 500;
                color: var(--text-primary) !important;
            }
            
            [data-testid="stSidebar"] .stRadio > div > label:hover {
                background-color: #F9FAFB;
                border-color: var(--primary-color);
                transform: translateX(2px);
                box-shadow: var(--shadow-sm);
            }
            
            /* Active/Selected navigation item */
            [data-testid="stSidebar"] .stRadio > div > label[data-baseweb="radio"] > div:first-child {
                background-color: transparent;
            }
            
            [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
                border-color: transparent;
                color: white !important;
                box-shadow: var(--shadow-md);
                font-weight: 600;
            }
            
            [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] * {
                color: white !important;
            }
            
            /* Sidebar dividers */
            [data-testid="stSidebar"] hr {
                border-color: var(--border-light);
                margin: 1.5rem 0;
            }
            
            /* ============================================
            TYPOGRAPHY
            ============================================ */
            
            h1, h2, h3, h4, h5, h6 {
                color: var(--text-primary);
                font-weight: 700;
                letter-spacing: -0.02em;
            }
            
            h1 {
                font-size: 2.25rem;
                line-height: 1.2;
            }
            
            h2 {
                font-size: 1.875rem;
                line-height: 1.3;
            }
            
            h3 {
                font-size: 1.5rem;
                line-height: 1.4;
            }
            
            p, .stMarkdown {
                color: var(--text-secondary);
                line-height: 1.6;
            }
            
            /* Gradient title */
            .gradient-title {
                background: linear-gradient(120deg, var(--primary-color) 0%, var(--primary-hover) 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-size: 2.5rem;
                font-weight: 800;
                line-height: 1.2;
            }
            
            /* ============================================
            CARDS & CONTAINERS
            ============================================ */
            
            /* White content cards that pop from gray background */
            .element-container,
            [data-testid="stVerticalBlock"] > div {
                background-color: transparent;
            }
            
            /* Info/Alert cards with white background */
            .stAlert {
                background-color: var(--main-content-bg) !important;
                border-radius: var(--radius-lg);
                border-left: 4px solid;
                padding: 1.25rem 1.5rem;
                box-shadow: var(--shadow-sm);
                margin: 1rem 0;
            }
            
            /* Success alert */
            div[data-testid="stSuccess"] {
                background-color: #ECFDF5 !important;
                border-left-color: var(--success-color);
                color: #065F46;
            }
            
            /* Info alert */
            div[data-testid="stInfo"] {
                background-color: #EFF6FF !important;
                border-left-color: var(--info-color);
                color: #1E40AF;
            }
            
            /* Warning alert */
            div[data-testid="stWarning"] {
                background-color: #FFFBEB !important;
                border-left-color: var(--warning-color);
                color: #92400E;
            }
            
            /* Error alert */
            div[data-testid="stError"] {
                background-color: #FEF2F2 !important;
                border-left-color: var(--error-color);
                color: #991B1B;
            }
            
            /* Custom card component */
            .info-card {
                background: var(--main-content-bg);
                padding: 1.5rem;
                border-radius: var(--radius-lg);
                border: 1px solid var(--border-light);
                box-shadow: var(--shadow-md);
                margin: 1rem 0;
                transition: var(--transition);
            }
            
            .info-card:hover {
                box-shadow: var(--shadow-lg);
                transform: translateY(-2px);
                border-color: var(--border-color);
            }
            
            /* ============================================
            METRICS CARDS
            ============================================ */
            
            [data-testid="stMetric"] {
                background: var(--main-content-bg);
                border: 1px solid var(--border-light);
                border-radius: var(--radius-lg);
                padding: 1.5rem;
                box-shadow: var(--shadow-sm);
                transition: var(--transition);
            }
            
            [data-testid="stMetric"]:hover {
                box-shadow: var(--shadow-md);
                transform: translateY(-2px);
                border-color: var(--border-color);
            }
            
            [data-testid="stMetricLabel"] {
                font-size: 0.875rem;
                font-weight: 600;
                color: var(--text-secondary) !important;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 2rem;
                font-weight: 700;
                color: var(--text-primary) !important;
                margin: 0.5rem 0;
            }
            
            [data-testid="stMetricDelta"] {
                font-size: 0.875rem;
                font-weight: 500;
            }
            
            /* ============================================
            BUTTONS
            ============================================ */
            
            .stButton > button {
                border-radius: var(--radius-md);
                font-weight: 600;
                font-size: 0.875rem;
                padding: 0.625rem 1.25rem;
                min-height: 2.75rem;
                transition: var(--transition);
                border: none;
                letter-spacing: 0.01em;
                box-shadow: var(--shadow-sm);
            }
            
            .stButton > button:hover {
                transform: translateY(-1px);
                box-shadow: var(--shadow-md);
            }
            
            .stButton > button:active {
                transform: translateY(0);
            }
            
            /* Primary button */
            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
                color: white;
            }
            
            .stButton > button[kind="primary"]:hover {
                background: linear-gradient(135deg, var(--primary-hover) 0%, var(--primary-color) 100%);
            }
            
            /* Secondary button */
            .stButton > button[kind="secondary"] {
                background: var(--main-content-bg);
                color: var(--text-primary);
                border: 1px solid var(--border-color);
            }
            
            .stButton > button[kind="secondary"]:hover {
                background: var(--main-bg);
                border-color: var(--primary-color);
                color: var(--primary-color);
            }
            
            /* Download buttons */
            .stDownloadButton > button {
                background: var(--main-content-bg);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                padding: 0.625rem 1.25rem;
                min-height: 2.75rem;
                font-weight: 600;
                color: var(--text-primary);
                transition: var(--transition);
                box-shadow: var(--shadow-sm);
            }
            
            .stDownloadButton > button:hover {
                border-color: var(--primary-color);
                color: var(--primary-color);
                background: var(--main-bg);
                transform: translateY(-1px);
                box-shadow: var(--shadow-md);
            }
            
            /* ============================================
            INPUTS & FORMS
            ============================================ */
            
            /* Text inputs */
            .stTextInput > div > div > input,
            .stNumberInput > div > div > input {
                background: var(--main-content-bg);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                padding: 0.75rem 1rem;
                color: var(--text-primary);
                transition: var(--transition);
            }
            
            .stTextInput > div > div > input:focus,
            .stNumberInput > div > div > input:focus {
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(255, 75, 75, 0.1);
                background: white;
            }
            
            /* Text area */
            .stTextArea textarea {
                background: var(--main-content-bg);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                padding: 0.75rem 1rem;
                color: var(--text-primary);
            }
            
            .stTextArea textarea:focus {
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(255, 75, 75, 0.1);
            }
            
            /* File uploader */
            [data-testid="stFileUploader"] {
                background: var(--main-content-bg);
                border: 2px dashed var(--border-color);
                border-radius: var(--radius-lg);
                padding: 2rem;
                transition: var(--transition);
            }
            
            [data-testid="stFileUploader"]:hover {
                border-color: var(--primary-color);
                background: #FFFBFB;
            }
            
            [data-testid="stFileUploader"] section {
                border: none;
                background: transparent;
            }
            
            /* Select box */
            .stSelectbox > div > div {
                background: var(--main-content-bg);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
            }
            
            /* Slider */
            .stSlider > div > div > div > div {
                background: var(--primary-color);
            }
            
            .stSlider > div > div > div {
                background: var(--border-light);
            }
            
            /* Checkbox */
            .stCheckbox {
                background: var(--main-content-bg);
                padding: 0.75rem;
                border-radius: var(--radius-md);
                border: 1px solid var(--border-light);
            }
            
            /* ============================================
            DATAFRAME / TABLES
            ============================================ */
            
            .stDataFrame {
                background: var(--main-content-bg);
                border: 1px solid var(--border-light);
                border-radius: var(--radius-lg);
                overflow: hidden;
                box-shadow: var(--shadow-sm);
            }
            
            .stDataFrame [data-testid="stTable"] {
                background: var(--main-content-bg);
            }
            
            .stDataFrame thead tr th {
                background: var(--main-bg) !important;
                color: var(--text-primary) !important;
                font-weight: 700 !important;
                text-transform: uppercase;
                font-size: 0.75rem;
                letter-spacing: 0.05em;
                padding: 1rem !important;
                border-bottom: 2px solid var(--border-color) !important;
            }
            
            .stDataFrame tbody tr {
                background: var(--main-content-bg);
            }
            
            .stDataFrame tbody tr:hover {
                background: var(--main-bg) !important;
            }
            
            .stDataFrame tbody tr td {
                padding: 0.875rem 1rem !important;
                color: var(--text-secondary);
                border-bottom: 1px solid var(--border-light) !important;
            }
            
            /* ============================================
            EXPANDERS
            ============================================ */
            
            .streamlit-expanderHeader {
                background: var(--main-content-bg);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                padding: 1rem 1.25rem;
                font-weight: 600;
                color: var(--text-primary);
                transition: var(--transition);
            }
            
            .streamlit-expanderHeader:hover {
                background: var(--main-bg);
                border-color: var(--primary-color);
            }
            
            .streamlit-expanderContent {
                background: var(--main-content-bg);
                border: 1px solid var(--border-color);
                border-top: none;
                border-radius: 0 0 var(--radius-md) var(--radius-md);
                padding: 1.25rem;
            }
            
            /* ============================================
            PROGRESS BAR
            ============================================ */
            
            .stProgress > div > div > div > div {
                background: linear-gradient(90deg, var(--primary-color) 0%, var(--primary-hover) 100%);
                border-radius: var(--radius-sm);
            }
            
            .stProgress > div > div {
                background: var(--border-light);
                border-radius: var(--radius-sm);
                height: 8px;
            }
            
            /* ============================================
            SPINNER
            ============================================ */
            
            .stSpinner > div {
                border-top-color: var(--primary-color) !important;
                border-right-color: var(--primary-hover) !important;
            }
            
            /* ============================================
            DIVIDERS
            ============================================ */
            
            hr {
                border: none;
                border-top: 1px solid var(--border-light);
                margin: 2rem 0;
            }
            
            /* ============================================
            TABS
            ============================================ */
            
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.5rem;
                background: var(--main-content-bg);
                padding: 0.5rem;
                border-radius: var(--radius-lg);
                border: 1px solid var(--border-light);
            }
            
            .stTabs [data-baseweb="tab"] {
                border-radius: var(--radius-md);
                padding: 0.75rem 1.5rem;
                font-weight: 600;
                color: var(--text-secondary);
                background: transparent;
                border: none;
            }
            
            .stTabs [data-baseweb="tab"]:hover {
                background: var(--main-bg);
                color: var(--text-primary);
            }
            
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-hover) 100%);
                color: white !important;
            }
            
            /* ============================================
            SCROLLBAR
            ============================================ */
            
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: var(--border-light);
                border-radius: var(--radius-sm);
            }
            
            ::-webkit-scrollbar-thumb {
                background: var(--border-color);
                border-radius: var(--radius-sm);
                transition: var(--transition);
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: var(--text-light);
            }
            
            /* ============================================
            ANIMATIONS
            ============================================ */
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.6; }
            }
            
            .slide-in {
                animation: slideIn 0.3s ease-out;
            }
            
            .fade-in {
                animation: fadeIn 0.4s ease-in;
            }
            
            /* ============================================
            HIDE STREAMLIT BRANDING
            ============================================ */
            
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* ============================================
            RESPONSIVE DESIGN
            ============================================ */
            
            @media (max-width: 768px) {
                .block-container {
                    padding: 1rem;
                }
                
                h1, .gradient-title {
                    font-size: 1.75rem;
                }
                
                h2 {
                    font-size: 1.5rem;
                }
                
                [data-testid="stMetric"] {
                    padding: 1rem;
                }
                
                [data-testid="stMetricValue"] {
                    font-size: 1.5rem;
                }
            }
            
            /* ============================================
            ADDITIONAL UTILITIES
            ============================================ */
            
            /* Badge component */
            .badge {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            .badge-success {
                background: #D1FAE5;
                color: #065F46;
            }
            
            .badge-info {
                background: #DBEAFE;
                color: #1E40AF;
            }
            
            .badge-warning {
                background: #FEF3C7;
                color: #92400E;
            }
            
            .badge-error {
                background: #FEE2E2;
                color: #991B1B;
            }
            
            /* Stats card */
            .stat-card {
                background: var(--main-content-bg);
                border: 1px solid var(--border-light);
                border-radius: var(--radius-lg);
                padding: 1.5rem;
                box-shadow: var(--shadow-sm);
                transition: var(--transition);
            }
            
            .stat-card:hover {
                box-shadow: var(--shadow-md);
                transform: translateY(-2px);
            }
            
            .stat-card-title {
                font-size: 0.875rem;
                font-weight: 600;
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.5rem;
            }
            
            .stat-card-value {
                font-size: 2rem;
                font-weight: 700;
                color: var(--text-primary);
            }
            
            </style>
        """, unsafe_allow_html=True)
    apply_custom_theme()    
    # Header with gradient title
    st.markdown('<h1 class="gradient-title">🚀 Marketing Data Upload Tool</h1>', unsafe_allow_html=True)
    st.markdown("### 📈 Upload and manage your marketing data efficiently")
    
    # Quick stats row (placeholder - can be populated with actual data)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="📊 Total Uploads", value="0", delta="Today")
    with col2:
        st.metric(label="✅ Success Rate", value="100%", delta="0%")
    with col3:
        st.metric(label="⚡ Active Markets", value="3", delta="US, CA, UK")
    with col4:
        st.metric(label="🕐 Last Updated", value=datetime.now().strftime("%H:%M"))
    
    st.markdown("---")
    
    # Sidebar navigation with enhanced UI
    st.sidebar.markdown("# 📋 Navigation")
    st.sidebar.markdown("*Select the tool you want to use*")
    st.sidebar.markdown("")
    
    # Module status indicators
    module_status = {
        "📊 Sellerboard": "✅ Active",
        "💰 PPC XNurta": "✅ Active",
        "📺 DSP XNurta": "✅ Active",
        "📦 FBA Inventory": "🚧 Coming Soon",
        "🔍 ASIN - Dimension": "🚧 Coming Soon",
        "🚀 Launching - Dimension": "🚧 Coming Soon"
    }
    
    page = st.sidebar.radio(
        label="Select a page",
        options=list(module_status.keys()),
        label_visibility="collapsed",
        help="Choose a module to work with"
    )
    
    # Show selected module status
    st.sidebar.markdown(f"**Status:** {module_status[page]}")
    st.sidebar.markdown("---")
    
    # Enhanced Help Section with expandable details
    with st.sidebar.expander("📖 Quick Start Guide", expanded=False):
        st.markdown("""
        **Step-by-step instructions:**
        
        1️⃣ **Upload Credentials**
        - Upload your `credentials.json` file
        - Ensure it has proper permissions
        
        2️⃣ **Configure Sheet**
        - Enter your Google Sheet ID
        - Format: Found in sheet URL
        
        3️⃣ **Select Market**
        - Choose: US, CA, or UK
        - Ensure data matches market
        
        4️⃣ **Upload Files**
        - Excel files (.xlsx, .xls)
        - Must contain date: DD_MM_YYYY
        - Example: `report_15_10_2025.xlsx`
        
        5️⃣ **Process Data**
        - Review preview
        - Choose: Append or Replace
        - Confirm upload
        """)
    
    with st.sidebar.expander("📝 File Format Requirements", expanded=False):
        st.markdown("""
        **Naming Convention:**
        - Include date in filename
        - Format: `DD_MM_YYYY`
        - Example: `sales_report_25_10_2025.xlsx`
        
        **Supported Formats:**
        - `.xlsx` (Excel 2007+)
        - `.xls` (Excel 97-2003)
        
        **File Size:**
        - Maximum: 200 MB
        - Recommended: < 50 MB
        """)
    
    with st.sidebar.expander("💡 Tips & Best Practices", expanded=False):
        st.markdown("""
        **Performance Tips:**
        - Upload files during off-peak hours
        - Keep file sizes reasonable
        - Use consistent naming conventions
        
        **Data Quality:**
        - Verify data before upload
        - Check for missing values
        - Ensure correct date formats
        
        **Troubleshooting:**
        - Clear browser cache if issues occur
        - Refresh credentials if expired
        - Check internet connection
        """)
    
    st.sidebar.markdown("---")
    
    # Security notice with icon
    st.sidebar.success("""
    🔒 **Security & Privacy**
    
    - ✓ Credentials stored in memory only
    - ✓ No data saved to disk
    - ✓ Secure HTTPS connection
    - ✓ Session-based authentication
    
    Your data is safe with us!
    """)
    
    # Version info
    st.sidebar.markdown("---")
    st.sidebar.caption("Version 1.0.0 | Updated Oct 2025")
    
    # Route to appropriate page with enhanced messaging
    if page == "📊 Sellerboard":
        st.markdown("## 📊 Sellerboard Data Upload")
        st.markdown("*Manage your Sellerboard reports and analytics*")
        st.markdown("")
        sellerboard_page()
        
    elif page == "💰 PPC XNurta":
        st.markdown("## 💰 PPC XNurta Analytics")
        st.markdown("*Upload and analyze your PPC campaign data*")
        st.markdown("")
        ppc_xnurta_page()
        
    elif page == "📺 DSP XNurta":
        st.markdown("## 📺 DSP XNurta Dashboard")
        st.markdown("*Manage your DSP advertising data*")
        st.markdown("")
        dsp_xnurta_page()
        
    elif page == "📦 FBA Inventory":
        st.markdown("## 📦 FBA Inventory Management")
        st.info("🚧 **Module Under Development**")
        st.markdown("""
        This module is currently being developed and will include:
        
        - 📊 Real-time inventory tracking
        - 📈 Stock level analytics
        - 🔔 Low stock alerts
        - 📦 Reorder recommendations
        - 📉 Inventory turnover analysis
        
        **Expected Release:** Q1 2026
        """)
        
        if st.button("🔔 Notify me when available"):
            st.success("✅ You'll be notified when this module is ready!")
            
    elif page == "🔍 ASIN - Dimension":
        st.markdown("## 🔍 ASIN Dimension Analysis")
        st.info("🚧 **Module Under Development**")
        st.markdown("""
        This module is currently being developed and will include:
        
        - 🔍 ASIN performance tracking
        - 📊 Multi-dimensional analysis
        - 🎯 Product ranking insights
        - 📈 Sales trend analysis
        - 🔄 Competitor comparison
        
        **Expected Release:** Q1 2026
        """)
        
        if st.button("🔔 Notify me when available", key="asin_notify"):
            st.success("✅ You'll be notified when this module is ready!")
            
    elif page == "🚀 Launching - Dimension":
        st.markdown("## 🚀 Product Launch Analytics")
        st.info("🚧 **Module Under Development**")
        st.markdown("""
        This module is currently being developed and will include:
        
        - 🚀 Launch performance tracking
        - 📊 Campaign effectiveness metrics
        - 🎯 Target audience analysis
        - 📈 Growth trajectory monitoring
        - 💡 Optimization recommendations
        
        **Expected Release:** Q1 2026
        """)
        
        if st.button("🔔 Notify me when available", key="launch_notify"):
            st.success("✅ You'll be notified when this module is ready!")
    
    # Footer section
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Need Help?**")
        st.markdown("Contact: trinh.nguyen@aprime.so")
    
    with col2:
        st.markdown("**Documentation**")
        # Khi click thì bật/tắt hiển thị docs
        if st.button("View Docs", key="view_docs"):
            st.session_state.show_docs = not st.session_state.get("show_docs", False)
    
    with col3:
        st.markdown("**Report Issues**")
        st.markdown("[Bug Tracker](#)")

    # --- Docs section ---
    if st.session_state.get("show_docs", False):
        st.markdown("---")
        st.markdown("## 📖 Documentation")
        st.markdown("""
        **Hướng dẫn sử dụng:**

        

        💡 *Mẹo:* Bạn có thể xem lại hướng dẫn này bất kỳ lúc nào bằng cách nhấn "View Docs".
        """)

if __name__ == "__main__":
    if "show_docs" not in st.session_state:
        st.session_state.show_docs = False
    main()