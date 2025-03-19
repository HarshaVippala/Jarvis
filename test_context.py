#!/usr/bin/env python3
"""
Test script for Jarvis context awareness functionality.

This script tests screen capture, OCR processing, and context management.
"""
import sys
import logging
import time
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

from jarvis.context.screen_capture import screen_capture_service
from jarvis.context.ocr_processor import ocr_processor
from jarvis.context.app_context import app_context_service
from jarvis.context.context_manager import context_manager

def test_dependencies():
    """Test if required dependencies are available."""
    logger.info("Checking dependencies...")
    
    # Check screen capture dependencies
    screen_info = screen_capture_service.get_info()
    if screen_info["dependencies_available"]:
        logger.info("✅ Screen capture dependencies available")
    else:
        logger.warning("❌ Screen capture dependencies missing")
    
    # Check OCR dependencies
    ocr_info = ocr_processor.get_info()
    if ocr_info["available"]:
        logger.info(f"✅ OCR available (Tesseract version: {ocr_info.get('tesseract_version', 'unknown')})")
    else:
        logger.warning("❌ OCR dependencies missing")
    
    # Check if on macOS for app context
    app_info = app_context_service.get_service_info()
    if app_info["is_macos"]:
        logger.info("✅ Running on macOS, app context available")
    else:
        logger.warning("❌ Not running on macOS, app context not available")

def test_screen_capture():
    """Test screen capture functionality."""
    logger.info("\nTesting screen capture...")
    
    # Start screen capture service
    logger.info("Starting screen capture service")
    success = screen_capture_service.start()
    
    if not success:
        logger.error("Failed to start screen capture service")
        return
    
    logger.info("Screen capture service started")
    
    # Wait for initial capture
    logger.info("Waiting for initial capture (5 seconds)...")
    time.sleep(5)
    
    # Get screen text
    text = screen_capture_service.get_screen_text()
    if text:
        logger.info(f"Captured screen text ({len(text)} chars)")
        logger.info(f"Text preview: {text[:200]}...")
    else:
        logger.warning("No text captured from screen")
    
    # Stop screen capture
    logger.info("Stopping screen capture service")
    screen_capture_service.stop()

def test_app_context():
    """Test application context functionality."""
    logger.info("\nTesting application context...")
    
    # Start app context service
    logger.info("Starting app context service")
    success = app_context_service.start()
    
    if not success:
        logger.error("Failed to start app context service (requires macOS)")
        return
    
    logger.info("App context service started")
    
    # Get current application
    app_context = app_context_service.get_app_context()
    logger.info(f"Current application: {app_context.get('app_name', 'Unknown')}")
    logger.info(f"Current window title: {app_context.get('window_title', 'Unknown')}")
    logger.info(f"Current bundle ID: {app_context.get('bundle_id', 'Unknown')}")
    
    # Test multiple updates
    logger.info("Testing multiple updates for 5 seconds...")
    start_time = time.time()
    
    while time.time() - start_time < 5:
        app_context_service.update_context()
        app_name = app_context_service.get_current_app()
        window_title = app_context_service.get_current_window_title()
        logger.info(f"Active app: {app_name}, Window: {window_title}")
        time.sleep(1)
    
    # Stop app context service
    logger.info("Stopping app context service")
    app_context_service.stop()

def test_context_manager():
    """Test context manager functionality."""
    logger.info("\nTesting context manager...")
    
    # Start context manager
    logger.info("Starting context manager")
    context_manager.start()
    
    # Test screen observation
    logger.info("Testing screen observation...")
    success = context_manager.start_screen_observation()
    
    if success:
        logger.info("Screen observation started")
        time.sleep(5)
        
        screen_context = context_manager.get_screen_context()
        if screen_context:
            logger.info(f"Screen context ({len(screen_context)} chars)")
            logger.info(f"Preview: {screen_context[:200]}...")
        else:
            logger.warning("No screen context available")
        
        context_manager.stop_screen_observation()
    else:
        logger.error("Failed to start screen observation")
    
    # Test app context
    logger.info("Testing app context...")
    success = context_manager.start_app_context()
    
    if success:
        logger.info("App context monitoring started")
        time.sleep(2)
        
        app_context = context_manager.get_app_context()
        logger.info(f"App context: {app_context}")
        
        context_manager.stop_app_context()
    else:
        logger.error("Failed to start app context monitoring")
    
    # Get full context
    logger.info("Getting full context...")
    full_context = context_manager.get_full_context()
    logger.info(f"Full context: {full_context}")
    
    # Stop context manager
    logger.info("Stopping context manager")
    context_manager.stop()

def main():
    """Main test function."""
    logger.info("Starting context awareness tests")
    
    # Test dependencies
    test_dependencies()
    
    # Test screen capture
    test_screen_capture()
    
    # Test app context
    test_app_context()
    
    # Test context manager
    test_context_manager()
    
    logger.info("All tests completed")

if __name__ == "__main__":
    main() 