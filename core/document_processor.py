# core/document_processor.py - The Robust, Extensible, and Production-Grade Document Processing Pipeline

# ======================================================================================
#  FILE OVERVIEW
# ======================================================================================
# This file is responsible for the crucial first step in the RAG pipeline: Ingestion.
# Its job is to take raw, user-uploaded files in various formats and convert them
# into a clean, standardized format that LangChain can understand (a list of
# LangChain `Document` objects).
#
# Key Architectural Decisions:
# 1.  **Modularity and Extensibility:** A `LOADER_MAPPING` dictionary is used to
#     easily add support for new file types in the future without changing the core logic.
# 2.  **Robustness:** The processing loop is wrapped in a `try...except` block for each
#     file, ensuring that a single corrupted or unreadable file does not halt the
#     entire batch processing operation.
# 3.  **Informative Feedback:** The function provides real-time feedback to both the
#     developer (via `print` statements) and the end-user (via `st.write` and `st.error`).
# 4.  **Decoupling:** This module is solely responsible for loading and preparing documents.
#     It does NOT perform text splitting; that responsibility is delegated to the
#     `VectorStoreHandler` (specifically the `ParentDocumentRetriever`), adhering to the
#     Single Responsibility Principle.
# ======================================================================================


# --- Core Streamlit and Python Imports ---
import os
import streamlit as st
from typing import List, Dict, Any, Callable

# --- LangChain Document Loader Imports ---
# We import all the necessary loaders for handling different file formats.
from langchain_community.document_loaders import (
    PyPDFLoader,          # For PDF files
    TextLoader,           # For .txt files
    Docx2txtLoader,       # For Microsoft Word .docx files
    UnstructuredFileLoader # A powerful fallback for various other types
)
from langchain_core.documents import Document

# ======================================================================================
# SECTION 1: LOADER CONFIGURATION
# ======================================================================================

# This mapping is the key to making our document processor extensible.
# To add a new file type, you simply add a new entry to this dictionary.
# The key is the file extension, and the value is a lambda function that
# returns an instance of the appropriate loader.
LOADER_MAPPING: Dict[str, Callable[[str], Any]] = {
    ".pdf": lambda path: PyPDFLoader(path, extract_images=False),
    ".txt": lambda path: TextLoader(path, encoding='utf-8'),
    ".docx": lambda path: Docx2txtLoader(path),
    # Add other file types here if needed in the future, e.g.:
    # ".csv": lambda path: CSVLoader(path),
    # ".html": lambda path: UnstructuredHTMLLoader(path),
}

# ======================================================================================
# SECTION 2: HELPER FUNCTIONS
# ======================================================================================

def get_loader_for_file(file_path: str, file_name: str) -> Any:
    """
    Selects the most appropriate document loader for a given file based on its extension.
    If a specific loader is not found for the extension, it defaults to the powerful
    `UnstructuredFileLoader` as a general-purpose fallback.

    Args:
        file_path (str): The full path to the temporary file on disk.
        file_name (str): The original name of the uploaded file.

    Returns:
        An instance of a LangChain DocumentLoader ready to be used.
    """
    # Extract the file extension and convert it to lowercase for case-insensitive matching.
    file_extension = os.path.splitext(file_name)[1].lower()
    
    # Look up the loader in our mapping.
    loader_callable = LOADER_MAPPING.get(file_extension)
    
    if loader_callable:
        # If a specific loader is found, instantiate it with the file path.
        print(f"Found specific loader for '{file_extension}' files.")
        st.write(f"-> Using `{loader_callable(file_path).__class__.__name__}` for `{file_name}`")
        return loader_callable(file_path)
    else:
        # If no specific loader is found, use the robust UnstructuredFileLoader.
        # This loader can handle a wide variety of file types, making our system flexible.
        print(f"No specific loader for '{file_extension}'. Defaulting to UnstructuredFileLoader.")
        st.write(f"-> Using `UnstructuredFileLoader` for unsupported type: `{file_name}`")
        return UnstructuredFileLoader(file_path, mode="single")

