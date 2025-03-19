"""
Context Manager for Jarvis.

This module provides a centralized service for managing contextual awareness,
including screen content, application state, and environmental context.
"""

import logging
import time
from typing import Dict, List, Optional, Any

from jarvis.context.screen_capture import screen_capture_service
from jarvis.context.ocr_processor import ocr_processor
from jarvis.context.app_context import app_context_service

logger = logging.getLogger(__name__)

class ContextManager:
    """Central service for managing contextual awareness in Jarvis."""
    
    def __init__(self):
        """Initialize the context manager service."""
        self.active = False
        self.screen_observation_active = False
        self.app_context_active = False
        self.max_context_length = 4000  # Maximum characters for context
        self.last_context_update = 0
        self.context_update_interval = 5.0  # seconds
        
        # Internal state
        self._current_screen_text = ""
        self._current_application = ""
        self._current_window_title = ""
        self._current_app_bundle_id = ""
        
        logger.info("Context Manager initialized")
    
    def start(self) -> bool:
        """Start the context manager service.
        
        Returns:
            bool: True if successfully started, False otherwise
        """
        if self.active:
            logger.info("Context Manager already running")
            return True
        
        logger.info("Starting Context Manager")
        self.active = True
        return True
    
    def stop(self) -> None:
        """Stop the context manager service."""
        if not self.active:
            return
        
        logger.info("Stopping Context Manager")
        
        # Stop screen observation if active
        self.stop_screen_observation()
        
        # Stop app context if active
        self.stop_app_context()
        
        self.active = False
    
    def start_screen_observation(self) -> bool:
        """Start observing the screen content.
        
        Returns:
            bool: True if successfully started, False otherwise
        """
        if not self.active:
            logger.error("Cannot start screen observation: Context Manager not active")
            return False
        
        if self.screen_observation_active:
            logger.info("Screen observation already active")
            return True
        
        logger.info("Starting screen observation")
        
        # Start the screen capture service
        success = screen_capture_service.start()
        if not success:
            logger.error("Failed to start screen capture service")
            return False
        
        self.screen_observation_active = True
        logger.info("Screen observation started")
        return True
    
    def stop_screen_observation(self) -> None:
        """Stop observing the screen content."""
        if not self.screen_observation_active:
            return
        
        logger.info("Stopping screen observation")
        
        # Stop the screen capture service
        screen_capture_service.stop()
        
        self.screen_observation_active = False
        logger.info("Screen observation stopped")

    def start_app_context(self) -> bool:
        """Start monitoring application context.
        
        Returns:
            bool: True if successfully started, False otherwise
        """
        if not self.active:
            logger.error("Cannot start app context: Context Manager not active")
            return False
        
        if self.app_context_active:
            logger.info("App context monitoring already active")
            return True
        
        logger.info("Starting app context monitoring")
        
        # Start the app context service
        success = app_context_service.start()
        if not success:
            logger.error("Failed to start app context service")
            return False
        
        self.app_context_active = True
        logger.info("App context monitoring started")
        return True
    
    def stop_app_context(self) -> None:
        """Stop monitoring application context."""
        if not self.app_context_active:
            return
        
        logger.info("Stopping app context monitoring")
        
        # Stop the app context service
        app_context_service.stop()
        
        self.app_context_active = False
        logger.info("App context monitoring stopped")
    
    def get_screen_context(self) -> str:
        """Get the current screen content as text.
        
        Returns:
            str: Extracted text from the screen or empty string if not available
        """
        if not self.screen_observation_active:
            return ""
        
        # Get the latest text from the screen capture service
        text = screen_capture_service.get_screen_text()
        
        # Truncate if necessary
        if len(text) > self.max_context_length:
            text = text[:self.max_context_length] + "..."
        
        return text
    
    def get_app_context(self) -> Dict[str, str]:
        """Get the current application context.
        
        Returns:
            dict: Information about the current application or empty dict if not available
        """
        if not self.app_context_active:
            return {}
        
        # Get the latest app context
        return app_context_service.get_app_context()
    
    def update_context(self) -> None:
        """Update the internal context state."""
        # Only update if enough time has passed since last update
        current_time = time.time()
        if current_time - self.last_context_update < self.context_update_interval:
            return
        
        if self.screen_observation_active:
            self._current_screen_text = screen_capture_service.get_screen_text()
        
        if self.app_context_active:
            app_context = app_context_service.get_app_context()
            self._current_application = app_context.get("app_name", "")
            self._current_window_title = app_context.get("window_title", "")
            self._current_app_bundle_id = app_context.get("bundle_id", "")
        
        self.last_context_update = current_time
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context.
        
        Returns:
            dict: Summary of available context
        """
        # Update the context first
        self.update_context()
        
        return {
            "active": self.active,
            "screen_observation": {
                "active": self.screen_observation_active,
                "text_available": bool(self._current_screen_text),
                "text_length": len(self._current_screen_text) if self._current_screen_text else 0
            },
            "app_context": {
                "active": self.app_context_active,
                "current_application": self._current_application,
                "current_window": self._current_window_title
            },
            "last_update": self.last_context_update
        }
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get the full context data.
        
        Returns:
            dict: Complete context data including screen text and app context
        """
        # Update the context first
        self.update_context()
        
        return {
            "screen_text": self._current_screen_text,
            "application": {
                "name": self._current_application,
                "window_title": self._current_window_title,
                "bundle_id": self._current_app_bundle_id
            },
            "timestamp": self.last_context_update
        }
    
    def set_context_update_interval(self, seconds: float) -> None:
        """Set the interval for context updates.
        
        Args:
            seconds: The interval in seconds
        """
        self.context_update_interval = max(1.0, float(seconds))
        logger.info(f"Context update interval set to {self.context_update_interval} seconds")


# Create a singleton instance
context_manager = ContextManager()