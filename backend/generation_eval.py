# backend/generation_eval.py

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

from agent.orchestrator import handle_user_message

BASE_DIR = Path(__file__).resolve().parents[1]
EVAL_FILE = BASE_DIR / "data" / "eval" / "test_cases.json"


def load_test_cases() -> List[Dict[str, Any]]:
    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def tokenize(text: str) -> List[str]:
    return text.lower().strip().split()


def lcs_length(a: List[str], b: List[str]) -> int:
    """
    Longest Common Subsequence length for two token sequences.
    Used for ROUGE-L.
    """
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n):
        for j in range(m):
            if a[i] == b[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i][j + 1], dp[i + 1][j])
    return dp[n][m]


def rouge_l(pred: str, ref: str) -> Tuple[float, float, float]:
    """
    Compute ROUGE-L (precision, recall, F1) between prediction and reference.
    """
    pred_tokens = tokenize(pred)
    ref_tokens = tokenize(ref)
    if not pred_tokens or not ref_tokens:
        return 0.0, 0.0, 0.0

    lcs = lcs_length(pred_tokens, ref_tokens)
    recall = lcs / len(ref_tokens)
    precision = lcs / len(pred_tokens) if pred_tokens else 0.0
    if recall + precision == 0:
        f1 = 0.0
    else:
        f1 = 2 * recall * precision / (recall + precision)
    return precision, recall, f1


def main():
    cases = load_test_cases()

    print("=== Answer Quality Evaluation (ROUGE-L, Routing) ===\n")

    f1_scores = []
    hallucination_flags = []
    routing_ok = []

    for case in cases:
        qid = case["id"]
        query = case["query"]
        expected_answer = case["expected_answer"]
        expected_route_prefix = case.get("expected_route_prefix")

        print(f"--- Case: {qid} ---")
        print(f"Query: {query}")

        result = handle_user_message(query)
        answer = result.get("answer", "")
        route = result.get("route", "")
        intent = result.get("intent", "")

        print(f"Route: {route} | Intent: {intent}")
        print(f"Answer:\n{answer}\n")

        # ROUGE-L
        p, r, f1 = rouge_l(answer, expected_answer)
        print(f"ROUGE-L -> Precision: {p:.2f}, Recall: {r:.2f}, F1: {f1:.2f}")

        f1_scores.append(f1)

        # Simple routing correctness: route starts with expected prefix
        if expected_route_prefix:
            is_route_ok = route.startswith(expected_route_prefix)
        else:
            is_route_ok = True
        routing_ok.append(1.0 if is_route_ok else 0.0)
        print(f"Route matches expected prefix '{expected_route_prefix}': {is_route_ok}")

        # Very simple hallucination check for product/policy questions:
        # If it's a product_search or policy_question but the answer doesn't contain
        # any obvious keyword, we flag it.
        lowered_ans = answer.lower()
        hallucinated = False

        if intent in ("product_search", "policy_question", "general_rag"):
            # If it doesn't mention any of the main domains, we mark as suspicious
            domain_keywords = ["order", "return", "refund", "warranty", "shipping",
                               "laptop", "headphone", "mouse", "keyboard", "policy",
                               "store", "company", "support"]
            if not any(k in lowered_ans for k in domain_keywords):
                hallucinated = True

        hallucination_flags.append(1.0 if hallucinated else 0.0)
        print(f"Hallucination flag (simple heuristic): {hallucinated}")
        print()

    # Overall statistics
    if f1_scores:
        avg_f1 = sum(f1_scores) / len(f1_scores)
    else:
        avg_f1 = 0.0

    avg_route_ok = sum(routing_ok) / len(routing_ok) if routing_ok else 0.0
    avg_hallucination_rate = (
        sum(hallucination_flags) / len(hallucination_flags) if hallucination_flags else 0.0
    )

    print("=== Overall Answer Quality ===")
    print(f"Average ROUGE-L F1: {avg_f1:.2f}")
    print(f"Routing accuracy (route prefix match): {avg_route_ok * 100:.1f}%")
    print(f"Hallucination rate (heuristic): {avg_hallucination_rate * 100:.1f}%")
    print()


if __name__ == "__main__":
    main()
