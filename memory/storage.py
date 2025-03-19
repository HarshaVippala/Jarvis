"""
Memory storage module for Jarvis.
This module handles persisting conversation history and user preferences.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from jarvis.config import settings

logger = logging.getLogger(__name__)

class MemoryStorage:
    """Memory storage for Jarvis assistant."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize the memory storage."""
        self.storage_path = storage_path or settings.MEMORY_STORAGE_PATH
        self.max_entries = settings.MEMORY_MAX_ENTRIES
        self.memory_data = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory data from storage."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            else:
                # Create default memory structure
                default_memory = {
                    "conversation_history": [],
                    "user_preferences": {},
                    "command_history": [],
                }
                return default_memory
        except Exception as e:
            logger.error(f"Error loading memory: {str(e)}")
            # Return default structure in case of error
            return {
                "conversation_history": [],
                "user_preferences": {},
                "command_history": [],
            }
    
    def _save_memory(self):
        """Save memory data to storage."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            with open(self.storage_path, 'w') as f:
                json.dump(self.memory_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {str(e)}")
    
    def add_conversation(self, user_input: str, assistant_response: str):
        """Add a conversation entry to memory."""
        if not settings.MEMORY_ENABLED:
            return
        
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "assistant_response": assistant_response
        }
        
        self.memory_data["conversation_history"].append(conversation)
        
        # Trim to max entries
        if len(self.memory_data["conversation_history"]) > self.max_entries:
            self.memory_data["conversation_history"] = self.memory_data["conversation_history"][-self.max_entries:]
        
        self._save_memory()
    
    def add_command(self, command_name: str, kwargs: Dict[str, Any], result: Dict[str, Any]):
        """Add a command execution entry to memory."""
        if not settings.MEMORY_ENABLED:
            return
        
        command = {
            "timestamp": datetime.now().isoformat(),
            "command_name": command_name,
            "kwargs": kwargs,
            "result": result
        }
        
        self.memory_data["command_history"].append(command)
        
        # Trim to max entries
        if len(self.memory_data["command_history"]) > self.max_entries:
            self.memory_data["command_history"] = self.memory_data["command_history"][-self.max_entries:]
        
        self._save_memory()
    
    def set_user_preference(self, key: str, value: Any):
        """Set a user preference."""
        if not settings.MEMORY_ENABLED:
            return
        
        self.memory_data["user_preferences"][key] = value
        self._save_memory()
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        if not settings.MEMORY_ENABLED:
            return default
        
        return self.memory_data["user_preferences"].get(key, default)
    
    def get_recent_conversations(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get the N most recent conversations."""
        if not settings.MEMORY_ENABLED or not self.memory_data["conversation_history"]:
            return []
        
        return self.memory_data["conversation_history"][-n:]
    
    def get_recent_commands(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get the N most recent commands."""
        if not settings.MEMORY_ENABLED or not self.memory_data["command_history"]:
            return []
        
        return self.memory_data["command_history"][-n:]
    
    def search_conversations(self, query: str) -> List[Dict[str, Any]]:
        """Search conversations for a query."""
        if not settings.MEMORY_ENABLED or not self.memory_data["conversation_history"]:
            return []
        
        # Simple search implementation
        results = []
        for conv in self.memory_data["conversation_history"]:
            if (query.lower() in conv["user_input"].lower() or 
                query.lower() in conv["assistant_response"].lower()):
                results.append(conv)
        
        return results
    
    def clear_memory(self):
        """Clear all memory data."""
        self.memory_data = {
            "conversation_history": [],
            "user_preferences": {},
            "command_history": [],
        }
        self._save_memory()

# Create a singleton instance of the memory storage
memory_storage = MemoryStorage() 