"""
Memory Manager for Jarvis.
Combines traditional and vector-based storage for enhanced memory capabilities.
"""
import logging
from typing import Dict, List, Any, Optional

from jarvis.memory.storage import memory_storage
from jarvis.memory.vector_store import vector_store
from jarvis.config import settings

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Memory manager for Jarvis that combines traditional and vector-based storage.
    Provides enhanced context retrieval capabilities for conversations.
    """
    
    def __init__(self):
        """Initialize the memory manager."""
        self.storage = memory_storage
        self.vector_store = vector_store
    
    def add_conversation(self, 
                        user_input: str, 
                        assistant_response: str,
                        context_info: Optional[Dict[str, Any]] = None):
        """
        Add a conversation to memory (both traditional and vector storage).
        
        Args:
            user_input: User's input text
            assistant_response: Assistant's response text
            context_info: Optional context information
        """
        # Add to traditional storage
        self.storage.add_conversation(user_input, assistant_response)
        
        # Add to vector storage if enabled
        if settings.VECTOR_MEMORY_ENABLED:
            try:
                self.vector_store.add_conversation(user_input, assistant_response, context_info)
            except Exception as e:
                logger.error(f"Error adding to vector store: {str(e)}")
    
    def get_context_for_query(self, query: str, max_entries: int = 5) -> str:
        """
        Get relevant context for a query, formatted for inclusion in a prompt.
        Uses vector search for semantic similarity.
        
        Args:
            query: The query to find relevant context for
            max_entries: Maximum number of entries to include
            
        Returns:
            Formatted context string for inclusion in a prompt
        """
        if not settings.VECTOR_MEMORY_ENABLED:
            return ""
            
        try:
            return self.vector_store.get_relevant_context(query, max_entries)
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return ""
    
    def search_conversations(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search conversations using vector search for semantic similarity.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant conversation entries
        """
        if not settings.VECTOR_MEMORY_ENABLED:
            # Fall back to traditional search
            return self.storage.search_conversations(query)
            
        try:
            return self.vector_store.search(query, top_k=max_results)
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            # Fall back to traditional search
            return self.storage.search_conversations(query)
    
    def add_command(self, command_name: str, kwargs: Dict[str, Any], result: Dict[str, Any]):
        """Add a command execution entry to memory."""
        self.storage.add_command(command_name, kwargs, result)
    
    def set_user_preference(self, key: str, value: Any):
        """Set a user preference."""
        self.storage.set_user_preference(key, value)
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        return self.storage.get_user_preference(key, default)
    
    def get_recent_conversations(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get the N most recent conversations."""
        return self.storage.get_recent_conversations(n)
    
    def get_recent_commands(self, n: int = 5) -> List[Dict[str, Any]]:
        """Get the N most recent commands."""
        return self.storage.get_recent_commands(n)
    
    def clear_memory(self, include_vector: bool = True):
        """
        Clear memory data.
        
        Args:
            include_vector: Whether to clear vector store as well
        """
        self.storage.clear_memory()
        
        if include_vector and settings.VECTOR_MEMORY_ENABLED:
            try:
                self.vector_store.clear()
            except Exception as e:
                logger.error(f"Error clearing vector store: {str(e)}")

# Create a singleton instance
memory_manager = MemoryManager() 