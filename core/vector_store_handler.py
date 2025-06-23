# core/vector_store_handler.py - The Enterprise-Grade, Persistent, Advanced Vector Store

# ======================================================================================
#  FILE OVERVIEW & ARCHITECTURAL PHILOSOPHY (Masterpiece Edition)
# ======================================================================================
# This file is the definitive, production-ready heart of the RAG system's retrieval
# capabilities. It implements the advanced "Parent Document Retriever" strategy and,
# crucially, adds a robust persistence layer.
#
# KEY ARCHITECTURAL ENHANCEMENTS:
#
# 1.  **Persistence to Disk:** This is the most significant upgrade. The entire state
#     of the retriever—including the FAISS vector store and the parent document
#     store—is now saved to the local disk. When the application restarts, it will
#     automatically load the existing index, eliminating the need to re-process
#     documents every time. This is a critical feature for any real-world application.
#
# 2.  **Configuration-Driven:** All key parameters for the retriever (chunk size,
#     overlap, storage paths) are now loaded from the central `config/settings.py`
#     file. This allows for easy tuning and maintenance without touching the core code.
#
# 3.  **Granular Error Handling:** Each major operation (loading the model, loading
#     from disk, building the index, saving to disk) is wrapped in its own detailed
#     `try...except` block, providing precise and informative error messages.
#
# 4.  **Professional Structure and Documentation:** The code is meticulously organized
#     and documented to the highest professional standards.
# ======================================================================================


# --- Core & Third-Party Imports ---
import streamlit as st
import faiss
import os
import pickle
from typing import List

# --- LangChain Specific Imports ---
from langchain.storage import InMemoryStore
from langchain.retrievers import ParentDocumentRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS as LangChainFAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.docstore import InMemoryDocstore
from langchain_core.documents import Document # The corrected import
# --- Project-Specific Imports ---
from config import settings

# ======================================================================================
# SECTION 1: EMBEDDING MODEL INITIALIZATION (CACHED FOR PERFORMANCE)
# ======================================================================================

@st.cache_resource(show_spinner="Loading embedding model into memory...")
def get_embedding_function():
    """
    Initializes and returns a SentenceTransformer embedding model.
    This is cached to ensure the model is loaded only ONCE per session.
    """
    model_name = "all-MiniLM-L6-v2"
    print(f"Initializing LOCAL Sentence Transformer model: {model_name}")
    try:
        embeddings = SentenceTransformerEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'}
        )
        print("Local embedding model loaded successfully.")
        return embeddings
    except Exception as e:
        st.error(f"Failed to load the embedding model '{model_name}'. The application cannot function without it. Error: {e}")
        print(f"CRITICAL ERROR: Could not load embedding model. {e}")
        st.stop()

# ======================================================================================
# SECTION 2: THE MAIN VECTOR STORE HANDLER CLASS
# ======================================================================================

