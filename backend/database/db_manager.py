# backend/database/db_manager.py

"""
Database manager for SQLite operations.
Handles all CRUD operations for users, sessions, and conversation history.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "assistant.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class DatabaseManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database with schema."""
        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
        
        with open(SCHEMA_PATH, 'r') as f:
            schema = f.read()
        
        conn = self._get_connection()
        conn.executescript(schema)
        conn.commit()
        conn.close()

    # ==================== USER OPERATIONS ====================
    
    def create_user(self, user_id: str, name: str, email: str, password_hash: str) -> bool:
        """Create a new user."""
        try:
            conn = self._get_connection()
            conn.execute(
                "INSERT INTO users (user_id, name, email, password_hash) VALUES (?, ?, ?, ?)",
                (user_id, name, email, password_hash)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user_id."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None

    # ==================== SESSION OPERATIONS ====================
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new session. Returns session_id."""
        session_id = str(uuid.uuid4())
        conn = self._get_connection()
        conn.execute(
            "INSERT INTO sessions (session_id, user_id) VALUES (?, ?)",
            (session_id, user_id)
        )
        conn.commit()
        conn.close()
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by session_id."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ? AND is_active = TRUE",
            (session_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None

    def update_session_activity(self, session_id: str):
        """Update last_active timestamp for a session."""
        conn = self._get_connection()
        conn.execute(
            "UPDATE sessions SET last_active = ? WHERE session_id = ?",
            (datetime.now(), session_id)
        )
        conn.commit()
        conn.close()

    def link_session_to_user(self, session_id: str, user_id: str):
        """Link an anonymous session to a user after login."""
        conn = self._get_connection()
        conn.execute(
            "UPDATE sessions SET user_id = ? WHERE session_id = ?",
            (user_id, session_id)
        )
        conn.commit()
        conn.close()

    def end_session(self, session_id: str):
        """Mark session as inactive."""
        conn = self._get_connection()
        conn.execute(
            "UPDATE sessions SET is_active = FALSE WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
        conn.close()

    # ==================== CONVERSATION HISTORY ====================
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        intent: Optional[str] = None,
        route: Optional[str] = None
    ):
        """Add a message to conversation history."""
        conn = self._get_connection()
        conn.execute(
            """INSERT INTO conversation_history 
               (session_id, user_id, role, content, intent, route) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, user_id, role, content, intent, route)
        )
        conn.commit()
        conn.close()

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session (last N messages)."""
        conn = self._get_connection()
        cursor = conn.execute(
            """SELECT role, content, intent, route, timestamp 
               FROM conversation_history 
               WHERE session_id = ? 
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (session_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        # Reverse to get chronological order
        messages = [dict(row) for row in reversed(rows)]
        return messages

    # ==================== CONVERSATION STATE ====================
    
    def save_state(
        self,
        session_id: str,
        current_intent: Optional[str] = None,
        awaiting_field: Optional[str] = None,
        collected_slots: Optional[Dict] = None
    ):
        """Save conversation state for multi-step flows."""
        slots_json = json.dumps(collected_slots) if collected_slots else None
        
        conn = self._get_connection()
        conn.execute(
            """INSERT OR REPLACE INTO conversation_state 
               (session_id, current_intent, awaiting_field, collected_slots, last_updated)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, current_intent, awaiting_field, slots_json, datetime.now())
        )
        conn.commit()
        conn.close()

    def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation state for a session."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT * FROM conversation_state WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            state = dict(row)
            if state.get('collected_slots'):
                state['collected_slots'] = json.loads(state['collected_slots'])
            return state
        return None

    def clear_state(self, session_id: str):
        """Clear conversation state."""
        conn = self._get_connection()
        conn.execute("DELETE FROM conversation_state WHERE session_id = ?", (session_id,))
        conn.commit()
        conn.close()


# Singleton instance
db = DatabaseManager()