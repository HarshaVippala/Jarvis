"""
System tools for Jarvis.

This module provides tools for interacting with the operating system,
such as getting system information, running commands, and managing processes.
"""

import os
import sys
import logging
import platform
import subprocess
import shutil
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime

from jarvis.brain.langchain_service import langchain_service
from jarvis.config import settings

# Configure logging
logger = logging.getLogger(__name__)

def get_system_info() -> Dict[str, Any]:
    """Get system information.
    
    Returns:
        dict: System information including OS, Python version, etc.
    """
    try:
        info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "architecture": platform.architecture()[0]
        }
        
        # Add macOS-specific info if available
        if platform.system() == "Darwin":
            # Get macOS version using system_profiler
            try:
                result = subprocess.run(
                    ["system_profiler", "SPSoftwareDataType"], 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                for line in result.stdout.split("\n"):
                    if "System Version" in line:
                        info["macos_version"] = line.strip()
                        break
            except Exception:
                info["macos_version"] = "Unknown"
        
        # Get memory info
        memory = psutil.virtual_memory()
        info["memory_total"] = f"{memory.total / (1024 ** 3):.2f} GB"
        info["memory_available"] = f"{memory.available / (1024 ** 3):.2f} GB"
        info["memory_percent"] = f"{memory.percent}%"
        
        # Get CPU info
        info["cpu_cores"] = psutil.cpu_count(logical=False)
        info["cpu_threads"] = psutil.cpu_count(logical=True)
        info["cpu_usage"] = f"{psutil.cpu_percent(interval=1)}%"
        
        # Get disk info
        disk = psutil.disk_usage('/')
        info["disk_total"] = f"{disk.total / (1024 ** 3):.2f} GB"
        info["disk_free"] = f"{disk.free / (1024 ** 3):.2f} GB"
        info["disk_percent"] = f"{disk.percent}%"
        
        return {
            "status": "success",
            "message": "System information retrieved successfully",
            "data": info
        }
    
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {
            "status": "error",
            "message": f"Error getting system information: {str(e)}"
        }

def run_command(command: str, safe_mode: bool = True) -> Dict[str, Any]:
    """Run a shell command.
    
    Args:
        command: The command to run
        safe_mode: If True, only allow safe commands
        
    Returns:
        dict: Result of the command execution
    """
    # List of potentially dangerous commands
    dangerous_commands = [
        "rm", "sudo", "mkfs", "dd", "chmod", "chown",
        "passwd", "shutdown", "reboot", "halt",
        ">", ">>", "&&", "||", ";", "|"
    ]
    
    # Sanitize the command
    command = command.strip()
    
    # Check if the command is dangerous
    if safe_mode:
        for dangerous in dangerous_commands:
            if dangerous in command:
                return {
                    "status": "error",
                    "message": f"Potentially dangerous command '{dangerous}' detected. Command not executed for safety."
                }
    
    try:
        # Run the command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Check if command was successful
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Command executed successfully",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
        else:
            return {
                "status": "error",
                "message": f"Command returned non-zero exit code: {result.returncode}",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            }
    
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Command execution timed out after 10 seconds"
        }
    except Exception as e:
        logger.error(f"Error running command: {str(e)}")
        return {
            "status": "error",
            "message": f"Error executing command: {str(e)}"
        }

def get_environment_variables() -> Dict[str, Any]:
    """Get system environment variables.
    
    Returns:
        dict: Environment variables (excluding sensitive ones)
    """
    try:
        # Get all environment variables
        env_vars = dict(os.environ)
        
        # Remove sensitive variables
        sensitive_keys = ["API_KEY", "SECRET", "PASSWORD", "TOKEN", "CREDENTIAL", "KEY"]
        
        for key in list(env_vars.keys()):
            # Check if it's a sensitive variable
            if any(sensitive in key.upper() for sensitive in sensitive_keys):
                env_vars[key] = "******"  # Mask sensitive values
        
        return {
            "status": "success",
            "message": "Environment variables retrieved successfully",
            "data": env_vars
        }
    
    except Exception as e:
        logger.error(f"Error getting environment variables: {str(e)}")
        return {
            "status": "error",
            "message": f"Error retrieving environment variables: {str(e)}"
        }

def get_current_directory() -> Dict[str, Any]:
    """Get the current working directory.
    
    Returns:
        dict: Current directory information
    """
    try:
        cwd = os.getcwd()
        return {
            "status": "success",
            "message": "Current directory retrieved successfully",
            "data": {
                "path": cwd,
                "exists": os.path.exists(cwd),
                "is_directory": os.path.isdir(cwd)
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting current directory: {str(e)}")
        return {
            "status": "error",
            "message": f"Error retrieving current directory: {str(e)}"
        }

def get_running_processes() -> Dict[str, Any]:
    """Get a list of running processes.
    
    Returns:
        dict: List of running processes
    """
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            processes.append(proc.info)
        
        # Sort by CPU usage (highest first)
        processes.sort(key=lambda x: x['cpu_percent'] if x['cpu_percent'] is not None else 0, reverse=True)
        
        # Limit to top 20 processes
        top_processes = processes[:20]
        
        return {
            "status": "success",
            "message": "Running processes retrieved successfully",
            "data": top_processes
        }
    
    except Exception as e:
        logger.error(f"Error getting running processes: {str(e)}")
        return {
            "status": "error",
            "message": f"Error retrieving running processes: {str(e)}"
        }

def register_system_tools() -> bool:
    """Register all system tools with the LangChain service.
    
    Returns:
        bool: True if all tools were registered successfully
    """
    if not langchain_service.active:
        logger.error("Cannot register system tools: LangChain service not active")
        return False
    
    try:
        # Register each tool
        langchain_service.register_tool(
            name="get_system_info",
            func=get_system_info,
            description="Get information about the operating system and hardware"
        )
        
        langchain_service.register_tool(
            name="run_command",
            func=run_command,
            description="Run a shell command (with safety checks)"
        )
        
        langchain_service.register_tool(
            name="get_environment_variables",
            func=get_environment_variables,
            description="Get the system environment variables (sensitive values are masked)"
        )
        
        langchain_service.register_tool(
            name="get_current_directory",
            func=get_current_directory,
            description="Get the current working directory"
        )
        
        langchain_service.register_tool(
            name="get_running_processes",
            func=get_running_processes,
            description="Get a list of running processes (limited to top 20 by CPU usage)"
        )
        
        logger.info("System tools registered successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error registering system tools: {str(e)}")
        return False 