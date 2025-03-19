import asyncio

class VoiceController:
    def start_wake_word_detection(self):
        """Start wake word detection."""
        if self.voice_system and not self.is_wake_word_active:
            try:
                # First ensure wake word detector is initialized
                asyncio.create_task(self._start_wake_word_detector())
                return True
            except Exception as e:
                self.logger.error(f"Error starting wake word detection: {e}")
                return False
        return False
        
    async def _start_wake_word_detector(self):
        """Initialize and start wake word detector."""
        if self.voice_system.wake_word_detector:
            # Initialize if needed
            if not self.voice_system.wake_word_detector.porcupine:
                await self.voice_system.wake_word_detector.initialize()
            
            # Start detection
            self.voice_system.wake_word_detector.start(callback=self._on_wake_word_detected)
            self.is_wake_word_active = True
            self.wakeWordStateChanged.emit(True) 