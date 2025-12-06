# agent/router.py

"""
Simple rule-based router for the ecommerce assistant.

Given a user message, we:
- Detect the high-level intent (order_status, return_eligibility, refund,
  warranty_status, product_search, policy_question, troubleshooting,
  chitchat, date_query, general_rag).
- Extract key "slots" like order_id, max_price, and product category.
"""

from __future__ import annotations

import re
from typing import Dict, Any, Optional

ORDER_ID_PATTERN = re.compile(r"\bORD\d+\b", re.IGNORECASE)


def extract_order_id(text: str) -> Optional[str]:
    match = ORDER_ID_PATTERN.search(text)
    if match:
        return match.group(0).upper()
    return None


def extract_max_price(text: str) -> Optional[float]:
    """
    Very simple heuristic: look for patterns like 'under 60000' or 'below 5000'.
    """
    lowered = text.lower()
    keywords = ["under", "below", "less than", "<", "upto", "up to"]

    for kw in keywords:
        if kw in lowered:
            idx = lowered.find(kw)
            substring = lowered[idx : idx + 30]
            nums = re.findall(r"\d+", substring)
            if nums:
                try:
                    return float(nums[0])
                except ValueError:
                    continue
    return None


def detect_category(text: str) -> Optional[str]:
    """
    Map natural language mentions to a coarse product category.
    Extended to support:
    - laptop
    - headphones / headset
    - mouse
    - keyboard
    - phone (kept for completeness)
    """
    lowered = text.lower()
    if "laptop" in lowered or "laptops" in lowered:
        return "laptop"
    if "headphone" in lowered or "headphones" in lowered or "headset" in lowered:
        return "headphones"
    if "mouse" in lowered or "mice" in lowered:
        return "mouse"
    if "keyboard" in lowered or "key board" in lowered:
        return "keyboard"
    if "phone" in lowered or "mobile" in lowered or "smartphone" in lowered:
        return "phone"
    return None


def is_chitchat(lowered: str) -> bool:
    # Keep chitchat STRICT: short greetings / thanks etc.
    return any(
        phrase in lowered
        for phrase in [
            " hi",        # leading space to avoid matching "this"
            "hello",
            " hey",
            "how are you",
            "how r you",
            "who are you",
            "what can you do",
            "thanks",
            "thank you",
            "good morning",
            "good evening",
        ]
    )


def is_troubleshooting_issue(lowered: str) -> bool:
    """
    Detect if the message looks like a device/usage issue.
    We check this BEFORE chitchat so that things like
    'great, my laptop is not working properly' don't get misrouted.
    """
    issue_phrases = [
        "not turning on",
        "won't turn on",
        "does not turn on",
        "doesn't turn on",
        "won't power on",
        "no sound",
        "not working",
        "not working properly",
        "stopped working",
        "stop working",
        "broken",
        "issue with",
        "problem with",
        "overheating",
    ]
    return any(p in lowered for p in issue_phrases)


def detect_intent(user_message: str) -> Dict[str, Any]:
    """
    Detects intent and basic slots from the user message.

    Returns a dict:
    {
      "intent": str,
      "order_id": Optional[str],
      "category": Optional[str],
      "max_price": Optional[float],
    }
    """
    text = user_message.strip()
    lowered = text.lower()

    # 0) Troubleshooting FIRST (so "not working" doesn't become chitchat/general)
    if is_troubleshooting_issue(lowered):
        category = detect_category(text)
        order_id = extract_order_id(text)
        max_price = extract_max_price(text)
        return {
            "intent": "troubleshooting",
            "order_id": order_id,
            "category": category,
            "max_price": max_price,
        }

    # 1) Chitchat (small talk)
    if is_chitchat(lowered):
        return {
            "intent": "chitchat",
            "order_id": None,
            "category": None,
            "max_price": None,
        }

    # 2) Simple date query
    if (
        "date today" in lowered
        or "today's date" in lowered
        or "what day is it" in lowered
    ):
        return {
            "intent": "date_query",
            "order_id": None,
            "category": None,
            "max_price": None,
        }

    order_id = extract_order_id(text)
    category = detect_category(text)
    max_price = extract_max_price(text)

    # 3) Order status
    if (
        "where is my order" in lowered
        or "track my order" in lowered
        or ("order" in lowered and "status" in lowered)
        or ("order" in lowered and "tracking" in lowered)
        or (order_id is not None and "status" in lowered)
    ):
        return {
            "intent": "order_status",
            "order_id": order_id,
            "category": category,
            "max_price": max_price,
        }

    # 4) Policy questions
    if (
        "return policy" in lowered
        or "shipping policy" in lowered
        or "refund policy" in lowered
        or "policy" in lowered
    ):
        return {
            "intent": "policy_question",
            "order_id": order_id,
            "category": category,
            "max_price": max_price,
        }

    # 5) Refund
    if any(
        kw in lowered
        for kw in ["refund", "money back", "get my money", "refund status"]
    ):
        return {
            "intent": "refund",
            "order_id": order_id,
            "category": category,
            "max_price": max_price,
        }

    # 6) Return / exchange
    if any(
        kw in lowered
        for kw in ["return", "exchange", "replace", "replacement"]
    ):
        return {
            "intent": "return_eligibility",
            "order_id": order_id,
            "category": category,
            "max_price": max_price,
        }

    # 7) Warranty
    if "warranty" in lowered or "guarantee" in lowered:
        return {
            "intent": "warranty_status",
            "order_id": order_id,
            "category": category,
            "max_price": max_price,
        }

        # 8) Product search / recommendation
    search_verbs = [
        "suggest",
        "recommend",
        "show me",
        "find",
        "looking for",
        "under",
        "below",
        "tell me about",
        "have in store",
        "available",
        "all the",
        "sell",
        "you sell",
        "you guys sell",
        # preference / suitability language
        "best",
        "good for",
        "suitable for",
        "ideal for",
    ]

    # Case A: category present + search verbs -> product_search for that category
    if category and any(kw in lowered for kw in search_verbs):
        return {
            "intent": "product_search",
            "order_id": order_id,
            "category": category,
            "max_price": max_price,
        }

    # Case B: explicit catalogue / what you offer questions (no category)
    if any(
        kw in lowered
        for kw in [
            "catalog",
            "catalogue",
            "product catalog",
            "product catalogue",
            "what all you offer",
            "what all u offer",
            "what do you offer",
            "what do u offer",
            "what all you guys offer",
            "what all u guys offer",
            "what all you have",
            "what all u have",
        ]
    ):
        return {
            "intent": "product_search",
            "order_id": order_id,
            "category": None,  # means "all categories"
            "max_price": max_price,
        }

    # Case C: no specific category, but clearly asking about products we sell
    if any(
        kw in lowered
        for kw in [
            "products do you sell",
            "what all products",
            "what products you sell",
            "what all products u guys sell",
            "what all products do you have",
            "you sell products",
            "sell products",
            "all products",
        ]
    ) or ("products" in lowered and "sell" in lowered):
        return {
            "intent": "product_search",
            "order_id": order_id,
            "category": None,  # means "all categories"
            "max_price": max_price,
        }

    # 9) Default: general RAG / FAQ
    return {
        "intent": "general_rag",
        "order_id": order_id,
        "category": category,
        "max_price": max_price,
    }
