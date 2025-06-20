# utils/helpers.py

import streamlit as st
import os
from pathlib import Path

def load_css(file_name):
    """
    Loads a CSS file using a path relative to the project's root directory.
    This is the most reliable method for Streamlit apps.
    
    How it works:
    1. `Path.cwd()` gets the current working directory, which is the project root
       when you run `streamlit run main.py`.
    2. We then join this root path with the relative path to our CSS file.
    """
    # Get the project root directory (where you run the command from)
    project_root = Path.cwd()
    
    # Construct the full path to the CSS file
    # This will be something like 'D:/Agentic Ai/Project 1/ui/static/styles.css'
    file_path = project_root / "ui" / "static" / file_name

    try:
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        # Optional: Add a success message in the terminal for debugging
        print(f"✅ CSS loaded successfully from: {file_path}")

    except FileNotFoundError:
        # Provide a very clear error message if the file is not found
        st.error(f"CSS file not found at the expected path.")
        st.code(str(file_path), language="text")
        st.warning("Please verify the following:\n"
                   "1. You are running `streamlit run main.py` from the project's root directory (`cognitive_query_pro`).\n"
                   "2. The folder structure is exactly `ui/static/styles.css`.")