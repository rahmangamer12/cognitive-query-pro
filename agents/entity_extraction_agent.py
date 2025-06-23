# agents/entity_extraction_agent.py - The Advanced, Multi-Schema, Structured Data Extraction Pipeline (Powered by Gemini)

# ======================================================================================
#  FILE OVERVIEW & ARCHITECTURAL PHILOSOPHY
# ======================================================================================
# This file contains the logic for a professional-grade entity extraction agent. It
# moves beyond a single extraction call to a sophisticated, multi-step pipeline that
# significantly improves accuracy, robustness, and the richness of the extracted data.
#
# Key Architectural Features:
#
# 1.  **Multi-Schema Extraction Engine:**
#     Instead of one large, complex schema, this agent utilizes multiple, smaller,
#     domain-specific schemas (e.g., for People/Orgs, Financial Data, Project Details).
#     This modular approach allows the LLM to focus its "attention" on one type of
#     information at a time, dramatically increasing the accuracy of the extraction.
#
# 2.  **Intelligent Text Chunking for Large Documents:**
#     The agent is designed to handle documents of any size. It includes a text
#     splitter that breaks down massive documents into manageable, overlapping chunks.
#     It then runs the extraction process on each chunk and intelligently merges the
#     unique entities found across all chunks, ensuring comprehensive analysis.
#
# 3.  **Powered by Gemini with Function Calling:**
#     It leverages the powerful instruction-following and function-calling capabilities
#     of the Google Gemini model, which is highly effective for structured data tasks.
#
# 4.  **Structured DataFrame Output:**
#     The final output is a clean, well-organized Pandas DataFrame, perfect for direct
#     rendering in the Streamlit UI. This provides a professional, dashboard-like
#     experience for the end-user.
#
# 5.  **Comprehensive Error Handling and Logging:**
#     Every step of the complex pipeline is wrapped in robust error handling and
#     provides detailed logs to the console, making it transparent and easy to debug.
# ======================================================================================

# --- Core & Third-Party Imports ---
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional

# --- LangChain & Google Imports ---
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_extraction_chain

# --- Project-Specific Imports ---
from config import settings

# ======================================================================================
# SECTION 1: ADVANCED SCHEMA DEFINITIONS
# ======================================================================================

# We define multiple schemas to guide the LLM's extraction process.

# Schema for extracting key figures and organizations.
KEY_FIGURES_SCHEMA = {
    "properties": {
        "people": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of full names of individuals (e.g., 'John Doe', 'Dr. Jane Smith')."
        },
        "organizations": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of company, government, or institutional names (e.g., 'Cognitive Corp', 'University of AI')."
        },
    },
    "required": ["people", "organizations"],
}

# Schema for extracting numerical and financial data.
FINANCIAL_DATA_SCHEMA = {
    "properties": {
        "monetary_values": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of specific monetary values mentioned (e.g., '$1.5 million', '€250,000 budget')."
        },
        "key_percentages": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of important percentages or statistical figures (e.g., '25% market share', '10% growth')."
        },
    },
    "required": ["monetary_values", "key_percentages"],
}

# Schema for extracting project-specific details.
PROJECT_DETAILS_SCHEMA = {
    "properties": {
        "project_names": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of official project names or codenames (e.g., 'Project Phoenix', 'The Alpha Initiative')."
        },
        "key_dates_and_deadlines": {
            "type": "array",
            "items": {"type": "string"},
            "description": "A list of crucial dates, milestones, or deadlines (e.g., 'Q4 2024 Launch', 'deadline of June 1st')."
        },
    },
    "required": ["project_names", "key_dates_and_deadlines"],
}

# A master list of all schemas to iterate over. Adding new extraction tasks is as
# simple as defining a new schema and adding it to this list.
ALL_SCHEMAS = {
    "Key Figures & Orgs": KEY_FIGURES_SCHEMA,
    "Financial & Numerical Data": FINANCIAL_DATA_SCHEMA,
    "Project Details": PROJECT_DETAILS_SCHEMA,
}

# ======================================================================================
# SECTION 2: CORE EXTRACTION LOGIC
# ======================================================================================

def run_single_extraction(llm: ChatGoogleGenerativeAI, text_chunk: str, schema: Dict, schema_name: str) -> List:
    """
    Runs a single extraction chain for a given text chunk and schema.
    
    Args:
        llm: The initialized Gemini model instance.
        text_chunk: A piece of text to extract entities from.
        schema: The JSON schema defining what to extract.
        schema_name: The name of the schema (for logging).

    Returns:
        The raw list output from the LangChain extraction chain.
    """
    try:
        # `create_extraction_chain` is a powerful function that uses the LLM's
        # function-calling capabilities to force a structured JSON output.
        extraction_chain = create_extraction_chain(schema, llm)
        print(f"  - Running extraction for schema: '{schema_name}'...")
        
        # Invoke the chain with the text chunk.
        extracted_results = extraction_chain.invoke({"input": text_chunk})
        
        # The result is a dictionary, with the data inside the "text" key.
        return extracted_results.get("text", [])
    except Exception as e:
        print(f"  - WARNING: Extraction for schema '{schema_name}' failed: {e}")
        return []

