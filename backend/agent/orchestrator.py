# backend/agent/orchestrator.py

"""
Agentic orchestrator using Gemini's native function calling.

The LLM autonomously decides which tools to call and in what sequence.
This implements a true agentic workflow with multi-step reasoning.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import os
import traceback

from dotenv import load_dotenv
import google.generativeai as genai

from agent.router import detect_intent
from agent.tool_definitions import GEMINI_TOOL_DEFINITIONS
from rag.rag_chain import answer_with_rag
from llm_adapter import get_llm

# Import all tool functions
from tools.order_tool import get_order_status_tool, find_order_by_id
from tools.product_tool import search_products_tool
from tools.returns_tool import check_return_eligibility_tool
from tools.warranty_tool import check_warranty_status_tool
from tools.refund_tool import check_refund_possibility_tool
from tools.troubleshooting_tool import get_troubleshooting_steps_tool
from tools.user_tool import find_orders_by_user_id_tool


def get_today_str() -> str:
    return datetime.today().strftime("%Y-%m-%d")


# Intents that need user authentication/identification
PRIVATE_INTENTS = [
    "order_status",
    "return_eligibility",
    "refund",
    "warranty_status"
]

# Intents that don't need user context
PUBLIC_INTENTS = [
    "product_search",
    "policy_question",
    "general_rag",
    "chitchat",
    "date_query",
    "troubleshooting"
]


def execute_tool_call(tool_name: str, tool_args: Dict[str, Any], today: str) -> Dict[str, Any]:
    """
    Execute a tool call and return the result.
    Maps Gemini function names to actual tool implementations.
    """
    # Add today to relevant tool calls automatically
    if tool_name in ["check_return_eligibility", "check_refund_possibility", "check_warranty_status"]:
        if "today" not in tool_args:
            tool_args["today"] = today
    
    tool_map = {
        "find_orders_by_user_id": find_orders_by_user_id_tool,
        "get_order_status": get_order_status_tool,
        "search_products": search_products_tool,
        "check_return_eligibility": check_return_eligibility_tool,
        "check_refund_possibility": check_refund_possibility_tool,
        "check_warranty_status": check_warranty_status_tool,
        "get_troubleshooting_steps": get_troubleshooting_steps_tool,
    }
    
    # Special case: RAG-based policy search
    if tool_name == "search_policy_docs":
        query = tool_args.get("query", "")
        rag_result = answer_with_rag(query, k=3)
        return {
            "answer": rag_result.get("answer", ""),
            "sources": rag_result.get("sources", [])
        }
    
    # Execute the tool
    tool_func = tool_map.get(tool_name)
    if not tool_func:
        return {"error": f"Unknown tool: {tool_name}"}
    
    try:
        result = tool_func.invoke(tool_args)
        return result
    except Exception as e:
        return {"error": str(e)}


def format_history_for_gemini(conversation_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert our DB history format to Gemini's expected format.
    """
    formatted = []
    for msg in conversation_history:
        role = msg.get("role")
        content = msg.get("content", "")
        
        if role == "user":
            formatted.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            formatted.append({"role": "model", "parts": [{"text": content}]})
    
    return formatted


def clean_tool_args(args_obj) -> Dict[str, Any]:
    """
    Helper to convert Google Protobuf maps/lists into standard Python dicts/lists.
    This fixes the 'RepeatedComposite' serialization error in FastAPI.
    """
    cleaned = {}
    for key, value in args_obj.items():
        # Check if it looks like a list (Google RepeatedComposite)
        if hasattr(value, "append") or hasattr(value, "__iter__") and not isinstance(value, str):
            cleaned[key] = list(value)
        else:
            cleaned[key] = value
    return cleaned


