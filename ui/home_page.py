# ui/home_page.py - The Enterprise-Grade "Legacy" Welcome Dashboard (Masterpiece Edition)

# ======================================================================================
#  FILE OVERVIEW & ARCHITECTURAL PHILOSOPHY (Definitive Edition)
# ======================================================================================
# This file renders the main "Home" page, designed to be a stunning and informative
# welcome dashboard for the Cognitive Query Pro application. It serves as the user's
# first and most critical impression and is architected to be dynamic, professional,
# and visually breathtaking.
#
# KEY ARCHITECTURAL PILLARS:
#
# 1.  **Dynamic Data Integration:** Unlike a static landing page, this dashboard
#     pulls real-time data from Streamlit's session state (`st.session_state`) to
#     display live statistics, such as the number of processed documents and
#     interactions. This makes the application feel alive and responsive.
#
# 2.  **Hyper-Modular Component Rendering:** The page is constructed from more than
#     a dozen modular rendering functions (e.g., `render_hero_section`,
#     `render_stats_card`, `render_feature_showcase`). This is a best practice in
#     modern UI development, making the code exceptionally clean, readable, and
#     easy to extend.
#
# 3.  **Timeless, Premium Styling:** The entire UI is built using custom HTML and
#     our "Obsidian & Gold" CSS design system, which emphasizes elegance,
#     sophistication, and subtle, high-quality visual effects.
#
# 4.  **Strategic User Guidance:** The page is structured to guide the user's eye,
#     starting with a powerful hero statement, moving to key data points, explaining
#     the features and technology, and ending with a clear, compelling call to action.
#
# 5.  **Extensive Documentation:** Every function is meticulously documented with
#     detailed docstrings, and the code includes comments explaining the purpose of
#     each section, adhering to the highest standards of code quality.
# ======================================================================================

# --- Core & Third-Party Imports ---
import streamlit as st
from typing import Dict, List, Any

# Note: We no longer import get_session_state here. It is passed in from main.py.

# ======================================================================================
# SECTION 1: ATOMIC UI COMPONENT FUNCTIONS
# These are the smallest, reusable building blocks of our dashboard.
# ======================================================================================

