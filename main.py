"""
Enhanced CSV Search Application for Large Files
Main application entry point with improved architecture.
"""

import streamlit as st
import os
import sys
import logging

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.config import config
from src.core.logging_config import setup_logging
from src.auth.auth_manager import auth_manager
from src.database.connection import db_manager
from src.database.file_processor import file_processor
from src.ui.dashboard import dashboard
from src.ui.search_interface import search_interface
from src.ui.file_manager import file_manager

# Configure Streamlit page
st.set_page_config(
    page_title=config.ui.page_title,
    layout=config.ui.layout,
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "# Gharp Search\nAdvanced CSV search for large files"
    }
)

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

def initialize_application():
    """Initialize the application components."""
    try:
        # Initialize database schema
        db_manager.initialize_schema()
        
        # Ensure required directories exist
        config.ensure_directories()
        
        logger.info("Application initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        st.error(f"❌ Application initialization failed: {e}")
        return False

def render_header():
    """Render application header."""
    st.title("☿ Gharp Search - Large CSV Analytics")
    st.markdown("*Advanced search capabilities for large CSV files with high-performance processing*")

def render_sidebar_navigation():
    """Render sidebar navigation."""
    with st.sidebar:
        # User info and logout
        user = auth_manager.get_current_user()
        if user:
            st.success(f'Welcome **{user["name"]}**')
            auth_manager.logout()
        
        st.divider()
        
        # Navigation
        page = st.selectbox(
            "📍 Navigation",
            ["🏠 Dashboard", "🔍 Search", "📁 File Manager"],
            help="Select the page you want to view"
        )
        
        return page

def render_dashboard_page(user_name: str):
    """Render the dashboard page."""
    dashboard.render_full_dashboard(user_name)

def render_search_page(user_name: str):
    """Render the search page."""
    # Render search interface
    search_params = search_interface.render_search_sidebar(user_name)
    
    # Main content area
    if not search_params:
        st.info("👈 Configure your search options in the sidebar to get started")
        return
    
    # Show basic overview
    st.header("🔍 CSV Search Interface")
    
    # Quick stats
    try:
        metadata_df = file_processor.get_all_file_metadata()
        if not metadata_df.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📁 Files Available", len(metadata_df))
            with col2:
                st.metric("📊 Total Rows", f"{metadata_df['row_count'].sum():,}")
            with col3:
                st.metric("💾 Total Size", f"{metadata_df['file_size_mb'].sum():.1f} MB")
    except Exception as e:
        logger.error(f"Error displaying search stats: {e}")
    
    # Execute search if button clicked
    if search_params.get('search_button'):
        search_interface.execute_search(search_params, user_name)

def render_file_manager_page():
    """Render the file manager page."""
    file_manager.render_file_upload_interface()

def main():
    """Main application function."""
    # Initialize application
    if not initialize_application():
        st.stop()
    
    # Handle authentication
    auth_manager.require_authentication()
    
    # Get current user
    user = auth_manager.get_current_user()
    if not user:
        st.error("❌ Authentication failed")
        st.stop()
    
    user_name = user['username']
    
    # Render header
    render_header()
    
    # Render navigation and get selected page
    selected_page = render_sidebar_navigation()
    
    # Render selected page
    try:
        if selected_page == "🏠 Dashboard":
            render_dashboard_page(user_name)
        elif selected_page == "🔍 Search":
            render_search_page(user_name)
        elif selected_page == "📁 File Manager":
            render_file_manager_page()
        else:
            st.error("❌ Unknown page selected")
            
    except Exception as e:
        logger.error(f"Error rendering page {selected_page}: {e}")
        st.error(f"❌ Error loading page: {e}")
        
        # Show error details in expander for debugging
        with st.expander("🔧 Error Details"):
            st.exception(e)

if __name__ == "__main__":
    main()