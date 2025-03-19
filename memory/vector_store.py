"""
Vector-based memory storage for Jarvis.
This module provides semantic search capabilities using FAISS and sentence-transformers.
"""
import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import faiss
from sentence_transformers import SentenceTransformer

from jarvis.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Vector-based memory storage using FAISS and sentence-transformers.
    Provides semantic search capabilities for conversations and memories.
    """
    
    def __init__(self, 
                 storage_dir: Optional[Path] = None,
                 model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the vector store.
        
        Args:
            storage_dir: Directory to store vector indices and metadata
            model_name: Name of the sentence-transformer model to use
        """
        self.storage_dir = storage_dir or Path(settings.MEMORY_STORAGE_PATH).parent / "vector_store"
        self.storage_dir.mkdir(exist_ok=True, parents=True)
        
        self.index_path = self.storage_dir / "faiss_index.bin"
        self.metadata_path = self.storage_dir / "metadata.json"
        
        # Initialize the sentence transformer model
        logger.info(f"Loading sentence transformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.vector_dim = self.model.get_sentence_embedding_dimension()
        
        # Initialize or load the FAISS index and metadata
        self.index, self.metadata = self._initialize_index()
    
    def _initialize_index(self) -> Tuple[faiss.Index, List[Dict[str, Any]]]:
        """Initialize or load the FAISS index and metadata."""
        # Check if index already exists
        if self.index_path.exists() and self.metadata_path.exists():
            try:
                # Load existing index
                index = faiss.read_index(str(self.index_path))
                
                # Load metadata
                with open(self.metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                logger.info(f"Loaded existing index with {index.ntotal} entries")
                return index, metadata
            except Exception as e:
                logger.error(f"Error loading index: {str(e)}. Creating new index.")
        
        # Create new index
        index = faiss.IndexFlatL2(self.vector_dim)
        metadata = []
        logger.info(f"Created new vector index with dimension {self.vector_dim}")
        return index, metadata
    
    def _save_index(self):
        """Save the FAISS index and metadata to disk."""
        try:
            faiss.write_index(self.index, str(self.index_path))
            
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
                
            logger.info(f"Saved vector index with {self.index.ntotal} entries")
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
    
    def add_entry(self, text: str, metadata_entry: Dict[str, Any]):
        """
        Add an entry to the vector store.
        
        Args:
            text: Text to vectorize and store
            metadata_entry: Associated metadata for this entry
        """
        # Create embedding
        embedding = self.model.encode([text])[0]
        
        # Add to FAISS index
        self.index.add(np.array([embedding], dtype=np.float32))
        
        # Add metadata with the same index
        entry_id = self.index.ntotal - 1
        metadata_entry["id"] = entry_id
        metadata_entry["text"] = text
        metadata_entry["timestamp"] = datetime.now().isoformat()
        
        self.metadata.append(metadata_entry)
        
        # Save index periodically (every 10 entries)
        if entry_id % 10 == 0:
            self._save_index()
    
    def add_conversation(self, 
                         user_input: str, 
                         assistant_response: str,
                         context_info: Optional[Dict[str, Any]] = None):
        """
        Add a conversation to the vector store.
        
        Args:
            user_input: User's input text
            assistant_response: Assistant's response text
            context_info: Optional context information
        """
        # Combine for better semantic search
        combined_text = f"User: {user_input}\nAssistant: {assistant_response}"
        
        metadata = {
            "type": "conversation",
            "user_input": user_input,
            "assistant_response": assistant_response,
            "context": context_info or {}
        }
        
        self.add_entry(combined_text, metadata)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the vector store for entries similar to the query.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            
        Returns:
            List of metadata entries for the most similar items
        """
        if self.index.ntotal == 0:
            return []
        
        # Encode the query
        query_vector = self.model.encode([query])[0]
        query_vector = np.array([query_vector], dtype=np.float32)
        
        # Search the index
        top_k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_vector, top_k)
        
        # Get metadata for results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result["distance"] = float(distances[0][i])
                results.append(result)
        
        return results
    
    def get_relevant_context(self, query: str, max_entries: int = 5) -> str:
        """
        Get relevant context for a query, formatted for inclusion in a prompt.
        
        Args:
            query: The query to find relevant context for
            max_entries: Maximum number of entries to include
            
        Returns:
            Formatted context string for inclusion in a prompt
        """
        results = self.search(query, top_k=max_entries)
        
        if not results:
            return ""
        
        context_parts = ["Here are some relevant past interactions:"]
        
        for i, result in enumerate(results):
            user_input = result.get("user_input", "")
            assistant_response = result.get("assistant_response", "")
            timestamp = datetime.fromisoformat(result.get("timestamp", datetime.now().isoformat()))
            
            # Format timestamp as relative time
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M")
            
            context_parts.append(f"{i+1}. [{timestamp_str}]")
            context_parts.append(f"   User: {user_input}")
            context_parts.append(f"   Assistant: {assistant_response}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def clear(self):
        """Clear the vector store."""
        self.index = faiss.IndexFlatL2(self.vector_dim)
        self.metadata = []
        self._save_index()
        logger.info("Vector store cleared")

# Create a singleton instance
vector_store = VectorStore() 