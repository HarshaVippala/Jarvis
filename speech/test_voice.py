#!/usr/bin/env python3
"""
Test script for the Jarvis voice system.
Tests voice recognition and text-to-speech functionality.
"""

import os
import sys
import asyncio
import logging
import signal
from pathlib import Path

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

from jarvis.speech import VoiceSystem

class VoiceSystemTester:
    """Test harness for the Jarvis voice system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.voice_system = VoiceSystem()
        self.running = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
    
    def _handle_signal(self, signum, frame):
        """Handle termination signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def initialize(self):
        """Initialize the voice system."""
        self.logger.info("Initializing voice system...")
        await self.voice_system.initialize()
        self.logger.info("Voice system initialized.")
    
    async def run_tts_test(self):
        """Test text-to-speech functionality."""
        self.logger.info("Testing text-to-speech...")
        
        test_phrases = [
            "Hello, I am Jarvis, your personal AI assistant.",
            "I can help you with tasks, answer questions, and control your computer.",
            "My voice comes from Coqui TTS, an open-source text-to-speech system."
        ]
        
        for phrase in test_phrases:
            self.logger.info(f"TTS test: '{phrase}'")
            await self.voice_system.speak(phrase)
            await asyncio.sleep(0.5)
        
        self.logger.info("TTS test completed.")
    
    async def run_listening_test(self, duration=30):
        """Test speech recognition functionality for a specified duration."""
        self.logger.info(f"Testing speech recognition for {duration} seconds...")
        self.logger.info("Please speak into your microphone.")
        
        async def on_transcription(text):
            self.logger.info(f"Recognized: {text}")
            
            # Echo back what was heard
            await self.voice_system.speak(f"I heard: {text}")
            
            # Check for exit command
            if "exit" in text.lower() or "stop" in text.lower() or "quit" in text.lower():
                self.logger.info("Exit command recognized.")
                self.running = False
        
        await self.voice_system.start_listening(on_transcription)
        
        # Run for specified duration or until stopped
        self.running = True
        start_time = asyncio.get_event_loop().time()
        
        while self.running and (asyncio.get_event_loop().time() - start_time < duration):
            await asyncio.sleep(0.1)
        
        await self.voice_system.stop_listening()
        self.logger.info("Listening test completed.")
    
    async def cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up...")
        self.voice_system.shutdown()
        self.logger.info("Cleanup completed.")

async def main():
    """Main entry point for the voice system test."""
    print("=== Jarvis Voice System Test ===")
    print("This test will check speech recognition and text-to-speech functionality.")
    print("Press Ctrl+C to exit at any time.")
    
    tester = VoiceSystemTester()
    
    try:
        await tester.initialize()
        
        # Test TTS first
        await tester.run_tts_test()
        
        # Then test listening (speech recognition)
        await tester.run_listening_test(60)  # Run for 60 seconds or until exit command
        
    except Exception as e:
        logging.error(f"Error during testing: {e}")
    finally:
        await tester.cleanup()
        
    print("=== Test completed ===")

if __name__ == "__main__":
    asyncio.run(main()) 