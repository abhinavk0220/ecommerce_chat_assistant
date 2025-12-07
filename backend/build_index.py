# backend/build_index.py

"""
Build the vector store index from raw documents.
Run this once to create the RAG knowledge base.
"""

from rag.chunking import load_raw_documents, split_documents
from rag.vectorstore import build_vectorstore_from_chunks

def main():
    print("🔨 Building RAG vector store index...")
    
    # Step 1: Load raw documents
    print("\n📄 Loading raw documents...")
    raw_docs = load_raw_documents()
    print(f"✅ Loaded {len(raw_docs)} document(s)")
    
    # Step 2: Split into chunks
    print("\n✂️  Splitting documents into chunks...")
    chunks = split_documents(raw_docs, chunk_size=1000, chunk_overlap=200)
    print(f"✅ Created {len(chunks)} chunks")
    
    # Step 3: Build vector store
    print("\n🗄️  Building vector store (this may take a minute)...")
    vectordb = build_vectorstore_from_chunks(chunks)
    print(f"✅ Vector store created with {vectordb._collection.count()} embeddings")
    
    print("\n✨ Index building complete!")
    print("You can now start the FastAPI server with: uvicorn app:app --reload")

if __name__ == "__main__":
    main()