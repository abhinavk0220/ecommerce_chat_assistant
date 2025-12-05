# backend/tools/product_tool.py

"""
Product tool module.

Provides:
1. A helper to load product catalog from data/structured/products.json.
2. A filtering/search function based on simple criteria.
3. A LangChain-compatible tool for the LLM to call when the user asks
   for product recommendations or catalog queries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain_core.tools import tool


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STRUCTURED_DATA_DIR = PROJECT_ROOT / "data" / "structured"
PRODUCTS_PATH = STRUCTURED_DATA_DIR / "products.json"


def load_products() -> List[Dict[str, Any]]:
    """
    Load all products from the JSON file.
    """
    if not PRODUCTS_PATH.exists():
        raise FileNotFoundError(f"products.json not found at: {PRODUCTS_PATH}")

    with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("products.json must contain a list of products")

    return data


def filter_products(
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    brand: Optional[str] = None,
    required_tags: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Filter products based on simple criteria.

    All filters are optional. If provided, they act as AND conditions.
    """
    products = load_products()
    required_tags = required_tags or []

    def matches(p: Dict[str, Any]) -> bool:
        if category and str(p.get("category", "")).lower() != category.lower():
            return False
        if brand and str(p.get("brand", "")).lower() != brand.lower():
            return False
        if max_price is not None and float(p.get("price", 0)) > float(max_price):
            return False
        # All required tags must be present
        tags = [t.lower() for t in p.get("tags", [])]
        for t in required_tags:
            if t.lower() not in tags:
                return False
        return True

    return [p for p in products if matches(p)]


@tool("search_products", return_direct=False)
def search_products_tool(
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    brand: Optional[str] = None,
    required_tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Search for products in the catalog using simple filters.

    Args:
        category: e.g. "laptop", "headphones".
        max_price: maximum price in numeric form, e.g. 60000.
        brand: brand name, e.g. "Asus".
        required_tags: list of tags such as ["wireless", "noise-cancelling"].

    Returns:
        A dictionary with:
        - count: number of matching products
        - products: list of product dicts (id, name, price, brand, category, tags)
        - message: a short human-readable description of the results
    """
    matches = filter_products(
        category=category,
        max_price=max_price,
        brand=brand,
        required_tags=required_tags,
    )

    simplified = []
    for p in matches:
        simplified.append(
            {
                "product_id": p.get("product_id"),
                "name": p.get("name"),
                "category": p.get("category"),
                "brand": p.get("brand"),
                "price": p.get("price"),
                "currency": p.get("currency", "INR"),
                "tags": p.get("tags", []),
                "rating": p.get("rating"),
            }
        )

    if not simplified:
        msg = "No products found matching the given filters."
    else:
        msg = f"Found {len(simplified)} product(s) matching the given filters."

    return {
        "count": len(simplified),
        "products": simplified,
        "message": msg,
    }
