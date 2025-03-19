import os
import logging
import time
import threading
import tempfile
import asyncio
from typing import Optional, Callable, Dict, Any, Union

class WhisperService:
    """
    Service for speech-to-text using Whisper models.
    This version supports both the OpenAI Whisper API and local Whisper models.
    """
    
    def __init__(self, app_controller=None, use_local=False, model_size="tiny"):
        self.logger = logging.getLogger(__name__)
        self.app_controller = app_controller
        self.use_local = use_local
        self.model_size = model_size
        self.model = None
        self.is_initialized = False
        self.is_loading = False
        self.download_path = os.path.expanduser("~/.cache/whisper")
        self.api_key = None
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "total_processing_time": 0,
            "avg_processing_time": 0,
            "total_audio_duration": 0
        }
        
        self.logger.info(f"Whisper Service initialized (use_local={use_local}, model_size={model_size})")
    
    async def initialize(self):
        """Initialize the Whisper service and load models if using local mode."""
        if self.is_initialized:
            return True
            
        if self.is_loading:
            self.logger.info("Whisper model is already loading")
            return False
            
        self.is_loading = True
        
        try:
            if self.use_local:
                # For local model initialization
                await self._initialize_local_whisper()
            else:
                # For API mode, just check if API key is available
                await self._initialize_api_mode()
                
            self.is_initialized = True
            self.is_loading = False
            self.logger.info("Whisper Service initialized successfully")
            return True
        except Exception as e:
            self.is_loading = False
            self.logger.error(f"Failed to initialize Whisper Service: {e}")
            return False
    
    async def _initialize_local_whisper(self):
        """Initialize the local Whisper model."""
        self.logger.info(f"Loading local Whisper model: {self.model_size}")
        
        def load_model():
            try:
                import whisper
                from whisper.utils import get_writer
                import torch
                
                # Ensure download directory exists
                os.makedirs(self.download_path, exist_ok=True)
                
                # Detect device (use CUDA if available, otherwise default to CPU)
                device = "cuda" if torch.cuda.is_available() else "cpu"
                if device == "cuda":
                    self.logger.info("Using GPU for Whisper model")
                else:
                    self.logger.info("Using CPU for Whisper model")
                
                # For Apple Silicon, we can use MPS if available
                if device == "cpu" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    device = "mps"
                    self.logger.info("Using Apple MPS (Metal Performance Shaders) for Whisper model")
                
                # Load the model (this will download it if not already downloaded)
                self.model = whisper.load_model(
                    self.model_size,
                    device=device,
                    download_root=self.download_path
                )
                
                self.logger.info(f"Local Whisper model {self.model_size} loaded successfully")
                return True
            except Exception as e:
                self.logger.error(f"Error loading local Whisper model: {str(e)}")
                return False
        
        # Run the model loading in a separate thread to not block the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, load_model)
        return result
    
    async def _initialize_api_mode(self):
        """Initialize API mode by checking for API key."""
        # Get API key from settings manager or environment
        if self.app_controller and hasattr(self.app_controller, 'settings_manager'):
            self.api_key = self.app_controller.settings_manager.get_setting('openai_api_key')
        else:
            # Try to get from environment
            self.api_key = os.environ.get('OPENAI_API_KEY')
        
        if not self.api_key:
            self.logger.warning("OpenAI API key not found, Whisper API functionality will be limited")
            return False
            
        try:
            # Import openai to check if it's installed
            import openai
            return True
        except ImportError:
            self.logger.error("OpenAI package not installed, but required for API mode")
            return False
    
    async def transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file to text using either local Whisper model or OpenAI API.
        
        Args:
            audio_file_path: Path to the audio file to transcribe
            
        Returns:
            Dictionary with transcription results
        """
        if not os.path.exists(audio_file_path):
            self.logger.error(f"Audio file not found: {audio_file_path}")
            return {"error": "Audio file not found", "text": ""}
        
        start_time = time.time()
        self.metrics["total_requests"] += 1
        
        try:
            if self.use_local:
                return await self._transcribe_local(audio_file_path)
            else:
                return await self._transcribe_api(audio_file_path)
        finally:
            processing_time = time.time() - start_time
            self.metrics["total_processing_time"] += processing_time
            self.metrics["avg_processing_time"] = (
                self.metrics["total_processing_time"] / self.metrics["total_requests"]
            )
            self.logger.debug(f"Transcription completed in {processing_time:.2f} seconds")
    
    async def _transcribe_local(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio using the local Whisper model."""
        if not self.model:
            self.logger.error("Local Whisper model not initialized")
            return {"error": "Model not initialized"}
            
        def process_audio():
            try:
                import torch
                start_time = time.time()
                
                # Transcribe the audio file
                result = self.model.transcribe(
                    audio_file_path,
                    fp16=torch.cuda.is_available(),  # Use FP16 precision if on GPU
                    language="en",  # Specify language or use None for auto-detection
                    task="transcribe"
                )
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Update metrics
                self.metrics["total_requests"] += 1
                self.metrics["total_processing_time"] += processing_time
                self.metrics["avg_processing_time"] = (
                    self.metrics["total_processing_time"] / self.metrics["total_requests"]
                )
                
                # Get the audio duration if possible
                try:
                    import librosa
                    duration = librosa.get_duration(path=audio_file_path)
                    self.metrics["total_audio_duration"] += duration
                except Exception as e:
                    self.logger.warning(f"Could not determine audio duration: {str(e)}")
                
                self.logger.info(f"Transcription completed in {processing_time:.2f}s")
                
                # Return the transcription result
                return {
                    "text": result["text"].strip(),
                    "segments": result["segments"],
                    "language": result.get("language", "en"),
                    "processing_time": processing_time
                }
                
            except Exception as e:
                self.logger.error(f"Error in local transcription: {str(e)}")
                return {"error": str(e)}
        
        # Run transcription in a separate thread
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, process_audio)
        return result
    
    async def _transcribe_api(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio using OpenAI Whisper API."""
        if not self.api_key:
            if not await self._initialize_api_mode():
                return {"error": "OpenAI API key not available", "text": ""}
        
        try:
            import openai
            import asyncio
            
            # Set API key
            openai.api_key = self.api_key
            
            # Define function to call API (to use with executor)
            def call_api():
                try:
                    with open(audio_file_path, "rb") as audio_file:
                        response = openai.Audio.transcribe(
                            model="whisper-1",
                            file=audio_file
                        )
                    return response
                except Exception as e:
                    self.logger.error(f"OpenAI API error: {e}")
                    return {"error": str(e), "text": ""}
            
            # Run API call in a separate thread
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, call_api)
            
            if "text" in response:
                return {
                    "text": response["text"].strip(),
                    "language": response.get("language", "unknown"),
                    "duration": 0,  # API doesn't return duration
                    "segments": [],  # API doesn't return segments
                    "error": None
                }
            else:
                return {"error": "Unknown API response format", "text": ""}
                
        except ImportError:
            self.logger.error("OpenAI package not installed")
            return {"error": "OpenAI package not installed", "text": ""}
    
    def get_metrics(self) -> Dict[str, Union[int, float]]:
        """Get performance metrics for the Whisper service."""
        return self.metrics
    
    def set_model_size(self, model_size: str) -> bool:
        """
        Change the local Whisper model size.
        
        Args:
            model_size: One of "tiny", "base", "small", "medium", "large"
            
        Returns:
            True if successful, False otherwise
        """
        if not self.use_local:
            self.logger.warning("Cannot change model size in API mode")
            return False
            
        valid_sizes = ["tiny", "base", "small", "medium", "large"]
        if model_size not in valid_sizes:
            self.logger.error(f"Invalid model size: {model_size}. Must be one of {valid_sizes}")
            return False
            
        if model_size == self.model_size:
            return True
            
        self.model_size = model_size
        self.model = None
        self.is_initialized = False
        
        # Initialize with new model size
        asyncio.create_task(self.initialize())
        return True
    
    def toggle_mode(self, use_local: bool) -> bool:
        """
        Toggle between local model and API mode.
        
        Args:
            use_local: True for local model, False for API
            
        Returns:
            True if successful, False otherwise
        """
        if use_local == self.use_local:
            return True
            
        self.use_local = use_local
        self.model = None
        self.is_initialized = False
        
        # Initialize with new mode
        asyncio.create_task(self.initialize())
        return True
    
    def shutdown(self):
        """Clean up resources."""
        self.logger.info("Shutting down Whisper Service")
        # No specific cleanup needed for this service, but good to have
        self.model = None 