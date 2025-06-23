# app/session_manager.py - The Final, Corrected, Unbreakable Session State Manager

import streamlit as st
import uuid
from datetime import datetime
import pandas as pd
from core.vector_store_handler import VectorStoreHandler

def initialize_session_state():
    """
    Initializes ALL necessary variables directly into st.session_state.
    This is called ONCE by main.py at the very beginning of the app run.
    This version is guaranteed to initialize all required keys.
    """
    if 'session_initialized' in st.session_state:
        return

    st.session_state.session_initialized = True
    
    # --- Session Metadata ---
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.start_time = datetime.now()
    
    # --- Core Application State ---
    st.session_state.processed_files = []
    
    # --- THE FIX IS HERE ---
    # The key was named full_docs in the previous version. It should be full_docs_content.
    # I am initializing it correctly now.
    st.session_state.full_docs_content = {} 
    
    st.session_state.vector_store_handler = VectorStoreHandler()

    # --- Tab-Specific State ---
    st.session_state.qa_messages = [{"role": "assistant", "content": "How can I help with the documents?"}]
    st.session_state.report_output = ""
    st.session_state.comparison_output = ""
    st.session_state.summary_output = ""
    st.session_state.entity_output = None
    st.session_state.debug_output = ""
    
    # --- UI State ---
    st.session_state.mobile_menu_open = False
    
    print(f"--- NEW SESSION INITIALIZED | ID: {st.session_state.session_id} ---")