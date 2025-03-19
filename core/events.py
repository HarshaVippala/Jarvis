"""
Event system for Jarvis.
This module provides an event bus for communication between components.
"""
import logging
from enum import Enum
from typing import Dict, List, Callable, Any

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of events that can be emitted in the system."""
    STREAMING_RESPONSE = "streaming_response"
    STREAMING_AUDIO = "streaming_audio"
    COMMAND_EXECUTED = "command_executed"
    ERROR_OCCURRED = "error_occurred"

class EventBus:
    """
    Simple event bus for communication between components.
    """
    
    def __init__(self):
        """Initialize the event bus."""
        self.listeners: Dict[EventType, List[Callable]] = {}
        
    def on(self, event_type: EventType, callback: Callable):
        """
        Register a callback for an event type.
        
        Args:
            event_type: The type of event to listen for
            callback: The function to call when the event is emitted
        """
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        
        self.listeners[event_type].append(callback)
        
    def off(self, event_type: EventType, callback: Callable):
        """
        Remove a callback for an event type.
        
        Args:
            event_type: The type of event
            callback: The callback to remove
        """
        if event_type in self.listeners:
            self.listeners[event_type].remove(callback)
            
    def emit(self, event_type: EventType, data: Any = None):
        """
        Emit an event to all registered listeners.
        
        Args:
            event_type: The type of event to emit
            data: The data to pass to the listeners
        """
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event listener: {str(e)}")

# Create a singleton instance of the event bus
event_bus = EventBus() 