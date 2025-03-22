#!/usr/bin/env python3
"""
Test script for the voice system, including speech recognition, TTS, and wake word detection.
"""

import os
import sys
import logging
import asyncio
import time
from pathlib import Path

# Add the jarvis directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jarvis.speech.voice_system import VoiceSystem
from jarvis.speech.tts_service import TTSService
from jarvis.speech.whisper_service import WhisperService
from jarvis.speech.wake_word_detector import WakeWordDetector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceSystemTester:
    """Test harness for the voice system."""
    
    def __init__(self):
        self.voice_system = VoiceSystem()
        self.test_audio_file = Path(__file__).parent / "resources" / "test_audio.wav"
        
    async def initialize(self):
        """Initialize the voice system."""
        logger.info("Initializing voice system...")
        await self.voice_system.initialize()
        logger.info("Voice system initialized")
        
    async def test_tts(self):
        """Test text-to-speech functionality."""
        logger.info("Testing TTS...")
        
        # Test basic TTS
        result = await self.voice_system.speak("Hello, I am Jarvis. This is a test of the text to speech system.")
        logger.info(f"TTS test result: {'SUCCESS' if result else 'FAILED'}")
        
        # Get available voices
        voices = await self.voice_system.get_available_tts_voices()
        logger.info(f"Available voices: {voices}")
        
        # Test each available voice
        for voice_id in voices:
            logger.info(f"Testing voice: {voice_id}")
            await self.voice_system.set_tts_voice(voice_id)
            await self.voice_system.speak(f"This is the {voice_id} voice.")
            await asyncio.sleep(0.5)
        
        # Restore default voice
        await self.voice_system.set_tts_voice("female_standard")
        
        logger.info("TTS tests completed")
        
    async def test_speech_recognition_from_file(self):
        """Test speech recognition from an audio file."""
        if not self.test_audio_file.exists():
            logger.warning(f"Test audio file not found: {self.test_audio_file}")
            return
            
        logger.info(f"Testing speech recognition from file: {self.test_audio_file}")
        
        # Test API version
        await self.voice_system.toggle_local_whisper(False)
        transcription = await self.voice_system.whisper_service.transcribe_file(self.test_audio_file)
        logger.info(f"API Transcription: {transcription}")
        
        # Test local version if available
        await self.voice_system.toggle_local_whisper(True)
        if self.voice_system.whisper_service.is_initialized:
            transcription = await self.voice_system.whisper_service.transcribe_file(self.test_audio_file)
            logger.info(f"Local Transcription: {transcription}")
        else:
            logger.warning("Local Whisper model not initialized")
        
    async def test_microphone_recognition(self):
        """Test speech recognition from the microphone."""
        logger.info("Testing microphone recognition (5 seconds)...")
        
        # Set up callback to print transcriptions
        def transcription_callback(text):
            logger.info(f"Transcription: {text}")
        
        # Start listening
        await self.voice_system.start_listening(transcription_callback)
        
        # Listen for 5 seconds
        logger.info("Speak now...")
        await asyncio.sleep(5)
        
        # Stop listening
        await self.voice_system.stop_listening()
        logger.info("Microphone test completed")

    async def test_wake_word_detection(self):
        """Test wake word detection."""
        logger.info("Testing wake word detection for 20 seconds...")
        logger.info("Say 'Jarvis' to activate...")
        
        # Set up callback for wake word detection
        def wake_word_callback(text):
            logger.info(f"Wake word detected, transcription: {text}")
        
        # Start wake word detection
        await self.voice_system.start_wake_word_detection(wake_word_callback)
        
        # Listen for 20 seconds
        for i in range(20):
            logger.info(f"Listening for wake word... ({i+1}/20)")
            await asyncio.sleep(1)
        
        # Stop wake word detection
        await self.voice_system.stop_wake_word_detection()
        logger.info("Wake word test completed")
        
    async def test_conversation_loop(self):
        """Test the complete conversation loop with wake word, recognition, and response."""
        logger.info("Testing conversation loop for 10 seconds...")
        logger.info("Say 'Jarvis' to start, then ask a question...")
        
        # Set up callback for the conversation
        conversation_handled = False
        
        async def conversation_callback(text):
            nonlocal conversation_handled
            if conversation_handled:
                return
                
            conversation_handled = True
            logger.info(f"Heard: {text}")
            
            # Simple response logic for testing
            response = "I didn't understand that."
            
            if "hello" in text.lower() or "hi" in text.lower():
                response = "Hello there! How can I help you today?"
            elif "time" in text.lower():
                response = f"The current time is {time.strftime('%I:%M %p')}."
            elif "date" in text.lower():
                response = f"Today is {time.strftime('%A, %B %d, %Y')}."
            elif "weather" in text.lower():
                response = "I'm sorry, I can't check the weather right now."
            elif "name" in text.lower():
                response = "My name is Jarvis, your AI assistant."
            
            logger.info(f"Responding: {response}")
            await self.voice_system.speak(response)
            
            # After responding, stop wake word detection to avoid continued processing
            await self.voice_system.stop_wake_word_detection()
        
        # Start wake word detection with conversation callback
        await self.voice_system.start_wake_word_detection(
            lambda text: asyncio.create_task(conversation_callback(text))
        )
        
        # Run for 10 seconds (reduced from 30)
        for i in range(10):
            logger.info(f"Listening for wake word... ({i+1}/10)")
            await asyncio.sleep(1)
            if conversation_handled:
                break
        
        # Stop wake word detection
        await self.voice_system.stop_wake_word_detection()
        logger.info("Conversation loop test completed")
    
    async def run_all_tests(self):
        """Run all voice system tests."""
        await self.initialize()
        
        # Update tests - only run TTS test to focus on that implementation
        tests = [
            self.test_tts,
            # Temporarily disable other tests that require microphone/wake word
            # self.test_speech_recognition_from_file,
            # self.test_microphone_recognition,
            # self.test_wake_word_detection,
            # self.test_conversation_loop
        ]
        
        for test in tests:
            try:
                logger.info(f"Running test: {test.__name__}")
                await test()
                logger.info(f"Test {test.__name__} completed")
                await asyncio.sleep(1)  # Brief pause between tests
            except Exception as e:
                logger.error(f"Error in {test.__name__}: {e}")
        
        # Shutdown
        self.voice_system.shutdown()
        logger.info("All tests completed")

async def main():
    """Main entry point for the test script."""
    tester = VoiceSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    # Create test resources directory if it doesn't exist
    resource_dir = Path(__file__).parent / "resources"
    resource_dir.mkdir(exist_ok=True)
    
    # Run tests
    asyncio.run(main()) 