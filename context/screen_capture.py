"""
Screen capture service for Jarvis.

This module provides functionality for capturing the screen and extracting
text content using OCR.
"""

import io
import os
import logging
import threading
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

try:
    import mss
    import numpy as np
    import cv2
    from PIL import Image
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = False
    # Check if tesseract is installed and configured
    try:
        pytesseract.get_tesseract_version()
        TESSERACT_AVAILABLE = True
    except Exception:
        pass
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)

class ScreenCaptureService:
    """Service for screen capture and OCR processing."""
    
    def __init__(self):
        """Initialize the screen capture service."""
        self.active = False
        self.capture_thread = None
        self.capture_interval = 2.0  # seconds
        self.last_capture_time = 0
        self.last_capture = None
        self.last_text = ""
        self.last_hash = None
        self.change_threshold = 0.10  # 10% change threshold
        self.cache_dir = Path.home() / ".jarvis" / "cache" / "screenshots"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for required dependencies
        if not MSS_AVAILABLE:
            logger.warning("Screen capture dependencies not available. "
                          "Install mss, numpy, opencv-python, and Pillow.")
        
        if not TESSERACT_AVAILABLE:
            logger.warning("Tesseract OCR not available. Install pytesseract "
                          "and ensure Tesseract is installed on your system.")
    
    def start(self) -> bool:
        """Start the screen capture service.
        
        Returns:
            bool: True if service started successfully, False otherwise
        """
        if self.active:
            logger.info("Screen capture service already running")
            return True
            
        if not MSS_AVAILABLE:
            logger.error("Cannot start screen capture: required dependencies missing")
            return False
            
        logger.info("Starting screen capture service")
        self.active = True
        self.capture_thread = threading.Thread(
            target=self._capture_loop,
            daemon=True
        )
        self.capture_thread.start()
        return True
    
    def stop(self) -> None:
        """Stop the screen capture service."""
        if not self.active:
            return
            
        logger.info("Stopping screen capture service")
        self.active = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
            self.capture_thread = None
    
    def _capture_loop(self) -> None:
        """Background thread for periodic screen capture."""
        logger.info("Screen capture loop started")
        
        while self.active:
            try:
                # Only capture if enough time has passed
                current_time = time.time()
                if current_time - self.last_capture_time >= self.capture_interval:
                    self._capture_screen()
                    self.last_capture_time = current_time
            except Exception as e:
                logger.error(f"Error in screen capture loop: {str(e)}")
            
            # Sleep a short time to prevent high CPU usage
            time.sleep(0.5)
        
        logger.info("Screen capture loop stopped")
    
    def _capture_screen(self) -> bool:
        """Capture the current screen.
        
        Returns:
            bool: True if capture was successful and had significant changes
        """
        if not MSS_AVAILABLE:
            return False
            
        try:
            # Capture the screen
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                
                # Convert to numpy array for OpenCV processing
                img_np = np.array(img)
                
                # Check for significant changes if we have a previous capture
                if self.last_capture is not None:
                    if not self._has_significant_changes(img_np):
                        return False
                
                # Store the current capture
                self.last_capture = img_np
                
                # Process with OCR if available
                if TESSERACT_AVAILABLE:
                    self._process_ocr(img)
                
                return True
                
        except Exception as e:
            logger.error(f"Screen capture failed: {str(e)}")
            return False
    
    def _has_significant_changes(self, current_img: np.ndarray) -> bool:
        """Check if the current image differs significantly from the last one.
        
        Args:
            current_img: The current screenshot as numpy array
            
        Returns:
            bool: True if significant changes detected
        """
        try:
            # Convert images to grayscale
            current_gray = cv2.cvtColor(current_img, cv2.COLOR_RGB2GRAY)
            last_gray = cv2.cvtColor(self.last_capture, cv2.COLOR_RGB2GRAY)
            
            # Calculate image hash for quick comparison
            current_hash = cv2.img_hash.averageHash(current_gray)[0]
            
            # If we have a previous hash, compare them
            if self.last_hash is not None:
                # Calculate hash difference (0 = identical, >0 = different)
                hash_diff = cv2.norm(current_hash, self.last_hash, cv2.NORM_HAMMING)
                
                # Normalize to 0-1 range (for 8-bit hash)
                hash_diff_norm = hash_diff / 64.0
                
                # Update the current hash
                self.last_hash = current_hash
                
                # Return true if change exceeds threshold
                return hash_diff_norm > self.change_threshold
            
            # First capture, store hash and return True
            self.last_hash = current_hash
            return True
            
        except Exception as e:
            logger.error(f"Error detecting screen changes: {str(e)}")
            return True  # On error, assume there are changes
    
    def _process_ocr(self, img: Image.Image) -> None:
        """Extract text from screenshot using OCR.
        
        Args:
            img: The screenshot as PIL Image
        """
        if not TESSERACT_AVAILABLE:
            return
            
        try:
            # Extract text using Tesseract
            text = pytesseract.image_to_string(img)
            
            # Only update if text has changed
            if text != self.last_text:
                self.last_text = text
                logger.debug(f"New screen text extracted ({len(text)} chars)")
                
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
    
    def get_screen_text(self) -> str:
        """Get the latest extracted text from the screen.
        
        Returns:
            str: The extracted text or empty string if not available
        """
        return self.last_text
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the screen capture service.
        
        Returns:
            dict: Information about the service state
        """
        return {
            "active": self.active,
            "dependencies_available": MSS_AVAILABLE,
            "ocr_available": TESSERACT_AVAILABLE,
            "last_capture_time": self.last_capture_time,
            "text_length": len(self.last_text) if self.last_text else 0,
            "capture_interval": self.capture_interval
        }
    
    def set_capture_interval(self, seconds: float) -> None:
        """Set the interval between screen captures.
        
        Args:
            seconds: The interval in seconds
        """
        self.capture_interval = max(0.5, float(seconds))
        logger.info(f"Screen capture interval set to {self.capture_interval} seconds")
    
    def set_change_threshold(self, threshold: float) -> None:
        """Set the threshold for detecting significant changes.
        
        Args:
            threshold: The threshold value (0.0-1.0)
        """
        self.change_threshold = max(0.01, min(1.0, float(threshold)))
        logger.info(f"Screen change threshold set to {self.change_threshold}")


# Create a singleton instance
screen_capture_service = ScreenCaptureService() 