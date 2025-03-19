"""
OCR processor module for Jarvis.

This module provides advanced OCR processing capabilities and text extraction
utilities for the screen capture service.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image

try:
    import pytesseract
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
    # Check if tesseract is installed and configured
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        OCR_AVAILABLE = False
except ImportError:
    OCR_AVAILABLE = False
    # Define np for type annotations if it's not available
    import numpy as np

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Advanced OCR processing capabilities."""
    
    def __init__(self):
        """Initialize the OCR processor."""
        self.available = OCR_AVAILABLE
        self.language = "eng"  # Default language
        self.config = ""  # Additional tesseract config
        self.preprocessing_enabled = True
        
        if not self.available:
            logger.warning("OCR processing not available. Install pytesseract, "
                          "opencv-python, and ensure Tesseract is installed.")
    
    def process_image(self, image: Image.Image) -> str:
        """Process an image and extract text.
        
        Args:
            image: The image to process
            
        Returns:
            str: Extracted text or empty string if processing failed
        """
        if not self.available:
            return ""
            
        try:
            # Convert PIL image to numpy array if needed
            if isinstance(image, Image.Image):
                img_np = np.array(image)
            else:
                img_np = image
                
            # Apply preprocessing if enabled
            if self.preprocessing_enabled:
                img_np = self._preprocess_image(img_np)
            
            # Perform OCR
            text = pytesseract.image_to_string(
                img_np, 
                lang=self.language,
                config=self.config
            )
            
            # Clean up the text
            text = self._clean_text(text)
            
            return text
        
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            return ""
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results.
        
        Args:
            image: The image as numpy array
            
        Returns:
            np.ndarray: Preprocessed image
        """
        try:
            # Convert to grayscale if image has 3 channels
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 
                255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                11, 
                2
            )
            
            # Apply noise reduction
            denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
            
            return denoised
        
        except Exception as e:
            logger.error(f"Image preprocessing failed: {str(e)}")
            return image  # Return original image on error
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text for better quality.
        
        Args:
            text: The raw OCR text
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
            
        # Replace multiple newlines with a single one
        text = re.sub(r'\n+', '\n', text)
        
        # Remove strange characters and unusual patterns
        text = re.sub(r'[^\x00-\x7F]+', '', text)  # Remove non-ASCII
        
        # Trim whitespace
        text = text.strip()
        
        return text
    
    def get_text_blocks(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Extract text blocks with position information.
        
        Args:
            image: The image to process
            
        Returns:
            list: List of dicts with text and position data
        """
        if not self.available:
            return []
            
        try:
            # Convert PIL image to numpy array if needed
            if isinstance(image, Image.Image):
                img_np = np.array(image)
            else:
                img_np = image
                
            # Get image dimensions
            h, w = img_np.shape[:2]
            
            # Get data including bounding boxes
            data = pytesseract.image_to_data(
                img_np, 
                lang=self.language,
                config=self.config,
                output_type=pytesseract.Output.DICT
            )
            
            # Process the data to get text blocks
            blocks = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                # Skip empty text
                if not data['text'][i].strip():
                    continue
                    
                # Get positional data
                x, y, width, height = (
                    data['left'][i],
                    data['top'][i],
                    data['width'][i],
                    data['height'][i]
                )
                
                # Calculate relative positions (0-1 range)
                rel_x = x / w
                rel_y = y / h
                rel_width = width / w
                rel_height = height / h
                
                # Add to blocks list
                blocks.append({
                    'text': data['text'][i],
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height,
                    'rel_x': rel_x,
                    'rel_y': rel_y,
                    'rel_width': rel_width,
                    'rel_height': rel_height,
                    'confidence': data['conf'][i]
                })
            
            return blocks
        
        except Exception as e:
            logger.error(f"Text block extraction failed: {str(e)}")
            return []
    
    def set_language(self, lang_code: str) -> None:
        """Set the OCR language.
        
        Args:
            lang_code: The language code (e.g., 'eng', 'fra', etc.)
        """
        self.language = lang_code
        logger.info(f"OCR language set to {lang_code}")
    
    def set_preprocessing(self, enabled: bool) -> None:
        """Enable or disable image preprocessing.
        
        Args:
            enabled: Whether preprocessing should be enabled
        """
        self.preprocessing_enabled = enabled
        logger.info(f"OCR preprocessing {'enabled' if enabled else 'disabled'}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the OCR processor.
        
        Returns:
            dict: Information about the processor state
        """
        info = {
            "available": self.available,
            "language": self.language,
            "preprocessing_enabled": self.preprocessing_enabled
        }
        
        # Add tesseract version if available
        if self.available:
            try:
                info["tesseract_version"] = pytesseract.get_tesseract_version()
            except Exception:
                info["tesseract_version"] = "unknown"
        
        return info


# Create a singleton instance
ocr_processor = OCRProcessor() 