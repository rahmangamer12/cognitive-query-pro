# ui/analyzer_page.py - The Definitive, Production-Grade, Dashboard-Style UI

# ======================================================================================
#  FILE OVERVIEW
# ======================================================================================
# This file constitutes the entire user interface for the "Analyzer" page.
# It is architected with a modular, professional approach, separating UI rendering
# from logic handling to ensure maintainability and scalability.
#
# Key Architectural Principles:
# 1.  **Component-Based UI:** Functions like `render_header`, `render_custom_card`,
#     and `render_sidebar` act as reusable UI components, keeping the code DRY
#     (Don't Repeat Yourself).
# 2.  **State-Driven Display:** The UI is a direct reflection of the data stored in
#     Streamlit's session state. Action handlers modify the state, and the UI
#     rendering functions read from it. This is a robust and predictable pattern.
# 3.  **Decoupled Logic:** This file is responsible for the "View" only. It calls
#     agent functions from the 'agents' module but is completely unaware of their
#     internal workings or API key management. This is a critical design principle.
# 4.  **Enhanced User Experience (UX):** Includes detailed spinners, informative
#     user guidance, a beautiful welcome screen, and a clean, 4-tab interface.
# 5.  **Diagnosability:** A dedicated "Debugging" tab provides transparency into the
#     RAG pipeline, a crucial feature for development and troubleshooting.
# ======================================================================================


# --- Core Streamlit and Python Imports ---
import streamlit as st
import time # Used to simulate realistic spinner delays for a better UX

# --- Project-Specific Imports from our Modular Structure ---
from app.session_manager import get_session_state
from core.document_processor import process_documents
# We import all our agents, which are the "brains" of the operation.
from agents.qa_agent import execute_qa_chain
from agents.report_agent import execute_report_chain
from agents.comparison_agent import execute_comparison_chain
from agents.debug_agent import execute_debug_chain


# ======================================================================================
# SECTION 1: ATOMIC UI COMPONENT FUNCTIONS
# These are small, reusable functions for rendering specific parts of the UI.
# ======================================================================================

def render_header():
    """
    Renders the main page header using custom HTML for a polished, professional look.
    This sets the tone for the application and creates a strong brand identity.
    """
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="color: #FFFFFF; font-size: 3rem; font-weight: 700;">
                🧠 Cognitive Query <span style="color: #6c63ff;">Pro</span>
            </h1>
            <p style="color: #a9a9aa; font-size: 1.1rem;">
                Your intelligent partner for deep document analysis. 
                Upload, analyze, and extract insights with the power of generative AI.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_font_awesome_icons():
    """
    Injects the Font Awesome CSS library into the Streamlit app's HTML head.
    This allows the use of a wide range of professional icons throughout the UI.
    """
    st.markdown(
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
        unsafe_allow_html=True,
    )

