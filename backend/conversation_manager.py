"""
Conversation manager for hybrid persistence supporting both server-native
conversation IDs and client-side conversation management.
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import uuid


@dataclass
class ConversationSession:
    """Represents a conversation session"""
    session_id: str
    messages: List[Dict[str, Any]]
    server_conversation_ids: Dict[str, str]  # server_id -> conversation_id
    created_at: float
    last_updated: float


class ConversationManager:
    """Manages conversation persistence using hybrid approach"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ConversationManager")
        # In-memory storage (could be extended to persistent storage)
        self.sessions: Dict[str, ConversationSession] = {}
        self.max_sessions = 100  # Limit memory usage
        self.session_timeout = 3600  # 1 hour timeout
    
    def create_session(self, initial_message: str) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        current_time = time.time()
        
        session = ConversationSession(
            session_id=session_id,
            messages=[{"role": "user", "content": initial_message}],
            server_conversation_ids={},
            created_at=current_time,
            last_updated=current_time
        )
        
        self.sessions[session_id] = session
        self._cleanup_old_sessions()
        
        self.logger.info(f"Created new conversation session: {session_id}")
        return session_id
    
    def add_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """Add a message to the conversation"""
        if session_id not in self.sessions:
            self.logger.warning(f"Session {session_id} not found")
            return
        
        self.sessions[session_id].messages.append(message)
        self.sessions[session_id].last_updated = time.time()
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a conversation"""
        if session_id not in self.sessions:
            self.logger.warning(f"Session {session_id} not found")
            return []
        
        return self.sessions[session_id].messages.copy()
    
    def extract_conversation_id(self, server_id: str, server_config: Dict[str, Any], 
                                response: Dict[str, Any]) -> Optional[str]:
        """Extract conversation ID from server response if configured"""
        conversation_field = server_config.get("conversation_field")
        if not conversation_field:
            return None
        
        conversation_location = server_config.get("conversation_location", "response")
        
        if conversation_location == "response":
            # Look for conversation ID in response content
            conversation_id = self._extract_from_response(response, conversation_field)
            if conversation_id:
                self.logger.info(f"Extracted conversation ID '{conversation_id}' from server {server_id}")
                return conversation_id
        
        return None
    
    def store_server_conversation_id(self, session_id: str, server_id: str, 
                                   conversation_id: str) -> None:
        """Store server-specific conversation ID for a session"""
        if session_id not in self.sessions:
            self.logger.warning(f"Session {session_id} not found")
            return
        
        self.sessions[session_id].server_conversation_ids[server_id] = conversation_id
        self.logger.info(f"Stored conversation ID '{conversation_id}' for server {server_id} in session {session_id}")
    
    def get_server_conversation_id(self, session_id: str, server_id: str) -> Optional[str]:
        """Get server-specific conversation ID for a session"""
        if session_id not in self.sessions:
            return None
        
        return self.sessions[session_id].server_conversation_ids.get(server_id)
    
    def prepare_tool_arguments(self, session_id: str, server_id: str, 
                             server_config: Dict[str, Any], 
                             arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare tool arguments, adding conversation ID if supported"""
        conversation_field = server_config.get("conversation_field")
        conversation_location = server_config.get("conversation_location", "response")
        
        if conversation_field and conversation_location == "params":
            # Add conversation ID to parameters if server expects it there
            conversation_id = self.get_server_conversation_id(session_id, server_id)
            if conversation_id:
                arguments = arguments.copy()
                arguments[conversation_field] = conversation_id
                self.logger.debug(f"Added {conversation_field}={conversation_id} to tool arguments")
        
        return arguments
    
    def _extract_from_response(self, response: Dict[str, Any], field_name: str) -> Optional[str]:
        """Extract conversation ID from response content"""
        def search_nested(obj, target_field):
            if isinstance(obj, dict):
                if target_field in obj:
                    return obj[target_field]
                for value in obj.values():
                    result = search_nested(value, target_field)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = search_nested(item, target_field)
                    if result:
                        return result
            elif isinstance(obj, str):
                # Try parsing as JSON in case it's a JSON string
                try:
                    parsed = json.loads(obj)
                    return search_nested(parsed, target_field)
                except (json.JSONDecodeError, TypeError):
                    pass
            return None
        
        return search_nested(response, field_name)
    
    def _cleanup_old_sessions(self) -> None:
        """Remove old sessions to prevent memory leaks"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session.last_updated > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            self.logger.debug(f"Removed expired session: {session_id}")
        
        # Also limit total number of sessions
        if len(self.sessions) > self.max_sessions:
            # Remove oldest sessions
            sorted_sessions = sorted(
                self.sessions.items(),
                key=lambda x: x[1].last_updated
            )
            
            to_remove = len(self.sessions) - self.max_sessions
            for session_id, _ in sorted_sessions[:to_remove]:
                del self.sessions[session_id]
                self.logger.debug(f"Removed old session due to limit: {session_id}")


# Global conversation manager instance
conversation_manager = ConversationManager()