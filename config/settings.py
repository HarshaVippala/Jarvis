"""
Configuration settings for the Jarvis assistant.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = Path(__file__).parents[1] / '.env'
load_dotenv(dotenv_path=dotenv_path)

# OpenAI API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4"
OPENAI_MAX_TOKENS = 1000
OPENAI_TEMPERATURE = 0.7

# Assistant settings
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Jarvis")
ASSISTANT_VOICE = os.getenv("ASSISTANT_VOICE", "male")
ASSISTANT_WAKE_WORD = os.getenv("ASSISTANT_WAKE_WORD", "jarvis").lower()

# Speech settings
STT_ENABLED = True
TTS_ENABLED = True
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = "your_voice_id_here"  # Replace with actual voice ID

# Memory settings
MEMORY_ENABLED = True
MEMORY_MAX_ENTRIES = 50
MEMORY_STORAGE_PATH = Path(__file__).parents[1] / "memory" / "storage.json"

# Vector Memory settings
VECTOR_MEMORY_ENABLED = True
VECTOR_MODEL_NAME = "all-MiniLM-L6-v2"  # Small, fast model for embeddings
VECTOR_MAX_RESULTS = 5

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = Path(__file__).parents[1] / "logs" / "jarvis.log"

# Command permissions - determine which commands require confirmation
SAFE_COMMANDS = {
    "open_browser": False,  # No confirmation needed
    "create_text_file": True,  # Confirmation required
    "delete_file": True,
    "read_file": False,
    "search_web": False,
    "take_screenshot": False,
    "open_folder": False,  # No confirmation needed
}

# Create necessary directories
def create_directories():
    """Create necessary directories for the assistant."""
    dirs = [
        Path(__file__).parents[1] / "logs",
        Path(__file__).parents[1] / "memory",
        Path(__file__).parents[1] / "data",
        Path(__file__).parents[1] / "memory" / "vector_store",
    ]
    for dir_path in dirs:
        dir_path.mkdir(exist_ok=True)

# Call this function when the module is imported
create_directories()
