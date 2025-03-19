"""
Model Manager for Jarvis

This module provides centralized management of all AI models used by Jarvis,
handling loading, unloading, and optimization of models.
"""
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Callable
import os
import psutil
import queue

logger = logging.getLogger(__name__)

class ModelInfo:
    """Information about a model and its resource requirements."""
    def __init__(self, 
                model_id: str,
                model_type: str,
                memory_required: int,  # in MB
                load_function: Callable,
                unload_function: Optional[Callable] = None,
                priority: int = 0,
                preload: bool = False):
        """
        Initialize model information.
        
        Args:
            model_id: Unique identifier for the model
            model_type: Type of model (e.g., llm, whisper, tts)
            memory_required: Estimated memory required in MB
            load_function: Function to call to load the model
            unload_function: Function to call to unload the model (optional)
            priority: Loading priority (higher numbers = higher priority)
            preload: Whether to preload this model on startup
        """
        self.model_id = model_id
        self.model_type = model_type
        self.memory_required = memory_required
        self.load_function = load_function
        self.unload_function = unload_function
        self.priority = priority
        self.preload = preload
        self.loaded = False
        self.instance = None
        self.last_used = 0  # timestamp when the model was last used


class ModelManager:
    """
    Centralized manager for AI models in Jarvis.
    
    Handles:
    - Model registration and discovery
    - Model lifecycle (loading/unloading)
    - Resource monitoring and optimization
    - Model access and caching
    """
    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        self._model_types: Dict[str, List[str]] = {}  # type -> [model_ids]
        self._running = False
        self._stop_event = threading.Event()
        self._resource_monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self._load_queue = queue.PriorityQueue()  # (priority, model_id)
        self._load_thread = threading.Thread(target=self._process_load_queue, daemon=True)
        self._max_memory_percent = 70  # Default max memory usage (%)
        self._lock = threading.RLock()  # For thread safety
        
    def start(self):
        """Start the model manager and resource monitoring."""
        with self._lock:
            if self._running:
                return
                
            logger.info("Starting Model Manager...")
            self._running = True
            self._stop_event.clear()
            
            # Start resource monitoring thread
            self._resource_monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
            self._resource_monitor_thread.start()
            
            # Start load queue processing thread
            self._load_thread = threading.Thread(target=self._process_load_queue, daemon=True)
            self._load_thread.start()
            
            # Preload models marked for preloading
            self._preload_models()
            
            logger.info("Model Manager started")
    
    def stop(self):
        """Stop the model manager and unload all models."""
        with self._lock:
            if not self._running:
                return
                
            logger.info("Stopping Model Manager...")
            self._running = False
            self._stop_event.set()
            
            # Wait for threads to terminate
            if self._resource_monitor_thread.is_alive():
                self._resource_monitor_thread.join(timeout=2.0)
            
            if self._load_thread.is_alive():
                self._load_thread.join(timeout=2.0)
            
            # Unload all loaded models
            for model_id, model_info in self._models.items():
                if model_info.loaded and model_info.instance is not None:
                    try:
                        self._unload_model(model_id)
                    except Exception as e:
                        logger.error(f"Error unloading model {model_id}: {e}")
            
            logger.info("Model Manager stopped")
    
    def register_model(self, model_info: ModelInfo) -> None:
        """
        Register a model with the manager.
        
        Args:
            model_info: Information about the model
        """
        with self._lock:
            model_id = model_info.model_id
            model_type = model_info.model_type
            
            self._models[model_id] = model_info
            
            # Add to model type mapping
            if model_type not in self._model_types:
                self._model_types[model_type] = []
            
            if model_id not in self._model_types[model_type]:
                self._model_types[model_type].append(model_id)
            
            logger.info(f"Registered model: {model_id} (type: {model_type})")
    
    def get_model(self, model_id: str, load_if_needed: bool = True) -> Optional[Any]:
        """
        Get a model instance by ID.
        
        Args:
            model_id: ID of the model to get
            load_if_needed: Whether to load the model if it's not loaded
            
        Returns:
            The model instance, or None if the model is not available
        """
        with self._lock:
            if model_id not in self._models:
                logger.warning(f"Model not found: {model_id}")
                return None
            
            model_info = self._models[model_id]
            
            # If the model is not loaded and we should load it
            if not model_info.loaded and load_if_needed:
                logger.info(f"Model {model_id} not loaded, loading...")
                self._load_model(model_id)
            
            # Update last used timestamp
            if model_info.loaded:
                model_info.last_used = time.time()
                
            return model_info.instance
    
    def get_model_of_type(self, model_type: str, load_if_needed: bool = True) -> Optional[Any]:
        """
        Get the first available model of a specific type.
        
        Args:
            model_type: Type of model to get
            load_if_needed: Whether to load the model if it's not loaded
            
        Returns:
            The model instance, or None if no model of the specified type is available
        """
        with self._lock:
            if model_type not in self._model_types or not self._model_types[model_type]:
                logger.warning(f"No models of type {model_type} registered")
                return None
            
            # Get the first model of the specified type
            model_id = self._model_types[model_type][0]
            return self.get_model(model_id, load_if_needed)
    
    def list_models(self) -> List[str]:
        """Get a list of all registered model IDs."""
        with self._lock:
            return list(self._models.keys())
    
    def list_models_of_type(self, model_type: str) -> List[str]:
        """Get a list of all registered model IDs of a specific type."""
        with self._lock:
            return self._model_types.get(model_type, [])
    
    def is_model_loaded(self, model_id: str) -> bool:
        """Check if a model is loaded."""
        with self._lock:
            if model_id not in self._models:
                return False
            return self._models[model_id].loaded
    
    def set_max_memory_percent(self, percent: int) -> None:
        """
        Set the maximum memory usage as a percentage of system memory.
        
        Args:
            percent: Percentage of system memory to use (0-100)
        """
        if not (0 <= percent <= 100):
            raise ValueError("Percentage must be between 0 and 100")
            
        self._max_memory_percent = percent
        logger.info(f"Set maximum memory usage to {percent}%")
    
    def _load_model(self, model_id: str) -> bool:
        """
        Load a model.
        
        Args:
            model_id: ID of the model to load
            
        Returns:
            True if the model was loaded successfully, False otherwise
        """
        if model_id not in self._models:
            logger.warning(f"Cannot load unknown model: {model_id}")
            return False
            
        model_info = self._models[model_id]
        
        # If model is already loaded, just update timestamp
        if model_info.loaded:
            model_info.last_used = time.time()
            return True
            
        logger.info(f"Loading model: {model_id}")
        try:
            # Call the model's load function
            start_time = time.time()
            model_instance = model_info.load_function()
            load_time = time.time() - start_time
            
            # Update model info
            model_info.instance = model_instance
            model_info.loaded = True
            model_info.last_used = time.time()
            
            logger.info(f"Model {model_id} loaded successfully in {load_time:.2f} seconds")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {e}")
            return False
    
    def _unload_model(self, model_id: str) -> bool:
        """
        Unload a model.
        
        Args:
            model_id: ID of the model to unload
            
        Returns:
            True if the model was unloaded successfully, False otherwise
        """
        if model_id not in self._models:
            logger.warning(f"Cannot unload unknown model: {model_id}")
            return False
            
        model_info = self._models[model_id]
        
        # If model is not loaded, nothing to do
        if not model_info.loaded:
            return True
            
        logger.info(f"Unloading model: {model_id}")
        try:
            # Call the model's unload function if available
            if model_info.unload_function is not None:
                model_info.unload_function(model_info.instance)
            
            # Update model info
            model_info.instance = None
            model_info.loaded = False
            
            logger.info(f"Model {model_id} unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading model {model_id}: {e}")
            return False
    
    def _preload_models(self) -> None:
        """Preload all models marked for preloading."""
        for model_id, model_info in self._models.items():
            if model_info.preload:
                # Add to load queue with priority
                self._load_queue.put((-model_info.priority, model_id))
                logger.info(f"Queued preload for model: {model_id}")
    
    def _process_load_queue(self) -> None:
        """Process the load queue, loading models in priority order."""
        while self._running and not self._stop_event.is_set():
            try:
                # Get the next model to load from the queue
                try:
                    _, model_id = self._load_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Check if we're still running
                if not self._running or self._stop_event.is_set():
                    break
                
                # Check if we have enough memory
                if not self._check_memory_available(model_id):
                    # Not enough memory, try to free some
                    freed = self._free_memory_for_model(model_id)
                    if not freed:
                        # Could not free enough memory, put back in queue with lower priority
                        model_info = self._models[model_id]
                        self._load_queue.put((-(model_info.priority - 10), model_id))
                        logger.warning(f"Insufficient memory for model {model_id}, requeued with lower priority")
                        continue
                
                # Load the model
                success = self._load_model(model_id)
                if not success:
                    logger.error(f"Failed to load model {model_id}")
                
                # Mark the task as done
                self._load_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in load queue processing: {e}")
                time.sleep(1.0)  # Avoid tight loop on error
    
    def _monitor_resources(self) -> None:
        """Monitor system resources and unload models if memory usage is too high."""
        check_interval = 30  # seconds
        
        while self._running and not self._stop_event.is_set():
            try:
                # Get current memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                
                # If memory usage is too high, unload some models
                if memory_percent > self._max_memory_percent:
                    logger.warning(f"Memory usage is high ({memory_percent}%), unloading unused models")
                    self._unload_least_used_models()
                
                # Wait for next check
                for _ in range(check_interval):
                    if not self._running or self._stop_event.is_set():
                        break
                    time.sleep(1.0)
                    
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                time.sleep(check_interval)  # Still sleep on error
    
    def _check_memory_available(self, model_id: str) -> bool:
        """
        Check if there is enough memory available to load a model.
        
        Args:
            model_id: ID of the model to check
            
        Returns:
            True if there is enough memory available, False otherwise
        """
        if model_id not in self._models:
            return False
            
        model_info = self._models[model_id]
        
        # Get current memory usage
        memory = psutil.virtual_memory()
        available_mb = memory.available / (1024 * 1024)  # Convert to MB
        
        # Check if we have enough memory
        return available_mb >= model_info.memory_required
    
    def _free_memory_for_model(self, model_id: str) -> bool:
        """
        Try to free enough memory to load a model by unloading other models.
        
        Args:
            model_id: ID of the model that needs memory
            
        Returns:
            True if enough memory was freed, False otherwise
        """
        if model_id not in self._models:
            return False
            
        model_info = self._models[model_id]
        memory_needed = model_info.memory_required
        
        # Get current memory usage
        memory = psutil.virtual_memory()
        available_mb = memory.available / (1024 * 1024)  # Convert to MB
        
        if available_mb >= memory_needed:
            return True  # Already enough memory
            
        # Sort loaded models by last used time (oldest first)
        loaded_models = [(m_id, m_info) for m_id, m_info in self._models.items() 
                        if m_info.loaded and m_id != model_id]
        loaded_models.sort(key=lambda x: x[1].last_used)
        
        # Unload models until we have enough memory
        memory_freed = 0
        for unload_id, unload_info in loaded_models:
            success = self._unload_model(unload_id)
            if success:
                memory_freed += unload_info.memory_required
                
                # Check if we have enough memory now
                memory = psutil.virtual_memory()
                available_mb = memory.available / (1024 * 1024)
                if available_mb >= memory_needed:
                    return True
        
        return False  # Could not free enough memory
    
    def _unload_least_used_models(self) -> None:
        """Unload the least recently used models to free memory."""
        # Get current time
        now = time.time()
        
        # Sort loaded models by last used time (oldest first)
        loaded_models = [(m_id, m_info) for m_id, m_info in self._models.items() if m_info.loaded]
        loaded_models.sort(key=lambda x: x[1].last_used)
        
        # Unload models that haven't been used in a while
        timeout = 300  # 5 minutes
        for model_id, model_info in loaded_models:
            # Skip models that have been used recently
            if now - model_info.last_used < timeout:
                continue
                
            # Unload the model
            logger.info(f"Unloading unused model {model_id} (last used {now - model_info.last_used:.0f} seconds ago)")
            self._unload_model(model_id)
            
            # Check if memory usage is back to normal
            memory = psutil.virtual_memory()
            if memory.percent <= self._max_memory_percent:
                break


# Create singleton instance
model_manager = ModelManager() 