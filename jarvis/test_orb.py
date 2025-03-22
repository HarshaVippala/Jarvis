#!/usr/bin/env python3
"""
Simple test script to show just the orb and verify visibility.
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Add the jarvis directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jarvis.desktop.ui.floating_orb import FloatingOrb

def main():
    """Run the test."""
    # Create the application
    app = QApplication(sys.argv)
    
    # Create the orb
    orb = FloatingOrb()
    
    # Set a large size
    orb.setFixedSize(300, 300)
    
    # Center on screen
    orb.moveToCenter()
    
    # Force show with maximum visibility
    orb.force_show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 