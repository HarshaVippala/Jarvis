import os
import logging
import asyncio
import threading
import time
import struct
import pyaudio
from typing import Optional, Callable, List, Dict, Any

class WakeWordDetector:
    """
    Wake word detection service using Porcupine by Picovoice.
    Provides lightweight and accurate detection of wake words like "Hey Jarvis".
    """
    
    def __init__(self, app_controller=None, sensitivity=0.5, access_key=None):
        self.logger = logging.getLogger(__name__)
        self.app_controller = app_controller
        self.sensitivity = sensitivity
        self.access_key = access_key
        
        # Try to get access key from environment if not provided
        if not self.access_key:
            self.access_key = os.environ.get('PICOVOICE_ACCESS_KEY', '')
        
        # Porcupine detector (will be initialized later)
        self.porcupine = None
        self.library_path = None
        self.model_path = None
        self.keyword_paths = []
        
        # Audio settings
        self.audio = None
        self.stream = None
        self.is_running = False
        self.thread = None
        
        # Callbacks
        self.on_wake_word_detected = None
        
        # Default keywords to detect
        self.available_keywords = ["jarvis", "hey jarvis", "computer"]
        self.active_keywords = ["jarvis"]
        
        self.logger.info("Wake Word Detector initialized")
    
    async def initialize(self):
        """Initialize the wake word detector."""
        try:
            # Import Porcupine here to avoid dependency if not used
            from pvporcupine import Porcupine, KEYWORD_PATHS
            
            # Set up paths
            self.library_path = None  # Use default
            self.model_path = None  # Use default
            
            # Check for access key
            if not self.access_key:
                self.logger.warning("No Picovoice access key provided. Set PICOVOICE_ACCESS_KEY environment variable or pass access_key parameter.")
                # For development, create a mock implementation that will trigger randomly
                self._setup_mock_detector()
                return True
            
            # Find built-in keyword paths
            selected_keywords = {}
            for keyword in self.active_keywords:
                for key, path in KEYWORD_PATHS.items():
                    if keyword.lower() in key.lower():
                        selected_keywords[keyword] = path
                        break
            
            if not selected_keywords:
                # Fall back to default if no keyword found
                self.keyword_paths = [KEYWORD_PATHS['jarvis']]
                self.logger.warning("No matching keywords found, using 'jarvis' as default")
            else:
                self.keyword_paths = list(selected_keywords.values())
                self.logger.info(f"Using keywords: {list(selected_keywords.keys())}")
            
            # Initialize Porcupine engine
            self.porcupine = Porcupine(
                access_key=self.access_key,
                library_path=self.library_path,
                model_path=self.model_path,
                keyword_paths=self.keyword_paths,
                sensitivities=[self.sensitivity] * len(self.keyword_paths)
            )
            
            # Initialize audio
            self.audio = pyaudio.PyAudio()
            
            self.logger.info("Wake Word Detector initialized successfully")
            return True
        except ImportError as e:
            self.logger.error(f"Porcupine not available: {e}. Install with 'pip install pvporcupine'")
            return False
        except Exception as e:
            self.logger.error(f"Failed to initialize wake word detector: {e}")
            return False
    
    def _setup_mock_detector(self):
        """Create a mock detector for development without access key."""
        self.logger.warning("Using MOCK wake word detector for development")
        # Simulated properties for compatibility
        class MockPorcupine:
            def __init__(self):
                self.sample_rate = 16000
                self.frame_length = 512
            
            def process(self, pcm):
                # Return -1 most of the time, and occasionally detect wake word
                if threading.current_thread().name == 'MainThread' and time.time() % 30 < 0.1:
                    return 0  # Simulate detection about once every 30 seconds
                return -1
            
            def delete(self):
                pass
        
        self.porcupine = MockPorcupine()
        self.audio = pyaudio.PyAudio()
    
    def start(self, callback: Callable[[], None] = None):
        """
        Start listening for wake words.
        
        Args:
            callback: Function to call when wake word is detected
        """
        if self.is_running:
            self.logger.warning("Wake word detector already running")
            return False
        
        if not self.porcupine:
            self.logger.error("Wake word detector not initialized")
            return False
        
        self.on_wake_word_detected = callback
        self.is_running = True
        
        # Start listening in a separate thread
        self.thread = threading.Thread(target=self._listen_loop)
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info("Wake word detector started")
        return True
    
    def stop(self):
        """Stop listening for wake words."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Wait for thread to finish
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        
        # Clean up audio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        self.logger.info("Wake word detector stopped")
    
    def _listen_loop(self):
        """Background worker that listens for wake words."""
        # Create audio stream
        try:
            self.stream = self.audio.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
                stream_callback=self._audio_callback
            )
            
            # Keep thread alive while running
            while self.is_running:
                time.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Error in wake word detection loop: {e}")
        finally:
            # Clean up if needed
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Process audio data and detect wake words."""
        try:
            # Process audio with Porcupine
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, in_data)
            keyword_index = self.porcupine.process(pcm)
            
            # If wake word detected
            if keyword_index >= 0:
                # Get the detected keyword name
                keyword_name = self.active_keywords[keyword_index] if keyword_index < len(self.active_keywords) else "unknown"
                self.logger.info(f"Wake word detected: {keyword_name}")
                
                # Trigger callback on main thread
                if self.on_wake_word_detected:
                    # Need to use a thread as we're in the audio callback
                    threading.Thread(target=self.on_wake_word_detected).start()
        except Exception as e:
            self.logger.error(f"Error processing audio for wake word: {e}")
        
        # Return to continue streaming
        return None, pyaudio.paContinue
    
    def set_sensitivity(self, sensitivity: float):
        """
        Set the detection sensitivity.
        
        Args:
            sensitivity: Value between 0 and 1, where higher is more sensitive
        """
        if sensitivity < 0 or sensitivity > 1:
            self.logger.error("Sensitivity must be between 0 and 1")
            return False
        
        self.sensitivity = sensitivity
        
        # Recreate detector with new sensitivity if running
        if self.porcupine:
            was_running = self.is_running
            if was_running:
                self.stop()
            
            # Clean up existing detector
            self.porcupine.delete()
            
            # Reinitialize with new sensitivity
            asyncio.create_task(self.initialize())
            
            # Restart if it was running
            if was_running:
                self.start(self.on_wake_word_detected)
        
        self.logger.info(f"Wake word sensitivity set to {sensitivity}")
        return True
    
    def set_active_keywords(self, keywords: List[str]):
        """
        Set which keywords to actively listen for.
        
        Args:
            keywords: List of keyword names to detect
        """
        # Filter keywords to ones we know are available
        valid_keywords = [k for k in keywords if any(k.lower() in ak.lower() for ak in self.available_keywords)]
        
        if not valid_keywords:
            self.logger.error(f"No valid keywords specified. Available: {self.available_keywords}")
            return False
        
        self.active_keywords = valid_keywords
        
        # Reinitialize detector with new keywords
        if self.porcupine:
            was_running = self.is_running
            if was_running:
                self.stop()
            
            # Clean up existing detector
            self.porcupine.delete()
            self.porcupine = None
            
            # Reinitialize with new keywords
            asyncio.create_task(self.initialize())
            
            # Restart if it was running
            if was_running:
                self.start(self.on_wake_word_detected)
        
        self.logger.info(f"Active wake words set to: {valid_keywords}")
        return True
    
    def get_available_keywords(self) -> List[str]:
        """Get list of available wake word keywords."""
        return self.available_keywords
    
    def get_active_keywords(self) -> List[str]:
        """Get list of currently active wake word keywords."""
        return self.active_keywords
    
    def shutdown(self):
        """Clean up resources."""
        self.logger.info("Shutting down Wake Word Detector")
        
        # Stop listening
        self.stop()
        
        # Clean up Porcupine
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
        
        # Clean up audio
        if self.audio:
            self.audio.terminate()
            self.audio = None 