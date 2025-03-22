#!/usr/bin/env python3
"""
Minimal starter script for Jarvis
"""
import os
import sys
import logging
import subprocess
from datetime import datetime

# Configure logging
log_dir = os.path.expanduser("~/.jarvis/logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"jarvis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("jarvis_starter")

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Install the correct version of huggingface_hub
try:
    import huggingface_hub
    logger.info(f"Installed huggingface_hub version: {huggingface_hub.__version__}")
    if huggingface_hub.__version__ != "0.16.4":
        logger.info("Reinstalling huggingface_hub to version 0.16.4...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub==0.16.4", "--force-reinstall"])
        logger.info("huggingface_hub reinstalled")
except Exception as e:
    logger.error(f"Error handling huggingface_hub: {str(e)}")

try:
    # Set environment variables
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    # Run Jarvis in interactive mode (CLI)
    from jarvis.main import interactive_mode
    logger.info("Starting Jarvis in interactive mode...")
    interactive_mode()
except Exception as e:
    logger.error(f"Failed to start Jarvis: {str(e)}")
    print(f"Error: {str(e)}")
    print("Check the logs for more details.") 