def merge_extracted_results(all_results: Dict[str, set]) -> pd.DataFrame:
    """
    Merges the results from multiple extraction runs into a single, clean Pandas DataFrame.

    Args:
        all_results: A dictionary where keys are entity types and values are sets of unique entities.

    Returns:
        A formatted Pandas DataFrame ready for display.
    """
    print("Merging all extracted entities into a final DataFrame...")
    
    display_data = []
    # Iterate through the dictionary of unique entities.
    for entity_type, entity_set in all_results.items():
        if entity_set: # Only process if entities of this type were found.
            for entity_name in sorted(list(entity_set)):
                display_data.append({
                    "Category": entity_type.replace("_", " ").title(),
                    "Extracted Information": entity_name
                })
    
    if not display_data:
        print("No entities were found across all schemas.")
        return pd.DataFrame([{"Status": "No specific entities could be extracted from this document."}])
        
    final_df = pd.DataFrame(display_data)
    print(f"Successfully created final DataFrame with {len(final_df)} entities.")
    return final_df

# ======================================================================================
# SECTION 3: MAIN AGENT EXECUTION FUNCTION
# ======================================================================================

def execute_entity_extraction_chain(document: Document) -> Optional[pd.DataFrame]:
    """
    Executes the full, multi-schema entity extraction pipeline on a document.

    This function orchestrates the entire process:
    1.  Validates API keys and input.
    2.  Initializes the Gemini model.
    3.  Chunks the document if it's too large.
    4.  Iterates through each schema and each text chunk, running extraction.
    5.  Collects and de-duplicates all found entities.
    6.  Formats the final results into a clean Pandas DataFrame.

    Args:
        document (Document): The full document object to be analyzed.

    Returns:
        A Pandas DataFrame containing the extracted entities, or None on failure.
    """
    print("-" * 50)
    print(f"Entity Extraction Agent invoked for document: '{document.metadata.get('source', 'Unknown')}'")
    
    # --- Step 1: Pre-execution Validation ---
    if not document or not document.page_content.strip():
        st.warning("Cannot extract entities from an empty document.")
        return None
        
    if not settings.GOOGLE_API_KEY:
        error_message = "Google Gemini API Key is not configured. Entity Extraction is unavailable."
        st.error(error_message)
        return None

    # --- Step 2: LLM Initialization ---
    try:
        # For extraction, we want a model that is good at following instructions.
        # Gemini Flash is fast and cost-effective for this structured data task.
        llm = ChatGoogleGenerativeAI(
            model=settings.QNA_MODEL, # Using Gemini as requested
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.0 # Temperature must be 0 for predictable, non-creative extraction.
        )
        print(f"Entity Extraction LLM ({settings.QNA_MODEL}) initialized.")
    except Exception as e:
        error_message = f"Failed to initialize Google Gemini model for extraction: {e}"
        st.error(error_message)
        return None

    # --- Step 3: Text Chunking for Large Documents ---
    # We create a text splitter to handle documents that might exceed the LLM's context window.
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=16000, chunk_overlap=800)
    text_chunks = text_splitter.split_text(document.page_content)
    print(f"Document split into {len(text_chunks)} chunk(s) for extraction.")

    # --- Step 4: Iterative Extraction Engine ---
    # This dictionary will store all unique entities found across all chunks and schemas.
    # Using a set automatically handles de-duplication.
    all_unique_entities = {
        "people": set(), "organizations": set(),
        "monetary_values": set(), "key_percentages": set(),
        "project_names": set(), "key_dates_and_deadlines": set(),
    }

    # Create a progress bar for the user.
    st.info(f"Analyzing {len(text_chunks) * len(ALL_SCHEMAS)} data points. This may take a moment...")
    progress_bar = st.progress(0, text="Starting entity extraction...")
    total_steps = len(text_chunks) * len(ALL_SCHEMAS)
    current_step = 0

    # Loop through each text chunk...
    for i, chunk in enumerate(text_chunks):
        print(f"Processing chunk {i + 1}/{len(text_chunks)}...")
        
        # ...and for each chunk, loop through each extraction schema.
        for schema_name, schema in ALL_SCHEMAS.items():
            
            # Update progress
            current_step += 1
            progress_bar.progress(current_step / total_steps, text=f"Analyzing for: {schema_name}")
            
            # Run the extraction for this specific schema and chunk.
            raw_results = run_single_extraction(llm, chunk, schema, schema_name)
            
            # The result is a list (usually with one item) of dictionaries.
            if raw_results:
                for result_dict in raw_results:
                    for entity_type, entity_list in result_dict.items():
                        # The key in the result dict is something like "people_mentioned".
                        # We need to match this to our `all_unique_entities` keys.
                        # e.g., "people_mentioned" -> "people"
                        matched_key = entity_type.split('_')[0]
                        if matched_key in all_unique_entities and isinstance(entity_list, list):
                            # Add all found entities to our set.
                            for entity in entity_list:
                                all_unique_entities[matched_key].add(entity)

    progress_bar.progress(1.0, text="Extraction complete! Compiling results...")
    
    # --- Step 5: Format Final Output ---
    # Convert the dictionary of sets into a clean Pandas DataFrame.
    final_dataframe = merge_extracted_results(all_unique_entities)
    
    print("Entity Extraction Agent finished execution.")
    print("-" * 50)
    return final_dataframe