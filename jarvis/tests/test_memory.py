#!/usr/bin/env python3
"""
Test script for Jarvis memory system with vector storage.
This script tests basic memory functionality and vector-based semantic search.
"""
import sys
import logging
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jarvis.memory.memory_manager import memory_manager
from jarvis.memory.vector_store import vector_store

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_add_conversations():
    """Test adding conversations to memory and vector store."""
    logger.info("Testing adding conversations...")
    
    # Add some test conversations
    memory_manager.add_conversation(
        "What's the weather today?", 
        "It's currently 72°F and sunny in your location.",
        {"context": "weather query"}
    )
    
    memory_manager.add_conversation(
        "Tell me about the solar system", 
        "The solar system consists of the Sun and everything that orbits around it, including planets, moons, asteroids, and comets.",
        {"context": "science query"}
    )
    
    memory_manager.add_conversation(
        "How do I create a Python virtual environment?", 
        "You can create a virtual environment using the command: python -m venv myenv. Then activate it with source myenv/bin/activate on Unix/macOS or myenv\\Scripts\\activate on Windows.",
        {"context": "programming query"}
    )
    
    memory_manager.add_conversation(
        "What's the capital of France?", 
        "The capital of France is Paris.",
        {"context": "geography query"}
    )
    
    memory_manager.add_conversation(
        "How do I install TensorFlow?", 
        "You can install TensorFlow using pip: pip install tensorflow. For GPU support, you would use: pip install tensorflow-gpu.",
        {"context": "programming query"}
    )
    
    logger.info("Added 5 test conversations to memory")

def test_vector_search():
    """Test vector-based semantic search."""
    logger.info("Testing vector search...")
    
    # Test queries and expected matches
    test_queries = [
        "What's the temperature outside?",
        "Tell me about planets",
        "How do I set up Python?",
        "What's the capital city of France?",
        "How do I install machine learning libraries?"
    ]
    
    for query in test_queries:
        logger.info(f"\nSearching for: \"{query}\"")
        results = vector_store.search(query, top_k=2)
        
        if results:
            logger.info(f"Found {len(results)} matches:")
            for i, result in enumerate(results):
                distance = result.get("distance", 0)
                text = result.get("text", "")
                logger.info(f"{i+1}. Distance: {distance:.4f}")
                logger.info(f"   {text[:100]}...")
        else:
            logger.info("No matches found.")

def test_context_retrieval():
    """Test context retrieval for prompts."""
    logger.info("\nTesting context retrieval...")
    
    # Test query for context
    query = "How do I install Python packages?"
    logger.info(f"Getting context for query: \"{query}\"")
    
    context = memory_manager.get_context_for_query(query)
    logger.info(f"Retrieved context:\n{context}")

def main():
    """Main test function."""
    logger.info("Starting memory system tests")
    
    # Test adding conversations
    test_add_conversations()
    
    # Test vector search
    test_vector_search()
    
    # Test context retrieval
    test_context_retrieval()
    
    logger.info("All tests completed")

if __name__ == "__main__":
    main() 