#!/usr/bin/env python3
"""
Patch for OpenAI client to fix common issues
"""
import logging
import os
import sys
import importlib.util
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("openai_patch")

def patch_openai() -> bool:
    """
    Apply patches to OpenAI to fix common issues
    
    Returns:
        bool: True if patch was successfully applied
    """
    logger.info("Checking if OpenAI is installed...")
    
    # Check if OpenAI is installed
    openai_spec = importlib.util.find_spec("openai")
    if not openai_spec:
        logger.warning("OpenAI is not installed, no patching needed.")
        return False
    
    # Import OpenAI
    try:
        import openai
        logger.info(f"Found OpenAI version: {openai.__version__}")
    except ImportError as e:
        logger.error(f"Failed to import OpenAI: {e}")
        return False
    
    # Set environment variables for OpenAI
    logger.info("Setting up OpenAI environment variables...")
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        # Try to load from .env file
        if os.path.exists("jarvis/.env"):
            logger.info("Loading API key from .env file...")
            try:
                with open("jarvis/.env", "r") as f:
                    for line in f:
                        if line.strip() and not line.startswith("#"):
                            key, value = line.strip().split("=", 1)
                            if key == "OPENAI_API_KEY":
                                os.environ["OPENAI_API_KEY"] = value
                                logger.info("API key loaded from .env file")
                                api_key = value
                                break
            except Exception as e:
                logger.error(f"Failed to load API key from .env file: {e}")
    
    # Check for API key again
    if not api_key:
        logger.warning("No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
        os.environ["OPENAI_API_KEY"] = "dummy-key-for-testing"
        logger.info("Set dummy key for testing")
    
    # Indicate that OpenAI is available in environment
    os.environ["JARVIS_OPENAI_AVAILABLE"] = "1"
    
    # Patch OpenAI client initialization to fix common issues
    logger.info("Patching OpenAI client initialization...")
    
    # Get the original client constructor
    try:
        original_init = openai.OpenAI.__init__
        
        # Define our patched constructor that handles the 'proxies' argument
        def patched_init(self, *args, **kwargs):
            # Remove 'proxies' argument if present (causes issues in some environments)
            if "proxies" in kwargs:
                logger.info("Removing 'proxies' argument from OpenAI client initialization")
                del kwargs["proxies"]
            
            # Call original constructor
            original_init(self, *args, **kwargs)
        
        # Apply the patch
        openai.OpenAI.__init__ = patched_init
        logger.info("Successfully patched OpenAI client initialization!")
        
        # Test that the patch works by creating a client
        try:
            client = openai.OpenAI()
            logger.info("Successfully created OpenAI client with patched initialization!")
        except Exception as e:
            logger.error(f"Failed to create OpenAI client with patched initialization: {e}")
            logger.warning("Patch application failed during testing")
            # Restore original method
            openai.OpenAI.__init__ = original_init
            return False
        
        return True
    
    except (AttributeError, Exception) as e:
        logger.error(f"Failed to patch OpenAI client: {e}")
        return False

if __name__ == "__main__":
    success = patch_openai()
    if success:
        logger.info("OpenAI patch applied successfully!")
        sys.exit(0)
    else:
        logger.error("Failed to apply OpenAI patch.")
        sys.exit(1) 