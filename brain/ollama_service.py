"""
Ollama Service for Jarvis

This module provides integration with Ollama for running local language models,
enabling Jarvis to use models like Mistral and GPT4All locally.
"""
import logging
import requests
import json
import time
import os
import subprocess
import threading
import shutil
from typing import Dict, List, Optional, Any, Callable, Tuple
import platform

logger = logging.getLogger(__name__)

# Default Ollama endpoint
DEFAULT_OLLAMA_ENDPOINT = "http://localhost:11434"

class OllamaModel:
    """Information about an Ollama model."""
    def __init__(self, 
                name: str,
                size: int,  # size in bytes
                modified_at: int,  # unix timestamp
                parameter_size: str = "",  # e.g. "7B"
                quantization_level: str = ""):  # e.g. "Q4_0"
        """
        Initialize Ollama model info.
        
        Args:
            name: Model name (e.g., "mistral:7b")
            size: Model size in bytes
            modified_at: Last modified timestamp
            parameter_size: Size in billions of parameters (e.g. "7B")
            quantization_level: Quantization level if applicable
        """
        self.name = name
        self.size = size
        self.modified_at = modified_at
        self.parameter_size = parameter_size
        self.quantization_level = quantization_level
        
        # Calculate memory estimate based on parameter size
        self.memory_estimate = self._estimate_memory()
    
    def _estimate_memory(self) -> int:
        """
        Estimate memory usage in MB based on parameter size and quantization.
        
        Returns:
            Estimated memory usage in MB
        """
        # Extract parameter size if available
        param_size = 7  # default to 7B if unknown
        if self.parameter_size:
            try:
                # Extract number from parameter size (e.g. "7B" -> 7)
                param_size = int(''.join(filter(str.isdigit, self.parameter_size)))
            except (ValueError, TypeError):
                pass
        
        # Base memory estimate: Parameter size in billions * 4 bytes per parameter
        base_memory = param_size * 4 * 1024  # Convert to MB
        
        # Adjust for quantization
        if self.quantization_level:
            if "Q4" in self.quantization_level:
                # 4-bit quantization uses roughly half the memory
                return base_memory // 2
            elif "Q5" in self.quantization_level:
                # 5-bit quantization uses roughly 5/8 the memory
                return base_memory * 5 // 8
            elif "Q8" in self.quantization_level:
                # 8-bit quantization uses roughly the same memory as base
                return base_memory
        
        # Default case (no quantization info)
        return base_memory


