# # backend/app.py

# from __future__ import annotations

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# from agent.orchestrator import handle_user_message

# app = FastAPI(
#     title="Ecommerce RAG Assistant",
#     description="RAG + Tools + Agentic workflow for ecommerce support",
#     version="0.1.0",
# )

# # CORS so frontend (localhost:5173, 3000, or just file://) can call API
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # you can restrict later
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# class ChatRequest(BaseModel):
#     user_message: str
#     session_id: str | None = None  # placeholder for future memory support


# class ChatResponse(BaseModel):
#     answer: str
#     intent: str
#     route: str
#     router_info: dict
#     tool_result: dict | None = None
#     rag_result: dict | None = None


# @app.get("/health")
# async def health_check():
#     return {"status": "ok"}


# @app.post("/chat", response_model=ChatResponse)
# async def chat_endpoint(payload: ChatRequest):
#     """
#     Main chat endpoint. Takes a user message and returns
#     the assistant's answer plus some debug metadata.
#     """
#     result = handle_user_message(payload.user_message)

#     # result is already a dict with keys:
#     # intent, answer, route, tool_result, rag_result, router_info
#     return ChatResponse(
#         answer=result["answer"],
#         intent=result["intent"],
#         route=result["route"],
#         router_info=result["router_info"],
#         tool_result=result.get("tool_result"),
#         rag_result=result.get("rag_result"),
#     )

# backend/app.py

from __future__ import annotations

from typing import Dict, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.orchestrator import handle_user_message
from guardrails import apply_guardrails, GuardrailResult


app = FastAPI(
    title="Ecommerce RAG Assistant",
    description="RAG + Tools + Agentic workflow for ecommerce support",
    version="0.1.0",
)

# CORS so frontend (localhost / file://) can call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    user_message: str
    session_id: str | None = None  # placeholder for future memory support


class ChatResponse(BaseModel):
    answer: str
    intent: str
    route: str
    router_info: dict
    tool_result: dict | None = None
    rag_result: dict | None = None

    # New metadata fields
    from_cache: bool = False
    guardrail_triggered: bool = False
    guardrail_reason: str | None = None


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# ----------------------------
# Simple in-memory cache
# ----------------------------

# Key: (session_id or "global", normalized_user_message)
CacheKey = Tuple[str, str]
CACHE: Dict[CacheKey, Dict] = {}
MAX_CACHE_SIZE = 100  # keep it small for demo


def make_cache_key(user_message: str, session_id: str | None) -> CacheKey:
    session = session_id or "global"
    normalized = " ".join(user_message.strip().lower().split())
    return (session, normalized)


def get_from_cache(key: CacheKey) -> Dict | None:
    return CACHE.get(key)


def set_in_cache(key: CacheKey, value: Dict) -> None:
    if len(CACHE) >= MAX_CACHE_SIZE:
        # very simple eviction: remove an arbitrary item
        try:
            first_key = next(iter(CACHE))
            CACHE.pop(first_key, None)
        except StopIteration:
            pass
    CACHE[key] = value


# ----------------------------
# Chat endpoint with guardrails + cache
# ----------------------------

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """
    Main chat endpoint. Takes a user message and returns
    the assistant's answer plus some debug metadata.

    Guardrails are applied FIRST.
    If allowed, we then:
      - check cache
      - if miss, call handle_user_message and populate cache
    """
    raw_message = payload.user_message

    # 1) Apply guardrails
    gr: GuardrailResult = apply_guardrails(raw_message)
    if not gr.allowed:
        # We DO NOT call the main assistant logic here.
        return ChatResponse(
            answer=gr.message or "I cannot respond to this request.",
            intent="guardrail",
            route=f"guardrail:{gr.reason or 'blocked'}",
            router_info={},
            tool_result=None,
            rag_result=None,
            from_cache=False,
            guardrail_triggered=True,
            guardrail_reason=gr.reason,
        )

    # 2) Build cache key
    key = make_cache_key(raw_message, payload.session_id)

    # 3) Check cache
    cached = get_from_cache(key)
    if cached is not None:
        # cached is the full result dict from handle_user_message
        return ChatResponse(
            answer=cached["answer"],
            intent=cached["intent"],
            route=cached["route"],
            router_info=cached["router_info"],
            tool_result=cached.get("tool_result"),
            rag_result=cached.get("rag_result"),
            from_cache=True,
            guardrail_triggered=False,
            guardrail_reason=None,
        )

    # 4) Cache miss -> call main assistant logic
    result = handle_user_message(raw_message)

    # Store raw result dict in cache
    set_in_cache(key, result)

    # 5) Return response (not from cache)
    return ChatResponse(
        answer=result["answer"],
        intent=result["intent"],
        route=result["route"],
        router_info=result["router_info"],
        tool_result=result.get("tool_result"),
        rag_result=result.get("rag_result"),
        from_cache=False,
        guardrail_triggered=False,
        guardrail_reason=None,
    )

