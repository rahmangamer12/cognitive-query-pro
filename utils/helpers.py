# utils/helpers.py - The Final, Corrected, and Robust Asset Loader

import streamlit as st
import os
from pathlib import Path

def load_css(file_name: str):
    """
    Loads a CSS file from the 'ui/static' directory using a robust,
    absolute path relative to this very file. This is the most reliable
    method to prevent FileNotFoundError.
    
    Args:
        file_name (str): The name of the CSS file (e.g., 'styles.css').
    """
    try:
        # Get the directory where this helpers.py file is located.
        current_dir = Path(__file__).parent
        # Get the project's root directory by going one level up.
        project_root = current_dir.parent
        # Construct the full, absolute path to the CSS file.
        file_path = project_root / "ui" / "static" / file_name
        
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        print(f"✅ CSS loaded successfully from: {file_path}")
    except FileNotFoundError:
        # Provide a very clear error message if the file is not found.
        st.error(f"CSS file not found. The application expected it to be at: {file_path}")
        print(f"ERROR: CSS file not found at path: {file_path}")
    except Exception as e:
        st.error(f"An error occurred while loading CSS: {e}")
        print(f"ERROR loading CSS: {e}")


# --- THE FIX IS HERE ---
# This function was missing in the previous version.
def inject_font_awesome():
    """
    Injects the Font Awesome CSS library into the Streamlit app's HTML head.
    This allows the use of a wide range of professional icons (like files, charts, etc.)
    throughout the UI by using their class names in HTML/Markdown.
    """
    st.markdown(
        # We use a reliable CDN for Font Awesome.
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
        unsafe_allow_html=True,
    )
    print("✅ Font Awesome icons injected successfully.")

# You can also add the inject_tailwind function here if you are using it.
def inject_tailwind():
    """Injects the Tailwind CSS CDN for professional UI styling."""
    st.markdown(
        """
        <script src="https://cdn.tailwindcss.com"></script>
        """,
        unsafe_allow_html=True
    )
    print("✅ Tailwind CSS injected successfully.")