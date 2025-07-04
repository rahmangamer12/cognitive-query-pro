# agents/report_agent.py - The Final, Self-Contained, and Production-Ready Report Agent

# This agent specializes in synthesizing information from multiple document chunks
# to generate structured, comprehensive, and insightful reports.

# --- Core LangChain and Third-Party Imports ---
import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# --- Project-Specific Imports ---
from config import settings, prompts

# ======================================================================================
# --- Helper Function for Document Formatting ---
# ======================================================================================

def format_retrieved_docs(docs: list) -> str:
    """
    A utility function to format the list of retrieved documents into a single,
    clean string block. This formatted string will serve as the 'context' for the LLM.

    Args:
        docs (list): A list of LangChain Document objects.

    Returns:
        str: A single string containing all document content, ready for the prompt.
    """
    # Using a clear separator helps the model understand document boundaries.
    separator = "\n\n--- Document Snippet ---\n\n"
    formatted_string = separator.join([doc.page_content for doc in docs])
    
    # Add a header for extra clarity to the LLM.
    return f"Context from relevant documents:\n{formatted_string}"

# ======================================================================================
# --- Main Agent Execution Function ---
# ======================================================================================

def execute_report_chain(retriever, query: str):
    """
    Executes the complete Report Generation chain using the OpenAI GPT-4o model.

    This function is the powerhouse of the application, designed for complex synthesis.

    Workflow:
    1.  **API Key Validation**: Securely checks for the OpenAI API key from the environment.
    2.  **LLM Initialization**: Configures the powerful GPT-4o model, optimized for report writing.
    3.  **Prompt Engineering**: Loads the detailed, persona-driven report prompt from config.
    4.  **Chain Construction (LCEL)**: Builds a RAG chain to feed context to the model.
    5.  **Invocation & Error Handling**: Runs the chain and manages any potential API failures.

    Args:
        retriever: The configured vector store retriever (from FAISS).
        query (str): The user's detailed request for a report or summary.

    Returns:
        A string containing the formatted report generated by the OpenAI model,
        or a user-friendly error message if the process fails.
    """
    # --- Step 1: Pre-execution Validation ---
    print("Executing Report Agent (OpenAI)...")
    if not settings.OPENAI_API_KEY:
        error_message = "OpenAI API Key is not configured. Please set it in your .env file or deployment secrets."
        st.error(error_message)
        print(f"ERROR: {error_message}")
        return error_message

    # --- Step 2: Language Model (LLM) Initialization ---
    try:
        # We initialize GPT-4o, a top-tier model ideal for complex reasoning,
        # synthesis, and following structured formatting instructions.
        # Temperature is balanced to allow for fluent writing while staying factual.
        llm = ChatOpenAI(
            model=settings.REPORT_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.5,  # Allows for well-written, coherent text.
            max_tokens=4000,  # Generous token limit for detailed reports.
        )
        print(f"Successfully initialized OpenAI model: {settings.REPORT_MODEL}")
    except Exception as e:
        error_message = f"Failed to initialize the OpenAI model: {e}"
        st.error(error_message)
        print(f"ERROR: {error_message}")
        return "Error: Could not connect to the report generation service. Please check your OpenAI API key."

    # --- Step 3: Prompt Template Setup ---
    try:
        report_prompt = ChatPromptTemplate.from_template(prompts.REPORT_PROMPT_TEMPLATE)
    except Exception as e:
        error_message = f"Failed to load Report prompt template: {e}"
        st.error(error_message)
        print(f"ERROR: {error_message}")
        return "Internal Error: Could not prepare the agent's instructions."

    # --- Step 4: Building the RAG Chain using LCEL ---
    # This chain is structured to provide the maximum relevant context to the LLM.
    
    # The flow is identical to the Q&A agent but uses the specialized report prompt and LLM.
    # 1. Retrieve documents based on the query.
    # 2. Format them into a single context string.
    # 3. Pass the context and the original query to the prompt template.
    # 4. Send the filled prompt to the powerful GPT-4o model.
    # 5. Parse the output into a clean string.
    
    rag_chain = (
        {"context": retriever | format_retrieved_docs, "input": RunnablePassthrough()}
        | report_prompt
        | llm
        | StrOutputParser()
    )

    # --- Step 5: Invoking the Chain and Final Output ---
    final_answer = ""
    st.info("The Report Agent is analyzing documents and compiling the report...")
    
    try:
        print(f"Invoking Report RAG chain with query: '{query[:50]}...'")
        # Run the entire pipeline. This might take a few seconds for complex reports.
        final_answer = rag_chain.invoke(query)
        
    except Exception as e:
        # This will catch common OpenAI API errors, like:
        # - AuthenticationError (if the key is invalid or has no credits)
        # - RateLimitError (if you make too many requests too quickly)
        # - APIConnectionError (if there's a network issue)
        error_message = f"An error occurred while generating the report from OpenAI: {e}"
        print(f"ERROR in Report Agent invocation: {error_message}")
        st.error(error_message)
        final_answer = "Sorry, the Report Agent encountered a problem and could not complete your request."
        
    print("Report Agent finished execution.")
    return final_answer