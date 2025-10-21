"""
Session Service - Manage chat sessions and history.
"""

import json
from typing import List, Optional, Dict
import redis
from core.settings import settings

# Redis client for session storage
redis_client = redis.from_url(settings.redis_url)


class SessionService:
    """Service for managing chat sessions."""
    
    SESSION_TTL = 86400 * 7  # 7 days
    
    @staticmethod
    def add_message(session_id: str, role: str, content: str, citations: Optional[List[Dict]] = None):
        """Add a message to the session history."""
        try:
            # Get existing messages
            messages = SessionService.get_messages(session_id)
            
            # Add new message
            message = {
                "role": role,
                "content": content,
                "timestamp": str(json.dumps(None)),  # Will be set by frontend
            }
            
            if citations:
                message["citations"] = citations
            
            messages.append(message)
            
            # Store back to Redis
            redis_client.setex(
                f"session:{session_id}:messages",
                SessionService.SESSION_TTL,
                json.dumps(messages)
            )
            
            return True
        except Exception as e:
            print(f"Failed to add message to session: {e}")
            return False
    
    @staticmethod
    def get_messages(session_id: str) -> List[Dict]:
        """Retrieve all messages from a session."""
        try:
            messages_json = redis_client.get(f"session:{session_id}:messages")
            if messages_json:
                return json.loads(messages_json)
            return []
        except Exception as e:
            print(f"Failed to get session messages: {e}")
            return []
    
    @staticmethod
    def clear_session(session_id: str) -> bool:
        """Clear all messages from a session."""
        try:
            redis_client.delete(f"session:{session_id}:messages")
            return True
        except Exception as e:
            print(f"Failed to clear session: {e}")
            return False
    
    @staticmethod
    def get_session_info(session_id: str) -> Dict:
        """Get session metadata."""
        try:
            messages = SessionService.get_messages(session_id)
            return {
                "session_id": session_id,
                "message_count": len(messages),
                "exists": len(messages) > 0
            }
        except Exception as e:
            print(f"Failed to get session info: {e}")
            return {
                "session_id": session_id,
                "message_count": 0,
                "exists": False
            }


# Initialize service instance
session_service = SessionService()

