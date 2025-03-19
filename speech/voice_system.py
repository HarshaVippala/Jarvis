import os
import logging
import asyncio
from typing import Optional, Callable, Dict, Any, List, Tuple

from .voice_manager import VoiceManager
from .whisper_service import WhisperService
from .tts_service import TTSService
from .wake_word_detector import WakeWordDetector

class VoiceSystem:
    """
    Centralized voice system service that coordinates voice recognition and synthesis.
    Integrates VoiceManager, WhisperService, TTSService, and WakeWordDetector into a unified interface.
    """
    
    def __init__(self, app_controller=None):
        self.logger = logging.getLogger(__name__)
        self.app_controller = app_controller
        
        # Initialize sub-components
        self.voice_manager = VoiceManager(app_controller)
        self.whisper_service = WhisperService(app_controller, use_local=False, model_size="tiny")  # Start with API mode
        self.tts_service = TTSService(app_controller)
        self.wake_word_detector = WakeWordDetector(app_controller)
        
        # Connection status
        self.is_initialized = False
        self.is_listening = False
        self.is_speaking = False
        self.is_wake_word_active = False
        
        # Callback for handling transcriptions
        self.transcription_callback = None
        
        # Settings
        self.use_local_whisper = False
        self.whisper_model_size = "tiny"  # tiny, base, small, medium, large
        self.tts_voice = "female_standard"
        self.wake_word_sensitivity = 0.5
        self.active_wake_words = ["jarvis"]
        
        self.logger.info("Voice System initialized")
    
    async def initialize(self):
        """Initialize all voice services."""
        self.logger.info("Initializing Voice System...")
        
        try:
            # Initialize voice manager
            if self.voice_manager:
                await self.voice_manager.initialize()
            
            # Initialize TTS service
            if self.tts_service:
                await self.tts_service.initialize()
                
            # Initialize Whisper service
            if self.whisper_service:
                await self.whisper_service.initialize()
            
            # Initialize wake word detector
            if self.wake_word_detector:
                # We'll pass None for access key, which will trigger the mock implementation 
                # in development environments
                await self.wake_word_detector.initialize()
                
            self.logger.info("Voice System initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Voice System: {e}")
            return False
    
    async def start_listening(self, callback: Callable[[str], None] = None):
        """Start listening for voice input with the specified callback for transcriptions."""
        if self.is_listening:
            self.logger.warning("Already listening")
            return False
            
        if not self.is_initialized:
            await self.initialize()
            
        self.transcription_callback = callback
        
        # Override voice manager's callback to process audio with our Whisper service
        def on_audio_processed(audio_data):
            asyncio.create_task(self._process_transcription(audio_data))
        
        result = self.voice_manager.start_listening(on_audio_processed)
        self.is_listening = result
        return result
    
    async def start_wake_word_detection(self, callback: Callable[[str], None] = None):
        """
        Start listening for wake words and automatically begin voice recognition when detected.
        
        Args:
            callback: Function to call with transcription after wake word detection
        """
        if not self.is_initialized:
            await self.initialize()
            
        if self.is_wake_word_active:
            self.logger.warning("Wake word detection already active")
            return False
            
        self.transcription_callback = callback
        
        # Set up wake word detection callback
        def on_wake_word_detected():
            self.logger.info("Wake word detected, starting voice recognition")
            
            # Stop wake word detection temporarily
            self.wake_word_detector.stop()
            
            # Start active listening
            asyncio.create_task(self._active_listening_session())
        
        # Start wake word detector
        result = self.wake_word_detector.start(on_wake_word_detected)
        if result:
            self.is_wake_word_active = True
            self.logger.info("Wake word detection started")
        
        return result
    
    async def _active_listening_session(self):
        """Start a listening session after wake word detection, then return to wake word mode."""
        # Start listening
        await self.start_listening(self.transcription_callback)
        
        # Provide audio feedback
        await self.speak("I'm listening")
        
        # Listen for 10 seconds maximum or until silence
        start_time = asyncio.get_event_loop().time()
        max_duration = 10  # seconds
        
        while self.is_listening and (asyncio.get_event_loop().time() - start_time < max_duration):
            await asyncio.sleep(0.1)
            
        # If still listening after timeout, stop listening
        if self.is_listening:
            await self.stop_listening()
            
        # If wake word detection was active before, restart it
        if self.is_wake_word_active:
            # Slight delay to avoid processing the same audio
            await asyncio.sleep(0.5)
            
            # Restart wake word detection
            self.wake_word_detector.start(
                lambda: asyncio.create_task(self._active_listening_session())
            )
    
    async def stop_wake_word_detection(self):
        """Stop listening for wake words."""
        if not self.is_wake_word_active:
            return True
            
        self.wake_word_detector.stop()
        self.is_wake_word_active = False
        return True
    
    async def _process_transcription(self, transcription: str):
        """Process transcription from Whisper service and call the callback."""
        if not transcription or not transcription.strip():
            return
            
        self.logger.info(f"Transcription: {transcription}")
        
        if self.transcription_callback:
            await asyncio.to_thread(self.transcription_callback, transcription)
    
    async def stop_listening(self):
        """Stop listening for voice input."""
        if not self.is_listening:
            return True
            
        self.voice_manager.stop_listening()
        self.is_listening = False
        return True
    
    async def speak(self, text: str) -> bool:
        """Convert text to speech and play it."""
        if self.is_speaking:
            self.logger.warning("Already speaking")
            return False
            
        if not self.is_initialized:
            await self.initialize()
            
        self.is_speaking = True
        
        try:
            return await self.tts_service.speak(text)
        finally:
            self.is_speaking = False
    
    async def toggle_local_whisper(self, use_local: bool) -> bool:
        """Toggle between local Whisper model and API."""
        if use_local == self.use_local_whisper:
            return True
            
        self.use_local_whisper = use_local
        return await self.whisper_service.toggle_mode(use_local)
    
    async def set_whisper_model_size(self, model_size: str) -> bool:
        """Set the Whisper model size for local processing."""
        if model_size == self.whisper_model_size:
            return True
            
        result = await self.whisper_service.set_model_size(model_size)
        if result:
            self.whisper_model_size = model_size
        return result
    
    async def set_tts_voice(self, voice: str) -> bool:
        """Set the TTS voice/model to use."""
        if voice == self.tts_voice:
            return True
            
        result = await self.tts_service.change_model(voice)
        if result:
            self.tts_voice = voice
        return result
    
    async def set_wake_word_sensitivity(self, sensitivity: float) -> bool:
        """Set the wake word detection sensitivity."""
        if sensitivity == self.wake_word_sensitivity:
            return True
            
        result = self.wake_word_detector.set_sensitivity(sensitivity)
        if result:
            self.wake_word_sensitivity = sensitivity
        return result
    
    async def set_active_wake_words(self, wake_words: List[str]) -> bool:
        """Set which wake words to listen for."""
        # Check if there's any change
        if set(wake_words) == set(self.active_wake_words):
            return True
            
        result = self.wake_word_detector.set_active_keywords(wake_words)
        if result:
            self.active_wake_words = wake_words
        return result
    
    async def get_available_wake_words(self) -> List[str]:
        """Get available wake words."""
        return self.wake_word_detector.get_available_keywords()
    
    async def get_available_tts_voices(self) -> Dict[str, str]:
        """Get available TTS voices/models."""
        return self.tts_service.get_available_models()
    
    async def get_whisper_metrics(self) -> Dict[str, Any]:
        """Get Whisper service performance metrics."""
        return self.whisper_service.get_metrics()
    
    async def get_tts_metrics(self) -> Dict[str, Any]:
        """Get TTS service performance metrics."""
        return self.tts_service.get_metrics()
    
    async def adjust_vad_settings(self, threshold: float = None, silence_duration: float = None) -> None:
        """Adjust voice activity detection settings."""
        self.voice_manager.adjust_vad_settings(threshold, silence_duration)
    
    def shutdown(self):
        """Clean up resources and shutdown all voice services."""
        self.logger.info("Shutting down Voice System")
        
        # Stop listening if active
        if self.is_listening:
            self.voice_manager.stop_listening()
            
        # Stop wake word detection if active
        if self.is_wake_word_active:
            self.wake_word_detector.stop()
            
        # Shutdown all components
        self.voice_manager.shutdown()
        self.whisper_service.shutdown()
        self.tts_service.shutdown()
        self.wake_word_detector.shutdown() 