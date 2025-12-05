# backend/tools/warranty_tool.py

"""
Warranty tool module.

Determines whether a product in an order is still under warranty based on:
- Order date (or delivery date)
- Product category
- Simple warranty rules

This is another deterministic tool built on top of:
- orders.json
- products.json
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.tools import tool

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


def get_warranty_days_for_category(category: str) -> int:
    """
    Simple demo mapping from product category to warranty duration (in days).
    """
    cat = category.lower()
    if cat == "laptop":
        return 365  # 1 year
    if cat == "headphones":
        return 180  # 6 months
    # default warranty for other categories
    return 90


@tool("check_warranty_status", return_direct=False)
def check_warranty_status_tool(order_id: str, product_id: str, today: str) -> Dict[str, Any]:
    """
    Check whether a specific product in an order is still under warranty.

    Args:
        order_id: ID of the order, e.g. "ORD1001"
        product_id: ID of the product, e.g. "LAP123"
        today: current date as "YYYY-MM-DD"

    Logic:
    - Look up the order and confirm that product_id is part of this order.
    - Use delivery_date if present, else fall back to order_date as purchase date.
    - Determine warranty duration based on product category.
    - Compute whether today is within the warranty period.

    Returns:
        {
          "found_order": bool,
          "found_product": bool,
          "in_warranty": bool or None,
          "order_id": str,
          "product_id": str,
          "category": str or None,
          "purchase_date": str or None,
          "warranty_end_date": str or None,
          "days_since_purchase": int or None,
          "reason": str,
        }
    """
    order = find_order(order_id)
    if order is None:
        return {
            "found_order": False,
            "found_product": False,
            "in_warranty": None,
            "order_id": order_id,
            "product_id": product_id,
            "category": None,
            "purchase_date": None,
            "warranty_end_date": None,
            "days_since_purchase": None,
            "reason": f"No order found with ID {order_id}.",
        }

    # Check if product_id is in the order items
    items = order.get("items", [])
    product_in_order = any(str(item.get("product_id")) == str(product_id) for item in items)
    if not product_in_order:
        return {
            "found_order": True,
            "found_product": False,
            "in_warranty": None,
            "order_id": order_id,
            "product_id": product_id,
            "category": None,
            "purchase_date": None,
            "warranty_end_date": None,
            "days_since_purchase": None,
            "reason": f"Product {product_id} is not part of order {order_id}.",
        }

    # Get product category
    product_index = build_product_index()
    product = product_index.get(str(product_id))
    category = None
    if product:
        category = str(product.get("category", "")).lower()

    # Determine purchase date: prefer delivery_date, else order_date
    delivery_date_str = order.get("delivery_date")
    order_date_str = order.get("order_date")
    purchase_date_str = delivery_date_str or order_date_str

    purchase_date = parse_date(purchase_date_str)
    today_dt = parse_date(today)

    if purchase_date is None or today_dt is None:
        return {
            "found_order": True,
            "found_product": True,
            "in_warranty": None,
            "order_id": order_id,
            "product_id": product_id,
            "category": category,
            "purchase_date": purchase_date_str,
            "warranty_end_date": None,
            "days_since_purchase": None,
            "reason": "Invalid or missing purchase date or 'today' date.",
        }

    days_since_purchase = (today_dt - purchase_date).days

    warranty_days = get_warranty_days_for_category(category or "")
    warranty_end_date = purchase_date + timedelta(days=warranty_days)

    in_warranty = today_dt <= warranty_end_date

    if in_warranty:
        reason = (
            f"Product {product_id} in order {order_id} is still under warranty. "
            f"Warranty duration is {warranty_days} days from {purchase_date_str}, "
            f"ending on {warranty_end_date.date()}. (Purchased {days_since_purchase} day(s) ago.)"
        )
    else:
        reason = (
            f"Product {product_id} in order {order_id} is no longer under warranty. "
            f"Warranty duration was {warranty_days} days from {purchase_date_str}, "
            f"which ended on {warranty_end_date.date()}. "
            f"(Purchased {days_since_purchase} day(s) ago.)"
        )

    return {
        "found_order": True,
        "found_product": True,
        "in_warranty": in_warranty,
        "order_id": order_id,
        "product_id": product_id,
        "category": category,
        "purchase_date": purchase_date_str,
        "warranty_end_date": warranty_end_date.date().isoformat(),
        "days_since_purchase": days_since_purchase,
        "reason": reason,
    }
