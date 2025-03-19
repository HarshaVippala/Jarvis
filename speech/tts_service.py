import os
import logging
import asyncio
import threading
import tempfile
import time
import numpy as np
import sounddevice as sd
from typing import Optional, Callable, Dict, Any, List, Tuple

class TTSService:
    """
    Text-to-speech service using Coqui TTS for local text-to-speech synthesis.
    Provides high-quality voice output with streaming capabilities.
    """
    
    def __init__(self, app_controller=None, model_name="tts_models/en/ljspeech/tacotron2-DDC"):
        self.logger = logging.getLogger(__name__)
        self.app_controller = app_controller
        self.model_name = model_name
        self.model = None
        self.vocoder = None
        self.is_initialized = False
        self.is_loading = False
        self.speaking = False
        self.streaming = True  # Whether to stream audio while generating
        self.download_path = os.path.expanduser("~/.cache/tts")
        
        # Default audio settings
        self.sample_rate = 22050  # Hz
        
        # Available voices/models
        self.available_models = {
            "female_standard": "tts_models/en/ljspeech/tacotron2-DDC",
            "male_standard": "tts_models/en/vctk/vits",
            "female_fast": "tts_models/en/ljspeech/fast_pitch",
            "multilingual": "tts_models/multilingual/multi-dataset/xtts_v2"
        }
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "total_processing_time": 0,
            "avg_processing_time": 0,
            "total_characters": 0,
            "chars_per_second": 0
        }
        
        self.logger.info(f"TTS Service initialized with model: {model_name}")
    
    async def initialize(self):
        """Initialize and load the TTS model."""
        if self.is_initialized:
            return True
            
        if self.is_loading:
            self.logger.info("TTS model is already loading")
            return False
            
        self.is_loading = True
        self.logger.info(f"Loading TTS model: {self.model_name}")
        
        try:
            # Use a thread for model loading to avoid blocking
            await self._load_model_in_thread()
            
            self.is_initialized = True
            self.is_loading = False
            self.logger.info("TTS Service initialized successfully")
            return True
        except Exception as e:
            self.is_loading = False
            self.logger.error(f"Failed to initialize TTS Service: {e}")
            return False
    
    async def _load_model_in_thread(self):
        """Load TTS model in a separate thread to avoid blocking."""
        # Define the model loading function
        def load_model():
            try:
                # Import here to avoid loading unnecessary dependencies
                from TTS.api import TTS
                
                # Ensure download directory exists
                os.makedirs(self.download_path, exist_ok=True)
                
                # Load the model
                self.model = TTS(
                    model_name=self.model_name,
                    progress_bar=False,
                    cache_dir=self.download_path
                )
                
                self.logger.info(f"TTS model loaded successfully: {self.model_name}")
                return True
            except Exception as e:
                self.logger.error(f"Error loading TTS model: {e}")
                return False
        
        # Start loading in a separate thread
        loading_thread = threading.Thread(target=load_model)
        loading_thread.daemon = True
        loading_thread.start()
        
        # Wait for model to load with timeout
        timeout = 60  # 60 seconds timeout
        start_time = time.time()
        while loading_thread.is_alive() and (time.time() - start_time < timeout):
            await asyncio.sleep(0.5)
        
        if loading_thread.is_alive():
            self.logger.warning(f"Model loading is taking longer than {timeout} seconds, continuing execution")
            return False
        
        return self.model is not None
    
    async def speak(self, text: str, voice_id: Optional[str] = None) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID/name to use (if supported by the model)
            
        Returns:
            True if successful, False otherwise
        """
        if self.speaking:
            self.logger.warning("Already speaking")
            return False
            
        if not self.is_initialized:
            if not await self.initialize():
                self.logger.error("Failed to initialize TTS model")
                return False
        
        self.speaking = True
        start_time = time.time()
        self.metrics["total_requests"] += 1
        self.metrics["total_characters"] += len(text)
        
        try:
            if self.streaming:
                return await self._speak_streaming(text, voice_id)
            else:
                return await self._speak_non_streaming(text, voice_id)
        finally:
            processing_time = time.time() - start_time
            self.metrics["total_processing_time"] += processing_time
            self.metrics["avg_processing_time"] = (
                self.metrics["total_processing_time"] / self.metrics["total_requests"]
            )
            self.metrics["chars_per_second"] = (
                self.metrics["total_characters"] / self.metrics["total_processing_time"]
            )
            self.speaking = False
    
    async def _speak_streaming(self, text: str, voice_id: Optional[str] = None) -> bool:
        """Generate and play speech in chunks for faster response time."""
        # Use for models that support streaming
        try:
            # Create a temporary file to store the audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # Define the TTS generation function for a thread
            def generate_audio():
                try:
                    # For models that support speaker IDs
                    kwargs = {}
                    if voice_id and self.model_name.startswith("tts_models/en/vctk"):
                        kwargs["speaker"] = voice_id
                    
                    # Generate and save audio
                    self.model.tts_to_file(
                        text=text,
                        file_path=temp_filename,
                        **kwargs
                    )
                    return True
                except Exception as e:
                    self.logger.error(f"Error generating TTS: {e}")
                    return False
            
            # Generate the audio in a thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, generate_audio)
            
            if not result:
                return False
                
            # Play the generated audio
            def play_audio():
                try:
                    import soundfile as sf
                    data, sample_rate = sf.read(temp_filename)
                    sd.play(data, sample_rate)
                    sd.wait()  # Wait until playback is finished
                    return True
                except Exception as e:
                    self.logger.error(f"Error playing audio: {e}")
                    return False
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_filename)
                    except Exception as e:
                        self.logger.error(f"Error removing temporary file: {e}")
            
            # Play the audio in a thread
            result = await loop.run_in_executor(None, play_audio)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in streaming TTS: {e}")
            return False
    
    async def _speak_non_streaming(self, text: str, voice_id: Optional[str] = None) -> bool:
        """Generate and play speech in a single operation."""
        try:
            # Define the TTS generation and playback function for a thread
            def generate_and_play():
                try:
                    # For models that support speaker IDs
                    kwargs = {}
                    if voice_id and self.model_name.startswith("tts_models/en/vctk"):
                        kwargs["speaker"] = voice_id
                    
                    # Generate audio array
                    wav = self.model.tts(text=text, **kwargs)
                    
                    # Play the generated audio
                    sd.play(wav, self.sample_rate)
                    sd.wait()  # Wait until playback is finished
                    return True
                except Exception as e:
                    self.logger.error(f"Error generating or playing TTS: {e}")
                    return False
            
            # Generate and play the audio in a thread
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, generate_and_play)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in non-streaming TTS: {e}")
            return False
    
    async def list_available_voices(self) -> List[str]:
        """List available voices for the current model."""
        if not self.is_initialized:
            if not await self.initialize():
                return []
        
        # For VCTK model that supports multiple speakers
        if self.model_name.startswith("tts_models/en/vctk"):
            try:
                speakers = getattr(self.model, "speakers", None)
                if speakers:
                    return list(speakers)
            except Exception as e:
                self.logger.error(f"Error getting voice list: {e}")
        
        # For other models that don't support multiple voices
        return ["default"]
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available TTS models/voices."""
        return self.available_models
    
    async def change_model(self, model_name: str) -> bool:
        """
        Change the TTS model.
        
        Args:
            model_name: Model name or key from available_models
            
        Returns:
            True if successful, False otherwise
        """
        # If a short name is provided, use it to look up the full model name
        if model_name in self.available_models:
            model_name = self.available_models[model_name]
        
        if model_name == self.model_name:
            return True
            
        self.model_name = model_name
        self.is_initialized = False
        self.model = None
        
        # Initialize with new model
        return await self.initialize()
    
    def set_streaming(self, enabled: bool) -> None:
        """Enable or disable audio streaming."""
        self.streaming = enabled
        self.logger.info(f"Audio streaming: {'enabled' if enabled else 'disabled'}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the TTS service."""
        return self.metrics
    
    def shutdown(self):
        """Clean up resources."""
        self.logger.info("Shutting down TTS Service")
        self.model = None
        self.vocoder = None 