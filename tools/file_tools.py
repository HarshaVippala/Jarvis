"""
File tools for Jarvis.

This module provides tools for interacting with the file system,
such as reading, writing, and manipulating files and directories.
"""

import os
import sys
import logging
import shutil
import json
import yaml
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from jarvis.brain.langchain_service import langchain_service
from jarvis.config import settings

# Configure logging
logger = logging.getLogger(__name__)

def list_directory(directory: str = ".") -> Dict[str, Any]:
    """List contents of a directory.
    
    Args:
        directory: Path to the directory to list (default: current directory)
        
    Returns:
        dict: Directory contents
    """
    try:
        # Normalize path
        directory = os.path.expanduser(directory)
        directory = os.path.abspath(directory)
        
        # Check if path exists and is a directory
        if not os.path.exists(directory):
            return {
                "status": "error",
                "message": f"Directory '{directory}' does not exist"
            }
        
        if not os.path.isdir(directory):
            return {
                "status": "error",
                "message": f"Path '{directory}' is not a directory"
            }
        
        # Get directory contents
        contents = {
            "directories": [],
            "files": [],
            "symlinks": []
        }
        
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            # Get item stats
            stats = os.stat(item_path)
            item_info = {
                "name": item,
                "path": item_path,
                "size": stats.st_size,
                "modified": stats.st_mtime
            }
            
            # Categorize items
            if os.path.islink(item_path):
                item_info["target"] = os.readlink(item_path)
                contents["symlinks"].append(item_info)
            elif os.path.isdir(item_path):
                contents["directories"].append(item_info)
            elif os.path.isfile(item_path):
                contents["files"].append(item_info)
        
        return {
            "status": "success",
            "message": f"Listed contents of '{directory}'",
            "data": {
                "path": directory,
                "contents": contents,
                "file_count": len(contents["files"]),
                "directory_count": len(contents["directories"]),
                "symlink_count": len(contents["symlinks"])
            }
        }
    
    except Exception as e:
        logger.error(f"Error listing directory '{directory}': {str(e)}")
        return {
            "status": "error",
            "message": f"Error listing directory: {str(e)}"
        }

def read_file(file_path: str, max_size: int = 100 * 1024) -> Dict[str, Any]:
    """Read contents of a file.
    
    Args:
        file_path: Path to the file to read
        max_size: Maximum file size to read in bytes (default: 100 KB)
        
    Returns:
        dict: File contents
    """
    try:
        # Normalize path
        file_path = os.path.expanduser(file_path)
        file_path = os.path.abspath(file_path)
        
        # Check if path exists and is a file
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"File '{file_path}' does not exist"
            }
        
        if not os.path.isfile(file_path):
            return {
                "status": "error",
                "message": f"Path '{file_path}' is not a file"
            }
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            return {
                "status": "error",
                "message": f"File size ({file_size} bytes) exceeds maximum allowed size ({max_size} bytes)"
            }
        
        # Determine file type based on extension
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Read file based on type
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico']:
            return {
                "status": "error",
                "message": f"Cannot read binary/image files"
            }
        else:
            # Read as text
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return {
                    "status": "success",
                    "message": f"Read file '{file_path}'",
                    "data": {
                        "path": file_path,
                        "size": file_size,
                        "content": content
                    }
                }
            except UnicodeDecodeError:
                return {
                    "status": "error",
                    "message": f"File '{file_path}' is not a text file or contains invalid Unicode characters"
                }
    
    except Exception as e:
        logger.error(f"Error reading file '{file_path}': {str(e)}")
        return {
            "status": "error",
            "message": f"Error reading file: {str(e)}"
        }

