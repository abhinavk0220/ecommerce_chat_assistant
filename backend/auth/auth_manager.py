# backend/auth/auth_manager.py

"""
Authentication manager for login/logout and session management.
"""

import bcrypt
from typing import Optional, Dict, Any
from database.db_manager import db


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user by email and password.
    Returns user dict if successful, None otherwise.
    """
    user = db.get_user_by_email(email)
    
    if not user:
        return None
    
    if not verify_password(password, user['password_hash']):
        return None
    
    # Remove password hash from returned user
    user_safe = {k: v for k, v in user.items() if k != 'password_hash'}
    return user_safe


def create_session_for_user(user_id: str) -> str:
    """Create a new session for a logged-in user."""
    return db.create_session(user_id=user_id)


def create_anonymous_session() -> str:
    """Create a new anonymous session (no user_id)."""
    return db.create_session(user_id=None)


def get_session_user(session_id: str) -> Optional[str]:
    """Get user_id associated with a session."""
    session = db.get_session(session_id)
    if session and session.get('is_active'):
        db.update_session_activity(session_id)
        return session.get('user_id')
    return None


def logout_session(session_id: str):
    """End a session (logout)."""
    db.end_session(session_id)


def link_session_to_user(session_id: str, user_id: str):
    """
    Link an anonymous session to a user.
    Useful when user provides user_id manually.
    """
    db.link_session_to_user(session_id, user_id)