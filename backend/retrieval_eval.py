# backend/retrieval_eval.py

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

from rag.rag_chain import answer_with_rag


BASE_DIR = Path(__file__).resolve().parents[1]
EVAL_FILE = BASE_DIR / "data" / "eval" / "test_cases.json"


def load_test_cases() -> List[Dict[str, Any]]:
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_source_path(path: str) -> str:
    """
    We only care about the filename, e.g. 'return_policy.txt'.
    """
    return Path(path).name.lower()


def compute_recall_precision_at_k(
    expected_files: List[str], retrieved_files: List[str]
) -> Dict[str, float]:
    """
    expected_files: e.g. ['return_policy.txt', 'general_faq.txt']
    retrieved_files: e.g. ['return_policy.txt', 'shipping_policy.txt', ...]
    """
    if not expected_files:
        return {"recall": 0.0, "precision": 0.0}

    exp_set = set(f.lower() for f in expected_files)
    ret_set = set(f.lower() for f in retrieved_files)

    hits = len(exp_set.intersection(ret_set))
    recall = hits / len(exp_set)
    precision = hits / len(ret_set) if ret_set else 0.0

    return {"recall": recall, "precision": precision}


def main():
    cases = load_test_cases()
    rag_cases = [
        c for c in cases if c.get("expected_source_files")
    ]  # only those with ground-truth docs

    if not rag_cases:
        print("No RAG test cases with expected_source_files defined.")
        return

    all_recalls = []
    all_precisions = []

    print("=== RAG Retrieval Evaluation (Recall@k, Precision@k) ===\n")

    for case in rag_cases:
        qid = case["id"]
        query = case["query"]
        expected_sources = case["expected_source_files"]

        print(f"--- Case: {qid} ---")
        print(f"Query: {query}")
        print(f"Expected source files: {expected_sources}")

        # Call our RAG pipeline directly
        rag_result = answer_with_rag(query, k=3)

        # Extract retrieved source file names from context_docs
        ctx_docs = rag_result.get("context_docs", []) or []
        retrieved_files = []
        for doc in ctx_docs:
            # doc should be a langchain Document-like object
            meta = getattr(doc, "metadata", None) or getattr(doc, "dict", lambda: {})().get("metadata", {})
            source_path = None
            if isinstance(meta, dict):
                source_path = meta.get("source")
            if not source_path and isinstance(doc, dict):
                # fallback if context_docs are already dicts
                source_path = doc.get("metadata", {}).get("source")

            if source_path:
                retrieved_files.append(normalize_source_path(source_path))

        print(f"Retrieved source files: {retrieved_files}")

        metrics = compute_recall_precision_at_k(
            expected_files=expected_sources, retrieved_files=retrieved_files
        )
        recall = metrics["recall"]
        precision = metrics["precision"]

        all_recalls.append(recall)
        all_precisions.append(precision)

        print(f"Recall@{len(retrieved_files)}: {recall:.2f}")
        print(f"Precision@{len(retrieved_files)}: {precision:.2f}")
        print()

    avg_recall = sum(all_recalls) / len(all_recalls)
    avg_precision = sum(all_precisions) / len(all_precisions)

    print("=== Overall Retrieval Scores ===")
    print(f"Average Recall@k   : {avg_recall:.2f}")
    print(f"Average Precision@k: {avg_precision:.2f}")


if __name__ == "__main__":
    main()
