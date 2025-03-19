import os
import logging
import asyncio
from typing import Optional, Callable, Dict, Any, List

from PySide6.QtCore import QObject, Signal, Slot, Qt, QTimer

from jarvis.speech import VoiceSystem

class VoiceController(QObject):
    """
    Controller for integrating the Voice System with the desktop UI.
    Provides signal/slot based interface for Qt applications.
    """
    
    # Define signals
    transcriptionReceived = Signal(str)  # Emitted when speech is transcribed
    speechCompleted = Signal()  # Emitted when speech playback is completed
    listeningStateChanged = Signal(bool)  # Emitted when listening state changes
    speakingStateChanged = Signal(bool)  # Emitted when speaking state changes
    wakeWordStateChanged = Signal(bool)  # Emitted when wake word detection state changes
    wakeWordDetected = Signal(str)  # Emitted when a wake word is detected
    initializationComplete = Signal(bool)  # Emitted when initialization completes (success/failure)
    errorOccurred = Signal(str)  # Emitted when an error occurs
    
    def __init__(self, app_controller=None):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.app_controller = app_controller
        
        # Create voice system
        self.voice_system = VoiceSystem(app_controller)
        
        # Status tracking
        self.is_initialized = False
        self.is_listening = False
        self.is_speaking = False
        self.is_wake_word_active = False
        
        # The main event loop for async operations
        self.loop = None
        self.initialization_task = None
        
        # Timer for periodic background tasks
        self.background_timer = QTimer()
        self.background_timer.timeout.connect(self._run_background_tasks)
        self.background_timer.start(100)  # Every 100ms
        
        self.logger.info("Voice Controller initialized")
    
    def _run_background_tasks(self):
        """Run background tasks in the event loop."""
        if self.loop is None or not self.loop.is_running():
            return
            
        # Process any pending tasks in the event loop
        asyncio.run_coroutine_threadsafe(asyncio.sleep(0), self.loop)
    
    @Slot()
    def initialize(self):
        """Initialize the voice system in the background."""
        if self.is_initialized or self.initialization_task is not None:
            return
            
        self.logger.info("Starting voice system initialization")
        
        # Create an event loop if needed
        if self.loop is None:
            self.loop = asyncio.new_event_loop()
            
        # Start the initialization in a separate thread
        def init_thread():
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_until_complete(self._initialize_async())
                self.loop.run_forever()
            except Exception as e:
                self.logger.error(f"Voice initialization thread error: {e}")
            finally:
                self.loop.close()
                self.loop = None
                
        import threading
        self.initialization_task = threading.Thread(target=init_thread)
        self.initialization_task.daemon = True
        self.initialization_task.start()
    
    async def _initialize_async(self):
        """Initialize the voice system asynchronously."""
        try:
            success = await self.voice_system.initialize()
            self.is_initialized = success
            self.initializationComplete.emit(success)
            if not success:
                self.errorOccurred.emit("Failed to initialize voice system")
                
            self.logger.info(f"Voice system initialization {'succeeded' if success else 'failed'}")
        except Exception as e:
            self.logger.error(f"Error initializing voice system: {e}")
            self.errorOccurred.emit(f"Voice system initialization error: {e}")
            self.initializationComplete.emit(False)
    
    @Slot()
    def start_listening(self):
        """Start listening for voice input."""
        if not self.is_initialized:
            self.errorOccurred.emit("Voice system not initialized")
            return
        
        if self.is_listening:
            return
            
        # Create a task to start listening
        async def start_listening_task():
            try:
                # Set up the callback for transcription
                def on_transcription(text):
                    # Emit on main thread
                    QTimer.singleShot(0, lambda: self.transcriptionReceived.emit(text))
                
                success = await self.voice_system.start_listening(on_transcription)
                if success:
                    self.is_listening = True
                    QTimer.singleShot(0, lambda: self.listeningStateChanged.emit(True))
                else:
                    QTimer.singleShot(0, lambda: self.errorOccurred.emit("Failed to start listening"))
            except Exception as e:
                self.logger.error(f"Error starting listening: {e}")
                QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Listening error: {e}"))
        
        asyncio.run_coroutine_threadsafe(start_listening_task(), self.loop)
    
    @Slot()
    def stop_listening(self):
        """Stop listening for voice input."""
        if not self.is_listening:
            return
            
        # Create a task to stop listening
        async def stop_listening_task():
            try:
                await self.voice_system.stop_listening()
                self.is_listening = False
                QTimer.singleShot(0, lambda: self.listeningStateChanged.emit(False))
            except Exception as e:
                self.logger.error(f"Error stopping listening: {e}")
                QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Error stopping listening: {e}"))
        
        asyncio.run_coroutine_threadsafe(stop_listening_task(), self.loop)
    
    @Slot()
    def start_wake_word_detection(self):
        """Start wake word detection mode."""
        if not self.is_initialized:
            self.errorOccurred.emit("Voice system not initialized")
            return
        
        if self.is_wake_word_active:
            return
            
        # Create a task to start wake word detection
        async def start_wake_word_task():
            try:
                # Set up the callback for transcription
                def on_transcription(text):
                    # Emit on main thread
                    QTimer.singleShot(0, lambda: self.transcriptionReceived.emit(text))
                    
                    # Also emit wake word detected when starting a new session
                    QTimer.singleShot(0, lambda: self.wakeWordDetected.emit("Detected"))
                
                success = await self.voice_system.start_wake_word_detection(on_transcription)
                if success:
                    self.is_wake_word_active = True
                    QTimer.singleShot(0, lambda: self.wakeWordStateChanged.emit(True))
                else:
                    QTimer.singleShot(0, lambda: self.errorOccurred.emit("Failed to start wake word detection"))
            except Exception as e:
                self.logger.error(f"Error starting wake word detection: {e}")
                QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Wake word detection error: {e}"))
        
        asyncio.run_coroutine_threadsafe(start_wake_word_task(), self.loop)
    
    @Slot()
    def stop_wake_word_detection(self):
        """Stop wake word detection mode."""
        if not self.is_wake_word_active:
            return
            
        # Create a task to stop wake word detection
        async def stop_wake_word_task():
            try:
                await self.voice_system.stop_wake_word_detection()
                self.is_wake_word_active = False
                QTimer.singleShot(0, lambda: self.wakeWordStateChanged.emit(False))
            except Exception as e:
                self.logger.error(f"Error stopping wake word detection: {e}")
                QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Error stopping wake word detection: {e}"))
        
        asyncio.run_coroutine_threadsafe(stop_wake_word_task(), self.loop)
    
    @Slot(str)
    def speak(self, text: str):
        """Convert text to speech and play it."""
        if not self.is_initialized:
            self.errorOccurred.emit("Voice system not initialized")
            return
            
        if self.is_speaking:
            self.logger.warning("Already speaking, ignoring request")
            return
            
        # Create a task to speak
        async def speak_task():
            try:
                self.is_speaking = True
                QTimer.singleShot(0, lambda: self.speakingStateChanged.emit(True))
                
                success = await self.voice_system.speak(text)
                
                self.is_speaking = False
                QTimer.singleShot(0, lambda: self.speakingStateChanged.emit(False))
                QTimer.singleShot(0, lambda: self.speechCompleted.emit())
                
                if not success:
                    QTimer.singleShot(0, lambda: self.errorOccurred.emit("Failed to speak text"))
            except Exception as e:
                self.logger.error(f"Error during speech: {e}")
                self.is_speaking = False
                QTimer.singleShot(0, lambda: self.speakingStateChanged.emit(False))
                QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Speech error: {e}"))
        
        asyncio.run_coroutine_threadsafe(speak_task(), self.loop)
    
    @Slot(bool)
    def toggle_local_whisper(self, use_local: bool):
        """Toggle between local Whisper model and API."""
        if not self.is_initialized:
            self.errorOccurred.emit("Voice system not initialized")
            return
            
        # Create a task to toggle local Whisper
        async def toggle_task():
            try:
                success = await self.voice_system.toggle_local_whisper(use_local)
                if not success:
                    QTimer.singleShot(0, lambda: self.errorOccurred.emit(
                        f"Failed to {'enable' if use_local else 'disable'} local Whisper"
                    ))
            except Exception as e:
                self.logger.error(f"Error toggling local Whisper: {e}")
                QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Error toggling local Whisper: {e}"))
        
        asyncio.run_coroutine_threadsafe(toggle_task(), self.loop)
    
    @Slot(str)
    def set_tts_voice(self, voice: str):
        """Set the TTS voice/model to use."""
        if not self.is_initialized:
            self.errorOccurred.emit("Voice system not initialized")
            return
            
        # Create a task to set TTS voice
        async def set_voice_task():
            try:
                success = await self.voice_system.set_tts_voice(voice)
                if not success:
                    QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Failed to set voice: {voice}"))
            except Exception as e:
                self.logger.error(f"Error setting TTS voice: {e}")
                QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Error setting TTS voice: {e}"))
        
        asyncio.run_coroutine_threadsafe(set_voice_task(), self.loop)
    
    @Slot(str)
    def set_whisper_model_size(self, model_size: str):
        """Set the Whisper model size for local processing."""
        if not self.is_initialized:
            self.errorOccurred.emit("Voice system not initialized")
            return
            
        # Create a task to set Whisper model size
        async def set_model_size_task():
            try:
                success = await self.voice_system.set_whisper_model_size(model_size)
                if not success:
                    QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Failed to set model size: {model_size}"))
            except Exception as e:
                self.logger.error(f"Error setting Whisper model size: {e}")
                QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Error setting Whisper model size: {e}"))
        
        asyncio.run_coroutine_threadsafe(set_model_size_task(), self.loop)
    
    @Slot(float)
    def set_wake_word_sensitivity(self, sensitivity: float):
        """Set the wake word detection sensitivity."""
        if not self.is_initialized:
            self.errorOccurred.emit("Voice system not initialized")
            return
            
        # Create a task to set wake word sensitivity
        async def set_sensitivity_task():
            try:
                success = await self.voice_system.set_wake_word_sensitivity(sensitivity)
                if not success:
                    QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Failed to set wake word sensitivity: {sensitivity}"))
            except Exception as e:
                self.logger.error(f"Error setting wake word sensitivity: {e}")
                QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Error setting wake word sensitivity: {e}"))
        
        asyncio.run_coroutine_threadsafe(set_sensitivity_task(), self.loop)
    
    @Slot(list)
    def set_active_wake_words(self, wake_words: List[str]):
        """Set which wake words to listen for."""
        if not self.is_initialized:
            self.errorOccurred.emit("Voice system not initialized")
            return
            
        # Create a task to set active wake words
        async def set_wake_words_task():
            try:
                success = await self.voice_system.set_active_wake_words(wake_words)
                if not success:
                    QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Failed to set active wake words: {wake_words}"))
            except Exception as e:
                self.logger.error(f"Error setting active wake words: {e}")
                QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Error setting active wake words: {e}"))
        
        asyncio.run_coroutine_threadsafe(set_wake_words_task(), self.loop)
    
    @Slot()
    def get_available_wake_words(self, callback: Callable[[List[str]], None]):
        """Get available wake words."""
        if not self.is_initialized:
            self.errorOccurred.emit("Voice system not initialized")
            callback([])
            return
            
        # Create a task to get available wake words
        async def get_wake_words_task():
            try:
                available_words = await self.voice_system.get_available_wake_words()
                # Call the callback on the main thread
                QTimer.singleShot(0, lambda: callback(available_words))
            except Exception as e:
                self.logger.error(f"Error getting available wake words: {e}")
                QTimer.singleShot(0, lambda: self.errorOccurred.emit(f"Error getting available wake words: {e}"))
                QTimer.singleShot(0, lambda: callback([]))
        
        asyncio.run_coroutine_threadsafe(get_wake_words_task(), self.loop)
    
    @Slot()
    def shutdown(self):
        """Clean up resources and shutdown the voice system."""
        self.logger.info("Shutting down Voice Controller")
        
        # Stop the background timer
        self.background_timer.stop()
        
        # Stop listening and wake word detection if active
        if self.is_listening:
            self.stop_listening()
            
        if self.is_wake_word_active:
            self.stop_wake_word_detection()
        
        # Shutdown the voice system
        if self.is_initialized and self.loop is not None:
            # Create a task to shutdown
            async def shutdown_task():
                try:
                    self.voice_system.shutdown()
                    self.is_initialized = False
                    self.loop.stop()
                except Exception as e:
                    self.logger.error(f"Error during shutdown: {e}")
            
            asyncio.run_coroutine_threadsafe(shutdown_task(), self.loop)
            
            # Wait for loop to stop (with timeout)
            import time
            start_time = time.time()
            while self.loop.is_running() and time.time() - start_time < 5:
                time.sleep(0.1)
        
        self.logger.info("Voice Controller shutdown complete") 