#!/usr/bin/env python3
"""
Test application for the wake word detection system.
"""

import os
import sys
import asyncio
import logging
import signal
import time
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

from jarvis.speech.wake_word_detector import WakeWordDetector

class WakeWordTester:
    """Test harness for the Jarvis wake word detection."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.wake_word_detector = WakeWordDetector()
        self.running = False
        
        # Register signal handlers for clean exit
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)
    
    def handle_interrupt(self, signum, frame):
        """Handle termination signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def run(self):
        """Run the wake word detection test."""
        self.logger.info("Initializing wake word detector...")
        
        # Initialize the wake word detector
        # This will create a mock implementation without an access key
        result = await self.wake_word_detector.initialize()
        
        if not result:
            self.logger.error("Failed to initialize wake word detector.")
            return False
            
        # Register wake word callback
        self.running = True
        self.wake_word_detector.start(callback=self.on_wake_word)
        
        # Wait indefinitely
        while self.running:
            await asyncio.sleep(0.1)
            
        return True
    
    def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up...")
        if self.wake_word_detector:
            self.wake_word_detector.shutdown()
        self.logger.info("Cleanup completed.")
        
    def on_wake_word(self):
        """Callback when wake word is detected."""
        self.logger.info("WAKE WORD DETECTED! 🎉")
        self.logger.info("I'm listening... (in a real app, this would start active listening)")

async def main():
    """Main entry point."""
    print("=== Jarvis Wake Word Detection Test ===")
    print("This test will check wake word detection functionality.")
    print("Say 'Jarvis' to trigger detection.")
    print("Press Ctrl+C to exit at any time.")
    
    tester = WakeWordTester()
    
    try:
        success = await tester.run()
        if not success:
            logging.error("Test failed to initialize properly.")
    except Exception as e:
        logging.error(f"Error during testing: {e}")
    finally:
        tester.cleanup()
        
    print("=== Test completed ===")

if __name__ == "__main__":
    asyncio.run(main()) 