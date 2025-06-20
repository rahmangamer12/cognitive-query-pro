# ui/home_page.py

import streamlit as st

def display_home_page():
    """Renders the professional-looking home page."""
    
    st.markdown("<h1 style='text-align: center; color: #6c63ff;'>🧠 Welcome to Cognitive Query Pro</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #BDBDC6;'>Your Intelligent Document Analysis Partner</h4>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🤖 Agentic Power")
        st.markdown("""
        Our system uses a smart **Router Agent** to understand your query. 
        - For simple questions, it uses the fast **Q&A Agent (Gemini)**.
        - For complex summaries or reports, it delegates to the powerful **Report Agent (OpenAI)**.
        """)

    with col2:
        st.subheader("🎯 Precision Q&A")
        st.markdown("""
        Ask questions about specific documents. For example:
        `"What is the conclusion in 'project_plan.pdf'?"`
        The agent will focus its search *only* on that file, providing accurate, source-specific answers.
        """)

    with col3:
        st.subheader("🚀 How to Start")
        st.markdown("""
        1.  Go to the **🔬 Analyzer** page from the sidebar.
        2.  Upload your PDF or TXT documents.
        3.  Click **Process Documents**.
        4.  Start chatting!
        """)

    st.markdown("---")
    st.info("This project is built using Streamlit, LangChain, OpenAI, and Google Gemini. The modular structure ensures scalability and maintainability.")