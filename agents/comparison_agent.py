# agents/comparison_agent.py - Specialized Comparative Analysis Agent

import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from config import settings, prompts

def format_docs_for_comparison(docs: list) -> str:
    """
    Formats retrieved documents for a comparison task.
    It clearly separates content from different sources to help the LLM.
    
    Args:
        docs (list): A list of LangChain Document objects with metadata.

    Returns:
        str: A formatted string with clear source indicators for each document chunk.
    """
    formatted_texts = []
    for doc in docs:
        # Extract the source filename from the metadata
        source = doc.metadata.get("source", "Unknown Source")
        # Prepend the source to the content for clarity
        formatted_text = f"--- START OF CONTENT FROM: {source} ---\n\n{doc.page_content}\n\n--- END OF CONTENT FROM: {source} ---"
        formatted_texts.append(formatted_text)
    
    # Join all formatted blocks with a clear separator
    return "\n\n================================\n\n".join(formatted_texts)

def execute_comparison_chain(retriever, query: str):
    """
    Executes a chain designed specifically for comparing information across documents.

    This function follows a structured process:
    1.  Configures the retriever to fetch a larger number of documents to ensure
        it gets context from all relevant sources for comparison.
    2.  Sets up a powerful language model (GPT-4o) capable of complex reasoning.
    3.  Uses a specialized prompt that guides the LLM to perform a structured comparison.
    4.  Formats the retrieved documents to clearly label their sources before
        passing them to the LLM.

    Args:
        retriever: The configured vector store retriever.
        query (str): The user's request to compare documents.

    Returns:
        A structured comparative analysis from the language model.
    """
    # --- 1. LLM Configuration ---
    # A powerful model is essential for the nuanced task of comparison.
    try:
        llm = ChatOpenAI(
            model=settings.REPORT_MODEL,  # GPT-4o is excellent for this
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.3,  # Low temperature to keep the analysis factual and grounded
            max_tokens=4000
        )
    except Exception as e:
        st.error(f"Failed to initialize the OpenAI model: {e}")
        return "Error: Could not connect to the comparison service."

    # --- 2. Prompt Template ---
    # We use the dedicated comparison prompt defined in our config.
    prompt = ChatPromptTemplate.from_template(prompts.COMPARISON_PROMPT_TEMPLATE)

    # --- 3. Retriever Configuration ---
    # For comparison, we need to retrieve more documents to ensure we have
    # context from all the files the user wants to compare.
    retriever.search_kwargs['k'] = 12  # Increase 'k' to fetch more chunks
    print(f"Retriever configured to fetch up to {retriever.search_kwargs['k']} chunks for comparison.")

    # --- 4. LangChain Expression Language (LCEL) Chain ---
    # This chain is optimized for comparison tasks.
    comparison_chain = (
        {"context": retriever | format_docs_for_comparison, "input": RunnablePassthrough()}
        | prompt
        | llm
    )

    # --- 5. Invocation and Output ---
    st.info("The Comparison Agent is performing a deep analysis across documents...")
    print("Executing Comparison Agent (OpenAI) with specialized chain...")
    
    try:
        # Invoke the chain with the user's comparison query.
        result = comparison_chain.invoke(query)
        final_answer = result.content
    except Exception as e:
        # Handle potential errors during the API call.
        print(f"ERROR in Comparison Agent invocation: {e}")
        st.error(f"An error occurred during the comparison: {e}")
        final_answer = "Sorry, an error prevented the comparison from being completed."

    print("Comparison Agent finished execution.")
    return final_answer