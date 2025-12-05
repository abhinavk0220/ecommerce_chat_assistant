# # backend/guardrails.py

"""
Guardrails module.

We apply lightweight, rule-based guardrails *before* calling the main
assistant logic. This helps us:

1. Block obviously unsafe or inappropriate queries (safety guardrail).
2. Optionally restrict to ecommerce topics (domain guardrail).
   - Currently, the domain guardrail is SOFT: we do not block, we just allow.
     This avoids accidentally blocking valid short queries like product names.

This module is intentionally simple and transparent so that it is easy
to explain and debug in the project report or viva.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class GuardrailResult:
    allowed: bool
    message: Optional[str] = None
    reason: Optional[str] = None  # e.g., "out_of_domain", "safety", "empty"


# Very lightweight word-based checks. This is NOT a full safety system,
# but enough for our project to demonstrate the concept.
BLOCKED_KEYWORDS = [
    "suicide",
    "kill myself",
    "harm myself",
    "bomb",
    "terrorist",
    "gun",
    "weapon",
]

# Keywords indicating the query is ecommerce-related.
# (We keep this list in case we want a stricter domain guardrail later.)
ECOMMERCE_KEYWORDS = [
    "order",
    "refund",
    "return",
    "exchange",
    "replacement",
    "warranty",
    "shipping",
    "delivery",
    "tracking",
    "cart",
    "checkout",
    "payment",
    "invoice",
    "product",
    "laptop",
    "headphone",
    "headphones",
    "device",
    "support",
    "policy",
]


def apply_guardrails(user_message: str) -> GuardrailResult:
    """
    Apply guardrails to the incoming user message.

    Returns:
        GuardrailResult:
            allowed: False -> we should NOT call the main assistant logic.
                      True  -> safe to proceed.
            message: Optional user-facing message to return instead.
            reason:  Short code for why it was blocked or redirected.
    """
    text = user_message.strip().lower()

    # 0) Empty input
    if not text:
        return GuardrailResult(
            allowed=False,
            message=(
                "Please enter a question related to your orders, products, "
                "returns, refunds, or warranty."
            ),
            reason="empty",
        )

    # 1) Basic safety guardrail
    for bad in BLOCKED_KEYWORDS:
        if bad in text:
            return GuardrailResult(
                allowed=False,
                message=(
                    "I'm not able to help with that topic. "
                    "If you are in distress or feel unsafe, please reach out to trusted people around you "
                    "or contact local emergency services or a helpline."
                ),
                reason="safety",
            )

    # 2) Domain guardrail (SOFT)
    #
    # Earlier we used this to hard-block non-ecommerce topics. That caused
    # valid queries like 'tell me about "ThinkPro 15"' to be blocked.
    #
    # For now, we keep it soft:
    # - If no ecommerce keyword is found, we STILL allow the query.
    # - The router + tools/RAG will handle it.
    # - Our documents and tools are already ecommerce-focused, so the model
    #   won't magically talk about unrelated domains.
    if not any(kw in text for kw in ECOMMERCE_KEYWORDS):
        return GuardrailResult(allowed=True, message=None, reason=None)

    # Passed all checks
    return GuardrailResult(allowed=True)
