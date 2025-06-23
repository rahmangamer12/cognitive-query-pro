# agents/qa_agent.py - The Final, Definitive, and Production-Grade Q&A Agent (v11.0)
# ======================================================================================
#  ARCHITECTURAL OVERVIEW (STABLE & CORRECT)
# ======================================================================================
# This is the definitive, stable, and correct rewrite of the Q&A Agent. It resolves
# the critical `AttributeError: 'str' object has no attribute 'get'` by implementing
# a more advanced LangChain Expression Language (LCEL) chain that guarantees a
# dictionary output containing both the answer and the source documents.
#
# KEY ARCHITECTURAL FIX:
#
# 1.  GUARANTEED DICTIONARY OUTPUT: The agent is rebuilt using `RunnableParallel` to
#     ensure the final output is ALWAYS a dictionary like `{"answer": ..., "source_documents": ...}`.
#     This is the definitive fix for the bug.
#
# 2.  STABLE & ROBUST: The chain logic is now modern, stable, and less prone to
#     unexpected output formats from the underlying LangChain functions.
#
# 3.  FUNCTIONAL "SHOW SOURCES": Because the source documents are now correctly
#     passed through the entire chain, the "Show Sources" feature in the UI will
#     now work perfectly.
# ======================================================================================

# --- Core LangChain and Third-Party Imports ---
import streamlit as st
from typing import List, Dict

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain

from config import settings

# ======================================================================================
# SECTION 1: CORE AGENT LOGIC (DEFINITIVE REWRITE)
# ======================================================================================

def create_conversational_rag_chain(retriever, llm):
    """
    Creates the main RAG chain, enhanced to be history-aware and to guarantee
    a dictionary output with both answer and sources.
    """
    # Prompt to rephrase a follow-up question into a standalone question
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    # This chain rephrases the question and then retrieves documents
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_q_prompt
    )

    # Prompt to generate the final answer using the retrieved context
    qa_system_prompt = """You are an expert assistant for question-answering tasks.
    Use the following pieces of retrieved context to answer the question.
    If you don't know the answer, just say that you don't know.
    Keep the answer concise and professional.

    CONTEXT:
    {context}
    """
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    # This chain takes the context and question and generates an answer
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

    # --- THE DEFINITIVE FIX: USING RunnableParallel ---
    # This `rag_chain` first runs the retriever to get documents, then passes those
    # documents AND the original question to the `question_answer_chain`.
    # `RunnableParallel` ensures that the `source_documents` are passed through alongside the answer.
    rag_chain = RunnableParallel(
        {"source_documents": history_aware_retriever, "question": RunnablePassthrough()}
    ).assign(
        answer=lambda x: question_answer_chain.invoke(
            {
                "context": x["source_documents"],
                "input": x["question"]["input"],
                "chat_history": x["question"]["chat_history"]
            }
        )
    )
    
    return rag_chain

# ======================================================================================
# SECTION 2: MAIN AGENT EXECUTION FUNCTION
# ======================================================================================

def execute_qa_chain(retriever, query: str, chat_history: List[Dict]) -> Dict:
    """
    Executes the complete, conversational Q&A chain. This is the public-facing
    function called by the UI. It now robustly returns a dictionary.

    Returns:
        A dictionary containing the 'answer' and 'source_documents'.
    """
    print("Executing Stable Conversational Q&A Agent (v11)...")

    # --- Pre-execution Validation ---
    if not settings.GOOGLE_API_KEY:
        error_msg = "Google Gemini API Key is not configured."
        return {"answer": error_msg, "source_documents": []}

    # --- LLM Initialization ---
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=settings.GOOGLE_API_KEY, temperature=0.2)
    except Exception as e:
        error_msg = f"Failed to initialize Google Gemini model: {e}"
        return {"answer": error_msg, "source_documents": []}

    # --- Chain Creation & Invocation ---
    try:
        conversational_rag_chain = create_conversational_rag_chain(retriever, llm)
        response_dict = conversational_rag_chain.invoke(
            {"input": query, "chat_history": chat_history}
        )
        print("Q&A Agent finished execution successfully.")
        return response_dict

    except Exception as e:
        error_msg = f"An error occurred in the Q&A agent pipeline: {e}"
        print(f"ERROR: {error_msg}")
        st.error(error_msg)
        return {"answer": "Sorry, an internal error occurred. Please check the system logs.", "source_documents": []}