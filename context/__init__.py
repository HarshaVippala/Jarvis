"""
Context awareness module for Jarvis.

This module provides functionality for Jarvis to be aware of the user's
environment, including screen contents and application context.
"""

from jarvis.context.screen_capture import screen_capture_service
from jarvis.context.ocr_processor import ocr_processor
from jarvis.context.app_context import app_context_service
from jarvis.context.context_manager import context_manager

__all__ = [
    "screen_capture_service", 
    "ocr_processor", 
    "app_context_service", 
    "context_manager"
] 