def create_and_log_temp_dir() -> str:
    """
    Creates a temporary directory for storing uploaded files if it doesn't already exist.
    This helps in keeping the project's root directory clean and organized.

    Returns:
        str: The path to the temporary directory.
    """
    # We name the directory clearly to indicate its purpose.
    temp_dir = "temp_uploaded_files"
    if not os.path.exists(temp_dir):
        print(f"Creating temporary directory for file processing at: '{temp_dir}'")
        os.makedirs(temp_dir)
    return temp_dir

# ======================================================================================
# SECTION 3: MAIN DOCUMENT PROCESSING FUNCTION
# ======================================================================================

@st.cache_data(show_spinner="Reading and preparing documents...")
def process_documents(uploaded_files: List[Any]) -> List[Document]:
    """
    The core function that orchestrates the entire document ingestion process.

    This function is cached using `@st.cache_data` to improve performance. If the same
    set of files is uploaded again, Streamlit will return the cached result instead of
    re-processing everything from scratch.

    The process involves:
    1.  Creating a temporary directory to store files.
    2.  Iterating through each uploaded file.
    3.  Saving the file to the temporary directory.
    4.  Selecting the appropriate loader for the file type.
    5.  Loading the document's content into memory.
    6.  Crucially, tagging each loaded document with its source filename in the metadata.
        This is essential for source-specific Q&A and for providing references.
    7.  Aggregating all loaded documents into a single list.

    Args:
        uploaded_files (list): A list of file-like objects from Streamlit's uploader.

    Returns:
        A list of LangChain `Document` objects. This list contains the full,
        un-chunked content of all successfully processed files.
    """
    if not uploaded_files:
        st.warning("No files were provided to the document processor.")
        return []

    # Get the path to the temporary directory.
    temp_dir = create_and_log_temp_dir()
    
    all_loaded_docs: List[Document] = []

    # Create a progress bar in the UI for a better user experience.
    progress_bar = st.progress(0, text="Starting document processing...")
    
    # Iterate through each uploaded file with an index for the progress bar.
    for i, file in enumerate(uploaded_files):
        # Update the progress bar and status text.
        progress_text = f"Processing file {i + 1}/{len(uploaded_files)}: {file.name}"
        progress_bar.progress((i + 1) / len(uploaded_files), text=progress_text)
        
        # Construct a temporary path and write the file's content to it.
        # This is necessary because LangChain loaders typically operate on file paths.
        temp_file_path = os.path.join(temp_dir, file.name)
        with open(temp_file_path, "wb") as f:
            f.write(file.getvalue())
        
        try:
            # Get the correct loader for the current file type.
            loader = get_loader_for_file(temp_file_path, file.name)
            
            # Load the document(s) from the file. A single file (like a PDF) can
            # result in multiple Document objects (one per page).
            docs_from_file = loader.load()
            
            # --- Metadata Enrichment ---
            # This is a critical step. We iterate through each document part (e.g., each page)
            # and add the original filename to its metadata. This allows us to trace
            # any piece of information back to its source file.
            for doc in docs_from_file:
                if 'source' not in doc.metadata:
                    doc.metadata['source'] = file.name
                # We could add more metadata here, like the upload timestamp.
                # doc.metadata['upload_time'] = time.time()
            
            # Add the processed documents from this file to our main list.
            all_loaded_docs.extend(docs_from_file)
            
            print(f"SUCCESS: Successfully loaded '{file.name}', found {len(docs_from_file)} document parts.")
            
        except Exception as e:
            # If any error occurs during the loading of a single file, we catch it,
            # display an error message in the UI, log it to the console, and
            # continue to the next file. This makes the process robust.
            error_msg = f"Error processing file '{file.name}': {e}"
            st.error(error_msg)
            print(f"ERROR: {error_msg}")
            # Continue to the next iteration of the loop.
            continue
    
    # Finalize the progress bar.
    progress_bar.progress(1.0, text="Document processing complete!")
    
    if not all_loaded_docs:
        st.error("Could not load any content from the uploaded files. Please check the files and try again.")
        return []

    # IMPORTANT: We return the full, un-chunked documents.
    # The responsibility of splitting these documents into smaller "child" chunks
    # now belongs to the ParentDocumentRetriever in the VectorStoreHandler.
    st.success(f"Successfully loaded {len(all_loaded_docs)} document pages from {len(uploaded_files)} files. Ready for indexing.")
    print(f"Document processing finished. Returning {len(all_loaded_docs)} full document objects.")

    return all_loaded_docs