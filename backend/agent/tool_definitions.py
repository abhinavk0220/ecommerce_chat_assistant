# backend/agent/tool_definitions.py

"""
Gemini function calling tool definitions.
These define the interface that Gemini uses to decide which tools to call.
"""

GEMINI_TOOL_DEFINITIONS = [
    {
        "name": "find_orders_by_user_id",
        "description": "Find all orders placed by a specific user. Use this when you have the user_id and need to see their order history.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user ID, e.g., U001, U002"
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "get_order_status",
        "description": "Get the detailed status of a specific order including delivery date, items, and current status.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID, e.g., ORD1001, ORD1002"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "search_products",
        "description": "Search for products in the catalog based on category, price, brand, or tags. Returns a list of matching products.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Product category: laptop, headphones, mouse, keyboard, or null for all"
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum price filter in INR"
                },
                "brand": {
                    "type": "string",
                    "description": "Brand name filter, e.g., Asus, Lenovo"
                },
                "required_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Required tags like gaming, wireless, office, etc."
                }
            },
            "required": []
        }
    },
    {
        "name": "check_return_eligibility",
        "description": "Check if a specific order is eligible for return based on delivery date and return policy.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to check"
                },
                "today": {
                    "type": "string",
                    "description": "Today's date in YYYY-MM-DD format"
                }
            },
            "required": ["order_id", "today"]
        }
    },
    {
        "name": "check_refund_possibility",
        "description": "Check if a refund is possible for an order and get expected refund timeline.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to check"
                },
                "today": {
                    "type": "string",
                    "description": "Today's date in YYYY-MM-DD format"
                }
            },
            "required": ["order_id", "today"]
        }
    },
    {
        "name": "check_warranty_status",
        "description": "Check if a product in an order is still under warranty.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID"
                },
                "product_id": {
                    "type": "string",
                    "description": "The product ID, e.g., LAP123"
                },
                "today": {
                    "type": "string",
                    "description": "Today's date in YYYY-MM-DD format"
                }
            },
            "required": ["order_id", "product_id", "today"]
        }
    },
    {
        "name": "get_troubleshooting_steps",
        "description": "Get troubleshooting steps for common device issues.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_type": {
                    "type": "string",
                    "description": "Type of product: laptop, headphones, mouse, keyboard"
                },
                "issue": {
                    "type": "string",
                    "description": "Description of the issue the user is facing"
                }
            },
            "required": ["product_type", "issue"]
        }
    },
    {
        "name": "search_policy_docs",
        "description": "Search company policy documents for information about return policy, shipping, refunds, warranty terms, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question or topic to search for in policy documents"
                }
            },
            "required": ["query"]
        }
    }
]