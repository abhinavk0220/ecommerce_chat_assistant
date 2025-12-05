# backend/agent/orchestrator.py

"""
Orchestrator for the ecommerce assistant.

Given a user message, we:
1. Detect intent using the rule-based router.
2. Route to the appropriate capability:
   - Tools (orders, products, returns, refunds, warranty, troubleshooting)
   - RAG (policy/manual-based answers)
   - Chitchat / date queries
3. Return a unified response object.

For product search, we use a hybrid pattern:
- Tools (search_products_tool) to fetch the actual catalog entries.
- LLM (Gemini via get_llm) to summarize and recommend based on those entries.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from agent.router import detect_intent
from rag.rag_chain import answer_with_rag
from tools.order_tool import get_order_status_tool, find_order_by_id
from tools.product_tool import search_products_tool
from tools.returns_tool import check_return_eligibility_tool
from tools.warranty_tool import check_warranty_status_tool
from tools.refund_tool import check_refund_possibility_tool
from tools.troubleshooting_tool import get_troubleshooting_steps_tool
from llm_adapter import get_llm  # returns google.generativeai.GenerativeModel


def get_today_str() -> str:
    return datetime.today().strftime("%Y-%m-%d")


def handle_user_message(user_message: str, today: str | None = None) -> Dict[str, Any]:
    """
    Main entrypoint for the backend assistant logic.

    Returns a dict:
    {
      "intent": str,
      "answer": str,
      "route": str,        # e.g. "tool:order_status" or "rag" or "tool+llm:product_search"
      "tool_result": Any,  # raw tool output if applicable
      "rag_result": Any,   # raw rag result if applicable
      "router_info": {...} # what the router detected
    }
    """
    today = today or get_today_str()

    router_info = detect_intent(user_message)
    intent = router_info["intent"]
    order_id = router_info.get("order_id")
    category = router_info.get("category")
    max_price = router_info.get("max_price")

    # 0. Chitchat (no tools, no RAG needed)
    if intent == "chitchat":
        lowered = user_message.strip().lower()

        if "how are you" in lowered or "how r you" in lowered:
            ans = (
                "I’m doing great and ready to help you with your orders, products, "
                "and support questions! How can I assist you today?"
            )
        elif "who are you" in lowered:
            ans = (
                "I’m an AI assistant for Antigravity Electronics, a demo online store "
                "for laptops and headphones. I can help with orders, returns, refunds, "
                "warranty, product suggestions, and basic troubleshooting."
            )
        elif "what can you do" in lowered:
            ans = (
                "I can help you track orders, check return and refund eligibility, "
                "look up warranty information, suggest products based on your needs, "
                "and assist with basic troubleshooting for devices."
            )
        elif "thank" in lowered:
            ans = "You’re welcome! If you have any questions about your orders or products, just ask."
        else:
            ans = "Hi! I’m here to help you with orders, products, returns, refunds, warranty, and troubleshooting."

        return {
            "intent": intent,
            "answer": ans,
            "route": "builtin:chitchat",
            "tool_result": None,
            "rag_result": None,
            "router_info": router_info,
        }

    # 0b. Date query
    if intent == "date_query":
        ans = f"Today’s date is {today}."
        return {
            "intent": intent,
            "answer": ans,
            "route": "builtin:date",
            "tool_result": None,
            "rag_result": None,
            "router_info": router_info,
        }

    # 1. Order status
    if intent == "order_status":
        if not order_id:
            ans = (
                "I can help track your order. "
                "Please provide your order ID (for example, ORD1001)."
            )
            return {
                "intent": intent,
                "answer": ans,
                "route": "tool:order_status",
                "tool_result": None,
                "rag_result": None,
                "router_info": router_info,
            }

        tool_res = get_order_status_tool.invoke({"order_id": order_id})
        answer_text = tool_res.get("message", "Here is the status of your order.")
        return {
            "intent": intent,
            "answer": answer_text,
            "route": "tool:order_status",
            "tool_result": tool_res,
            "rag_result": None,
            "router_info": router_info,
        }

    # 2. Return eligibility
    if intent == "return_eligibility":
        if not order_id:
            ans = (
                "To check return eligibility, please share your order ID "
                "(for example, ORD1001)."
            )
            return {
                "intent": intent,
                "answer": ans,
                "route": "tool:return_eligibility",
                "tool_result": None,
                "rag_result": None,
                "router_info": router_info,
            }

        tool_res = check_return_eligibility_tool.invoke(
            {
                "order_id": order_id,
                "today": today,
            }
        )
        answer_text = tool_res.get("reason", "Here is the return eligibility result.")
        return {
            "intent": intent,
            "answer": answer_text,
            "route": "tool:return_eligibility",
            "tool_result": tool_res,
            "rag_result": None,
            "router_info": router_info,
        }

    # 3. Refund
    if intent == "refund":
        if not order_id:
            ans = (
                "To check your refund possibility or status, please provide your order ID "
                "(for example, ORD1001)."
            )
            return {
                "intent": intent,
                "answer": ans,
                "route": "tool:refund",
                "tool_result": None,
                "rag_result": None,
                "router_info": router_info,
            }

        tool_res = check_refund_possibility_tool.invoke(
            {
                "order_id": order_id,
                "today": today,
            }
        )

        reason = tool_res.get("reason", "")
        timeline = tool_res.get("expected_refund_timeline")

        if timeline:
            answer_text = reason + "\n\n" + timeline
        else:
            answer_text = reason

        return {
            "intent": intent,
            "answer": answer_text,
            "route": "tool:refund",
            "tool_result": tool_res,
            "rag_result": None,
            "router_info": router_info,
        }

    # 4. Warranty status
    if intent == "warranty_status":
        if not order_id:
            ans = (
                "To check warranty, please provide your order ID "
                "(for example, ORD1001). If there are multiple products in the order, "
                "I will ask you which one."
            )
            return {
                "intent": intent,
                "answer": ans,
                "route": "tool:warranty_status",
                "tool_result": None,
                "rag_result": None,
                "router_info": router_info,
            }

        order = find_order_by_id(order_id)
        if not order or not order.get("items"):
            ans = f"I couldn't find products for order {order_id}."
            return {
                "intent": intent,
                "answer": ans,
                "route": "tool:warranty_status",
                "tool_result": None,
                "rag_result": None,
                "router_info": router_info,
            }

        # For demo: assume only one product per order, take first
        product_id = order["items"][0]["product_id"]

        tool_res = check_warranty_status_tool.invoke(
            {
                "order_id": order_id,
                "product_id": product_id,
                "today": today,
            }
        )
        answer_text = tool_res.get("reason", "Here is the warranty status.")
        return {
            "intent": intent,
            "answer": answer_text,
            "route": "tool:warranty_status",
            "tool_result": tool_res,
            "rag_result": None,
            "router_info": router_info,
        }

    # 5. Product search / recommendations (TOOLS + LLM)
    if intent == "product_search":
        tool_res = search_products_tool.invoke(
            {
                "category": category,
                "max_price": max_price,
                "brand": None,
                "required_tags": [],
            }
        )
        count = tool_res.get("count", 0)
        products = tool_res.get("products", [])

        if count == 0:
            answer_text = (
                "I couldn't find products matching those filters. "
                "You might try adjusting the budget or category."
            )
            return {
                "intent": intent,
                "answer": answer_text,
                "route": "tool:product_search",
                "tool_result": tool_res,
                "rag_result": None,
                "router_info": router_info,
            }

        # Convert structured products into a text context for the LLM
        context_lines = []
        for p in products:
            tags = ", ".join(p.get("tags", []))
            context_lines.append(
                f"- id: {p['product_id']}, name: {p['name']}, brand: {p['brand']}, "
                f"category: {p['category']}, price: ₹{p['price']}, "
                f"rating: {p.get('rating', 'N/A')}, tags: {tags}"
            )
        context_text = "\n".join(context_lines)
        user_query = user_message.strip()

        llm = get_llm()

        prompt = f"""
