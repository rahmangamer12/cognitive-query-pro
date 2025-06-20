# agents/qa_agent.py - The Final, Advanced, and Production-Grade Q&A Agent

# ======================================================================================
#  FILE OVERVIEW
# ======================================================================================
# This file contains the logic for the most critical user-facing agent: the Q&A Agent.
# This version is a complete, production-grade rewrite that addresses previous issues
# by implementing a more robust and advanced RAG (Retrieval-Augmented Generation) pipeline.
#
# Key Architectural Enhancements:
# 1.  **Correct Usage of ParentDocumentRetriever**: The chain is now built to be
#     100% compatible with the `ParentDocumentRetriever`, ensuring full context is
#     always passed to the Language Model. This is the primary fix for the
#     "information not available" issue.
# 2.  **Conversational Chain**: We will introduce the capability to handle conversational
#     follow-up questions by rephrasing the user's question based on chat history.
# 3.  **Extreme Robustness**: Every step, from API key validation to the final API call,
#     is wrapped in detailed error handling to provide clear feedback and prevent crashes.
# 4.  **Clarity and Documentation**: The code is heavily documented with explanations for
#     every major decision, making it a professional and maintainable asset.
# ======================================================================================


# --- Core LangChain and Third-Party Imports ---
import streamlit as st
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# --- Project-Specific Imports ---
from config import settings, prompts

# ======================================================================================
# SECTION 1: HELPER AND UTILITY FUNCTIONS
# ======================================================================================

def get_chat_history(chat_history_list: List[Dict]) -> str:
    """
    A simple formatter to convert a list of chat messages into a single string.
    This is used for the question rephrasing step.
    
    Args:
        chat_history_list: A list of dictionaries, e.g., [{"role": "user", "content": "..."}]

    Returns:
        A formatted string of the conversation.
    """
    return "\n".join(f"{msg['role']}: {msg['content']}" for msg in chat_history_list)

# ======================================================================================
# SECTION 2: CORE AGENT LOGIC
# ======================================================================================

def create_conversational_rag_chain(retriever, llm):
    """
    Creates the main RAG chain, now enhanced to be aware of conversation history.
    This allows the user to ask follow-up questions.
    """
    # --- Contextual Question Rephrasing Prompt ---
    # This prompt helps the LLM rephrase a follow-up question into a standalone question
    # based on the prior conversation. e.g., "what about that one?" -> "what about the financial report?"
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    
    # --- History-Aware Retriever ---
    # This chain first takes the user's input and chat history, rephrases the
    # question, and then uses that rephrased question to call the retriever.
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # --- Final Answering Prompt ---
    # This is the prompt that will be used to generate the final answer,
    # now using the retrieved context.
    qa_system_prompt = prompts.QNA_PROMPT_TEMPLATE  # We use our professional prompt from config
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )

    # --- Document Combining Chain ---
    # This chain takes the retrieved documents and "stuffs" them into the final prompt.
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # --- The Final Retrieval Chain ---
    # This ties everything together. It first runs the history-aware retriever
    # and then passes the results to the question-answering chain.
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    return rag_chain

# ======================================================================================
# SECTION 3: MAIN AGENT EXECUTION FUNCTION
# ======================================================================================

def execute_qa_chain(retriever, query: str, chat_history: List[Dict]):
    """
    Executes the complete, conversational Question-Answering (Q&A) chain.
    This is the public-facing function called by the UI.

    Workflow:
    1.  **API Key Validation**: Ensures the Google API key is available.
    2.  **LLM Initialization**: Configures the Gemini model.
    3.  **Chain Creation**: Builds the advanced, history-aware RAG chain.
    4.  **Invocation & Error Handling**: Runs the chain with the current query and
        past conversation, handling any errors gracefully.
    
    Args:
        retriever: The configured ParentDocumentRetriever instance.
        query (str): The user's latest question.
        chat_history (List[Dict]): The history of the conversation from the UI.

    Returns:
        A string containing the answer generated by the Gemini model.
    """
    print("Executing Advanced Conversational Q&A Agent (Gemini)...")

    # --- Step 1: Pre-execution Validation ---
    if not settings.GOOGLE_API_KEY:
        error_message = "Google Gemini API Key is not configured. Please set it in your environment."
        st.error(error_message)
        print(f"ERROR: {error_message}")
        return error_message

    # --- Step 2: Language Model (LLM) Initialization ---
    try:
        llm = ChatGoogleGenerativeAI(
            model=settings.QNA_MODEL, 
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
        )
        print(f"Successfully initialized Google Gemini model: {settings.QNA_MODEL}")
    except Exception as e:
        error_message = f"Failed to initialize Google Gemini model: {e}"
        st.error(error_message)
        print(f"ERROR: {error_message}")
        return "Error: Could not connect to the Q&A service."

    # --- Step 3: Create the RAG Chain ---
    try:
        conversational_rag_chain = create_conversational_rag_chain(retriever, llm)
        print("Conversational RAG chain created successfully.")
    except Exception as e:
        error_message = f"Failed to build the Q&A chain: {e}"
        st.error(error_message)
        print(f"ERROR: {error_message}")
        return "Internal Error: Could not prepare the agent's logic."

    # --- Step 4: Invocation and Final Output ---
    final_answer = ""
    try:
        print(f"Invoking Conversational RAG chain with query: '{query[:50]}...'")
        
        # We now pass the chat history along with the user input.
        response_dict = conversational_rag_chain.invoke(
            {"input": query, "chat_history": chat_history}
        )
        
        # The output of create_retrieval_chain is a dictionary. The final answer is in the 'answer' key.
        final_answer = response_dict.get("answer", "No answer was generated.")

    except Exception as e:
        error_message = f"An error occurred while getting the answer from Gemini: {e}"
        print(f"ERROR in Q&A Agent invocation: {error_message}")
        st.error(error_message)
        final_answer = "Sorry, the Q&A Agent encountered a problem and could not provide an answer."
        
    print("Q&A Agent finished execution.")

    # --- Final Sanity Check ---
    if "not available in the provided documents" in final_answer:
        final_answer += "\n\n*(**Developer Note:** The agent could not find a relevant answer. Please use the 'Debugging' tab to inspect the context being retrieved for your query. The issue is likely with the retrieved context, not the agent itself.)*"

    return final_answer