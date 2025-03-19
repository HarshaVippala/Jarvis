"""
Language Model Service for Jarvis

This module provides a unified interface for language model functionality,
integrating both local models (via Ollama) and cloud models (via OpenAI).
"""
import logging
import threading
import time
import os
from typing import Dict, List, Optional, Any, Callable, Tuple, Union

from jarvis.brain.model_manager import model_manager, ModelInfo
from jarvis.brain.ollama_service import ollama_service
from jarvis.config.settings_manager import settings_manager

# Try to import OpenAI
try:
    import openai
    HAVE_OPENAI = True
except ImportError:
    HAVE_OPENAI = False

logger = logging.getLogger(__name__)

class LanguageModelService:
    """
    Service providing access to language models, both local and cloud-based.
    
    Handles:
    - Model selection based on settings
    - Registration with model manager
    - Unified interface for generating text
    - Fallback strategies
    """
    def __init__(self):
        """Initialize the language model service."""
        self._running = False
        self._lock = threading.RLock()
        self._preferred_model = "mistral:7b"  # Default preferred model
        self._openai_api_key = None
        self._openai_client = None
        self._use_local_models = True  # Default to local models
        
        # Register models with the model manager
        self._register_models()
    
    def start(self):
        """Start the language model service."""
        with self._lock:
            if self._running:
                return
                
            logger.info("Starting Language Model Service...")
            
            # Start Ollama service if using local models
            if self._use_local_models:
                ollama_service.start()
            
            # Initialize OpenAI client if API key is available
            if HAVE_OPENAI:
                self._init_openai()
            
            self._running = True
            logger.info("Language Model Service started")
    
    def stop(self):
        """Stop the language model service."""
        with self._lock:
            if not self._running:
                return
                
            logger.info("Stopping Language Model Service...")
            
            # Nothing to clean up specifically
                
            self._running = False
            logger.info("Language Model Service stopped")
    
    def _register_models(self):
        """Register available models with the model manager."""
        # Register Mistral 7B local model
        model_manager.register_model(ModelInfo(
            model_id="local.mistral.7b",
            model_type="llm",
            memory_required=7 * 1024,  # 7GB
            load_function=self._load_mistral,
            unload_function=None,  # No specific unload needed
            priority=10,  # High priority
            preload=settings_manager.is_feature_enabled("language_model")
        ))
        
        # Register OpenAI GPT-4 model if available
        if HAVE_OPENAI:
            model_manager.register_model(ModelInfo(
                model_id="openai.gpt4",
                model_type="llm",
                memory_required=0,  # Cloud model, no local memory
                load_function=self._load_openai,
                unload_function=None,  # No specific unload needed
                priority=5,  # Medium priority
                preload=False  # Don't preload
            ))
    
    def _load_mistral(self) -> Any:
        """
        Load the Mistral model via Ollama.
        
        Returns:
            A model handle (in this case, just the model name)
        """
        model_name = "mistral:7b"
        
        # Check if Ollama is available
        if not ollama_service.is_available():
            logger.warning("Ollama is not available, cannot load Mistral model")
            return None
        
        # Check if model exists, try to pull if not
        models = ollama_service.get_available_models()
        if not any(model.name == model_name for model in models):
            logger.info(f"Model {model_name} not found, pulling...")
            
            def progress_callback(status, current, total):
                # Log progress
                if total > 0:
                    percent = int(current / total * 100)
                    logger.info(f"Pulling {model_name}: {percent}% ({status})")
            
            success = ollama_service.pull_model(model_name, progress_callback)
            if not success:
                logger.error(f"Failed to pull model {model_name}")
                return None
        
        logger.info(f"Mistral model {model_name} ready for use")
        
        # Return the model name as the handle
        return model_name
    
    def _load_openai(self) -> Any:
        """
        Initialize the OpenAI client.
        
        Returns:
            The OpenAI client
        """
        if not HAVE_OPENAI:
            logger.warning("OpenAI package not installed, cannot use OpenAI models")
            return None
        
        # Check if API key is available
        if not self._openai_api_key:
            self._openai_api_key = os.environ.get("OPENAI_API_KEY")
            if not self._openai_api_key:
                logger.warning("OpenAI API key not found, cannot use OpenAI models")
                return None
        
        # Initialize client
        try:
            self._openai_client = openai.OpenAI(api_key=self._openai_api_key)
            logger.info("OpenAI client initialized")
            return self._openai_client
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            return None
    
    def _init_openai(self):
        """Initialize OpenAI client if not already done."""
        if self._openai_client is None and HAVE_OPENAI:
            # Get API key from environment or settings
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                api_key = settings_manager.get_setting("openai.api_key")
            
            if api_key:
                self._openai_api_key = api_key
                try:
                    self._openai_client = openai.OpenAI(api_key=api_key)
                    logger.info("OpenAI client initialized")
                except Exception as e:
                    logger.error(f"Error initializing OpenAI client: {e}")
    
    def set_preferred_model(self, model_id: str) -> bool:
        """
        Set the preferred language model.
        
        Args:
            model_id: ID of the model to use
            
        Returns:
            True if the model was set successfully, False otherwise
        """
        with self._lock:
            # Check if model exists
            if model_id.startswith("local."):
                # For local models, check if Ollama supports it
                model_name = model_id.replace("local.", "")
                if not any(model.name == model_name for model in ollama_service.get_available_models()):
                    logger.warning(f"Model {model_id} not available in Ollama")
                    return False
            elif model_id.startswith("openai."):
                # For OpenAI models, check if we have API access
                if not HAVE_OPENAI or not self._openai_api_key:
                    logger.warning("OpenAI models not available (missing package or API key)")
                    return False
            else:
                logger.warning(f"Unknown model type: {model_id}")
                return False
            
            # Set the preferred model
            self._preferred_model = model_id
            logger.info(f"Preferred model set to {model_id}")
            return True
    
    def get_preferred_model(self) -> str:
        """Get the ID of the currently preferred model."""
        return self._preferred_model
    
    def set_use_local_models(self, use_local: bool) -> None:
        """
        Set whether to prefer local models over cloud models.
        
        Args:
            use_local: Whether to use local models
        """
        with self._lock:
            self._use_local_models = use_local
            logger.info(f"Use local models: {use_local}")
    
    def use_local_models(self) -> bool:
        """Check if local models are being used."""
        return self._use_local_models
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get a list of available language models.
        
        Returns:
            List of model info dictionaries
        """
        models = []
        
        # Add local models
        if ollama_service.is_available():
            for model in ollama_service.get_available_models():
                models.append({
                    "id": f"local.{model.name}",
                    "name": model.name,
                    "type": "local",
                    "parameter_size": model.parameter_size,
                    "quantization": model.quantization_level,
                    "memory_required": model.memory_estimate
                })
        
        # Add OpenAI models
        if HAVE_OPENAI and self._openai_api_key:
            models.append({
                "id": "openai.gpt4",
                "name": "GPT-4",
                "type": "cloud",
                "parameter_size": "Unknown",
                "quantization": "None",
                "memory_required": 0
            })
            
            models.append({
                "id": "openai.gpt4o",
                "name": "GPT-4o",
                "type": "cloud",
                "parameter_size": "Unknown",
                "quantization": "None",
                "memory_required": 0
            })
            
            models.append({
                "id": "openai.gpt35turbo",
                "name": "GPT-3.5 Turbo",
                "type": "cloud",
                "parameter_size": "Unknown",
                "quantization": "None",
                "memory_required": 0
            })
        
        return models
    
    def generate_text(self, prompt: str, 
                     system_prompt: Optional[str] = None,
                     model_id: Optional[str] = None,
                     max_tokens: int = 500,
                     temperature: float = 0.7,
                     stream: bool = False,
                     callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """
        Generate text using a language model.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            model_id: ID of the model to use (defaults to preferred model)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            stream: Whether to stream the response
            callback: Function to call with each chunk when streaming
            
        Returns:
            Generated text, or None if an error occurred
        """
        with self._lock:
            # Use preferred model if none specified
            if model_id is None:
                model_id = self._preferred_model
            
            # Handle local models
            if model_id.startswith("local."):
                return self._generate_with_local_model(
                    model_id.replace("local.", ""),
                    prompt,
                    system_prompt,
                    max_tokens,
                    temperature,
                    stream,
                    callback
                )
            
            # Handle OpenAI models
            elif model_id.startswith("openai."):
                return self._generate_with_openai(
                    model_id.replace("openai.", ""),
                    prompt,
                    system_prompt,
                    max_tokens,
                    temperature,
                    stream,
                    callback
                )
            
            else:
                logger.warning(f"Unknown model type: {model_id}")
                return None
    
    def _generate_with_local_model(self, model_name: str, prompt: str,
                                  system_prompt: Optional[str] = None,
                                  max_tokens: int = 500,
                                  temperature: float = 0.7,
                                  stream: bool = False,
                                  callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """
        Generate text using a local model via Ollama.
        
        Args:
            model_name: Name of the Ollama model
            prompt: User prompt
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            stream: Whether to stream the response
            callback: Function to call with each chunk when streaming
            
        Returns:
            Generated text, or None if an error occurred
        """
        # Check if Ollama is available
        if not ollama_service.is_available():
            logger.warning("Ollama is not available, cannot generate text")
            return None
        
        # Generate text
        return ollama_service.generate(
            model_name=model_name,
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream,
            callback=callback
        )
    
    def _generate_with_openai(self, model_name: str, prompt: str,
                             system_prompt: Optional[str] = None,
                             max_tokens: int = 500,
                             temperature: float = 0.7,
                             stream: bool = False,
                             callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """
        Generate text using OpenAI API.
        
        Args:
            model_name: Name of the OpenAI model
            prompt: User prompt
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            stream: Whether to stream the response
            callback: Function to call with each chunk when streaming
            
        Returns:
            Generated text, or None if an error occurred
        """
        if not HAVE_OPENAI or not self._openai_client:
            logger.warning("OpenAI not available, cannot generate text")
            return None
        
        # Map model ID to OpenAI model name
        openai_model = "gpt-3.5-turbo"  # Default
        if model_name == "gpt4":
            openai_model = "gpt-4"
        elif model_name == "gpt4o":
            openai_model = "gpt-4o"
        elif model_name == "gpt35turbo":
            openai_model = "gpt-3.5-turbo"
        
        # Prepare messages
        messages = []
        
        # Add system message if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add user message
        messages.append({"role": "user", "content": prompt})
        
        try:
            # Generate response
            if stream:
                return self._generate_with_openai_stream(
                    openai_model, messages, max_tokens, temperature, callback
                )
            else:
                response = self._openai_client.chat.completions.create(
                    model=openai_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {e}")
            return None
    
    def _generate_with_openai_stream(self, model_name: str, messages: List[Dict[str, str]],
                                    max_tokens: int, temperature: float,
                                    callback: Optional[Callable[[str], None]]) -> Optional[str]:
        """
        Generate text using OpenAI API with streaming.
        
        Args:
            model_name: OpenAI model name
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            callback: Function to call with each chunk
            
        Returns:
            Complete generated text, or None if an error occurred
        """
        try:
            # Start streaming response
            response = self._openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True
            )
            
            # Collect full response
            full_response = []
            
            # Process chunks
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response.append(content)
                    
                    # Call callback if provided
                    if callback:
                        callback(content)
            
            return "".join(full_response)
            
        except Exception as e:
            logger.error(f"Error streaming response from OpenAI: {e}")
            return None


# Create singleton instance
language_model_service = LanguageModelService() 