# backend/test_embeddings.py

from backend.rag.embeddings import get_embedding_model, embed_texts

def main():
    texts = [
        "The customer ordered a laptop and wants to know the delivery status.",
        "When will my laptop arrive? I want to track my order.",
        "I am asking about refund policies for headphones."
    ]

    # Get embeddings via helper
    vectors = embed_texts(texts)
    print(f"Got {len(vectors)} vectors with dimension {len(vectors[0])}")

    # (Optional) Quick similarity check using cosine similarity
    # Between text[0] and text[1] vs text[0] and text[2]
    import numpy as np

    v0, v1, v2 = map(lambda v: np.array(v), vectors)

    def cosine(a, b):
        return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

    sim_0_1 = cosine(v0, v1)
    sim_0_2 = cosine(v0, v2)

    print("Similarity(text0, text1) =", sim_0_1)
    print("Similarity(text0, text2) =", sim_0_2)

if __name__ == "__main__":
    main()