def handle_user_message_agentic(
    user_message: str,
    conversation_history: List[Dict[str, Any]],
    user_id: str | None,
    session_id: str,
    today: str | None = None
) -> Dict[str, Any]:
    """
    Main agentic orchestrator using Gemini function calling.
    
    The LLM autonomously:
    1. Decides which tools to call
    2. Chains multiple tool calls
    3. Synthesizes final answer
    """
    today = today or get_today_str()
    
    # Quick intent detection (for logging and fallback)
    router_info = detect_intent(user_message)
    intent = router_info["intent"]
    
    # ========== HANDLE CHITCHAT (no agentic loop needed) ==========
    if intent == "chitchat":
        lowered = user_message.strip().lower()
        
        if "how are you" in lowered or "how r you" in lowered:
            ans = "I'm doing great and ready to help you! How can I assist you today?"
        elif "who are you" in lowered:
            ans = (
                "I'm an AI assistant for Antigravity Electronics. I can help with "
                "orders, returns, refunds, warranty, product recommendations, and troubleshooting."
            )
        elif "what can you do" in lowered:
            ans = (
                "I can help you:\n"
                "• Track orders and check delivery status\n"
                "• Check return and refund eligibility\n"
                "• Look up warranty information\n"
                "• Suggest products based on your needs\n"
                "• Assist with device troubleshooting\n"
                "• Answer questions about our policies"
            )
        elif "thank" in lowered:
            ans = "You're welcome! Feel free to ask if you need anything else."
        else:
            ans = "Hi! I'm here to help with orders, products, returns, refunds, and more. What can I do for you?"
        
        return {
            "intent": intent,
            "answer": ans,
            "route": "builtin:chitchat",
            "tool_calls": [],
            "iterations": 0,
            "router_info": router_info,
        }
    
    # ========== DATE QUERY ==========
    if intent == "date_query":
        return {
            "intent": intent,
            "answer": f"Today's date is {today}.",
            "route": "builtin:date",
            "tool_calls": [],
            "iterations": 0,
            "router_info": router_info,
        }
    
    # ========== CHECK IF USER AUTHENTICATION NEEDED ==========
    if intent in PRIVATE_INTENTS and user_id is None:
        return {
            "intent": intent,
            "answer": (
                "To help with your order, return, refund, or warranty query, "
                "I need to identify you. You can either:\n"
                "1. Log in to your account (top right), OR\n"
                "2. Provide your User ID (e.g., U001, U002)\n\n"
                "If you don't know your User ID, you can ask me to look it up by email."
            ),
            "route": "auth:user_id_required",
            "tool_calls": [],
            "iterations": 0,
            "router_info": router_info,
        }
    
    # ========== AGENTIC LOOP WITH GEMINI FUNCTION CALLING ==========
    
    # Load environment variables
    load_dotenv()
    
    # Configure Gemini with API key
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        # Fallback: try GOOGLE_API_KEY
        GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    if not GEMINI_API_KEY:
        return {
            "intent": intent,
            "answer": (
                "API key not configured. Please set GEMINI_API_KEY or GOOGLE_API_KEY "
                "in your .env file."
            ),
            "route": "error:no_api_key",
            "tool_calls": [],
            "iterations": 0,
            "router_info": router_info,
        }
    
    # Configure Gemini
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Configure Gemini with tools
    model = genai.GenerativeModel(
        model_name='models/gemini-2.5-flash',
        tools=[{"function_declarations": GEMINI_TOOL_DEFINITIONS}]
    )
    
    # Build conversation context with user_id awareness
    user_context = ""
    if user_id:
        user_context = f"""
🔐 IMPORTANT - USER CONTEXT:
The user is currently logged in as user_id: {user_id}

CRITICAL RULES:
1. When the user asks about "my orders", "my order", "return my laptop", etc., 
   YOU MUST automatically use the find_orders_by_user_id tool with user_id="{user_id}"
2. DO NOT ask the user for their user_id - you already have it!
3. DO NOT say "Please provide your user ID" - you have direct access to it!
4. Always start by finding their orders using find_orders_by_user_id("{user_id}")

Examples:
- User: "Show me my orders" → Immediately call find_orders_by_user_id("{user_id}")
- User: "I want to return my laptop" → Call find_orders_by_user_id("{user_id}") first
- User: "Check my refund status" → Call find_orders_by_user_id("{user_id}") first
"""
    else:
        user_context = f"""
🔓 USER CONTEXT:
The user is NOT logged in (anonymous session).

For personalized queries (orders, returns, refunds, warranty):
- Politely ask them to either log in OR provide their user_id manually
- Example: "To check your orders, please log in or provide your user ID (e.g., U001)"
"""
    
    system_prompt = f"""You are an intelligent e-commerce support assistant for Antigravity Electronics.

{user_context}

Current context:
- Today's date: {today}
- Session ID: {session_id}

Your capabilities:
1. Track orders and shipments
2. Check return/refund eligibility
3. Verify warranty status
4. Recommend products
5. Troubleshoot device issues
6. Answer policy questions

Guidelines:
- Use the available tools to get accurate, real-time information
- Chain multiple tool calls when needed (e.g., find user orders → check return eligibility)
- Be concise but helpful and friendly
- If the user is logged in, USE THEIR USER_ID automatically - don't ask for it!
- For complex issues beyond your tools, suggest escalation to support team

Available tools: {', '.join([t['name'] for t in GEMINI_TOOL_DEFINITIONS])}
"""
    
    # Format history
    formatted_history = format_history_for_gemini(conversation_history)
    
    # Agentic loop (max 10 iterations to prevent infinite loops)
    tool_calls_log = []
    
    # Initialize tool_result to safe default
    tool_result = None

    try:
        # Start chat with history
        chat = model.start_chat(history=formatted_history)
        
        # Send initial user message with system context
        full_user_message = f"{system_prompt}\n\nUser question: {user_message}"
        response = chat.send_message(full_user_message)
        
        for iteration in range(10):
            # Better error handling for response
            if not response.candidates:
                print("[Agent Error] No candidates in response")
                break
            
            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                print("[Agent Error] No content parts in candidate")
                break
            
            first_part = candidate.content.parts[0]
            
            # Check if model wants to call a function
            if hasattr(first_part, 'function_call') and first_part.function_call:
                function_call = first_part.function_call
                tool_name = function_call.name
                
                # CLEAN THE ARGS: Convert from Protobuf Map to Python Dict
                # This fixes the "RepeatedComposite" serialization error
                tool_args = clean_tool_args(function_call.args)
                
                # Log the tool call
                tool_calls_log.append({
                    "tool": tool_name,
                    "args": tool_args
                })
                
                print(f"[Agent] Calling tool: {tool_name} with args: {tool_args}")
                
                # Execute the tool
                tool_result = execute_tool_call(tool_name, tool_args, today)
                
                print(f"[Agent] Tool result: {tool_result}")
                
                # Send function response back to continue the conversation
                response = chat.send_message(
                    genai.protos.Content(
                        parts=[
                            genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=tool_name,
                                    response={"result": tool_result}
                                )
                            )
                        ]
                    )
                )
                
                # Continue loop - the model will process the result
                continue
                
            elif hasattr(first_part, 'text') and first_part.text:
                # Model has final answer
                final_answer = first_part.text
                
                return {
                    "intent": intent,
                    "answer": final_answer,
                    "route": "gemini:agentic_function_calling",
                    "tool_calls": tool_calls_log,
                    "iterations": iteration + 1,
                    "router_info": router_info,
                }
            else:
                print(f"[Agent Error] Unexpected part type: {type(first_part)}")
                break
        
        # Max iterations reached or error
        if tool_calls_log:
            # If we called tools but didn't get a final answer, return the last tool result
            if isinstance(tool_result, dict) and "message" in tool_result:
                fallback_answer = tool_result["message"]
            else:
                fallback_answer = (
                    "I gathered some information but encountered an issue generating "
                    "the final response. Please try rephrasing your question."
                )
            
            return {
                "intent": intent,
                "answer": fallback_answer,
                "route": "gemini:max_iterations_with_tools",
                "tool_calls": tool_calls_log,
                "iterations": 10,
                "router_info": router_info,
            }
        else:
            # No tools called, fall back
            return handle_user_message_fallback(
                user_message, user_id, today, router_info, intent
            )
    
    except Exception as e:
        import traceback
        print(f"[Agent Error] {str(e)}")
        print(traceback.format_exc())
        
        # If we got tool results before the error, try to use them
        if tool_calls_log and isinstance(tool_result, dict):
            if "message" in tool_result:
                return {
                    "intent": intent,
                    "answer": tool_result["message"],
                    "route": "gemini:error_with_partial_results",
                    "tool_calls": tool_calls_log,
                    "iterations": len(tool_calls_log),
                    "router_info": router_info,
                }
        
        # Fallback to non-agentic handling
        return handle_user_message_fallback(
            user_message, user_id, today, router_info, intent
        )


def handle_user_message_fallback(
    user_message: str,
    user_id: str | None,
    today: str,
    router_info: Dict[str, Any],
    intent: str
) -> Dict[str, Any]:
    """
    Fallback handler if agentic loop fails.
    Uses the old rule-based routing.
    """
    # Simple RAG fallback
    rag_res = answer_with_rag(user_message, k=3)
    answer_text = rag_res.get("answer", "I'm having trouble answering that. Please try rephrasing.")
    
    return {
        "intent": intent,
        "answer": answer_text,
        "route": "fallback:rag",
        "tool_calls": [],
        "iterations": 0,
        "router_info": router_info,
        "rag_result": rag_res,
    }


# Alias for backward compatibility
def handle_user_message(
    user_message: str,
    conversation_history: List[Dict[str, Any]] = None,
    user_id: str | None = None,
    session_id: str = "default",
    today: str | None = None
) -> Dict[str, Any]:
    """
    Wrapper for agentic handler.
    """
    conversation_history = conversation_history or []
    return handle_user_message_agentic(
        user_message, conversation_history, user_id, session_id, today
    )