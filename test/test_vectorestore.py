# backend/test_vectorstore.py

from rag.chunking import load_raw_documents, split_documents
from rag.vectorstore import build_vectorstore_from_chunks, get_vectorstore, VECTORSTORE_DIR


def main():
    print("Using vectorstore dir:", VECTORSTORE_DIR)

    # 1. Load raw docs
    docs = load_raw_documents()
    print(f"Loaded {len(docs)} raw document(s).")

    # 2. Chunk docs
    chunked_docs = split_documents(docs, chunk_size=300, chunk_overlap=60)
    print(f"Split into {len(chunked_docs)} chunks.")

    # 3. Build vector store
    vectordb = build_vectorstore_from_chunks(chunked_docs)
    print("Vector store built and persisted.")

    # 4. Test similarity search
    query = "My device is not turning on. What should I do?"
    results = vectordb.similarity_search(query, k=3)

    print("\n--- Search Results (Fresh Vectorstore) ---")
    for i, doc in enumerate(results, start=1):
        print(f"\nResult {i}:")
        print(doc.page_content)
        print("Source:", doc.metadata.get("source"))

    # 5. Reload vector store from disk
    vectordb_reloaded = get_vectorstore()
    results_reloaded = vectordb_reloaded.similarity_search(query, k=3)

    print("\n--- Search Results (Reloaded Vectorstore) ---")
    for i, doc in enumerate(results_reloaded, start=1):
        print(f"\nResult {i}:")
        print(doc.page_content)
        print("Source:", doc.metadata.get("source"))


if __name__ == "__main__":
    main()