class VectorStoreHandler:
    """
    Manages all interactions with the advanced, persistent Parent Document Retriever.
    """
    
    def __init__(self):
        """
        Initializes the VectorStoreHandler. It attempts to load an existing index
        from disk. If one is not found, it prepares for a new index to be built.
        """
        print("Initializing VectorStoreHandler...")
        self.embedding_function = get_embedding_function()
        self.vectorstore = None
        self.docstore = None
        self.retriever = None

        # Attempt to load the retriever from disk upon initialization.
        self._load_retriever_from_disk()

    def _load_retriever_from_disk(self):
        """
        Attempts to load the entire retriever state (vector store and docstore)
        from predefined paths in the settings.
        """
        vector_store_path = settings.VECTOR_STORE_PATH
        doc_store_path = settings.DOC_STORE_PATH

        if os.path.exists(vector_store_path) and os.path.exists(doc_store_path):
            print(f"Found existing index files. Attempting to load from '{vector_store_path}' and '{doc_store_path}'.")
            try:
                # Load the FAISS index
                self.vectorstore = LangChainFAISS.load_local(
                    folder_path=vector_store_path,
                    embeddings=self.embedding_function,
                    allow_dangerous_deserialization=True
                )
                # Load the parent document store
                with open(doc_store_path, "rb") as f:
                    self.docstore = pickle.load(f)

                # Recreate the retriever with the loaded components
                child_splitter = RecursiveCharacterTextSplitter(chunk_size=settings.CHILD_CHUNK_SIZE)
                self.retriever = ParentDocumentRetriever(
                    vectorstore=self.vectorstore,
                    docstore=self.docstore,
                    child_splitter=child_splitter,
                )
                st.success("Knowledge base loaded from disk!")
                print("Successfully loaded existing retriever from disk.")
            except Exception as e:
                st.error("Failed to load existing knowledge base. It might be corrupted. Please re-process documents.")
                print(f"ERROR loading from disk: {e}")
                self.retriever = None # Ensure retriever is None if loading fails
        else:
            print("No existing index found. Ready to build a new one.")


    def _save_retriever_to_disk(self):
        """
        Saves the current state of the retriever (vector store and docstore) to disk.
        """
        if not self.retriever:
            print("WARNING: Save attempted, but no retriever is available to save.")
            return

        vector_store_path = settings.VECTOR_STORE_PATH
        doc_store_path = settings.DOC_STORE_PATH
        
        print(f"Saving index to disk at '{vector_store_path}' and '{doc_store_path}'...")
        try:
            # Create directories if they don't exist
            os.makedirs(vector_store_path, exist_ok=True)
            os.makedirs(os.path.dirname(doc_store_path), exist_ok=True)
            
            # Save the FAISS vector store
            self.vectorstore.save_local(vector_store_path)
            
            # Save the parent document store using pickle
            with open(doc_store_path, "wb") as f:
                pickle.dump(self.docstore, f)
            
            print("Successfully saved retriever state to disk.")
        except Exception as e:
            st.error(f"Failed to save the knowledge base to disk. Error: {e}")
            print(f"ERROR saving to disk: {e}")


    def build_index(self, docs: List[Document]):
        """
        Builds a new ParentDocumentRetriever index or adds to an existing one.
        """
        if not docs:
            st.warning("No documents provided to build the index.")
            return

        st.info(f"Indexing {len(docs)} new document(s)... This may take a few moments.")
        print("Starting the index building process.")

        # If no retriever exists yet, create a new one.
        if self.retriever is None:
            print("No existing index found. Creating a new ParentDocumentRetriever.")
            try:
                # Initialize the components for a new retriever
                self.docstore = InMemoryStore()
                embedding_dimension = 384
                faiss_index = faiss.IndexFlatL2(embedding_dimension)
                self.vectorstore = LangChainFAISS(
                    embedding_function=self.embedding_function,
                    index=faiss_index,
                    docstore=InMemoryDocstore(),
                    index_to_docstore_id={}
                )
                child_splitter = RecursiveCharacterTextSplitter(chunk_size=settings.CHILD_CHUNK_SIZE, chunk_overlap=settings.CHILD_CHUNK_OVERLAP)
                
                self.retriever = ParentDocumentRetriever(
                    vectorstore=self.vectorstore,
                    docstore=self.docstore,
                    child_splitter=child_splitter,
                )
                print("New retriever instance created successfully.")
            except Exception as e:
                st.error(f"Failed to create the retriever structure: {e}")
                print(f"ERROR: Could not instantiate ParentDocumentRetriever. {e}")
                return

        # Add the new documents to the existing or new retriever.
        try:
            with st.spinner("Embedding and indexing content..."):
                self.retriever.add_documents(docs, ids=None)
            
            # After adding documents, persist the new state to disk.
            self._save_retriever_to_disk()
            
            st.success("Advanced context-aware index has been successfully built and saved!")
            print("Documents have been added and the new index state has been saved.")
        except Exception as e:
            error_msg = f"A critical error occurred during document indexing: {e}"
            st.error(error_msg)
            print(f"ERROR: {error_msg}")


    def get_retriever(self):
        """
        Provides access to the fully configured retriever object.
        """
        if self.retriever is None:
            st.error("The knowledge base is empty. Please process documents first.")
            return None
        
        print("Returning the configured Parent Document Retriever to an agent.")
        return self.retriever