#!/usr/bin/env python3
"""
Minimal desktop application for Jarvis.
This version uses a minimal set of dependencies and ensures proper OpenAI client initialization.
"""
import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("jarvis_debug.log")
    ]
)
logger = logging.getLogger("jarvis_starter")

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for the minimal desktop application."""
    # Apply OpenAI patch first if not already applied
    if not os.environ.get("OPENAI_PATCH_APPLIED"):
        try:
            from patch_openai import patch_openai
            patch_openai()
            os.environ["OPENAI_PATCH_APPLIED"] = "1"
            logger.info("Applied OpenAI patch")
        except ImportError:
            logger.warning("patch_openai.py not found, continuing without patching")
        except Exception as e:
            logger.error(f"Error applying OpenAI patch: {e}")
    
    # Set OpenAI API key via environment variable
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent / 'jarvis' / '.env'
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            logger.info(f"Loaded .env file from {env_path}")
            if 'OPENAI_API_KEY' in os.environ:
                logger.info("OPENAI_API_KEY is now set from .env file")
        
        # Set HAVE_OPENAI environment variable for language_model_service.py
        os.environ["JARVIS_OPENAI_AVAILABLE"] = "1"
        
        # Ensure we have a clean OpenAI module
        if 'openai' in sys.modules:
            sys.modules.pop('openai', None)
            logger.info("Removed existing 'openai' module")
        
        # Test OpenAI client initialization
        from openai import OpenAI
        client = OpenAI()
        logger.info("OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        # Even if OpenAI fails, we still want to set this to False so code doesn't crash
        os.environ["JARVIS_OPENAI_AVAILABLE"] = "0"
    
    # Import with the correct path
    try:
        from jarvis.desktop.main import main as desktop_main
        logger.info("Successfully imported Jarvis main module")
        
        # Start the application
        return desktop_main()
    except Exception as e:
        logger.error(f"Failed to start Jarvis: {str(e)}")
        print(f"Error: {str(e)}")
        print("Check the logs for more details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 