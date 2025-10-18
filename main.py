import streamlit as st
from sellerboard_app import sellerboard_page, load_credentials_from_file # Import the page function and helper function

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
        label="Select a page",
        options=[
            "📊 Sellerboard",
            "💰 PPC XNurta",
            "📺 DSP XNurta",
            "📦 FBA Inventory",
            "🔍 ASIN - Dimension",
            "🚀 Launching - Dimension"
        ],
        label_visibility="collapsed"
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