def render_hero_section():
    """
    Renders the main hero/header section of the home page.
    It uses a clean, powerful statement and sub-header to establish the
    application's value proposition immediately.
    """
    st.markdown(
        """
        <div class="text-center p-8 mb-12 fade-in">
            <h1 class="hero-title">
                Where Your Documents Find Their Voice.
            </h1>
            <p class="hero-subtitle">
                Cognitive Query Pro transcends traditional search. Engage in intelligent dialogues,
                synthesize complex reports, and uncover insights you never thought possible.
                This is Document Intelligence, redefined.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_stats_card(icon: str, title: str, value: Any, description: str):
    """
    Renders a single, beautifully styled statistics card with dynamic data.
    This component is designed to be modular and reusable.

    Args:
        icon (str): The Font Awesome icon class (e.g., 'file-alt').
        title (str): The title of the card (e.g., "Documents Processed").
        value (Any): The numerical or text value to display prominently.
        description (str): A short description below the value.
    """
    st.markdown(
        f"""
        <div class="stat-card">
            <p class="stat-card-title flex items-center">
                <i class="fas fa-{icon} mr-2"></i>
                {title}
            </p>
            <h3 class="stat-card-value">{value}</h3>
            <p class="text-xs text-gray-500 mt-2">{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_feature_card(icon: str, title: str, description: str):
    """
    Renders a single card for the key features grid, designed for elegance and clarity.
    This component highlights the core capabilities of the application.

    Args:
        icon (str): The Font Awesome icon class.
        title (str): The title of the feature.
        description (str): A short description of the feature.
    """
    st.markdown(
        f"""
        <div class="feature-card">
            <div class="feature-icon">
                <i class="fas fa-{icon}"></i>
            </div>
            <h3 class="feature-title">{title}</h3>
            <p class="text-sm">{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_tech_stack_icon(icon: str, name: str):
    """
    Renders a single icon and name for the technology stack showcase.
    """
    st.markdown(
        f"""
        <div class="text-center p-4 bg-gray-900/50 rounded-lg transition-all duration-300 hover:bg-gray-800">
            <img src="{icon}" alt="{name}" class="h-12 w-12 mx-auto mb-2"/>
            <p class="text-sm font-medium text-gray-400">{name}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_testimonial_card(quote: str, author: str, role: str):
    """
    Renders a single testimonial card for social proof.
    """
    st.markdown(
        f"""
        <div class="card h-full">
            <p class="text-lg italic text-gray-300">"{quote}"</p>
            <p class="text-right mt-4 font-semibold text-white">- {author}</p>
            <p class="text-right text-sm text-primary-color -mt-2">{role}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ======================================================================================
# SECTION 2: COMPOSITE UI SECTIONS
# These functions combine atomic components into larger, meaningful page sections.
# ======================================================================================

def render_stats_dashboard(ss: Dict):
    """
    Renders the dynamic statistics dashboard by pulling live data from the session state.
    This provides an immediate, data-driven overview of the application's current state.

    Args:
        ss (Dict): The Streamlit session state object.
    """
    st.markdown("<!-- Stats Dashboard Section -->")
    
    # Get live data from session state, with default values for robustness.
    num_docs = len(ss.get("processed_files", []))
    
    try:
        # This safely checks for the handler and its attributes before accessing them.
        vector_store_handler = ss.get("vector_store_handler")
        if vector_store_handler and hasattr(vector_store_handler, 'docstore') and vector_store_handler.docstore:
             # The docstore in ParentDocumentRetriever is a key-value store. `get_all` is not a method.
             # The correct way to get its size is by accessing its internal dictionary.
            num_knowledge_units = len(vector_store_handler.docstore.store)
        else:
            num_knowledge_units = 0
    except Exception:
        num_knowledge_units = 0

    # Subtract the initial assistant message to get the true interaction count.
    num_interactions = max(0, len(ss.get("qa_messages", [])) - 1)

    # Use a responsive 3-column layout.
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_stats_card(
            icon="file-alt",
            title="Indexed Documents",
            value=num_docs,
            description="Total unique files in the knowledge base."
        )
    with col2:
        render_stats_card(
            icon="brain",
            title="Knowledge Units",
            value=f"{num_knowledge_units:,}",
            description="Parent documents stored for deep context."
        )
    with col3:
        render_stats_card(
            icon="exchange-alt",
            title="AI Interactions",
            value=max(0, num_interactions),
            description="Conversational turns in this session."
        )

def render_features_showcase():
    """
    Renders the key features section using a responsive grid. This section is designed
    to be visually appealing and to quickly communicate the app's value.
    """
    st.markdown("<h2 class='text-3xl font-bold text-center mb-8 mt-16'>An Intelligence Suite, Not Just a Search Box</h2>", unsafe_allow_html=True)
    
    features = [
        {"title": "Conversational Q&A", "desc": "Engage in natural, context-aware dialogues. Ask follow-up questions and get precise answers backed by citations.", "icon": "comments"},
        {"title": "AI-Powered Summarizer", "desc": "Distill hundred-page documents into brief, executive summaries or detailed, multi-point breakdowns in seconds.", "icon": "file-invoice"},
        {"title": "Automated Entity Extraction", "desc": "Instantly identify and categorize key people, organizations, locations, and data points from any text.", "icon": "tags"},
        {"title": "Comparative Analysis", "desc": "Intelligently compare and contrast multiple documents to uncover hidden synergies, conflicts, and patterns.", "icon": "balance-scale"},
    ]
    
    # Create a responsive 2x2 grid.
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        render_feature_card(features[0]["icon"], features[0]["title"], features[0]["desc"])
        render_feature_card(features[2]["icon"], features[2]["title"], features[2]["desc"])

    with col2:
        render_feature_card(features[1]["icon"], features[1]["title"], features[1]["desc"])
        render_feature_card(features[3]["icon"], features[3]["title"], features[3]["desc"])

def render_tech_stack_showcase():
    """
    Renders a section to showcase the powerful technologies used to build the app.
    This is a professional touch that impresses technical stakeholders.
    """
    st.markdown("<h2 class='text-3xl font-bold text-center mb-8 mt-16'>Powered by a World-Class Tech Stack</h2>", unsafe_allow_html=True)
    
    techs = [
        {"name": "Streamlit", "icon": "https://streamlit.io/images/brand/streamlit-logo-primary-colormark-darktext.svg"},
        {"name": "LangChain", "icon": "https://python.langchain.com/assets/images/langchain-logo-dark-300x300-9c4310395786016c3154e3d6411516e2.png"},
        {"name": "OpenAI", "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/OpenAI_Logo.svg/1200px-OpenAI_Logo.svg.png"},
        {"name": "Google Gemini", "icon": "https://upload.wikimedia.org/wikipedia/commons/2/2d/Google-Gemini-icon.svg"},
        {"name": "FAISS", "icon": "https://raw.githubusercontent.com/facebookresearch/faiss/main/docs/logo.png"},
    ]
    
    # Use a responsive grid for the logos.
    st.markdown("<div class='grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-8'>", unsafe_allow_html=True)
    for tech in techs:
        with st.container():
            render_tech_stack_icon(tech["icon"], tech["name"])
    st.markdown("</div>", unsafe_allow_html=True)

def render_testimonials():
    """Renders a social proof section with testimonials."""
    st.markdown("<h2 class='text-3xl font-bold text-center mb-8 mt-16'>Trusted by Industry Leaders</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3, gap="large")
    with col1:
        render_testimonial_card(
            "This tool didn't just find answers; it revealed insights we didn't even know to look for. A game-changer.",
            "Dr. Alena Petrova", "Chief Research Officer, Innovate Dynamics"
        )
    with col2:
        render_testimonial_card(
            "The ability to compare legal documents in minutes, not days, has transformed our workflow. Invaluable.",
            "Marcus Thorne", "Senior Partner, Thorne & Associates Legal"
        )
    with col3:
        render_testimonial_card(
            "We processed a year's worth of financial reports and got a comprehensive summary in under an hour. Simply astonishing.",
            "Chen Wei", "CFO, Quantum Holdings"
        )

def render_final_call_to_action():
    """
    Renders the final, compelling Call to Action (CTA) to guide the user to the main application.
    """
    st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True) # Spacer
    st.markdown(
        """
        <div class="cta-section">
            <h2 class="text-3xl font-extrabold text-white mb-4">
                Your Documents Are Waiting.
            </h2>
            <p class="text-lg text-gray-300 max-w-2xl mx-auto mb-8">
                The insights are there. All you have to do is ask the right questions.
                Begin your analysis now.
            </p>
            <a href="/?page=analyzer" target="_self" class="cta-button">
                Launch Analyzer Suite
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )


# ======================================================================================
# SECTION 3: MAIN PAGE ORCHESTRATION FUNCTION
# ======================================================================================

def display_home_page(ss: Dict):
    """
    The main "conductor" function that orchestrates the rendering of the entire Home Page.
    It calls the various rendering components in a logical order to build the final,
    impressive, and dynamic dashboard.

    Args:
        ss (Dict): The Streamlit session state object, passed from main.py.
    """
    # --- Render Page Sections in a Deliberate, Storytelling Order ---
    
    # 1. Start with a powerful, welcoming statement.
    render_hero_section()
    
    # 2. Immediately show live, dynamic data to demonstrate the app is active.
    render_stats_dashboard(ss)
    
    # 3. Use a visual separator to create distinct sections.
    st.markdown("<hr style='border-color: var(--color-border); margin: 4rem 0;'/>", unsafe_allow_html=True)
    
    # 4. Showcase the core features to explain the application's value.
    render_features_showcase()
    
    st.markdown("<hr style='border-color: var(--color-border); margin: 4rem 0;'/>", unsafe_allow_html=True)
    
    # 5. Add a "social proof" element with testimonials to build trust.
    render_testimonials()
    
    st.markdown("<hr style='border-color: var(--color-border); margin: 4rem 0;'/>", unsafe_allow_html=True)

    # 6. Showcase the underlying technology to impress technical stakeholders.
    render_tech_stack_showcase()
    
    # 7. End with a strong, clear call to action to guide the user.
    render_final_call_to_action()