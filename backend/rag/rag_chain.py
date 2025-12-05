# backend/rag/rag_chain.py

"""
RAG chain module.

This module wires together:
- The Chroma vector store (retriever)
- The embedding-based retrieval
- The Gemini LLM (via our llm_adapter)

It exposes a high-level function `answer_with_rag` that:
1. Retrieves relevant document chunks for a user query.
2. Builds a grounded prompt that includes those chunks as context.
3. Asks Gemini to answer based ONLY on that context.
4. Returns both the answer and the underlying context documents.
"""

from typing import List, Dict, Any

from langchain_core.documents import Document

from .vectorstore import get_vectorstore
from llm_adapter import get_llm

def dedupe_docs(docs: List[Document]) -> List[Document]:
    """
    Deduplicate documents based on (source, content).

    This is a safety net in case the vector store contains repeated
    entries for the same chunk.
    """
    seen = set()
    unique_docs: List[Document] = []
    for d in docs:
        key = (d.metadata.get("source", ""), d.page_content.strip())
        if key not in seen:
            seen.add(key)
            unique_docs.append(d)
    return unique_docs


def get_retriever(k: int = 3):
    """
    Returns a retriever built on top of the Chroma vector store.

    `k` controls how many top similar chunks we retrieve for each query.
    """
    vectordb = get_vectorstore()
    retriever = vectordb.as_retriever(search_kwargs={"k": k})
    return retriever


def build_rag_prompt(question: str, docs: List[Document]) -> str:
    """
    Builds a RAG-style prompt for the LLM.

    Includes:
    - Clear instructions to only use context
    - The retrieved document chunks
    - The user question

    We also label each document as [Doc i] so the model can cite them.
    """

    context_blocks = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        block = f"[Doc {i} | Source: {source}]\n{doc.page_content}"
        context_blocks.append(block)

    context_text = "\n\n".join(context_blocks)

    instructions = """
You are a helpful assistant that answers questions based ONLY on the provided context documents.

Rules:
- If the answer is clearly present in the context, answer concisely and clearly.
- If the answer is NOT in the context, say: "I’m not sure based on the available information."
- Do NOT invent facts that are not supported by the context.
- When you use information from a specific document, mention it in brackets like [Doc 1], [Doc 2], etc.
- You can refer to multiple documents if needed, e.g., [Doc 1][Doc 3].
"""

    prompt = f"""{instructions}

Context:
{context_text}

User question:
{question}

Answer (follow the rules above):
"""
    return prompt


def answer_with_rag(
    question: str,
    k: int = 3,
) -> Dict[str, Any]:
    ...

    # Step 1: retrieve relevant documents
    retriever = get_retriever(k=k)
    raw_docs: List[Document] = retriever.invoke(question)
    context_docs: List[Document] = dedupe_docs(raw_docs)

    # Step 2: build the RAG prompt
    prompt = build_rag_prompt(question, context_docs)

    # Step 3: call Gemini LLM
    llm = get_llm(provider="gemini")
    response = llm.generate_content(prompt)

    answer_text = response.text if hasattr(response, "text") else str(response)

    return {
        "answer": answer_text,
        "context_docs": context_docs,
        "sources": [
            {
                "id": i,
                "source": doc.metadata.get("source", "unknown"),
                "preview": doc.page_content[:200],
            }
            for i, doc in enumerate(context_docs, start=1)
        ],
    }
