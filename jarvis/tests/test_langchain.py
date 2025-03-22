#!/usr/bin/env python3
"""
Test script for Jarvis LangChain integration and tools.

This script tests the LangChain service with various tools.
"""
import sys
import logging
import time
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

from langchain.llms import Ollama
from jarvis.brain.langchain_service import langchain_service
from jarvis.tools.system_tools import register_system_tools
from jarvis.tools.file_tools import register_file_tools
from jarvis.tools.web_tools import register_web_tools

def test_langchain_service():
    """Test basic LangChain service functionality."""
    logger.info("Testing LangChain service...")
    
    # Check if service is available
    if not langchain_service.available:
        logger.error("LangChain service not available. Install langchain and langchain-community packages.")
        return False
    
    # Start the service
    logger.info("Starting LangChain service")
    success = langchain_service.start()
    
    if not success:
        logger.error("Failed to start LangChain service")
        return False
    
    logger.info("LangChain service started successfully")
    
    # Get service info
    service_info = langchain_service.get_service_info()
    logger.info(f"Service info: {service_info}")
    
    return True

def test_ollama_integration():
    """Test Ollama integration with LangChain."""
    logger.info("\nTesting Ollama integration...")
    
    try:
        # Initialize Ollama LLM
        logger.info("Initializing Ollama LLM...")
        
        llm = Ollama(
            model="mistral",
            temperature=0.7,
            num_ctx=2048
        )
        
        # Set the language model for LangChain
        langchain_service.set_language_model(llm)
        
        # Test with a simple prompt
        logger.info("Testing simple prompt...")
        
        result = langchain_service.run_prompt_template(
            template="You are Jarvis, an AI assistant. Answer the following question in a concise way: {question}",
            variables={"question": "What is the capital of France?"}
        )
        
        logger.info(f"Result: {result}")
        
        return "success" in result["status"]
        
    except Exception as e:
        logger.error(f"Error testing Ollama integration: {str(e)}")
        return False

def test_tools():
    """Test tool registration and execution."""
    logger.info("\nTesting tool registration...")
    
    # Register system tools
    logger.info("Registering system tools...")
    system_success = register_system_tools()
    logger.info(f"System tools registration {'successful' if system_success else 'failed'}")
    
    # Register file tools
    logger.info("Registering file tools...")
    file_success = register_file_tools()
    logger.info(f"File tools registration {'successful' if file_success else 'failed'}")
    
    # Register web tools
    logger.info("Registering web tools...")
    web_success = register_web_tools()
    logger.info(f"Web tools registration {'successful' if web_success else 'failed'}")
    
    # Get registered tools
    tools = langchain_service.get_registered_tools()
    logger.info(f"Registered tools: {len(tools)}")
    for tool in tools:
        logger.info(f"  - {tool['name']}: {tool['description']}")
    
    return system_success or file_success or web_success

def test_agent():
    """Test the LangChain agent with tools."""
    logger.info("\nTesting agent with tools...")
    
    # Create agent
    langchain_service._create_agent()
    
    if not langchain_service.agent:
        logger.error("Failed to create agent")
        return False
    
    logger.info("Agent created successfully")
    
    # Test agent with query
    logger.info("Testing agent with query...")
    
    result = langchain_service.execute_with_tools(
        query="What is the current directory and system information?",
        context="The user wants to know about their system and the current directory."
    )
    
    logger.info(f"Agent result: {result}")
    
    return "success" in result["status"]

def main():
    """Main test function."""
    logger.info("Starting LangChain integration tests")
    
    # Test basic service
    if not test_langchain_service():
        logger.error("LangChain service test failed")
        return
    
    # Test tool registration
    if not test_tools():
        logger.warning("Tool registration partially failed")
    
    # Test Ollama integration
    if not test_ollama_integration():
        logger.error("Ollama integration test failed")
        return
    
    # Test agent
    if not test_agent():
        logger.error("Agent test failed")
        return
    
    logger.info("All tests completed")

if __name__ == "__main__":
    main() 