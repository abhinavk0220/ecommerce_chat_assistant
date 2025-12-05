# backend/rag/vectorstore.py

"""
Vector store module using ChromaDB.

This module is responsible for:
1. Building a persistent Chroma vector store from chunked documents.
2. Reloading the existing vector store for use in RAG retrieval.

We use Chroma because:
- It runs locally without extra services.
- It supports persistence (survives restarts).
- It supports metadata filtering.
- It integrates cleanly with LangChain.
"""

from pathlib import Path
from typing import List
import shutil


from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from .embeddings import get_embedding_model


# Compute project root (same logic as in chunking.py)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTORSTORE_DIR = PROJECT_ROOT / "data" / "vectorstore"


def build_vectorstore_from_chunks(
    chunked_docs: List[Document],
    persist_directory: Path = VECTORSTORE_DIR,
) -> Chroma:
    """
    Creates a Chroma vector store from a list of chunked Documents and
    persists it to disk.

    This should be run as an indexing step (e.g., one-time or whenever
    the knowledge base is updated).
    """
    # During development, clear any previous index to avoid duplicates.
    if persist_directory.exists():
        shutil.rmtree(persist_directory)

    persist_directory.mkdir(parents=True, exist_ok=True)

    embedding_model = get_embedding_model()

    vectordb = Chroma.from_documents(
        documents=chunked_docs,
        embedding=embedding_model,
        persist_directory=str(persist_directory),
    )

    # Persist to disk explicitly (though Chroma does it implicitly as well)
    vectordb.persist()
    return vectordb


def get_vectorstore(
    persist_directory: Path = VECTORSTORE_DIR,
) -> Chroma:
    """
    Loads an existing Chroma vector store from disk.

    Assumes that `build_vectorstore_from_chunks` has already been run
    at least once to populate the database.
    """
    if not persist_directory.exists():
        raise FileNotFoundError(
            f"Vectorstore directory not found: {persist_directory}. "
            "Have you run the indexing step?"
        )

    embedding_model = get_embedding_model()

    vectordb = Chroma(
        embedding_function=embedding_model,
        persist_directory=str(persist_directory),
    )
    return vectordb
