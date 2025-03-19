"""
Application context awareness module for Jarvis on macOS.

This module provides functionality to detect the currently active application,
window title, and other application-specific context on macOS.
"""

import logging
import time
import subprocess
from typing import Dict, Optional, Any, List, Tuple

logger = logging.getLogger(__name__)

class AppContextService:
    """Service for detecting application context on macOS."""
    
    def __init__(self):
        """Initialize the application context service."""
        self.active = False
        self.update_interval = 1.0  # seconds
        self.last_update_time = 0
        
        # Internal state
        self._current_app = ""
        self._current_window_title = ""
        self._current_app_bundle_id = ""
        self._is_macos = self._check_macos()
        
        logger.info("Application Context Service initialized")
    
    def _check_macos(self) -> bool:
        """Check if the system is macOS.
        
        Returns:
            bool: True if the system is macOS, False otherwise
        """
        try:
            result = subprocess.run(
                ["uname"], 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip() == "Darwin"
        except Exception:
            return False
    
    def start(self) -> bool:
        """Start the application context service.
        
        Returns:
            bool: True if successfully started, False otherwise
        """
        if self.active:
            logger.info("Application Context Service already running")
            return True
        
        if not self._is_macos:
            logger.error("Application Context Service requires macOS")
            return False
        
        logger.info("Starting Application Context Service")
        self.active = True
        
        # Initial update
        self.update_context()
        
        return True
    
    def stop(self) -> None:
        """Stop the application context service."""
        if not self.active:
            return
        
        logger.info("Stopping Application Context Service")
        self.active = False
    
    def update_context(self) -> bool:
        """Update the current application context.
        
        Returns:
            bool: True if update was successful, False otherwise
        """
        # Only update if enough time has passed
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return True
        
        if not self.active or not self._is_macos:
            return False
        
        try:
            # Get frontmost application using AppleScript
            app_script = """
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                set frontAppId to bundle identifier of first application process whose frontmost is true
                
                set windowTitle to ""
                try
                    tell process frontApp
                        if exists (1st window whose value of attribute "AXMain" is true) then
                            set windowTitle to name of 1st window whose value of attribute "AXMain" is true
                        end if
                    end tell
                end try
                
                return {frontApp, windowTitle, frontAppId}
            end tell
            """
            
            result = subprocess.run(
                ["osascript", "-e", app_script], 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # Parse the output (comma-separated list)
            output = result.stdout.strip()
            parts = output.split(", ")
            
            if len(parts) >= 3:
                self._current_app = parts[0]
                self._current_window_title = parts[1] if len(parts) > 1 else ""
                self._current_app_bundle_id = parts[2] if len(parts) > 2 else ""
                
                logger.debug(f"Active app: {self._current_app}, Window: {self._current_window_title}")
                self.last_update_time = current_time
                return True
            else:
                logger.warning(f"Unexpected output format: {output}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating application context: {str(e)}")
            return False
    
    def get_current_app(self) -> str:
        """Get the name of the currently active application.
        
        Returns:
            str: Name of the current application or empty string if unknown
        """
        if self.active:
            self.update_context()
        return self._current_app
    
    def get_current_window_title(self) -> str:
        """Get the title of the currently active window.
        
        Returns:
            str: Title of the current window or empty string if unknown
        """
        if self.active:
            self.update_context()
        return self._current_window_title
    
    def get_current_app_bundle_id(self) -> str:
        """Get the bundle ID of the currently active application.
        
        Returns:
            str: Bundle ID of the current application or empty string if unknown
        """
        if self.active:
            self.update_context()
        return self._current_app_bundle_id
    
    def get_app_context(self) -> Dict[str, str]:
        """Get the full application context.
        
        Returns:
            dict: Dictionary with current application context
        """
        if self.active:
            self.update_context()
            
        return {
            "app_name": self._current_app,
            "window_title": self._current_window_title,
            "bundle_id": self._current_app_bundle_id
        }
    
    def set_update_interval(self, seconds: float) -> None:
        """Set the interval for context updates.
        
        Args:
            seconds: The interval in seconds
        """
        self.update_interval = max(0.5, float(seconds))
        logger.info(f"Application context update interval set to {self.update_interval} seconds")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the service state.
        
        Returns:
            dict: Information about the service
        """
        return {
            "active": self.active,
            "is_macos": self._is_macos,
            "update_interval": self.update_interval,
            "current_app": self._current_app,
            "current_window": self._current_window_title
        }


# Create a singleton instance
app_context_service = AppContextService() 