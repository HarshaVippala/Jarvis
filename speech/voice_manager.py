import os
import logging
import asyncio
import threading
import tempfile
import wave
import pyaudio
import numpy as np
from typing import Optional, Callable, List, Dict, Any

class VoiceManager:
    """Centralized manager for voice-related functionality including speech recognition and synthesis."""
    
    def __init__(self, app_controller=None):
        self.logger = logging.getLogger(__name__)
        self.app_controller = app_controller
        self.listening = False
        self.speaking = False
        
        # Audio recording parameters
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Speech-to-text parameters
        self.whisper_service = None
        self.vad_threshold = 0.1  # Voice activity detection threshold (silence level)
        self.min_silence_duration = 1.0  # Seconds of silence to end recording
        
        # Text-to-speech parameters
        self.tts_service = None
        self.voice_id = "default"  # Default voice ID
        
        # Callbacks
        self.on_transcription_complete = None
        self.on_tts_complete = None
        
        # Threading
        self.recording_thread = None
        self.processing_thread = None
        
        self.logger.info("Voice Manager initialized")
    
    async def initialize(self):
        """Initialize voice-related services."""
        self.logger.info("Initializing voice services")
        # Will be used to initialize Whisper and TTS services once implemented
        return True
    
    def start_listening(self, callback: Callable[[str], None] = None):
        """Start listening for voice input."""
        if self.listening:
            self.logger.warning("Already listening")
            return False
        
        self.on_transcription_complete = callback
        self.listening = True
        
        self.stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        self.logger.info("Started listening")
        return True
    
    def stop_listening(self):
        """Stop listening for voice input."""
        if not self.listening:
            return
        
        self.listening = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        self.logger.info("Stopped listening")
    
    def _record_audio(self):
        """Record audio from microphone with voice activity detection."""
        self.logger.info("Recording audio...")
        frames = []
        silent_frames = 0
        silent_threshold = int(self.rate / self.chunk * self.min_silence_duration)
        
        while self.listening:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                frames.append(data)
                
                # Simple voice activity detection
                audio_data = np.frombuffer(data, dtype=np.int16)
                volume_norm = np.abs(audio_data).mean() / 32768.0
                
                if volume_norm < self.vad_threshold:
                    silent_frames += 1
                else:
                    silent_frames = 0
                
                # If enough silent frames, end recording
                if len(frames) > 10 and silent_frames > silent_threshold:
                    self.logger.info("Silence detected, processing speech")
                    audio_data = b''.join(frames)
                    self.process_audio(audio_data)
                    frames = []
                    silent_frames = 0
            except Exception as e:
                self.logger.error(f"Error recording audio: {e}")
                break
    
    def process_audio(self, audio_data):
        """Process recorded audio data and convert to text using Whisper."""
        if not audio_data:
            return
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(audio_data)
            
            temp_filename = temp_file.name
        
        # Process with Whisper (placeholder until WhisperService is implemented)
        def process_in_thread(filename):
            try:
                # Placeholder for Whisper processing
                transcription = "This is a placeholder transcription until Whisper is implemented"
                
                # Call the callback with the transcription
                if self.on_transcription_complete:
                    self.on_transcription_complete(transcription)
                
                # Clean up temporary file
                try:
                    os.unlink(filename)
                except Exception as e:
                    self.logger.error(f"Error removing temporary file: {e}")
            except Exception as e:
                self.logger.error(f"Error processing audio: {e}")
        
        self.processing_thread = threading.Thread(target=process_in_thread, args=(temp_filename,))
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    async def speak(self, text: str, voice_id: Optional[str] = None) -> bool:
        """Convert text to speech and play it."""
        if self.speaking:
            self.logger.warning("Already speaking")
            return False
        
        self.speaking = True
        
        try:
            # Placeholder for TTS functionality
            self.logger.info(f"TTS placeholder: '{text}'")
            # Would call self.tts_service.generate_speech(text, voice_id or self.voice_id)
            
            # Simulate speaking delay
            await asyncio.sleep(len(text) * 0.05)  # Rough estimate of speaking time
            
            if self.on_tts_complete:
                self.on_tts_complete()
                
            return True
        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {e}")
            return False
        finally:
            self.speaking = False
    
    def set_voice(self, voice_id: str):
        """Set the voice to use for text-to-speech."""
        self.voice_id = voice_id
        self.logger.info(f"Set voice to: {voice_id}")
    
    def adjust_vad_settings(self, threshold: float = None, silence_duration: float = None):
        """Adjust voice activity detection settings."""
        if threshold is not None:
            self.vad_threshold = max(0.0, min(1.0, threshold))
        
        if silence_duration is not None:
            self.min_silence_duration = max(0.2, silence_duration)
            
        self.logger.info(f"Adjusted VAD settings: threshold={self.vad_threshold}, silence_duration={self.min_silence_duration}")
    
    def shutdown(self):
        """Clean up resources."""
        self.logger.info("Shutting down Voice Manager")
        self.stop_listening()
        
        if self.audio:
            self.audio.terminate() 