def render_custom_card(icon_class: str, title: str, text: str):
    """
    Renders a styled card component. This is a reusable function to maintain UI consistency.
    """
    st.markdown(
        f"""
        <div class="card">
            <h3><i class="{icon_class}"></i>{title}</h3>
            <p>{text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_results_container(title: str, content_key: str, ss):
    """
    Renders a styled container for displaying AI agent output stored in the session state.
    This function reads from the session state, ensuring the UI is always in sync.
    """
    # Only render the container if there is content to display for that key.
    if content_key in ss and ss[content_key]:
        st.markdown("---") # Add a separator for visual clarity
        st.markdown(
            f"""
            <div class="response-container">
                <h4>{title}</h4>
                {ss[content_key]}
            </div>
            """,
            unsafe_allow_html=True,
        )

def render_initial_welcome_screen():
    """
    Displays a beautiful and informative welcome screen when no documents are processed.
    This guides the user on how to get started, improving usability.
    """
    st.info("👋 **Welcome to Cognitive Query Pro!** Please upload and process documents using the sidebar to activate the analysis tools.")
    
    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.image("https://images.pexels.com/photos/3184418/pexels-photo-3184418.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1", caption="Unlock Insights From Your Data")
    
    with col2:
        st.markdown("### How It Works in 3 Simple Steps")
        st.markdown("""
        1.  **<i class="fa-solid fa-upload"></i> Upload:** Add your PDF, TXT, or DOCX files using the "Document Hub" in the sidebar.
        2.  **<i class="fa-solid fa-cogs"></i> Process:** Click the "Process Documents" button. Our system reads and indexes your files into a powerful, context-aware vector store.
        3.  **<i class="fa-solid fa-lightbulb"></i> Analyze:** Once processing is complete, use the tabs above to interact with our specialized AI agents:
            *   **Q&A Chat:** For quick, factual answers.
            *   **Generate Report:** For detailed summaries.
            *   **Compare Documents:** To find similarities & differences.
            *   **Debugging:** To inspect the retrieval process.
        """, unsafe_allow_html=True)
    st.success("Ready to begin? Your journey into intelligent document analysis starts now!")

def render_sidebar(ss):
    """
    Renders the sidebar, which is the main control panel for document management.
    It contains the file uploader, the processing button, and lists processed files.
    """
    with st.sidebar:
        st.title("📄 Document Hub")
        st.markdown(
            "**Upload, process, and manage your documents here.**",
            help="Supported formats: PDF, TXT, DOCX. You can upload multiple files at once."
        )

        uploaded_files = st.file_uploader(
            "Click to select files",
            type=["pdf", "txt", "docx"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        if st.button("🚀 Process Documents", use_container_width=True, disabled=not uploaded_files):
            handle_document_processing(uploaded_files, ss)

        if ss.get("processed_files"):
            st.markdown("---")
            st.markdown("#### ✅ Processed Files")
            # Use a set for efficient checking of processed files
            for file_name in sorted(list(set(ss.processed_files))):
                st.info(f"✔️ {file_name}")

# ======================================================================================
# SECTION 2: CORE ACTION HANDLER FUNCTIONS
# These functions contain the logic that runs when a user interacts with a widget.
# They are responsible for calling the backend agents and updating the session state.
# ======================================================================================

def handle_document_processing(uploaded_files, ss):
    """
    Handles the logic for the 'Process Documents' button click.
    """
    if not uploaded_files:
        st.warning("Please select at least one document to upload.")
        return

    with st.spinner("Analyzing document structure and content... This may take a moment for large files."):
        time.sleep(1) # Small UX delay to make the spinner feel responsive
        doc_chunks = process_documents(uploaded_files)

    if doc_chunks:
        ss.vector_store_handler.build_index(doc_chunks)
        current_files = ss.get("processed_files", [])
        new_files = [f.name for f in uploaded_files if f.name not in current_files]
        ss.processed_files.extend(new_files)
        # Clear any previous results when new documents are processed
        ss.report_output = ""
        ss.comparison_output = ""
        ss.debug_output = ""
        st.rerun()

def handle_qa_submission(prompt, ss):
    """Handles the logic for a Q&A chat submission."""
    ss.qa_messages.append({"role": "user", "content": prompt})
    with st.spinner("Q&A Agent is searching for the answer..."):
        retriever = ss.vector_store_handler.get_retriever()
        response = execute_qa_chain(
    retriever=retriever, 
    query=prompt, 
    chat_history=ss.qa_messages[:-1] # We pass the chat history here
    )
        ss.qa_messages.append({"role": "assistant", "content": response})

def handle_report_submission(report_query, ss):
    """Handles the logic for a 'Generate Report' form submission."""
    if not report_query:
        st.warning("Please describe the report you want to generate.")
        return
    with st.spinner("The Report Agent is writing... This may take a while for complex reports."):
        retriever = ss.vector_store_handler.get_retriever()
        response = execute_report_chain(retriever, report_query)
        ss.report_output = response # Store the result in the session state

def handle_comparison_submission(selected_files, comparison_query, ss):
    """Handles the logic for a 'Generate Comparison' form submission."""
    if len(selected_files) < 2:
        st.warning("Please select at least two documents to compare.")
        return
    if not comparison_query:
        st.warning("Please enter a specific comparison query.")
        return
    with st.spinner("The Comparison Agent is performing a deep cross-document analysis..."):
        st.info(f"Comparing documents: **{', '.join(selected_files)}**")
        full_query = (
            f"Perform a comparative analysis based on the following documents: '{', '.join(selected_files)}'. "
            f"The specific comparison request is: {comparison_query}"
        )
        retriever = ss.vector_store_handler.get_retriever()
        response = execute_comparison_chain(retriever, full_query)
        ss.comparison_output = response # Store the result in the session state

def handle_debug_submission(debug_query, ss):
    """Handles the logic for the 'Debug Query' button click."""
    if not debug_query:
        st.warning("Please enter a query to debug.")
        return
    with st.spinner("Debugging... Checking what the retriever finds..."):
        retriever = ss.vector_store_handler.get_retriever()
        debug_results = execute_debug_chain(retriever, debug_query)
        ss.debug_output = debug_results # Store the result in the session state

# ======================================================================================
# SECTION 3: TAB-SPECIFIC UI RENDERING FUNCTIONS
# These functions define the complete layout and widgets for each of the main tabs.
# ======================================================================================

def render_qa_tab(ss):
    """Renders the complete UI and logic for the Q&A Chat tab."""
    render_custom_card(
        "fa-solid fa-comments", "Direct Question & Answer",
        "Ask specific, factual questions. The <strong>Q&A Agent</strong> (powered by Gemini) provides fast answers directly from your document's text."
    )
    
    # Initialize chat history for this tab if it doesn't exist
    if "qa_messages" not in ss:
        ss.qa_messages = [{"role": "assistant", "content": "How can I help you with the documents today?"}]
    
    # Display the chat messages
    for msg in ss.qa_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Handle new input from the user
    if prompt := st.chat_input("Ask a factual question..."):
        handle_qa_submission(prompt, ss)
        # Rerun to display the new messages immediately in the chat history
        st.rerun()

def render_report_tab(ss):
    """Renders the complete UI and logic for the Report Generation tab."""
    render_custom_card(
        "fa-solid fa-chart-line", "In-Depth Report Generation",
        "Request a detailed summary or structured report. The <strong>Report Agent</strong> (powered by GPT-4o) synthesizes information into a professional document."
    )
    
    # Using a form ensures that the whole block is submitted at once.
    with st.form(key="report_form"):
        report_query = st.text_area(
            "**Report Topic:**", 
            height=150, 
            placeholder="Be descriptive. e.g., 'Summarize the key financial data from all documents, focusing on Q4 revenue and costs.'"
        )
        submitted = st.form_submit_button("📊 Generate Report")
        if submitted:
            # Clear old results before generating new ones for a clean UI.
            ss.report_output = ""
            handle_report_submission(report_query, ss)
    
    # The results container reads from the session state and displays the output.
    render_results_container("Report Agent's Findings", "report_output", ss)
    
def render_comparison_tab(ss):
    """Renders the complete UI and logic for the Document Comparison tab."""
    render_custom_card(
        "fa-solid fa-scale-balanced", "Comparative Analysis",
        "Select specific documents and ask the <strong>Comparison Agent</strong> (powered by GPT-4o) to analyze their similarities and differences."
    )
    
    with st.form(key="comparison_form"):
        st.markdown("**Step 1: Select the documents to compare**")
        selected_files = st.multiselect("Choose two or more documents:", options=ss.get("processed_files", []))
        
        st.markdown("**Step 2: Describe what you want to compare**")
        comparison_query = st.text_area(
            "Comparison Request:", 
            height=120, 
            placeholder="e.g., 'Compare the project costs and delivery timelines mentioned in the selected proposals.'"
        )
        submitted = st.form_submit_button("⚖️ Generate Comparison")
        if submitted:
            ss.comparison_output = ""
            handle_comparison_submission(selected_files, comparison_query, ss)

    render_results_container("Comparative Analysis Results", "comparison_output", ss)

def render_debug_tab(ss):
    """Renders the complete UI and logic for the Retriever Debugging tab."""
    render_custom_card(
        "fa-solid fa-magnifying-glass-chart", "Retriever Debugger",
        "This powerful tool shows you what content the AI sees for a given query. If the Q&A agent fails, use this to check if the retriever is finding the correct context. This is the key to solving most RAG issues."
    )
    
    with st.form(key="debug_form"):
        debug_query = st.text_input(
            "Enter the exact query you want to debug:", 
            placeholder="e.g., 'what is the title of detail.txt'"
        )
        submitted = st.form_submit_button("🔍 Debug Query")
        if submitted:
            ss.debug_output = ""
            handle_debug_submission(debug_query, ss)
    
    render_results_container("Retriever Debug Results", "debug_output", ss)


# ======================================================================================
# SECTION 5: MAIN PAGE ORCHESTRATION FUNCTION
# This is the main entry function called by main.py to render the entire page.
# ======================================================================================

def display_analyzer_page():
    """
    The main "conductor" function that orchestrates the rendering of the entire analyzer page.
    It initializes the UI, sets up the layout and sidebar, and manages the tabbed interface.
    """
    # Get the session state object, which is our app's "memory".
    ss = get_session_state()

    # Inject CSS for custom styling and Font Awesome for icons.
    render_font_awesome_icons()
    
    # Render the main page header.
    render_header()
    
    # Render the sidebar, which is always visible.
    render_sidebar(ss)

    # --- Conditional UI ---
    # The main analysis tools (tabs) should only be shown if documents have been processed.
    # This provides a guided experience for new users.
    if not ss.get("processed_files"):
        render_initial_welcome_screen()
        return

    # Define the titles for our tabs. Adding a new tab is as simple as adding a title here
    # and creating a new `with` block below.
    tab_titles = [
        "💬 Q&A Chat", 
        "📊 Generate Report", 
        "⚖️ Compare Documents",
        "🐞 Debugging"
    ]
    tab1, tab2, tab3, tab4 = st.tabs(tab_titles)

    # Render each tab's content by calling its dedicated function.
    with tab1:
        render_qa_tab(ss)
    with tab2:
        render_report_tab(ss)
    with tab3:
        render_comparison_tab(ss)
    with tab4:
        render_debug_tab(ss)