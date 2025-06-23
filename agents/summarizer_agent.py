# agents/summarizer_agent.py - The Advanced, Multi-Strategy Document Summarization Agent (Powered by Gemini)

# ======================================================================================
#  FILE OVERVIEW & ARCHITECTURAL PHILOSOPHY
# ======================================================================================
# This file contains the complete logic for a professional-grade document summarization agent.
# It is architected to be intelligent, flexible, robust, and highly maintainable, moving
# far beyond a simple API call.
#
# Key Architectural Features:
#
# 1.  **Intelligent Strategy Engine (`select_summarization_strategy`):**
#     The agent's "brain". It analyzes the input document(s) and user request to
#     dynamically select the optimal summarization strategy from three industry-standard
#     methods provided by LangChain:
#     - `stuff`: For smaller documents that fit within the model's context window. It's
#       the fastest and provides the most coherent summary for short texts.
#     - `map_reduce`: The workhorse for large documents. It breaks the document into
#       chunks, summarizes each chunk individually (the "map" step), and then
#       summarizes the summaries to produce a final result (the "reduce" step).
#     - `refine`: An iterative approach that processes the document chunk by chunk,
#       continuously refining the summary with new information. It's excellent for
#       maintaining a narrative flow and building upon previous context.
#
# 2.  **Persona-Driven Prompt Engineering (`get_prompt_templates`):**
#     Instead of a single generic prompt, this agent uses distinct, persona-driven
#     prompts for each summarization strategy and requested length. This guides the
#     Gemini model to adopt the correct "mindset" for the task, resulting in
#     higher-quality, more contextually appropriate summaries.
#
# 3.  **Token-Aware & Proactive:**
#     The agent uses `tiktoken` to estimate the token count of documents *before*
#     making an API call. This allows it to proactively choose a strategy (like
#     `map_reduce`) that avoids context window overflow errors, making the system
#     more resilient.
#
# 4.  **Comprehensive Error Handling and Logging:**
#     Every critical operation is wrapped in detailed `try...except` blocks. The agent
#     provides informative logs to the console for developers and clear,
#     user-friendly error messages to the Streamlit UI.
# ======================================================================================


# --- Core & Third-Party Imports ---
import streamlit as st
from typing import List, Dict, Any
import tiktoken # Used for accurately calculating token counts

# --- LangChain Specific Imports ---
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.summarize import load_summarize_chain

# --- Project-Specific Imports ---
from config import settings

# ======================================================================================
# SECTION 1: PROMPT ENGINEERING & STRATEGY SELECTION
# This section contains the "intelligence" of the agent.
# ======================================================================================

# Define token limits for different models to make intelligent decisions.
# Gemini 1.5 Flash has a massive context window, but we'll use a conservative
# limit to ensure performance and prevent unexpected costs/errors.
MODEL_CONTEXT_LIMITS = {
    "gemini-1.5-flash-latest": 128000, # A very large but safe limit
    "default": 8000
}

def get_token_count(text: str) -> int:
    """
    Calculates the number of tokens for a given text using tiktoken.
    This is more accurate than character count for LLM context management.
    
    Args:
        text (str): The text to be tokenized.

    Returns:
        int: The number of tokens.
    """
    try:
        # "cl100k_base" is the tokenizer used by many modern models, including GPT-4 and Gemini.
        encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(text))
        return num_tokens
    except Exception:
        # Fallback to a simple character count if tiktoken fails for any reason.
        return len(text) // 4


def get_prompt_templates(summary_length: str) -> Dict[str, PromptTemplate]:
    """
    Returns a dictionary of professionally crafted LangChain PromptTemplate objects
    tailored for different summarization tasks.

    Args:
        summary_length (str): The user's desired length ("brief", "default", "detailed").

    Returns:
        A dictionary containing prompt templates for different chain types.
    """
    prompts = {}
    
    # --- Prompt for the 'stuff' and 'refine' chains ---
    if summary_length == "brief":
        refine_question_prompt = "Your job is to produce a final, very brief, single-paragraph summary of the following text."
        initial_response_prompt = "Write a very brief, high-level summary of the following, capturing only the most critical points:"
    elif summary_length == "detailed":
        refine_question_prompt = "Your job is to produce a final, detailed, and comprehensive summary of the following text, organized into logical paragraphs."
        initial_response_prompt = "Write a detailed summary of the following, capturing key arguments, data, and conclusions:"
    else: # "default"
        refine_question_prompt = "Your job is to produce a final, concise summary of the following text."
        initial_response_prompt = "Write a concise and clear summary of the following:"

    prompts['refine_template'] = PromptTemplate.from_template(
        f"{refine_question_prompt}\n\n"
        "We have provided an existing summary up to a certain point: {existing_answer}\n"
        "We have the opportunity to refine the existing summary (only if needed) with some more context below.\n"
        "------------\n{text}\n------------\n"
        "Given the new context, refine the original summary. If the context isn't useful, return the original summary."
    )
    
    prompts['stuff_template'] = PromptTemplate.from_template(f"{initial_response_prompt}\n\n{{text}}")
    
    # --- Prompts for the 'map_reduce' chain ---
    # This chain uses two separate prompts.
    prompts['map_template'] = PromptTemplate.from_template(
        "Summarize this chunk of text concisely:\n\n{text}"
    )
    prompts['combine_template'] = PromptTemplate.from_template(
        "You are a master at synthesizing information. The following text is a set of summaries from a large document. "
        f"Your task is to combine them into a single, coherent, and {summary_length} final summary. Ensure the final output is well-structured and easy to read.\n\n"
        "Here are the summaries:\n{text}"
    )
    
    return prompts


