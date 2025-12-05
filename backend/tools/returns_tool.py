# backend/tools/returns_tool.py

"""
Returns tool module.

Determines whether an order is eligible for return based on:
- Delivery date
- Product category
- Simple return policy rules

This is a deterministic tool built on top of structured data:
- orders.json
- products.json

It is designed to be invoked by the LLM so that refund/return decisions
are grounded in explicit rules instead of model guesses.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.tools import tool

# Reuse structured data dirs
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STRUCTURED_DATA_DIR = PROJECT_ROOT / "data" / "structured"
ORDERS_PATH = STRUCTURED_DATA_DIR / "orders.json"
PRODUCTS_PATH = STRUCTURED_DATA_DIR / "products.json"


def _load_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"{path.name} not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path.name} must contain a list of objects")
    return data


def load_orders() -> List[Dict[str, Any]]:
    return _load_json_list(ORDERS_PATH)


def load_products() -> List[Dict[str, Any]]:
    return _load_json_list(PRODUCTS_PATH)


def find_order(order_id: str) -> Optional[Dict[str, Any]]:
    for order in load_orders():
        if str(order.get("order_id")) == str(order_id):
            return order
    return None


def build_product_index() -> Dict[str, Dict[str, Any]]:
    """
    Returns a dict mapping product_id -> product dict.
    """
    products = load_products()
    index = {}
    for p in products:
        pid = str(p.get("product_id"))
        index[pid] = p
    return index


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%d")


@tool("check_return_eligibility", return_direct=False)
def check_return_eligibility_tool(order_id: str, today: str) -> Dict[str, Any]:
    """
    Check whether an order is eligible for return based on simple rules.

    Args:
        order_id: The ID of the order, e.g. "ORD1001".
        today: Current date in "YYYY-MM-DD" format (e.g., "2025-12-05").

    Policy (for demo):
    - Electronics (laptops, headphones): return allowed within 7 days of delivery.
    - If the order is not yet delivered, returns are not allowed.
    - If there is no delivery_date, treat as not delivered.

    Returns:
        {
          "found": bool,
          "eligible": bool,
          "order_id": str,
          "status": str or None,
          "delivery_date": str or None,
          "days_since_delivery": int or None,
          "reason": str,
        }
    """
    order = find_order(order_id)
    if order is None:
        return {
            "found": False,
            "eligible": False,
            "order_id": order_id,
            "status": None,
            "delivery_date": None,
            "days_since_delivery": None,
            "reason": f"No order found with ID {order_id}.",
        }

    status = order.get("status")
    delivery_date_str = order.get("delivery_date")
    delivery_date = parse_date(delivery_date_str)
    today_dt = parse_date(today)

    if delivery_date is None:
        return {
            "found": True,
            "eligible": False,
            "order_id": order_id,
            "status": status,
            "delivery_date": delivery_date_str,
            "days_since_delivery": None,
            "reason": "Order has not been delivered yet. Returns are only possible after delivery.",
        }

    if today_dt is None:
        return {
            "found": True,
            "eligible": False,
            "order_id": order_id,
            "status": status,
            "delivery_date": delivery_date_str,
            "days_since_delivery": None,
            "reason": "Invalid 'today' date provided.",
        }

    days_since = (today_dt - delivery_date).days

    # Look up product categories in this order
    product_index = build_product_index()
    categories = []
    for item in order.get("items", []):
        pid = str(item.get("product_id"))
        product = product_index.get(pid)
        if product:
            categories.append(str(product.get("category", "")).lower())

    # Simple policy: electronics (laptop/headphones) -> 7 days return window
    is_electronic = any(
        c in ("laptop", "headphones", "phone", "electronics") for c in categories
    )
    return_window_days = 7 if is_electronic else 7  # same for demo; could vary by category

    if days_since <= return_window_days:
        reason = (
            f"Order {order_id} is within the {return_window_days}-day return window "
            f"(delivered {days_since} day(s) ago)."
        )
        eligible = True
    else:
        reason = (
            f"Order {order_id} is outside the {return_window_days}-day return window "
            f"(delivered {days_since} day(s) ago)."
        )
        eligible = False

    return {
        "found": True,
        "eligible": eligible,
        "order_id": order_id,
        "status": status,
        "delivery_date": delivery_date_str,
        "days_since_delivery": days_since,
        "reason": reason,
    }
