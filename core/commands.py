"""
Command execution module for Jarvis.
This module handles system operations and command execution.
"""
import os
import sys
import subprocess
import webbrowser
import logging
from pathlib import Path
from typing import Dict, List, Union, Optional, Callable, Any
import platform

from jarvis.utils.config import config_manager
from jarvis.context.context_manager import context_manager

logger = logging.getLogger(__name__)

class CommandExecutor:
    """Execute system commands for the assistant."""
    
    def __init__(self):
        """Initialize the command executor."""
        self.os_type = platform.system()
        self.commands = {
            'open_browser': self.open_browser,
            'create_text_file': self.create_text_file,
            'read_file': self.read_file,
            'delete_file': self.delete_file,
            'list_directory': self.list_directory,
            'search_web': self.search_web,
            'take_screenshot': self.take_screenshot,
            'get_system_info': self.get_system_info,
            'open_folder': self.open_folder,
            'start_watching': self.start_watching,
            'stop_watching': self.stop_watching,
            'show_screen_context': self.show_screen_context,
            'start_app_monitoring': self.start_app_monitoring,
            'stop_app_monitoring': self.stop_app_monitoring,
            'show_app_context': self.show_app_context,
        }
    
    def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a command by name with the given arguments.
        
        Args:
            command_name: The name of the command to execute
            **kwargs: Arguments to pass to the command
            
        Returns:
            Dict with results and status
        """
        if command_name not in self.commands:
            logger.error(f"Unknown command: {command_name}")
            return {"success": False, "error": f"Unknown command: {command_name}"}
        
        # Check if command requires confirmation
        requires_confirmation = config_manager.get_command_permission(command_name)
        
        if requires_confirmation:
            # In a real implementation, we would ask for user confirmation here
            # For now, we'll just log it
            logger.info(f"Command {command_name} requires confirmation")
        
        try:
            result = self.commands[command_name](**kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Error executing command {command_name}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def open_browser(self, url: str = "https://www.google.com") -> str:
        """Open the default web browser with the given URL."""
        try:
            webbrowser.open(url)
            return f"Browser opened with URL: {url}"
        except Exception as e:
            logger.error(f"Failed to open browser: {str(e)}")
            raise
    
    def create_text_file(self, content: str, file_path: str) -> str:
        """Create a text file with the given content."""
        try:
            # Ensure the directory exists
            file_path = Path(file_path).expanduser().resolve()
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the content to the file
            with open(file_path, 'w') as f:
                f.write(content)
            
            return f"File created at: {file_path}"
        except Exception as e:
            logger.error(f"Failed to create file: {str(e)}")
            raise
    
    def read_file(self, file_path: str) -> str:
        """Read the contents of a file."""
        try:
            file_path = Path(file_path).expanduser().resolve()
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(file_path, 'r') as f:
                content = f.read()
            
            return content
        except Exception as e:
            logger.error(f"Failed to read file: {str(e)}")
            raise
    
    def delete_file(self, file_path: str) -> str:
        """Delete a file."""
        try:
            file_path = Path(file_path).expanduser().resolve()
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            file_path.unlink()
            return f"File deleted: {file_path}"
        except Exception as e:
            logger.error(f"Failed to delete file: {str(e)}")
            raise
    
    def list_directory(self, directory_path: str = ".") -> List[str]:
        """List the contents of a directory."""
        try:
            directory_path = Path(directory_path).expanduser().resolve()
            
            if not directory_path.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            if not directory_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {directory_path}")
            
            files = [str(f.name) for f in directory_path.iterdir()]
            return files
        except Exception as e:
            logger.error(f"Failed to list directory: {str(e)}")
            raise
    
    def search_web(self, query: str) -> str:
        """Search the web for the given query."""
        try:
            # Format the query for a URL
            from urllib.parse import quote_plus
            search_url = f"https://www.google.com/search?q={quote_plus(query)}"
            
            # Open the browser with the search query
            webbrowser.open(search_url)
            return f"Web search initiated for: {query}"
        except Exception as e:
            logger.error(f"Failed to search web: {str(e)}")
            raise
    
    def take_screenshot(self, output_path: Optional[str] = None) -> str:
        """Take a screenshot and save it to the given path."""
        try:
            from PIL import ImageGrab
            
            # Generate a filename if not provided
            if output_path is None:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = Path.home() / "Pictures" / f"screenshot_{timestamp}.png"
            else:
                output_path = Path(output_path).expanduser().resolve()
            
            # Ensure the directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Take the screenshot
            screenshot = ImageGrab.grab()
            screenshot.save(output_path)
            
            return f"Screenshot saved to: {output_path}"
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
            raise
    
    def get_system_info(self) -> Dict[str, str]:
        """Get basic system information."""
        try:
            import psutil
            
            # Get system information
            info = {
                "os": platform.system(),
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "python_version": sys.version,
                "cpu_usage": f"{psutil.cpu_percent()}%",
                "memory_usage": f"{psutil.virtual_memory().percent}%",
                "disk_usage": f"{psutil.disk_usage('/').percent}%",
            }
            
            return info
        except Exception as e:
            logger.error(f"Failed to get system info: {str(e)}")
            raise

    def open_folder(self, directory_path: str = "~/Downloads") -> str:
        """Open a folder in the system's file explorer."""
        try:
            folder_path = Path(directory_path).expanduser().resolve()
            
            if not folder_path.exists():
                raise FileNotFoundError(f"Folder not found: {folder_path}")
            
            if not folder_path.is_dir():
                raise NotADirectoryError(f"Not a directory: {folder_path}")
            
            # Open folder based on platform
            if self.os_type == "Darwin":  # macOS
                subprocess.run(["open", str(folder_path)])
            elif self.os_type == "Windows":
                subprocess.run(["explorer", str(folder_path)])
            elif self.os_type == "Linux":
                subprocess.run(["xdg-open", str(folder_path)])
            else:
                raise OSError(f"Unsupported operating system: {self.os_type}")
                
            return f"Opened folder: {folder_path}"
        except Exception as e:
            logger.error(f"Failed to open folder: {str(e)}")
            raise

    def start_watching(self) -> Dict[str, Any]:
        """Start observing the screen content."""
        if not context_manager.active:
            context_manager.start()
        
        success = context_manager.start_screen_observation()
        
        if success:
            return {
                "status": "success",
                "message": "Screen observation started. I can now see what's on your screen."
            }
        else:
            return {
                "status": "error",
                "message": "Failed to start screen observation. Please check that required dependencies are installed."
            }

    def stop_watching(self) -> Dict[str, Any]:
        """Stop observing the screen content."""
        if context_manager.screen_observation_active:
            context_manager.stop_screen_observation()
            return {
                "status": "success",
                "message": "Screen observation stopped. I'm no longer watching your screen."
            }
        else:
            return {
                "status": "info",
                "message": "Screen observation is already stopped."
            }

    def show_screen_context(self) -> Dict[str, Any]:
        """Show the current context from the screen."""
        if not context_manager.screen_observation_active:
            return {
                "status": "error",
                "message": "Screen observation is not active. Please start watching first with 'start_watching'."
            }
        
        screen_context = context_manager.get_screen_context()
        
        if not screen_context:
            return {
                "status": "info",
                "message": "No text content detected on the screen yet."
            }
        
        return {
            "status": "success",
            "message": f"Current screen context:\n\n{screen_context[:1500]}..." if len(screen_context) > 1500 else screen_context
        }

    def start_app_monitoring(self) -> Dict[str, Any]:
        """Start monitoring the currently active application."""
        if not context_manager.active:
            context_manager.start()
        
        success = context_manager.start_app_context()
        
        if success:
            return {
                "status": "success",
                "message": "Application monitoring started. I can now see which apps you're using."
            }
        else:
            return {
                "status": "error",
                "message": "Failed to start application monitoring. This feature requires macOS."
            }

    def stop_app_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring the currently active application."""
        if context_manager.app_context_active:
            context_manager.stop_app_context()
            return {
                "status": "success",
                "message": "Application monitoring stopped. I'm no longer tracking which apps you're using."
            }
        else:
            return {
                "status": "info",
                "message": "Application monitoring is already stopped."
            }

    def show_app_context(self) -> Dict[str, Any]:
        """Show the current application context."""
        if not context_manager.app_context_active:
            return {
                "status": "error",
                "message": "Application monitoring is not active. Please start monitoring first with 'start_app_monitoring'."
            }
        
        app_context = context_manager.get_app_context()
        
        if not app_context:
            return {
                "status": "info",
                "message": "No application context detected yet."
            }
        
        app_name = app_context.get("app_name", "Unknown")
        window_title = app_context.get("window_title", "No window")
        
        return {
            "status": "success",
            "message": f"Current application: {app_name}\nWindow title: {window_title}"
        }

# Create a singleton instance of the command executor
command_executor = CommandExecutor()
