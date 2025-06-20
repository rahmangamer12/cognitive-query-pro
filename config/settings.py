# config/settings.py - FINAL PRODUCTION VERSION USING STREAMLIT SECRETS

import streamlit as st

# --- API Keys ---
# This is the OFFICIAL and most reliable way to handle secrets in Streamlit.
# st.secrets reads from the .streamlit/secrets.toml file.
# When you deploy, you will enter these same keys in the Streamlit Cloud secrets manager.
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

# --- Model Names ---
ROUTER_MODEL = "gpt-3.5-turbo"
REPORT_MODEL = "gpt-3.5-turbo"
QNA_MODEL = "gemini-1.5-flash"

# --- Vector Store Settings ---
FAISS_PERSIST_DIRECTORY = "faiss_index_store"

# --- Document Processing ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

def are_keys_configured():
    """Checks if keys are available via Streamlit secrets."""
    # st.secrets behaves like a dictionary.
    if not OPENAI_API_KEY or not GOOGLE_API_KEY:
        return False
    return True