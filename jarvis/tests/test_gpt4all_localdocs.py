#!/usr/bin/env python3
"""
Test script for GPT4All LocalDocs integration.

This script tests the document processing capabilities using
GPT4All's LocalDocs feature, verifying the document indexing,
search, and retrieval functions.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to the path so we can import from jarvis
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

# Import the document processor
from jarvis.docs_processor.document_processor import DocumentProcessor
from jarvis.docs_processor.document_service import DocumentService

# Create instance of document processor
document_processor = DocumentProcessor()

def test_add_document(document_path):
    """Test adding a document to the LocalDocs repository."""
    logger.info(f"Testing document addition: {document_path}")
    
    # Extract document type from path
    doc_type = os.path.splitext(document_path)[1].lower().replace('.', '')
    if not doc_type:
        doc_type = 'txt'
    
    # Add document
    doc_id = document_processor.add_document(
        document_path=document_path,
        document_type=doc_type,
        metadata={"source": "test", "description": "Test document"}
    )
    
    if doc_id:
        logger.info(f"Document added successfully with ID: {doc_id}")
        return doc_id
    else:
        logger.error("Failed to add document")
        return None

def test_search_documents(query, limit=3):
    """Test searching documents with GPT4All LocalDocs."""
    logger.info(f"Testing document search with query: '{query}'")
    
    # Search documents
    results = document_processor.search_documents(query, limit)
    
    if results:
        logger.info(f"Found {len(results)} documents:")
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.get('document_id')} - Score: {result.get('score')}")
            
            # Get content snippet
            doc_id = result.get('document_id')
            content = document_processor.get_document_content(doc_id)
            if content:
                snippet = content[:100] + "..." if len(content) > 100 else content
                logger.info(f"     Snippet: {snippet}")
    else:
        logger.warning("No documents found")
    
    return results

def test_document_context(query, max_results=2):
    """Test generating document context for a query."""
    logger.info(f"Testing document context generation for query: '{query}'")
    
    # Create document service to test context generation
    doc_service = DocumentService()
    doc_service.start()
    
    try:
        # Get context
        context = doc_service.get_document_context(query, max_results)
        
        if context:
            logger.info(f"Generated context ({len(context)} characters):")
            logger.info("------- Context Start -------")
            logger.info(context)
            logger.info("------- Context End -------")
        else:
            logger.warning("No context generated")
        
        return context
    finally:
        # Stop the document service but without stopping the underlying processor
        # This is a hack for testing purposes - we need to add a proper method to stop without affecting the processor
        doc_service.active = False
        logger.info("Document service stopped (without stopping the processor)")

def test_remove_document(doc_id):
    """Test removing a document from the LocalDocs repository."""
    logger.info(f"Testing document removal: {doc_id}")
    
    # Remove document
    result = document_processor.remove_document(doc_id)
    
    if result:
        logger.info(f"Document {doc_id} removed successfully")
    else:
        logger.error(f"Failed to remove document {doc_id}")
    
    return result

def main():
    """Run GPT4All LocalDocs tests."""
    parser = argparse.ArgumentParser(description='Test GPT4All LocalDocs integration')
    parser.add_argument('--document', help='Path to a test document', default='test_docs/sample_document.txt')
    parser.add_argument('--query', help='Test search query', default='voice assistants capabilities')
    args = parser.parse_args()
    
    # Start document processor
    logger.info("Starting document processor...")
    document_processor.start()
    
    # Run tests
    try:
        # Add document
        doc_id = test_add_document(args.document)
        
        if doc_id:
            # Search documents
            test_search_documents(args.query)
            
            # Get document context
            test_document_context(args.query)
            
            # Remove document (do this before stopping the processor)
            test_remove_document(doc_id)
    except Exception as e:
        logger.error(f"Error during test: {e}")
    finally:
        # Stop document processor
        logger.info("Stopping document processor...")
        document_processor.stop()

if __name__ == "__main__":
    main() 