# app/session_manager.py

import streamlit as st
from core.vector_store_handler import VectorStoreHandler

def initialize_session_state():
    """
    Initializes all the necessary variables in Streamlit's session state
    if they don't already exist. This is the single source of truth for the session.
    """
    if "session_initialized" not in st.session_state:
        st.session_state.session_initialized = True
        
        # Chat history
        st.session_state.messages = [{
            "role": "assistant", 
            "content": "Welcome to Cognitive Query Pro! Please go to the Analyzer page, upload your documents, and let's begin."
        }]
        
        # List of processed file names
        st.session_state.processed_files = []
        
        # The handler for our vector database (ChromaDB)
        st.session_state.vector_store_handler = VectorStoreHandler()
        
        print("Session state initialized for the first time.")

def get_session_state():
    """
    A simple utility function to return the session state object.
    This makes the code in UI files cleaner.
    """
    # Ensure it's initialized before returning
    if "session_initialized" not in st.session_state:
        initialize_session_state()
        
    return st.session_state