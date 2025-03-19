#!/usr/bin/env python3
"""
Launcher script for the Jarvis desktop application.
"""
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the desktop main module
from jarvis.desktop.main import main

if __name__ == "__main__":
    main() 