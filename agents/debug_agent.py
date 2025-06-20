# agents/debug_agent.py

import streamlit as st

def execute_debug_chain(retriever, query: str) -> str:
    """
    This is not a real agent. It's a debugging tool.
    It takes a query, uses the retriever to find relevant documents,
    and then simply SHOWS what it found, instead of sending it to an LLM.
    This helps us see exactly what context the real agents are working with.
    """
    print(f"DEBUG AGENT: Retrieving documents for query: '{query}'")
    
    try:
        # Use the retriever to get the relevant document chunks
        retrieved_docs = retriever.get_relevant_documents(query)
        
        # Check if any documents were found
        if not retrieved_docs:
            return "**DEBUG RESULT:**\n\nThe retriever did not find ANY relevant documents for your query. This is why the Q&A agent cannot answer."
        
        # If documents were found, format them for display
        response = "**DEBUG RESULT:**\n\nThe retriever found the following content to answer your query:\n\n---\n"
        
        for i, doc in enumerate(retrieved_docs):
            source = doc.metadata.get('source', 'Unknown')
            content_preview = doc.page_content[:500] # Show a preview of the content
            
            response += f"**Chunk {i+1} (from: {source})**\n"
            response += f"```text\n{content_preview}...\n```\n---\n"
            
        response += "\nIf this content does not contain the answer, the Q&A agent will fail. Check if the content of your files is correct."
        
        return response
        
    except Exception as e:
        error_message = f"**DEBUG ERROR:**\n\nAn error occurred during the retrieval process: {e}"
        st.error(error_message)
        return error_message