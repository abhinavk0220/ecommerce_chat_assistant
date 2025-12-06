# backend/guardrails.py

"""
Guardrails module.

We apply rule-based guardrails *before* calling the main
assistant logic. This helps us:

1. Block obviously unsafe or inappropriate queries (safety guardrail).
2. Block romantic / dating / sexual / pickup-line style queries that are not
   appropriate for a professional ecommerce assistant.
3. Optionally restrict to ecommerce topics (domain guardrail), but still allow
   basic chitchat (hi/hello/how are you, "oh nice", etc.).

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
    reason: Optional[str] = None  # e.g., "out_of_domain", "safety", "empty", "inappropriate"


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

# Additional keywords for romantic / dating / sexual requests.
DATING_KEYWORDS = [
    "date a girl",
    "date a boy",
    "date someone",
    "dating advice",
    "pick up line",
    "pickup line",
    "pick-up line",
    "flirt with",
    "flirting with",
    "crush on",
    "get a girlfriend",
    "get a boyfriend",
    "romantic advice",
    "seduce",
]

SEXUAL_KEYWORDS = [
    "sex",
    "sexual",
    "nsfw",
    "naughty",
    "hot girl",
    "hot boy",
    "horny",
]

ROMANTIC_PHRASES = [
    "in love with my laptop",
    "in love with her",
    "in love with him",
    "nights are going great",
]

# Keywords indicating the query is ecommerce-related.
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
    "products",
    "laptop",
    "headphone",
    "headphones",
    "device",
    "support",
    "policy",
    "store",
    "company",
    "status",
    "catalog",
    "catalogue",
    "catalog list",
    "product list",
    "offer",
    "offers",
    "setup",
    "bundle",
]

# Basic chitchat we want to ALLOW (router will handle it later).
CHITCHAT_KEYWORDS = [
    "hi",
    "hello",
    "hey",
    "how are you",
    "how r you",
    "good morning",
    "good evening",
    "thank you",
    "thanks",
    "oh nice",
    "ohh nice",
    "nice",
    "cool",
    "great",
    "awesome",
    "ok",
    "okay",
]


def _contains_inappropriate_content(text: str) -> bool:
    lowered = text.lower()
    if any(kw in lowered for kw in DATING_KEYWORDS):
        return True
    if any(kw in lowered for kw in SEXUAL_KEYWORDS):
        return True
    if any(phrase in lowered for phrase in ROMANTIC_PHRASES):
        return True
    return False


def _is_clearly_out_of_domain(text: str) -> bool:
    """
    Very rough domain guardrail:

    If the message does NOT mention any store-related concept AND also
    does not look like generic chitchat, we treat it as out-of-domain.
    """
    lowered = text.lower()

    if any(kw in lowered for kw in ECOMMERCE_KEYWORDS):
        return False
    if any(kw in lowered for kw in CHITCHAT_KEYWORDS):
        return False

    # Everything else is treated as out-of-domain for this demo.
    return True


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

    # 1) Basic SAFETY guardrail (self-harm, violence, etc.)
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

    # 2) INAPPROPRIATE content (dating, sexual, pickup lines, etc.)
    if _contains_inappropriate_content(text):
        return GuardrailResult(
            allowed=False,
            message=(
                "I’m here to help with your orders, products, returns, refunds, "
                "warranty, shipping, and basic troubleshooting. "
                "I can’t assist with romantic, sexual, or personal dating requests. "
                "Please keep your questions related to the store and support topics."
            ),
            reason="inappropriate",
        )

    # 3) Domain guardrail: clearly out-of-domain (e.g., hacking tutorials, random life advice)
    if _is_clearly_out_of_domain(text):
        return GuardrailResult(
            allowed=False,
            message=(
                "I’m designed to assist with our online store: orders, returns, "
                "refunds, shipping, warranty, product suggestions, and troubleshooting "
                "device issues. Please ask a question related to these topics."
            ),
            reason="out_of_domain",
        )

    # 4) Passed all checks → allowed to proceed to router + tools/RAG/LLM.
    return GuardrailResult(allowed=True)
