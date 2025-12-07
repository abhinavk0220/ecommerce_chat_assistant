# backend/app.py

"""
FastAPI application with authentication, session management, and agentic orchestration.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from agent.orchestrator import handle_user_message
from guardrails import apply_guardrails, GuardrailResult
from database.db_manager import db
from auth.auth_manager import (
    authenticate_user,
    create_session_for_user,
    create_anonymous_session,
    get_session_user,
    logout_session
)

app = FastAPI(
    title="Ecommerce RAG Assistant",
    description="Agentic RAG + Tools workflow for ecommerce support",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== PYDANTIC MODELS ====================

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    session_id: str | None = None
    user_id: str | None = None
    name: str | None = None
    message: str | None = None


class ChatRequest(BaseModel):
    user_message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    intent: str
    route: str
    session_id: str
    tool_calls: list = []
    iterations: int = 0
    router_info: dict = {}
    from_cache: bool = False
    guardrail_triggered: bool = False
    guardrail_reason: str | None = None


# ==================== ENDPOINTS ====================

@app.get("/health")
async def health_check():
    return {"status": "ok", "database": "connected"}


@app.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    """
    Authenticate user and create a session.
    """
    user = authenticate_user(payload.email, payload.password)
    
    if not user:
        return LoginResponse(
            success=False,
            message="Invalid email or password"
        )
    
    # Create session
    session_id = create_session_for_user(user["user_id"])
    
    return LoginResponse(
        success=True,
        session_id=session_id,
        user_id=user["user_id"],
        name=user["name"],
        message="Login successful"
    )


@app.post("/logout")
async def logout(session_id: str = Header(None)):
    """
    End a session (logout).
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="No session_id provided")
    
    logout_session(session_id)
    return {"success": True, "message": "Logged out successfully"}


@app.post("/create-anonymous-session")
async def create_anon_session():
    """
    Create an anonymous session for users who don't want to log in.
    """
    session_id = create_anonymous_session()
    return {"session_id": session_id}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """
    Main chat endpoint with agentic orchestration.
    
    Flow:
    1. Validate/create session
    2. Apply guardrails
    3. Load conversation history
    4. Call agentic orchestrator
    5. Save conversation
    6. Return response
    """
    raw_message = payload.user_message
    session_id = payload.session_id
    
    # Create anonymous session if none provided
    if not session_id:
        session_id = create_anonymous_session()
    
    # Get user_id from session (if logged in)
    user_id = get_session_user(session_id)
    
    # Apply guardrails
    gr: GuardrailResult = apply_guardrails(raw_message)
    if not gr.allowed:
        # Save blocked message to history
        db.add_message(
            session_id=session_id,
            role="user",
            content=raw_message,
            user_id=user_id,
            intent="guardrail_blocked",
            route=f"guardrail:{gr.reason}"
        )
        db.add_message(
            session_id=session_id,
            role="assistant",
            content=gr.message or "I cannot respond to this request.",
            user_id=user_id,
            intent="guardrail_response",
            route=f"guardrail:{gr.reason}"
        )
        
        return ChatResponse(
            answer=gr.message or "I cannot respond to this request.",
            intent="guardrail",
            route=f"guardrail:{gr.reason}",
            session_id=session_id,
            tool_calls=[],
            iterations=0,
            router_info={},
            from_cache=False,
            guardrail_triggered=True,
            guardrail_reason=gr.reason,
        )
    
    # Load conversation history (last 20 messages)
    conversation_history = db.get_conversation_history(session_id, limit=20)
    
    # Save user message
    db.add_message(
        session_id=session_id,
        role="user",
        content=raw_message,
        user_id=user_id
    )
    
    # Call agentic orchestrator
    result = handle_user_message(
        user_message=raw_message,
        conversation_history=conversation_history,
        user_id=user_id,
        session_id=session_id
    )
    
    # Save assistant response
    db.add_message(
        session_id=session_id,
        role="assistant",
        content=result["answer"],
        user_id=user_id,
        intent=result.get("intent"),
        route=result.get("route")
    )
    
    # Return response
    return ChatResponse(
        answer=result["answer"],
        intent=result["intent"],
        route=result["route"],
        session_id=session_id,
        tool_calls=result.get("tool_calls", []),
        iterations=result.get("iterations", 0),
        router_info=result.get("router_info", {}),
        from_cache=False,
        guardrail_triggered=False,
        guardrail_reason=None,
    )


@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 20):
    """
    Get conversation history for a session.
    """
    history = db.get_conversation_history(session_id, limit=limit)
    return {"session_id": session_id, "history": history}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)