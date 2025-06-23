# app/main_app_config.py
import streamlit as st
from ui.home_page import display_home_page
from ui.analyzer_page import display_analyzer_page

def get_app_pages(user_role: str) -> dict:
    """
    Returns a dictionary of available pages based on the user's role.
    This implements Role-Based Access Control (RBAC).
    """
    # Base pages available to all authenticated users
    pages = {
        "🏠 Home": display_home_page,
        "🔬 Analyzer": display_analyzer_page
    }

    # Add the Admin Dashboard only if the user has the 'admin' role.
    
    return pages

def render_main_app_ui(authenticator):
    """
    Renders the main application UI after a user has successfully logged in.
    This function acts as the entry point to the core features of the app.
    """
    from app.session_manager import initialize_session_state
    
    # Initialize the main app state only once per successful login session.
    if 'main_app_initialized' not in st.session_state:
        initialize_session_state()
        st.session_state.main_app_initialized = True
    
    # --- Sidebar Welcome & Logout ---
    st.sidebar.title(f"Welcome, {st.session_state['name']}!")
    user_role = st.session_state.get('role', 'user')
    st.sidebar.markdown(f"**Role:** `{user_role.title()}`")
    authenticator.logout('Logout', 'sidebar')
    
    # --- Main Application Page Navigation ---
    PAGES = get_app_pages(user_role)
    
    st.sidebar.markdown("---")
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(PAGES.keys()), key="main_nav")
    
    # Call the rendering function for the selected page.
    page_to_display = PAGES[selection]
    page_to_display()