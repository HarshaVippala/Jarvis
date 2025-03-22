#!/usr/bin/env python3
"""
Test script for the document processor.

This script demonstrates the document processing capabilities of Jarvis.
"""
import os
import sys
import logging
import tempfile
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the document processor test."""
    print("Jarvis Document Processor Test")
    print("==============================")
    
    # Import document processor
    from jarvis.docs_processor.document_service import document_service
    
    # Start the document service
    print("\nStarting document service...")
    if not document_service.start():
        print("Failed to start document service")
        return
    
    # Create a test document
    with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False) as f:
        test_file = Path(f.name)
        f.write("""
# Jarvis AI Assistant

Jarvis is an advanced AI assistant designed to help users with various tasks.

## Key Features

- Natural language understanding
- Document processing capabilities
- Voice interaction
- Context awareness
- Tool integration

## Technical Details

Jarvis uses a service-oriented architecture with a central application controller.
It leverages various AI models including GPT-4, Whisper, and FAISS for vector storage.

The document processing system enables semantic search across various document types
and provides relevant context for AI responses.
""")
    
    try:
        # Add the document
        print(f"\nAdding test document: {test_file}")
        document_id = document_service.add_document(
            document_path=test_file,
            document_type='txt',
            metadata={'name': 'Jarvis Overview'}
        )
        
        if not document_id:
            print("Failed to add document")
            return
        
        print(f"Document added successfully with ID: {document_id}")
        
        # Search for documents
        print("\nTesting document search...")
        
        search_queries = [
            "architecture",
            "AI models",
            "document processing",
            "context awareness"
        ]
        
        for query in search_queries:
            print(f"\nSearching for: '{query}'")
            results = document_service.search_documents(query, limit=3)
            
            if results:
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results):
                    doc_id = result.get('document_id')
                    score = result.get('score', 0)
                    metadata = result.get('metadata', {})
                    doc_name = metadata.get('name', 'Unnamed')
                    
                    print(f"  {i+1}. {doc_name} (ID: {doc_id[:8]}..., Score: {score:.2f})")
            else:
                print("No results found")
        
        # Get document content
        print("\nRetrieving document content...")
        content = document_service.get_document_content(document_id)
        
        if content:
            print("Document content summary:")
            print(f"  Length: {len(content)} characters")
            print(f"  First 100 chars: {content[:100].strip()}...")
        else:
            print("Failed to retrieve document content")
        
        # Get document context
        print("\nTesting context retrieval...")
        query = "What AI models does Jarvis use?"
        print(f"Query: '{query}'")
        
        context = document_service.get_document_context(query)
        if context:
            print("Context retrieved:")
            print("-" * 40)
            print(context)
            print("-" * 40)
        else:
            print("No context found")
        
        # Test document removal
        print("\nRemoving test document...")
        if document_service.remove_document(document_id):
            print("Document removed successfully")
        else:
            print("Failed to remove document")
        
    finally:
        # Clean up
        try:
            if test_file.exists():
                os.unlink(test_file)
        except Exception as e:
            print(f"Error cleaning up test file: {e}")
        
        # Stop document service
        print("\nStopping document service...")
        document_service.stop()
    
    print("\nTest completed")

if __name__ == "__main__":
    main() 