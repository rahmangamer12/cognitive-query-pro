# core/vector_store_handler.py - The Advanced Vector Store with Parent Document Retriever

# ======================================================================================
#  FILE OVERVIEW
# ======================================================================================
# This file is the heart of the RAG system's retrieval capabilities. Instead of a
# simple vector store, it implements an advanced strategy called the "Parent
# Document Retriever".
#
# Why Parent Document Retriever?
# - Standard RAG can suffer from context fragmentation. Small chunks might match a
#   query but lack the surrounding context needed for a high-quality answer (e.g.,
#   finding a "title" when the chunk only contains a paragraph).
# - The Parent Document Retriever solves this by searching over small, precise chunks
#   but returning the larger "parent" documents from which those chunks were derived.
#   This provides the LLM with the full, rich context needed for complex reasoning and Q&A.
#
# This implementation is robust, cached for performance, and well-documented.
# ======================================================================================


# --- Core Streamlit and Python Imports ---
import streamlit as st
import faiss # The core FAISS library for vector indexing

# --- LangChain Specific Imports ---
from langchain.storage import InMemoryStore
from langchain.retrievers import ParentDocumentRetriever
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS as LangChainFAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.docstore import InMemoryDocstore

# --- Project-Specific Imports ---
from config import settings

# ======================================================================================
# SECTION 1: EMBEDDING MODEL INITIALIZATION (CACHED FOR PERFORMANCE)
# ======================================================================================

@st.cache_resource(show_spinner="Loading embedding model into memory...")
def get_embedding_function():
    """
    Initializes and returns a SentenceTransformer embedding model.
    
    This function is decorated with `@st.cache_resource`, a powerful Streamlit feature.
    It ensures that the potentially large and slow-to-load embedding model is loaded
    into memory only ONCE for the entire duration of the app session. All subsequent
    calls to this function will instantly return the cached model object, dramatically
    improving performance and reducing resource usage.

    Returns:
        An instance of SentenceTransformerEmbeddings, ready to convert text to vectors.
    """
    # 'all-MiniLM-L6-v2' is a popular, high-performance model that is small enough
    # to run efficiently on a CPU. It creates 384-dimensional embeddings.
    model_name = "all-MiniLM-L6-v2"
    
    print(f"Initializing LOCAL Sentence Transformer embeddings model: {model_name}")
    print("This will be cached. If it's the first run, it may download the model.")
    
    # We specify the device as 'cpu' to ensure compatibility across different systems,
    # even those without a dedicated GPU.
    embeddings = SentenceTransformerEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'}
    )
    
    print("Local embedding model loaded successfully.")
    return embeddings

# ======================================================================================
# SECTION 2: THE MAIN VECTOR STORE HANDLER CLASS
# ======================================================================================

class VectorStoreHandler:
    """
    Manages all interactions with the advanced Parent Document Retriever.

    This class encapsulates the entire logic for:
    - Creating the vector store for small, searchable "child" chunks.
    - Creating a document store for the original, large "parent" documents.
    - Configuring and building the ParentDocumentRetriever.
    - Providing a method to get the fully configured retriever for use by the agents.
    """
    
    def __init__(self):
        """
        Initializes the VectorStoreHandler.
        
        It immediately gets the cached embedding function and sets the internal
        retriever attribute to None. The actual index is not built until the
        `build_index` method is called with documents.
        """
        self.embedding_function = get_embedding_function()
        self.vectorstore = None
        self.docstore = None
        self.retriever = None
        print("VectorStoreHandler initialized. Ready to build index.")

    def build_index(self, docs: list):
        """
        Builds the complete ParentDocumentRetriever index from a list of full documents.

        This is the core method that sets up the advanced RAG strategy.

        Args:
            docs (list): A list of LangChain Document objects (the full, original documents).
        """
        if not docs:
            st.warning("No documents provided to build the index. Process cannot continue.")
            return

        st.info("Building an advanced context-aware index... This may take a few moments.")
        print("Starting the build process for the Parent Document Retriever.")

        # --- Step 1: Initialize the Document Store ---
        # The `docstore` will hold the original, full-length documents (the "parents").
        # When the retriever finds a relevant small chunk, it will use the ID to
        # fetch the full parent document from this store.
        self.docstore = InMemoryStore()
        print("In-memory document store for parent documents initialized.")

        # --- Step 2: Initialize the Vector Store for Child Chunks ---
        # This is where the small, embedded chunks will live. We use FAISS for this
        # because it is extremely fast for similarity searches.
        
        # We need to define the dimensionality of the embeddings. For 'all-MiniLM-L6-v2', it's 384.
        embedding_dimension = 384
        # We use IndexFlatL2, a standard FAISS index for Euclidean distance search.
        faiss_index = faiss.IndexFlatL2(embedding_dimension)
        
        # We create a LangChain FAISS wrapper around the core FAISS index.
        # This wrapper needs its own docstore for mapping, which is different from our parent docstore.
        self.vectorstore = LangChainFAISS(
            embedding_function=self.embedding_function,
            index=faiss_index,
            docstore=InMemoryDocstore(), # Internal docstore for the vector store itself
            index_to_docstore_id={}
        )
        print("FAISS vector store for child chunks initialized.")

        # --- Step 3: Define the Child Splitter ---
        # This text splitter will be used by the retriever to create the small,
        # searchable chunks from the parent documents.
        # A smaller chunk size (e.g., 400) is good for finding very specific, relevant text.
        child_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
        print(f"Child splitter configured with chunk size {400}.")

        # --- Step 4: Create the Parent Document Retriever ---
        # This is the main object that ties everything together.
        # It takes the vector store (for searching) and the docstore (for retrieving parents).
        self.retriever = ParentDocumentRetriever(
            vectorstore=self.vectorstore,
            docstore=self.docstore,
            child_splitter=child_splitter,
            # We could also define a `parent_splitter` if we wanted to split
            # the original documents into medium-sized "parent" chunks, but for
            # simplicity, we are using the full original documents as parents.
        )
        print("Parent Document Retriever instantiated.")

        # --- Step 5: Add Documents to the Retriever ---
        # The `.add_documents()` method of the ParentDocumentRetriever is a powerful,
        # all-in-one function. It automatically:
        # 1. Stores the original `docs` in the `docstore`.
        # 2. Uses the `child_splitter` to create small chunks from `docs`.
        # 3. Generates embeddings for these small chunks.
        # 4. Adds the embedded chunks to the `vectorstore`.
        # 5. Manages the link between child chunks and their parent documents.
        
        try:
            with st.spinner("Indexing document content..."):
                self.retriever.add_documents(docs, ids=None)
            st.success("Advanced context-aware index has been successfully built!")
            print("Documents have been added to the Parent Document Retriever.")
        except Exception as e:
            error_msg = f"A critical error occurred during index building: {e}"
            st.error(error_msg)
            print(f"ERROR: {error_msg}")


    def get_retriever(self):
        """
        Provides access to the fully configured retriever object.

        The agents will call this method to get the tool they need for fetching
        relevant context before generating a response.

        Returns:
            The configured ParentDocumentRetriever instance, or None if the
            index has not been built yet.
        """
        if self.retriever is None:
            # This is a safeguard in case this method is called before `build_index`.
            st.error("The vector index has not been built yet. Please process documents first.")
            return None
        
        # Note: The ParentDocumentRetriever does not support metadata filtering in the same
        # way a standard vector store retriever does. Its strength lies in providing
        # the full context of the parent document, which often makes granular filtering
        # less necessary, as the LLM can discern the source from the full context.
        print("Returning the configured Parent Document Retriever to an agent.")
        return self.retriever