# agents/router_agent.py - The Final, Intelligent, and Robust Task Router Agent

# This agent acts as the central dispatcher. Its sole responsibility is to analyze
# the user's intent and route the query to the most appropriate specialized agent.

# --- Core LangChain and Third-Party Imports ---
import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# --- Project-Specific Imports ---
from config import settings, prompts

# ======================================================================================
# --- Helper Function for Fallback Routing ---
# ======================================================================================

def fallback_router(query: str) -> str:
    """
    A simple, rule-based fallback router that is used if the LLM-based router fails.
    This ensures the application remains functional even if the routing model is down.
    It uses keyword matching to make a "best guess" decision.

    Args:
        query (str): The user's query string.

    Returns:
        str: The name of the agent to route to ('QNA_AGENT', 'REPORT_AGENT', or 'COMPARISON_AGENT').
    """
    print("WARNING: LLM router failed. Engaging rule-based fallback router.")
    
    # Convert query to lowercase for case-insensitive matching
    lower_query = query.lower()
    
    # Define keywords for each agent
    comparison_keywords = ['compare', 'contrast', 'vs', 'versus', 'difference', 'similarities']
    report_keywords = ['summarize', 'summary', 'report', 'overview', 'outline', 'detail']
    
    # Check for keywords in a specific order of priority (most specific first)
    if any(keyword in lower_query for keyword in comparison_keywords):
        print("Fallback decision: COMPARISON_AGENT")
        return "COMPARISON_AGENT"
    
    if any(keyword in lower_query for keyword in report_keywords):
        print("Fallback decision: REPORT_AGENT")
        return "REPORT_AGENT"
    
    # If no other keywords match, default to the Q&A agent, which is the most general.
    print("Fallback decision: QNA_AGENT (default)")
    return "QNA_AGENT"

# ======================================================================================
# --- Main Agent Execution Function ---
# ======================================================================================

def route_query(query: str) -> str:
    """
    Uses a fast LLM (GPT-3.5-Turbo) to analyze the user's query and decide which
    specialized agent (Q&A, Report, or Comparison) should handle the task.

    This function is critical for the "Agentic" behavior of the system.

    Workflow:
    1.  **API Key Validation**: Checks for the necessary OpenAI API key.
    2.  **LLM Initialization**: Sets up the fast and cost-effective GPT-3.5-Turbo model.
    3.  **Prompt Engineering**: Loads the detailed routing prompt that instructs the LLM on its task.
    4.  **Chain Construction**: Builds a simple but effective chain to process the query.
    5.  **Invocation & Validation**: Calls the LLM and validates the response.
    6.  **Fallback Logic**: If the LLM call fails for any reason, it uses a simpler,
        rule-based router to ensure the app doesn't crash.

    Args:
        query (str): The user's input query.

    Returns:
        A string containing the name of the chosen agent (e.g., "QNA_AGENT").
    """
    # --- Step 1: Pre-execution Validation ---
    print("Executing Router Agent to determine user intent...")
    if not settings.OPENAI_API_KEY:
        error_message = "OpenAI API Key is not configured for the Router Agent. Cannot determine query route."
        st.warning(error_message) # Use a warning as this might be recoverable
        print(f"ERROR: {error_message}")
        # If no key, we can't use the LLM, so we go straight to the fallback.
        return fallback_router(query)

    # --- Step 2: Language Model (LLM) Initialization ---
    try:
        # We use a fast and inexpensive model like gpt-3.5-turbo for routing,
        # as this is a simple classification task that doesn't require deep reasoning.
        # Temperature is set to 0 for maximum predictability and consistency.
        router_llm = ChatOpenAI(
            model=settings.ROUTER_MODEL, 
            openai_api_key=settings.OPENAI_API_KEY, 
            temperature=0,
            max_tokens=20 # The response is very short, so we can limit tokens.
        )
        print(f"Successfully initialized Router LLM: {settings.ROUTER_MODEL}")
    except Exception as e:
        error_message = f"Failed to initialize the Router LLM: {e}"
        st.warning(error_message)
        print(f"ERROR: {error_message}")
        return fallback_router(query)

    # --- Step 3: Prompt and Chain Construction ---
    try:
        # The prompt template is the "instruction manual" for our router LLM.
        routing_prompt = PromptTemplate.from_template(prompts.ROUTER_PROMPT_TEMPLATE)
        
        # We build the chain: The prompt is filled, then sent to the LLM,
        # and the output is parsed into a clean string.
        chain = routing_prompt | router_llm | StrOutputParser()
        
    except Exception as e:
        error_message = f"Failed to build the routing chain: {e}"
        st.error(error_message) # This is a more critical internal error
        print(f"ERROR: {error_message}")
        # If the chain can't be built, we can't proceed with the LLM.
        return fallback_router(query)

    # --- Step 4: Invocation, Validation, and Fallback ---
    decision = ""
    try:
        # Invoke the chain with the user's query.
        print(f"Routing query: '{query[:50]}...'")
        result = chain.invoke({"query": query})
        decision = result.strip().upper() # Sanitize the output
        print(f"LLM Router Decision: {decision}")

        # Validate the LLM's response to ensure it's one of the expected agent names.
        valid_agents = ["QNA_AGENT", "REPORT_AGENT", "COMPARISON_AGENT"]
        if decision not in valid_agents:
            print(f"WARNING: LLM returned an invalid agent name ('{decision}'). Engaging fallback.")
            return fallback_router(query)
        
        return decision

    except Exception as e:
        # If the API call fails for any reason (rate limit, network, etc.),
        # we log the error and use our reliable fallback.
        error_message = f"LLM routing failed: {e}. Using rule-based fallback."
        st.info("The intelligent router is momentarily unavailable. Using standard routing.")
        print(f"ERROR: {error_message}")
        return fallback_router(query)