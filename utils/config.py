"""
Configuration utility for loading and validating settings.
"""
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from jarvis.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConfigManager:
    """Manager for configuration settings."""
    
    @staticmethod
    def validate_openai_key() -> bool:
        """Validate that the OpenAI API key is set."""
        if not settings.OPENAI_API_KEY:
            logger.error("OpenAI API key is not set in the environment variables.")
            return False
        return True
    
    @staticmethod
    def validate_elevenlabs_key() -> bool:
        """Validate that the ElevenLabs API key is set if TTS is enabled."""
        if settings.TTS_ENABLED and not settings.ELEVENLABS_API_KEY:
            logger.warning("ElevenLabs API key is not set, but TTS is enabled.")
            return False
        return True
    
    @staticmethod
    def get_command_permission(command_name: str) -> bool:
        """Get the permission setting for a command."""
        return settings.SAFE_COMMANDS.get(command_name, True)  # Default to requiring confirmation
    
    @staticmethod
    def validate_all() -> bool:
        """Validate all required configuration."""
        valid = True
        
        # Check OpenAI API key
        if not ConfigManager.validate_openai_key():
            valid = False
        
        # Check ElevenLabs API key if TTS is enabled
        if settings.TTS_ENABLED and not ConfigManager.validate_elevenlabs_key():
            valid = False
        
        return valid

# Create a singleton instance
config_manager = ConfigManager()
