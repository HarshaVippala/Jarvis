"""
Auto-launch utility for Jarvis

This module provides functionality to set up Jarvis to start automatically at login
on macOS using LaunchAgents.
"""
import logging
import os
import sys
import platform
import plistlib
from pathlib import Path
import subprocess
import shutil

logger = logging.getLogger(__name__)

# Constants
LAUNCH_AGENT_NAME = "com.jarvis.assistant"
LAUNCH_AGENT_LABEL = "Jarvis AI Assistant"

def is_mac():
    """Check if the system is macOS."""
    return platform.system() == "Darwin"

def get_launch_agent_path():
    """Get the path to the LaunchAgent plist file."""
    if not is_mac():
        logger.warning("Auto-launch is only supported on macOS")
        return None
    
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    return launch_agents_dir / f"{LAUNCH_AGENT_NAME}.plist"

def get_jarvis_executable():
    """Get the path to the Jarvis executable."""
    # If running from a bundled app
    if getattr(sys, 'frozen', False):
        return Path(sys.executable)
    
    # If running from source
    return Path(sys.executable).absolute()

def create_launch_agent(hidden=True):
    """
    Create a LaunchAgent plist file to start Jarvis at login.
    
    Args:
        hidden: Whether to start Jarvis hidden (no window)
        
    Returns:
        True if the LaunchAgent was created successfully, False otherwise
    """
    if not is_mac():
        logger.warning("Auto-launch is only supported on macOS")
        return False
    
    try:
        # Get the launch agent directory
        launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
        os.makedirs(launch_agents_dir, exist_ok=True)
        
        # Get the Jarvis executable path
        executable = get_jarvis_executable()
        working_dir = Path(sys.argv[0]).parent.absolute()
        
        # Build the command to run
        if getattr(sys, 'frozen', False):
            # If Jarvis is bundled as an app, open it
            cmd = ['/usr/bin/open', str(executable)]
            if hidden:
                cmd.append('--args')
                cmd.append('--hidden')
        else:
            # If running from source, run the Python script
            cmd = [str(executable), str(Path(__file__).parent.parent.parent / "start_desktop.py"), "--daemon"]
        
        # Create the plist content
        plist_content = {
            'Label': LAUNCH_AGENT_NAME,
            'ProgramArguments': cmd,
            'WorkingDirectory': str(working_dir),
            'RunAtLoad': True,
            'KeepAlive': False,
            'StandardOutPath': str(Path.home() / ".jarvis" / "stdout.log"),
            'StandardErrorPath': str(Path.home() / ".jarvis" / "stderr.log"),
        }
        
        # Ensure logs directory exists
        logs_dir = Path.home() / ".jarvis"
        os.makedirs(logs_dir, exist_ok=True)
        
        # Write the plist file
        plist_path = get_launch_agent_path()
        with open(plist_path, 'wb') as f:
            plistlib.dump(plist_content, f)
        
        # Set permissions
        os.chmod(plist_path, 0o644)
        
        # Load the LaunchAgent if system is running
        if os.geteuid() == 0:
            logger.warning("Running as root, not loading LaunchAgent")
        else:
            subprocess.run(['launchctl', 'load', str(plist_path)], check=False)
        
        logger.info(f"Created LaunchAgent at {plist_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating LaunchAgent: {e}")
        return False

def remove_launch_agent():
    """
    Remove the LaunchAgent plist file.
    
    Returns:
        True if the LaunchAgent was removed successfully, False otherwise
    """
    if not is_mac():
        logger.warning("Auto-launch is only supported on macOS")
        return False
    
    try:
        plist_path = get_launch_agent_path()
        
        if not plist_path or not plist_path.exists():
            logger.info("LaunchAgent not found, nothing to remove")
            return True
        
        # Unload the LaunchAgent if system is running
        if os.geteuid() == 0:
            logger.warning("Running as root, not unloading LaunchAgent")
        else:
            subprocess.run(['launchctl', 'unload', str(plist_path)], check=False)
        
        # Remove the plist file
        os.remove(plist_path)
        
        logger.info(f"Removed LaunchAgent at {plist_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error removing LaunchAgent: {e}")
        return False

def is_auto_launch_enabled():
    """
    Check if auto-launch is enabled.
    
    Returns:
        True if auto-launch is enabled, False otherwise
    """
    if not is_mac():
        return False
    
    plist_path = get_launch_agent_path()
    return plist_path and plist_path.exists()

def set_auto_launch(enabled, hidden=True):
    """
    Enable or disable auto-launch.
    
    Args:
        enabled: Whether to enable auto-launch
        hidden: Whether to start Jarvis hidden
        
    Returns:
        True if the operation was successful, False otherwise
    """
    if enabled:
        return create_launch_agent(hidden=hidden)
    else:
        return remove_launch_agent() 