You are an ecommerce assistant.

Here is the list of products retrieved from the catalog based on the user's filters:

{context_text}

The user asked:
\"\"\"{user_query}\"\"\"


Instructions:
1. Briefly summarize how many matching products we have and the price range.
2. For each product, give a short, friendly description (who it is good for).
3. If possible, recommend which option(s) are better for different scenarios
   (for example, students, office work, budget-conscious users).
4. Do NOT invent products that are not listed above. Only talk about these products.
5. Keep the tone clear and concise.
"""

        try:
            resp = llm.generate_content(prompt)
            answer_text = getattr(resp, "text", str(resp))
            route = "tool+llm:product_search"
        except Exception:
            # Fallback: if LLM fails for some reason, show simple list.
            lines = ["Here are some options for you:"]
            for p in products:
                lines.append(
                    f"- {p['name']} ({p['brand']}) - ₹{p['price']} [{p['category']}]"
                )
            lines.append("")
            lines.append("(Note: LLM-based explanation failed, showing raw list instead.)")
            answer_text = "\n".join(lines)
            route = "tool:product_search_fallback"

        return {
            "intent": intent,
            "answer": answer_text,
            "route": route,
            "tool_result": tool_res,
            "rag_result": None,
            "router_info": router_info,
        }

    # 6. Troubleshooting: use structured tool first, then optionally RAG
    if intent == "troubleshooting":
        product_type = category or "device"
        issue_text = user_message

        tool_res = get_troubleshooting_steps_tool.invoke(
            {
                "product_type": product_type,
                "issue": issue_text,
            }
        )

        if tool_res.get("found", False):
            answer_text = tool_res.get("message", "Here are some troubleshooting steps.")
            return {
                "intent": intent,
                "answer": answer_text,
                "route": "tool:troubleshooting",
                "tool_result": tool_res,
                "rag_result": None,
                "router_info": router_info,
            }
        else:
            rag_res = answer_with_rag(user_message, k=3)
            answer_text = rag_res.get("answer", "I generated an answer based on the documentation.")
            return {
                "intent": intent,
                "answer": answer_text,
                "route": "rag:troubleshooting_fallback",
                "tool_result": tool_res,
                "rag_result": rag_res,
                "router_info": router_info,
            }

    # 7. Policy questions, general FAQ → RAG with LLM fallback
    if intent in ("policy_question", "general_rag"):
        rag_res = answer_with_rag(user_message, k=3)
        answer_text = (rag_res.get("answer") or "").strip()

        # If RAG is clearly empty or "not sure", fall back to a generic LLM answer
        if (not answer_text) or (
            "not sure based on the available information" in answer_text.lower()
        ):
            llm = get_llm()
            fallback_prompt = f"""
