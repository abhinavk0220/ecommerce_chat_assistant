# backend/tools/order_tool.py

"""
Order tool module.

This provides:
1. A helper to load dummy order data from data/structured/orders.json.
2. A pure function to get order status by order_id.
3. A LangChain-compatible tool wrapper so that agents / LLMs can call
   this functionality in a structured way.

This is a key part of our "tools" concept: factual, operational data
like order status is fetched from a deterministic source instead of
being hallucinated by the LLM.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.tools import tool


# Locate project root and structured data dir
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STRUCTURED_DATA_DIR = PROJECT_ROOT / "data" / "structured"
ORDERS_PATH = STRUCTURED_DATA_DIR / "orders.json"


def load_orders() -> List[Dict[str, Any]]:
    """
    Load all orders from the JSON file.
    """
    if not ORDERS_PATH.exists():
        raise FileNotFoundError(f"orders.json not found at: {ORDERS_PATH}")

    with open(ORDERS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("orders.json must contain a list of orders")

    return data


def find_order_by_id(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Return a single order dict matching the given order_id, or None if not found.
    """
    orders = load_orders()
    for order in orders:
        if str(order.get("order_id")) == str(order_id):
            return order
    return None


@tool("get_order_status", return_direct=False)
def get_order_status_tool(order_id: str) -> Dict[str, Any]:
    """
    Look up the status of an order by its order_id.

    Args:
        order_id: The ID of the order, e.g. "ORD1001".

    Returns:
        A dictionary with keys:
        - found: bool, whether the order was found
        - order_id: str
        - status: str (e.g., "delivered", "shipped", "processing")
        - delivery_date: str or null
        - items: list of products in the order
        - message: human-readable summary
    """
    order = find_order_by_id(order_id)

    if order is None:
        return {
            "found": False,
            "order_id": order_id,
            "status": None,
            "delivery_date": None,
            "items": [],
            "message": f"No order found with ID {order_id}.",
        }

    status = order.get("status")
    delivery_date = order.get("delivery_date")
    items = order.get("items", [])

    # Build a human-readable message (can be improved later)
    if status == "delivered":
        msg = f"Order {order_id} has been delivered on {delivery_date}."
    elif status == "shipped":
        msg = f"Order {order_id} has been shipped. Estimated delivery date: {delivery_date}."
    elif status == "processing":
        msg = f"Order {order_id} is currently being processed."
    else:
        msg = f"Order {order_id} has status: {status}."

    return {
        "found": True,
        "order_id": order_id,
        "status": status,
        "delivery_date": delivery_date,
        "items": items,
        "message": msg,
    }
