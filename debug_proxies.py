#!/usr/bin/env python3
"""
Debug script to identify the source of the 'proxies' parameter error.
This script has been updated to DISABLE all monkeypatching that might affect OpenAI.
"""
import os
import sys
import logging
import importlib
import inspect
import traceback
from pathlib import Path

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug")

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# IMPORTANT: Set OpenAI API key via environment variable to avoid proxies issue
if 'OPENAI_API_KEY' in os.environ:
    logger.info("OPENAI_API_KEY is set in environment")
else:
    logger.info("OPENAI_API_KEY is NOT set in environment")
    # Try to get it from .env file
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent / 'jarvis' / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            logger.info(f"Loaded .env file from {env_path}")
            if 'OPENAI_API_KEY' in os.environ:
                logger.info("OPENAI_API_KEY is now set from .env file")
            else:
                logger.info("OPENAI_API_KEY still not set after loading .env")
    except Exception as e:
        logger.error(f"Error loading .env file: {e}")

def check_module(module_name):
    """Try to import a module and check its version if available."""
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "unknown")
        logger.info(f"Successfully imported {module_name} (version: {version})")
        return module
    except ImportError as e:
        logger.error(f"Failed to import {module_name}: {e}")
        return None

# Check important packages
check_module('openai')
check_module('huggingface_hub')
check_module('requests')
check_module('transformers')
check_module('sentence_transformers')
check_module('langchain')

# Test direct OpenAI client initialization
try:
    logger.info("Testing direct OpenAI client initialization...")
    from openai import OpenAI
    client = OpenAI()
    logger.info("OpenAI client initialized successfully without parameters")
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")

# IMPORTANT: Disable any monkeypatching for OpenAI
sys.modules.pop('openai', None)  # Remove module to ensure clean import
logger.info("Removed 'openai' from sys.modules for clean import")

try:
    # Re-import after cleanup
    import openai
    logger.info(f"Reimported openai module: {openai.__version__}")
except Exception as e:
    logger.error(f"Failed to reimport openai: {e}")

# Now try to initialize core Jarvis components one by one to find the issue
try:
    # Import core modules but don't run anything
    from jarvis.config.settings_manager import settings_manager
    logger.info("Imported settings_manager")
    
    from jarvis.brain.model_manager import model_manager
    logger.info("Imported model_manager")
    
    # Let's examine the vector_store module more carefully
    logger.info("Importing vector_store...")
    from jarvis.memory import vector_store
    logger.info(f"Available attributes in vector_store: {dir(vector_store)}")
    
    # Create an instance of VectorStore class
    logger.info("Creating VectorStore instance...")
    vector_store_instance = vector_store.VectorStore()
    logger.info("Vector store initialized successfully")
    
except Exception as e:
    logger.error(f"Error encountered: {str(e)}")
    traceback.print_exc()
    
    # Examine modules that might use 'proxies'
    logger.info("\nSearching for classes that might be using 'proxies' parameter...")
    
    # Check specific modules that are likely to have proxy settings
    modules_to_check = [
        'huggingface_hub',
        'requests',
        'transformers',
        'sentence_transformers'
    ]
    
    for module_name in modules_to_check:
        try:
            module = sys.modules.get(module_name)
            if not module:
                logger.info(f"Module {module_name} not loaded")
                continue
                
            logger.info(f"Checking module {module_name}...")
            
            # Look for classes with proxies parameter
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    try:
                        init_method = getattr(obj, '__init__', None)
                        if init_method and inspect.isfunction(init_method):
                            sig = inspect.signature(init_method)
                            if 'proxies' in sig.parameters:
                                logger.info(f"Class {module_name}.{name} accepts 'proxies' parameter")
                    except Exception as e:
                        logger.debug(f"Could not inspect {name}: {e}")
        except Exception as e:
            logger.error(f"Error examining module {module_name}: {e}")
    
    # Let's look at the actual code from vector_store class
    try:
        logger.info("\nExamining vector_store code...")
        from jarvis.memory import vector_store
        source_code = inspect.getsource(vector_store.VectorStore.__init__)
        logger.info(f"VectorStore.__init__ source code:\n{source_code}")
    except Exception as e:
        logger.error(f"Could not get source code: {e}") 

logger.info("Debug script completed.") 