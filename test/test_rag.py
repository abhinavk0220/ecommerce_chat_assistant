# backend/test_rag.py

from rag.chunking import load_raw_documents, split_documents
from rag.vectorstore import build_vectorstore_from_chunks, VECTORSTORE_DIR
from rag.rag_chain import answer_with_rag


def main():
    print("Vectorstore dir:", VECTORSTORE_DIR)

    # 1. Load & chunk docs (indexing step)
    docs = load_raw_documents()
    print(f"Loaded {len(docs)} raw document(s).")

    chunked_docs = split_documents(docs, chunk_size=300, chunk_overlap=60)
    print(f"Split into {len(chunked_docs)} chunks.")

    # 2. Build / refresh vector store
    vectordb = build_vectorstore_from_chunks(chunked_docs)
    print("Vector store built and persisted.")

    # 3. Ask a RAG question
    question = "My device is not turning on. What should I do?"
    print("\nUser Question:", question)

    result = answer_with_rag(question, k=3)
    answer = result["answer"]
    context_docs = result["context_docs"]

    print("\n--- RAG Answer ---")
    print(answer)

    print("\n--- Context Documents Used ---")
    for i, doc in enumerate(context_docs, start=1):
        print(f"\n[Doc {i}] Source:", doc.metadata.get("source"))
        print(doc.page_content)


if __name__ == "__main__":
    main()
