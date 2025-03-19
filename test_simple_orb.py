#!/usr/bin/env python3
"""
Test script to run just the simple orb widget.
"""
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication
from jarvis.desktop.ui.simple_orb import SimpleOrb

def main():
    """Run the simple orb test."""
    # Create the application
    app = QApplication(sys.argv)
    app.setApplicationName("Jarvis Simple Orb Test")
    
    # Create and show the orb
    orb = SimpleOrb()
    orb.show()
    
    print(f"Orb created and shown. Visible: {orb.isVisible()}")
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 