# backend/tools/user_tool.py

"""
User tool module for finding orders by user_id.
"""

from __future__ import annotations

from typing import List, Dict, Any

# Import the tool function directly (without decorator for now)
from tools.order_tool import load_orders


def normalize_user_id(user_id: str) -> str:
    """
    Normalize user ID format.
    Handles: "0001" -> "U001", "u001" -> "U001", "U001" -> "U001"
    """
    user_id = str(user_id).strip().upper()
    
    # If it's just a number, add U prefix
    if user_id.isdigit():
        user_id = f"U{user_id.zfill(3)}"  # U001, U002, etc.
    
    # If it starts with U but lowercase, uppercase it
    if not user_id.startswith("U"):
        user_id = f"U{user_id}"
    
    return user_id


def find_orders_by_user_id_func(user_id: str) -> List[Dict[str, Any]]:
    """
    Find all orders for a given user_id.
    Returns a list of order dicts.
    """
    # Normalize the user_id
    normalized_user_id = normalize_user_id(user_id)
    
    orders = load_orders()
    user_orders = [
        order for order in orders
        if normalize_user_id(str(order.get("user_id"))) == normalized_user_id
    ]
    return user_orders


class FindOrdersByUserIdTool:
    """
    Simple tool class for finding orders by user_id.
    """
    def __init__(self):
        self.name = "find_orders_by_user_id"
        self.description = "Find all orders placed by a specific user"
    
    def invoke(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find all orders placed by a specific user.
        
        Args:
            input_dict: Dictionary with 'user_id' key
        
        Returns:
            A dictionary with:
            - found: bool
            - user_id: str (normalized)
            - count: int (number of orders)
            - orders: list of order summaries
            - message: human-readable summary
        """
        user_id = input_dict.get("user_id", "")
        normalized_user_id = normalize_user_id(user_id)
        
        orders = find_orders_by_user_id_func(user_id)
        
        if not orders:
            return {
                "found": False,
                "user_id": normalized_user_id,
                "count": 0,
                "orders": [],
                "message": f"No orders found for user {normalized_user_id}. Please check if the user ID is correct (format: U001, U002, etc.)."
            }
        
        # Create simplified order summaries
        order_summaries = []
        for order in orders:
            items_desc = []
            for item in order.get("items", []):
                items_desc.append(f"{item.get('product_id')} (qty: {item.get('quantity')})")
            
            order_summaries.append({
                "order_id": order.get("order_id"),
                "status": order.get("status"),
                "order_date": order.get("order_date"),
                "delivery_date": order.get("delivery_date"),
                "items": items_desc
            })
        
        message_lines = [f"Found {len(orders)} order(s) for user {normalized_user_id}:"]
        for i, summary in enumerate(order_summaries, 1):
            message_lines.append(
                f"{i}. Order {summary['order_id']} - Status: {summary['status']} - "
                f"Items: {', '.join(summary['items'])}"
            )
        
        return {
            "found": True,
            "user_id": normalized_user_id,
            "count": len(orders),
            "orders": order_summaries,
            "message": "\n".join(message_lines)
        }


# Create instance
find_orders_by_user_id_tool = FindOrdersByUserIdTool()