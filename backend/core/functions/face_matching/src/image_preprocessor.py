"""
Image Preprocessor for Face Matching Service

Standardizes images before comparison: format conversion, resizing, orientation correction.
"""

import io
from typing import Optional

from PIL import Image, ImageOps, ExifTags
import numpy as np
from aws_lambda_powertools import Logger

from models import (
    PreprocessedImage,
    QualityMetrics,
    ImageSource,
    ImageTooSmallError,
    UnsupportedFormatError,
    PreprocessingError,
)

logger = Logger()

# Configuration
MIN_IMAGE_SIZE = 480
MAX_IMAGE_SIZE = 4096
SUPPORTED_FORMATS = {'JPEG', 'PNG', 'JPG'}
OUTPUT_FORMAT = 'JPEG'
OUTPUT_QUALITY = 95


class ImagePreprocessor:
    """Preprocesses images for face comparison."""
    
    def __init__(self, min_size: int = MIN_IMAGE_SIZE):
        self.min_size = min_size
    
    def preprocess(self, image_bytes: bytes, source_type: str) -> PreprocessedImage:
        """
        Preprocess an image for face comparison.
        
        Args:
            image_bytes: Raw image bytes
            source_type: One of 'customer', 'id_document', 'iprs'
            
        Returns:
            PreprocessedImage with standardized bytes and quality metrics
            
        Raises:
            ImageTooSmallError: If image is below minimum resolution
            UnsupportedFormatError: If image format is not supported
            PreprocessingError: If preprocessing fails
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            original_format = image.format or 'UNKNOWN'
            
            # Validate format
            if original_format.upper() not in SUPPORTED_FORMATS:
                raise UnsupportedFormatError(source_type, original_format)
            
            # Get original dimensions
            original_dimensions = image.size
            
            # Validate minimum size
            if min(original_dimensions) < self.min_size:
                raise ImageTooSmallError(source_type, original_dimensions, self.min_size)
            
            # Apply orientation correction from EXIF
            image = self._correct_orientation(image)
            
            # Convert to RGB if necessary (handles RGBA, P mode, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (maintain aspect ratio)
            image = self._resize_image(image)
            
            # Calculate quality metrics
            quality_metrics = self.calculate_quality_metrics(image)
            
            # Convert to JPEG bytes
            output_bytes = self._convert_to_jpeg(image)
            
            return PreprocessedImage(
                image_bytes=output_bytes,
                source_type=ImageSource(source_type),
                quality_metrics=quality_metrics,
                original_format=original_format,
                dimensions=image.size
            )
            
        except (ImageTooSmallError, UnsupportedFormatError):
            raise
        except Exception as e:
            logger.error(f"Preprocessing failed for {source_type}: {e}")
            raise PreprocessingError(source_type, str(e))
    
    def _correct_orientation(self, image: Image.Image) -> Image.Image:
        """
        Apply orientation correction using EXIF data.
        
        Args:
            image: PIL Image object
            
        Returns:
            Orientation-corrected image
        """
        try:
            # Use ImageOps.exif_transpose for automatic orientation correction
            return ImageOps.exif_transpose(image)
        except Exception as e:
            logger.warning(f"Could not correct orientation: {e}")
            return image
    
    def _resize_image(self, image: Image.Image) -> Image.Image:
        """
        Resize image if it exceeds maximum size while maintaining aspect ratio.
        
        Args:
            image: PIL Image object
            
        Returns:
            Resized image (or original if within limits)
        """
        width, height = image.size
        
        if max(width, height) <= MAX_IMAGE_SIZE:
            return image
        
        # Calculate new dimensions maintaining aspect ratio
        if width > height:
            new_width = MAX_IMAGE_SIZE
            new_height = int(height * (MAX_IMAGE_SIZE / width))
        else:
            new_height = MAX_IMAGE_SIZE
            new_width = int(width * (MAX_IMAGE_SIZE / height))
        
        logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _convert_to_jpeg(self, image: Image.Image) -> bytes:
        """
        Convert image to JPEG format.
        
        Args:
            image: PIL Image object
            
        Returns:
            JPEG bytes
        """
        buffer = io.BytesIO()
        image.save(buffer, format=OUTPUT_FORMAT, quality=OUTPUT_QUALITY)
        return buffer.getvalue()
    
    def calculate_quality_metrics(self, image: Image.Image) -> QualityMetrics:
        """
        Calculate quality metrics for an image.
        
        Args:
            image: PIL Image object
            
        Returns:
            QualityMetrics with brightness, sharpness, face_confidence scores
        """
        # Convert to numpy array for calculations
        img_array = np.array(image)
        
        # Calculate brightness (average luminance)
        brightness = self._calculate_brightness(img_array)
        
        # Calculate sharpness (Laplacian variance)
        sharpness = self._calculate_sharpness(img_array)
        
        # Face confidence will be set by Rekognition DetectFaces
        # For now, return placeholder
        return QualityMetrics(
            brightness_score=brightness,
            sharpness_score=sharpness,
            face_confidence=0.0,  # Will be updated by face detection
            face_bounding_box=None
        )
    
    def _calculate_brightness(self, img_array: np.ndarray) -> float:
        """
        Calculate brightness score (0-100) based on average luminance.
        
        Args:
            img_array: Numpy array of image
            
        Returns:
            Brightness score 0-100
        """
        # Convert to grayscale using luminance formula
        if len(img_array.shape) == 3:
            gray = 0.299 * img_array[:,:,0] + 0.587 * img_array[:,:,1] + 0.114 * img_array[:,:,2]
        else:
            gray = img_array
        
        # Calculate mean brightness and normalize to 0-100
        mean_brightness = np.mean(gray)
        # Normalize: 0-255 -> 0-100
        return min(100.0, (mean_brightness / 255.0) * 100.0)
    
    def _calculate_sharpness(self, img_array: np.ndarray) -> float:
        """
        Calculate sharpness score (0-100) using Laplacian variance.
        
        Args:
            img_array: Numpy array of image
            
        Returns:
            Sharpness score 0-100
        """
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = 0.299 * img_array[:,:,0] + 0.587 * img_array[:,:,1] + 0.114 * img_array[:,:,2]
        else:
            gray = img_array.astype(float)
        
        # Simple Laplacian kernel
        laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
        
        # Apply convolution (simplified - just calculate variance of gradients)
        # Using numpy gradient as a simpler approach
        gx = np.gradient(gray, axis=1)
        gy = np.gradient(gray, axis=0)
        gradient_magnitude = np.sqrt(gx**2 + gy**2)
        
        # Variance of gradient magnitude indicates sharpness
        variance = np.var(gradient_magnitude)
        
        # Normalize to 0-100 (empirically determined scale)
        # Higher variance = sharper image
        sharpness = min(100.0, variance / 10.0)
        return sharpness