class OllamaService:
    """
    Service for managing local language models through Ollama.
    
    Handles:
    - Checking Ollama installation
    - Pulling models
    - Running inference
    - Managing model lifecycle
    """
    def __init__(self, endpoint: str = DEFAULT_OLLAMA_ENDPOINT):
        """
        Initialize the Ollama service.
        
        Args:
            endpoint: Ollama API endpoint URL
        """
        self._endpoint = endpoint
        self._installed = False
        self._running = False
        self._ollama_process = None
        self._initialized = False
        self._lock = threading.RLock()
        self._active_models: Dict[str, Any] = {}  # Currently loaded models
    
    def start(self):
        """Start the Ollama service."""
        with self._lock:
            if self._running:
                return
                
            logger.info("Starting Ollama service...")
            
            # Check if Ollama is installed
            self._installed = self._check_installed()
            
            if not self._installed:
                logger.warning("Ollama is not installed. Please install it first.")
                return
            
            # Try to connect to Ollama
            if not self._check_running():
                # Start Ollama if not running
                self._start_ollama()
            
            self._running = True
            self._initialized = True
            logger.info("Ollama service started")
    
    def stop(self):
        """Stop the Ollama service."""
        with self._lock:
            if not self._running:
                return
                
            logger.info("Stopping Ollama service...")
            
            # Clean up active models
            self._active_models = {}
            
            # Stop the Ollama process if we started it
            if self._ollama_process is not None:
                logger.info("Stopping Ollama process...")
                try:
                    self._ollama_process.terminate()
                    self._ollama_process.wait(timeout=5)
                except Exception as e:
                    logger.error(f"Error stopping Ollama process: {e}")
                    try:
                        self._ollama_process.kill()
                    except Exception:
                        pass
                self._ollama_process = None
            
            self._running = False
            logger.info("Ollama service stopped")
    
    def is_available(self) -> bool:
        """
        Check if Ollama is available for use.
        
        Returns:
            True if Ollama is installed and running, False otherwise
        """
        with self._lock:
            if not self._initialized:
                self._installed = self._check_installed()
            
            if not self._installed:
                return False
            
            return self._check_running()
    
    def get_available_models(self) -> List[OllamaModel]:
        """
        Get a list of available Ollama models.
        
        Returns:
            List of available models
        """
        with self._lock:
            if not self.is_available():
                logger.warning("Ollama is not available")
                return []
            
            try:
                response = requests.get(f"{self._endpoint}/api/tags")
                if response.status_code == 200:
                    models = []
                    for model_data in response.json().get("models", []):
                        name = model_data.get("name", "")
                        size = model_data.get("size", 0)
                        modified_at = model_data.get("modified_at", 0)
                        
                        # Try to extract parameter size and quantization level from name
                        parameter_size = ""
                        quantization_level = ""
                        
                        # Example model names: 'mistral:7b', 'llama2:7b-q4_0'
                        if ':' in name:
                            _, model_variant = name.split(':', 1)
                            
                            # Extract parameter size (e.g., '7b')
                            if 'b' in model_variant.lower():
                                for part in model_variant.lower().split('-'):
                                    if 'b' in part and any(c.isdigit() for c in part):
                                        parameter_size = part.upper()
                                        break
                            
                            # Extract quantization (e.g., 'q4_0')
                            if 'q' in model_variant.lower():
                                for part in model_variant.lower().split('-'):
                                    if part.startswith('q') and '_' in part:
                                        quantization_level = part.upper()
                                        break
                        
                        model = OllamaModel(
                            name=name,
                            size=size,
                            modified_at=modified_at,
                            parameter_size=parameter_size,
                            quantization_level=quantization_level
                        )
                        models.append(model)
                    
                    return models
                else:
                    logger.error(f"Error getting Ollama models: {response.text}")
                    return []
            except Exception as e:
                logger.error(f"Error getting Ollama models: {e}")
                return []
    
    def pull_model(self, model_name: str, callback: Optional[Callable[[str, int, int], None]] = None) -> bool:
        """
        Pull an Ollama model.
        
        Args:
            model_name: Name of the model to pull (e.g., "mistral:7b")
            callback: Progress callback function (status, current, total)
            
        Returns:
            True if the model was pulled successfully, False otherwise
        """
        with self._lock:
            if not self.is_available():
                logger.warning("Ollama is not available")
                return False
            
            logger.info(f"Pulling Ollama model: {model_name}")
            
            try:
                # Start pull request in streaming mode for progress updates
                response = requests.post(
                    f"{self._endpoint}/api/pull",
                    json={"name": model_name},
                    stream=True
                )
                
                if response.status_code != 200:
                    logger.error(f"Error pulling model: {response.text}")
                    return False
                
                # Process streaming response for progress updates
                for line in response.iter_lines():
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        status = data.get("status", "")
                        
                        # Check if download is complete
                        if status == "success":
                            logger.info(f"Successfully pulled model {model_name}")
                            return True
                        
                        # Get progress information
                        current = data.get("completed", 0)
                        total = data.get("total", 0)
                        
                        # Call progress callback if provided
                        if callback and total > 0:
                            callback(status, current, total)
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in Ollama response: {line}")
                
                # If we get here, something went wrong
                logger.error(f"Failed to pull model {model_name}")
                return False
                
            except Exception as e:
                logger.error(f"Error pulling model {model_name}: {e}")
                return False
    
    def generate(self, model_name: str, prompt: str, 
                system_prompt: Optional[str] = None,
                max_tokens: int = 500,
                temperature: float = 0.7,
                stream: bool = False,
                callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """
        Generate text using an Ollama model.
        
        Args:
            model_name: Name of the model to use
            prompt: User prompt
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            stream: Whether to stream the response
            callback: Function to call with each chunk when streaming
            
        Returns:
            Generated text, or None if an error occurred
        """
        with self._lock:
            if not self.is_available():
                logger.warning("Ollama is not available")
                return None
            
            # Prepare request
            request_data = {
                "model": model_name,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            # Add system prompt if provided
            if system_prompt:
                request_data["system"] = system_prompt
            
            try:
                # Call Ollama API
                if stream:
                    return self._generate_stream(request_data, callback)
                else:
                    return self._generate_sync(request_data)
            except Exception as e:
                logger.error(f"Error generating text with model {model_name}: {e}")
                return None
    
    def _generate_sync(self, request_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate text synchronously.
        
        Args:
            request_data: Request data
            
        Returns:
            Generated text, or None if an error occurred
        """
        try:
            response = requests.post(
                f"{self._endpoint}/api/generate",
                json=request_data
            )
            
            if response.status_code != 200:
                logger.error(f"Error generating text: {response.text}")
                return None
            
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Error in sync generation: {e}")
            return None
    
    def _generate_stream(self, request_data: Dict[str, Any], 
                        callback: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """
        Generate text with streaming.
        
        Args:
            request_data: Request data
            callback: Function to call with each chunk
            
        Returns:
            Complete generated text, or None if an error occurred
        """
        full_response = []
        
        try:
            response = requests.post(
                f"{self._endpoint}/api/generate",
                json=request_data,
                stream=True
            )
            
            if response.status_code != 200:
                logger.error(f"Error generating text: {response.text}")
                return None
            
            for line in response.iter_lines():
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    chunk = data.get("response", "")
                    
                    # Add to full response
                    full_response.append(chunk)
                    
                    # Call callback if provided
                    if callback:
                        callback(chunk)
                    
                    # Check if this is the end
                    if data.get("done", False):
                        break
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in Ollama response: {line}")
            
            return "".join(full_response)
        
        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            return None
    
    def _check_installed(self) -> bool:
        """
        Check if Ollama is installed.
        
        Returns:
            True if Ollama is installed, False otherwise
        """
        try:
            # Look for the ollama executable
            ollama_path = shutil.which("ollama")
            if ollama_path:
                logger.info(f"Found Ollama at {ollama_path}")
                return True
            
            # Check common installation locations
            common_paths = []
            
            # Mac-specific paths
            if platform.system() == "Darwin":
                common_paths.extend([
                    "/usr/local/bin/ollama",
                    "/opt/homebrew/bin/ollama"
                ])
            
            # Linux-specific paths
            elif platform.system() == "Linux":
                common_paths.extend([
                    "/usr/bin/ollama",
                    "/usr/local/bin/ollama"
                ])
            
            # Windows-specific paths
            elif platform.system() == "Windows":
                common_paths.extend([
                    r"C:\Program Files\Ollama\ollama.exe",
                    r"C:\Ollama\ollama.exe"
                ])
            
            # Check each path
            for path in common_paths:
                if os.path.exists(path):
                    logger.info(f"Found Ollama at {path}")
                    return True
            
            logger.warning("Ollama not found. Please install it from https://ollama.com/")
            return False
            
        except Exception as e:
            logger.error(f"Error checking if Ollama is installed: {e}")
            return False
    
    def _check_running(self) -> bool:
        """
        Check if Ollama is running.
        
        Returns:
            True if Ollama is running, False otherwise
        """
        try:
            response = requests.get(f"{self._endpoint}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    def _start_ollama(self) -> bool:
        """
        Start the Ollama process.
        
        Returns:
            True if Ollama was started successfully, False otherwise
        """
        try:
            # Find the ollama executable
            ollama_path = shutil.which("ollama")
            if not ollama_path:
                logger.error("Cannot start Ollama: executable not found")
                return False
            
            # Start Ollama
            logger.info(f"Starting Ollama from {ollama_path}...")
            
            # Set up process with appropriate redirects
            self._ollama_process = subprocess.Popen(
                [ollama_path, "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for Ollama to start
            for _ in range(30):  # Wait up to 30 seconds
                if self._check_running():
                    logger.info("Ollama started successfully")
                    return True
                time.sleep(1)
            
            logger.error("Timed out waiting for Ollama to start")
            return False
            
        except Exception as e:
            logger.error(f"Error starting Ollama: {e}")
            return False
    
    def get_model_memory_estimate(self, model_name: str) -> int:
        """
        Get estimated memory usage for a model in MB.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Estimated memory usage in MB, or 0 if unknown
        """
        # Get available models
        models = self.get_available_models()
        
        # Find the requested model
        for model in models:
            if model.name == model_name:
                return model.memory_estimate
        
        # Default estimate if model not found
        # Base estimate on model name if possible (e.g., "mistral:7b")
        try:
            if "7b" in model_name.lower():
                return 7 * 1024  # 7GB
            elif "13b" in model_name.lower():
                return 13 * 1024  # 13GB
            elif "3b" in model_name.lower():
                return 3 * 1024  # 3GB
            else:
                return 7 * 1024  # Default to 7GB if unknown
        except Exception:
            return 7 * 1024  # Default to 7GB if unknown


# Create singleton instance
ollama_service = OllamaService() 