# backend/rag/chunking.py

"""
Chunking and document loading module.

This module is responsible for:
1. Loading raw text documents from the /data/raw directory.
2. Splitting them into semantically meaningful chunks using a
   recursive character-based text splitter with overlap.

These chunks will later be embedded and stored in the vector database
(Chroma) for our RAG pipeline.
"""

from pathlib import Path
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document


# Base project root = two levels up from this file: backend/rag/chunking.py -> backend -> project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def load_raw_documents(
    raw_dir: Path = RAW_DATA_DIR,
    glob_pattern: str = "**/*.txt",
) -> List[Document]:
    """
    Loads all .txt files from the raw data directory as LangChain Documents.

    Each file becomes one Document with metadata including the source path.

    For now, we support .txt (and .md if glob_pattern changed). We can
    extend this loader later for PDFs or other formats.
    """
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    documents: List[Document] = []

    for file_path in raw_dir.rglob(glob_pattern):
        # Use TextLoader for simple text files
        loader = TextLoader(str(file_path), encoding="utf-8")
        docs = loader.load()
        # Add extra metadata like filename
        for d in docs:
            d.metadata["source"] = str(file_path)
        documents.extend(docs)

    return documents


def get_text_splitter(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> RecursiveCharacterTextSplitter:
    """
    Returns a configured RecursiveCharacterTextSplitter.

    chunk_size and chunk_overlap are in characters.
    A chunk_size of ~1000 characters with 200 overlap roughly corresponds
    to ~250-300 word chunks, which is a good default for RAG.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,  # character-based measurement
    )
    return splitter


def split_documents(
    docs: List[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[Document]:
    """
    Splits a list of Documents into smaller chunks using the configured splitter.

    Returns a new list of Documents where:
    - page_content = chunk text
    - metadata is inherited from original docs (plus optional extra info)
    """
    splitter = get_text_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunked_docs = splitter.split_documents(docs)
    return chunked_docs
