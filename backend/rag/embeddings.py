# backend/rag/embeddings.py

"""
Embeddings module.

This provides a reusable function to get a sentence-transformer-based
embedding model for our RAG pipeline. We use a dedicated embedding model
instead of the main LLM because it's faster, cheaper, and optimized
for semantic similarity search.
"""

from typing import List
# from langchain_huggingface import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings


# Default embedding model name (Hugging Face repo id)
DEFAULT_EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL_NAME) -> HuggingFaceEmbeddings:
    """
    Returns a LangChain-compatible embedding model instance.

    The returned object exposes .embed_documents() and .embed_query()
    which we will plug directly into our vector store (ChromaDB).
    """
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    return embeddings


# Optional: small helper for direct use without LangChain vector store (for tests)
def embed_texts(texts: List[str], model_name: str = DEFAULT_EMBEDDING_MODEL_NAME):
    """
    Convenience helper to embed a list of texts into vectors.
    """
    embeddings = get_embedding_model(model_name=model_name)
    return embeddings.embed_documents(texts)
