# main.py

import sys
import os
import streamlit as st

# --- Path Setup ---
# This is a crucial step to ensure that all modules (e.g., 'ui', 'core') 
# can be imported correctly from anywhere in the project.
# It adds the project's root directory to Python's path.
try:
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
except NameError:
    # This will handle the case where the script is run in an interactive environment
    # where __file__ is not defined.
    sys.path.insert(0, os.getcwd())


# --- Import Custom Modules ---
# These imports must come AFTER the path setup.
from ui.home_page import display_home_page
from ui.analyzer_page import display_analyzer_page
from app.session_manager import initialize_session_state
from utils.helpers import load_css


def main():
    """
    The main function to run the Streamlit application.
    """
    # --- Page Configuration (should be the first Streamlit command) ---
    st.set_page_config(
        page_title="Cognitive Query Pro",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # --- Load Assets and Initialize State ---
    # Load custom CSS for styling
    load_css("styles.css")
    
    # Initialize the session state. This function creates all the necessary
    # session variables on the first run.
    initialize_session_state()

    # --- Page Navigation ---
    # A dictionary to map page names to their rendering functions.
    PAGES = {
        "🏠 Home": display_home_page,
        "🔬 Analyzer": display_analyzer_page
    }

    st.sidebar.title("Navigation")
    
    # Create a radio button in the sidebar for page selection.
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))

    # Call the function corresponding to the selected page.
    page_to_display = PAGES[selection]
    page_to_display()


# --- Application Entry Point ---
if __name__ == "__main__":
    main()