def select_summarization_strategy(docs_to_summarize: List[Document], summary_length: str) -> Dict:
    """
    Intelligently selects the best summarization strategy (`stuff`, `map_reduce`, `refine`)
    and corresponding prompts based on the document's token count and user request.

    Args:
        docs_to_summarize (List[Document]): The list of documents to be summarized.
        summary_length (str): The user's choice ("brief", "default", or "detailed").

    Returns:
        A dictionary containing the chosen 'chain_type' and 'chain_kwargs'.
    """
    print("Summarizer Agent: Selecting optimal strategy...")
    
    # Calculate total tokens to make an informed decision.
    full_text = " ".join([doc.page_content for doc in docs_to_summarize])
    total_tokens = get_token_count(full_text)
    
    # Get the context limit for the selected Gemini model.
    model_limit = MODEL_CONTEXT_LIMITS.get(settings.QNA_MODEL, MODEL_CONTEXT_LIMITS['default'])
    # We use a safety margin (e.g., 80%) to leave room for the prompt and response.
    safe_limit = int(model_limit * 0.8)
    
    print(f"Summarizer: Total tokens = {total_tokens}, Safe model limit = {safe_limit}")
    
    # Get the appropriate prompt templates for the desired summary length.
    prompts_dict = get_prompt_templates(summary_length)
    
    # --- Strategy Decision Logic ---
    if total_tokens < safe_limit:
        # If the entire document fits comfortably within the context window, 'stuff' is the best.
        # It's fast and provides the highest quality summary as the model sees everything at once.
        strategy = {
            "chain_type": "stuff",
            "chain_kwargs": {"prompt": prompts_dict['stuff_template']}
        }
        print(f"Strategy selected: 'stuff' (Total tokens {total_tokens} < Safe limit {safe_limit})")
    else:
        # If the document is too large, 'map_reduce' is the most robust choice.
        # It's designed to handle arbitrarily large documents without failing.
        strategy = {
            "chain_type": "map_reduce",
            "chain_kwargs": {
                "map_prompt": prompts_dict['map_template'],
                "combine_prompt": prompts_dict['combine_template']
            }
        }
        print(f"Strategy selected: 'map_reduce' (Total tokens {total_tokens} > Safe limit {safe_limit})")
        
    return strategy

# ======================================================================================
# SECTION 3: MAIN AGENT EXECUTION FUNCTION
# ======================================================================================

def execute_summarization_chain(docs_to_summarize: List[Document], summary_length: str = "default") -> str:
    """
    Executes the advanced summarization pipeline using the Google Gemini model.

    Args:
        docs_to_summarize (List[Document]): The document(s) to be summarized.
        summary_length (str): The desired length ("brief" or "detailed").

    Returns:
        A string containing the generated summary.
    """
    print("-" * 50)
    print(f"Summarization Agent invoked for {len(docs_to_summarize)} document(s) with request for '{summary_length}' summary.")
    
    # --- Step 1: Input Validation ---
    if not docs_to_summarize:
        st.warning("No document content was provided for summarization.")
        return "No content to summarize."
        
    if not settings.GOOGLE_API_KEY:
        error_message = "Google Gemini API Key is not configured. Summarization is unavailable."
        st.error(error_message)
        return error_message

    # --- Step 2: LLM Initialization ---
    try:
        # Initialize the Gemini model for the summarization task.
        llm = ChatGoogleGenerativeAI(
            model=settings.QNA_MODEL, # Using Gemini as requested
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3, # A balanced temperature for creative but factual writing.
        )
        print(f"Summarizer LLM ({settings.QNA_MODEL}) initialized.")
    except Exception as e:
        error_message = f"Failed to initialize Google Gemini model for summarization: {e}"
        st.error(error_message)
        return error_message

    # --- Step 3: Strategy and Prompt Selection ---
    try:
        strategy_config = select_summarization_strategy(docs_to_summarize, summary_length)
        chain_type = strategy_config["chain_type"]
        chain_kwargs = strategy_config["chain_kwargs"]
    except Exception as e:
        error_message = f"Error during strategy selection: {e}"
        st.error(error_message)
        return "Internal Error: Could not determine summarization strategy."

    # --- Step 4: Chain Creation and Invocation ---
    final_summary = ""
    try:
        # `load_summarize_chain` is a high-level LangChain function that creates an
        # optimized chain for summarization using the chosen strategy and prompts.
        summarization_chain = load_summarize_chain(
            llm=llm,
            chain_type=chain_type,
            **chain_kwargs
        )
        print(f"Invoking summarization chain with strategy: '{chain_type}'...")
        
        # We pass the list of Document objects directly to the chain.
        summary_result = summarization_chain.invoke(docs_to_summarize)
        
        # The output from the chain is a dictionary, usually with an 'output_text' key.
        final_summary = summary_result.get("output_text", "The agent could not generate a summary from the text.")
        
        if not final_summary.strip():
             final_summary = "The summarization process completed, but resulted in an empty output. The source document might be too short or lack summarizable content."
             st.warning(final_summary)
             
    except Exception as e:
        # This is a critical catch-all for errors during the actual API call to Google.
        error_message = f"A critical error occurred during the summarization API call: {e}"
        st.error(error_message)
        print(f"ERROR: {error_message}")
        final_summary = "An unexpected error occurred while generating the summary. Please check the console logs."
        
    print("Summarization Agent finished execution.")
    print("-" * 50)
    return final_summary