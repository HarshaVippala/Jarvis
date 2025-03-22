#!/usr/bin/env python3
"""
Main entry point for Jarvis with all patches applied.

This script ensures that:
1. The OpenAI patch is applied before any imports
2. Environment variables are set correctly
3. Proper error handling is in place
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("jarvis_run.log")
    ]
)
logger = logging.getLogger("jarvis_runner")

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for Jarvis with all patches applied."""
    # Step 1: Apply OpenAI patch before any imports
    logger.info("Applying OpenAI patch...")
    try:
        from patch_openai import patch_openai
        success = patch_openai()
        os.environ["OPENAI_PATCH_APPLIED"] = "1"
        logger.info(f"OpenAI patch applied: {success}")
    except Exception as e:
        logger.error(f"Failed to apply OpenAI patch: {e}")
        print(f"WARNING: OpenAI patch failed: {e}")
        # Continue anyway - the app may still work with local models

    # Step 2: Load environment variables
    logger.info("Loading environment variables...")
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent / 'jarvis' / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            logger.info(f"Loaded .env file from {env_path}")
            if 'OPENAI_API_KEY' in os.environ:
                logger.info("OPENAI_API_KEY is now set from .env file")
    except Exception as e:
        logger.error(f"Error loading environment variables: {e}")
        print(f"WARNING: Failed to load environment variables: {e}")

    # Step 3: Check OpenAI availability and set environment variable
    logger.info("Checking OpenAI availability...")
    try:
        # Clean any previous imports
        if 'openai' in sys.modules:
            sys.modules.pop('openai', None)
            logger.info("Cleaned existing OpenAI module")
        
        # Try to import and initialize
        from openai import OpenAI
        client = OpenAI()
        os.environ["JARVIS_OPENAI_AVAILABLE"] = "1"
        logger.info("OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        os.environ["JARVIS_OPENAI_AVAILABLE"] = "0"
        print(f"WARNING: OpenAI client initialization failed: {e}")
        print("Jarvis will continue with local models only.")

    # Step 4: Launch the main application
    logger.info("Starting Jarvis main application...")
    try:
        # We import this late to ensure all patches are applied first
        from minimal_desktop import main as desktop_main
        return desktop_main()
    except Exception as e:
        logger.error(f"Fatal error starting Jarvis: {e}")
        print(f"ERROR: Failed to start Jarvis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 