You are an AI assistant for Antigravity Electronics, a demo online store that sells laptops and headphones.

The user asked:
\"\"\"{user_message}\"\"\".

- If the question is about the store (company, what we sell, what we do), answer in general terms:
  say that we are an online electronics store focusing on laptops and headphones.
- If it is a general small question, you can answer normally.
- Do NOT invent specific facts about real customers, real payments, or real companies.
- Do NOT talk about specific real brands unless they were mentioned by the user or are part of the known catalog.
- Today’s date is {today}.

Answer briefly and clearly.
"""
            try:
                resp = llm.generate_content(fallback_prompt)
                answer_text = getattr(resp, "text", str(resp))
                route = "llm:fallback"
            except Exception:
                answer_text = (
                    "I’m not sure how to answer that in detail, but I’m here to help "
                    "with orders, products, returns, refunds, warranty, and troubleshooting."
                )
                route = "llm:fallback_error"

            return {
                "intent": intent,
                "answer": answer_text,
                "route": route,
                "tool_result": None,
                "rag_result": rag_res,
                "router_info": router_info,
            }

        # Normal RAG success path
        return {
            "intent": intent,
            "answer": answer_text or "I generated an answer based on the documentation.",
            "route": "rag",
            "tool_result": None,
            "rag_result": rag_res,
            "router_info": router_info,
        }

    # Fallback (should rarely happen)
    rag_res = answer_with_rag(user_message, k=3)
    answer_text = rag_res.get("answer", "I generated an answer based on the documentation.")
    return {
        "intent": intent,
        "answer": answer_text,
        "route": "rag",
        "tool_result": None,
        "rag_result": rag_res,
        "router_info": router_info,
    }
