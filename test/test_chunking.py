# backend/test_chunking.py

from backend.rag.chunking import load_raw_documents, split_documents, RAW_DATA_DIR

def main():
    print("Raw data dir:", RAW_DATA_DIR)

    docs = load_raw_documents()
    print(f"Loaded {len(docs)} raw document(s).")
    for d in docs:
        print("Source:", d.metadata.get("source"))
        print("Content preview:", d.page_content[:120], "...")
        break

    chunked_docs = split_documents(docs, chunk_size=300, chunk_overlap=60)
    print(f"After chunking: {len(chunked_docs)} chunks.")
    print("--- Example chunks ---")
    for i, cd in enumerate(chunked_docs[:3]):
        print(f"\nChunk {i+1}:")
        print(cd.page_content)
        print("Metadata:", cd.metadata)

if __name__ == "__main__":
    main()
