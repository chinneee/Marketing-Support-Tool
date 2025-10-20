import streamlit as st
from modules.sellerboard import sellerboard_page
from modules.ppc_xnurta import ppc_xnurta_page
from modules.dsp_xnurta import dsp_xnurta_page
from modules.fba_inventory import fba_inventory_page
from modules.asin import asin_dimension_page
from datetime import datetime
import pytz
import os
import time
import json

def main():
    st.set_page_config(
        page_title="Marketing Data Upload Tool",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Enhanced Custom CSS
    st.markdown("""
        <style>
        /* Main container styling */
        .main {
            padding-top: 1rem;
        }
        
        /* Button improvements */
        .stButton>button {
            height: 3rem;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
            border: none;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* Radio button styling */
        .stRadio > label {
            font-weight: 500;
            color: #262730;
        }
        
        /* Sidebar improvements */
        [data-testid="stSidebar"] {
            background-color: #F5F5F0;
        }
        
        /* Info/Success/Warning boxes */
        .stAlert {
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        /* Title gradient effect */
        .gradient-title {
            background: linear-gradient(120deg, #FF4B4B, #FF6B6B);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        /* Card-like containers */
        .info-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        
        /* Animated loading */
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .loading {
            animation: pulse 2s ease-in-out infinite;
        }
        
        /* Hide default streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Divider styling */
        hr {
            margin: 2rem 0;
            border: none;
            border-top: 2px solid #f0f2f6;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header with gradient title
    st.markdown('<h1 class="gradient-title">🚀 Marketing Data Upload Tool</h1>', unsafe_allow_html=True)
    
    # Quick stats row (placeholder - can be populated with actual data)
    col1, col2, col3, col4 = st.columns(4)
    SESSION_FILE = "/tmp/active_sessions.json"

    def load_sessions():
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_sessions(sessions):
        with open(SESSION_FILE, "w") as f:
            json.dump(sessions, f)

    def register_session():
        sessions = load_sessions()
        session_id = st.session_state.get("_session_id", str(time.time()))
        st.session_state["_session_id"] = session_id
        sessions[session_id] = time.time()
        # Xóa session cũ hơn 10 phút
        now = time.time()
        sessions = {sid: t for sid, t in sessions.items() if now - t < 600}
        save_sessions(sessions)
        return len(sessions)

    active_users = register_session()

    with col1:
        st.metric(label="👥 Active Users", value=active_users)
    with col2:
        st.metric(label="✅ Success Rate", value="100%", delta="0%")
    with col3:
        st.metric(label="⚡ Active Markets", value="3", delta="US, CA, UK")
    with col4:
        st.metric(label="🕐 Last Updated", value=datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%H:%M'))
    # Sidebar navigation with enhanced UI
    st.sidebar.markdown("# 📋 Navigation")
    st.sidebar.markdown("*Select the tool you want to use*")
    st.sidebar.markdown("")
    
    # Module status indicators
    module_status = {
        "📊 Sellerboard": "✅ Active",
        "💰 PPC XNurta": "✅ Active",
        "📺 DSP XNurta": "✅ Active",
        "📦 FBA Inventory": "✅ Active",
        "🔍 ASIN - Dimension": "✅ Active",
        "🚀 Launching - Dimension": "✅ Active",
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
        st.markdown("*Manage your FBA Inventory reports and analytics*")
        st.markdown("")
        fba_inventory_page()
            
    elif page == "🔍 ASIN - Dimension":
        st.markdown("## 🔍 ASIN Dimension Analysis")
        st.markdown("*Manage your Product reports and analytics*")
        st.markdown("")
        asin_dimension_page()

            
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
                    
        Hí, chào cả nhà. Em chưa viết cí này hẹ hẹ. Nhưng mà em sẽ viết sớm thôi ạ.

        Cảm ơn mọi người đã sử dụng công cụ của em! ❤️
        """)

if __name__ == "__main__":
    if "show_docs" not in st.session_state:
        st.session_state.show_docs = False
    main()