def write_file(file_path: str, content: str, append: bool = False) -> Dict[str, Any]:
    """Write content to a file.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        append: If True, append to existing file; otherwise overwrite (default: False)
        
    Returns:
        dict: Result of the write operation
    """
    try:
        # Normalize path
        file_path = os.path.expanduser(file_path)
        file_path = os.path.abspath(file_path)
        
        # Check if path is safe (not in system directories)
        unsafe_prefixes = [
            "/bin", "/sbin", "/usr/bin", "/usr/sbin", 
            "/etc", "/var", "/System", "/private"
        ]
        
        if any(file_path.startswith(prefix) for prefix in unsafe_prefixes):
            return {
                "status": "error",
                "message": f"Cannot write to system directory '{file_path}'"
            }
        
        # Make sure directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        # Write to file
        mode = 'a' if append else 'w'
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)
        
        return {
            "status": "success",
            "message": f"{'Appended to' if append else 'Wrote'} file '{file_path}'",
            "data": {
                "path": file_path,
                "size": len(content),
                "mode": mode
            }
        }
    
    except Exception as e:
        logger.error(f"Error writing to file '{file_path}': {str(e)}")
        return {
            "status": "error",
            "message": f"Error writing to file: {str(e)}"
        }

def search_file(directory: str, pattern: str, recursive: bool = True) -> Dict[str, Any]:
    """Search for files matching a pattern.
    
    Args:
        directory: Directory to search in
        pattern: Pattern to search for (glob pattern)
        recursive: If True, search recursively (default: True)
        
    Returns:
        dict: List of matching files
    """
    try:
        # Normalize path
        directory = os.path.expanduser(directory)
        directory = os.path.abspath(directory)
        
        # Check if directory exists
        if not os.path.exists(directory):
            return {
                "status": "error",
                "message": f"Directory '{directory}' does not exist"
            }
        
        if not os.path.isdir(directory):
            return {
                "status": "error",
                "message": f"Path '{directory}' is not a directory"
            }
        
        # Search for files
        matches = []
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if pattern.lower() in file.lower():
                        file_path = os.path.join(root, file)
                        matches.append({
                            "name": file,
                            "path": file_path,
                            "size": os.path.getsize(file_path),
                            "modified": os.path.getmtime(file_path)
                        })
        else:
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path) and pattern.lower() in file.lower():
                    matches.append({
                        "name": file,
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "modified": os.path.getmtime(file_path)
                    })
        
        # Sort by name
        matches.sort(key=lambda x: x["name"])
        
        return {
            "status": "success",
            "message": f"Found {len(matches)} matches for '{pattern}' in '{directory}'",
            "data": matches
        }
    
    except Exception as e:
        logger.error(f"Error searching for files: {str(e)}")
        return {
            "status": "error",
            "message": f"Error searching for files: {str(e)}"
        }

def create_directory(directory: str) -> Dict[str, Any]:
    """Create a directory.
    
    Args:
        directory: Path to the directory to create
        
    Returns:
        dict: Result of the operation
    """
    try:
        # Normalize path
        directory = os.path.expanduser(directory)
        directory = os.path.abspath(directory)
        
        # Check if already exists
        if os.path.exists(directory):
            if os.path.isdir(directory):
                return {
                    "status": "info",
                    "message": f"Directory '{directory}' already exists"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Path '{directory}' exists but is not a directory"
                }
        
        # Create directory
        os.makedirs(directory)
        
        return {
            "status": "success",
            "message": f"Created directory '{directory}'"
        }
    
    except Exception as e:
        logger.error(f"Error creating directory '{directory}': {str(e)}")
        return {
            "status": "error",
            "message": f"Error creating directory: {str(e)}"
        }

def register_file_tools() -> bool:
    """Register all file tools with the LangChain service.
    
    Returns:
        bool: True if all tools were registered successfully
    """
    if not langchain_service.active:
        logger.error("Cannot register file tools: LangChain service not active")
        return False
    
    try:
        # Register each tool
        langchain_service.register_tool(
            name="list_directory",
            func=list_directory,
            description="List contents of a directory"
        )
        
        langchain_service.register_tool(
            name="read_file",
            func=read_file,
            description="Read contents of a text file (max 100 KB)"
        )
        
        langchain_service.register_tool(
            name="write_file",
            func=write_file,
            description="Write content to a file (with safety checks)"
        )
        
        langchain_service.register_tool(
            name="search_file",
            func=search_file,
            description="Search for files matching a pattern"
        )
        
        langchain_service.register_tool(
            name="create_directory",
            func=create_directory,
            description="Create a new directory"
        )
        
        logger.info("File tools registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error registering file tools: {str(e)}")
        return False 