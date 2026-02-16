"""
Property-based tests for Image Preprocessor.

Tests universal properties across randomly generated inputs using Hypothesis.
"""

import io
import pytest
from PIL import Image
from hypothesis import given, strategies as st, settings, assume

from image_preprocessor import ImagePreprocessor
from models import UnsupportedFormatError, ImageTooSmallError


# Test settings - reduced for faster CI, increase for thorough testing
test_settings = settings(max_examples=20, deadline=None)


# ============================================================================
# Test Data Generators
# ============================================================================

def create_test_image(width: int, height: int, format: str = 'JPEG') -> bytes:
    """Create a test image with specified dimensions and format."""
    image = Image.new('RGB', (width, height), color='white')
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()


# Strategy for valid image dimensions (above minimum, capped for speed)
valid_dimensions = st.tuples(
    st.integers(min_value=480, max_value=800),
    st.integers(min_value=480, max_value=800)
)

# Strategy for small image dimensions (below minimum)
small_dimensions = st.tuples(
    st.integers(min_value=100, max_value=479),
    st.integers(min_value=100, max_value=479)
)

# Strategy for supported formats
supported_formats = st.sampled_from(['JPEG', 'PNG'])


# ============================================================================
# Property 4: Image Format Standardization
# ============================================================================

class TestImageFormatStandardization:
    """
    Property 4: Image Format Standardization
    
    For any input image in a supported format (JPEG, PNG), the Image_Preprocessor
    SHALL output a valid JPEG image that can be successfully decoded.
    
    Validates: Requirements 2.1
    """
    
    @test_settings
    @given(dimensions=valid_dimensions, format=supported_formats)
    def test_output_is_valid_jpeg(self, dimensions, format):
        """
        Feature: face-matching-verification, Property 4: Image Format Standardization
        Validates: Requirements 2.1
        
        Output image is always valid JPEG regardless of input format.
        """
        width, height = dimensions
        input_bytes = create_test_image(width, height, format)
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(input_bytes, 'customer')
        
        # Output should be decodable as JPEG
        output_image = Image.open(io.BytesIO(result.image_bytes))
        assert output_image.format == 'JPEG'
    
    @test_settings
    @given(dimensions=valid_dimensions)
    def test_jpeg_input_produces_jpeg_output(self, dimensions):
        """JPEG input produces JPEG output."""
        width, height = dimensions
        input_bytes = create_test_image(width, height, 'JPEG')
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(input_bytes, 'customer')
        
        output_image = Image.open(io.BytesIO(result.image_bytes))
        assert output_image.format == 'JPEG'
    
    @test_settings
    @given(dimensions=valid_dimensions)
    def test_png_input_produces_jpeg_output(self, dimensions):
        """PNG input is converted to JPEG output."""
        width, height = dimensions
        input_bytes = create_test_image(width, height, 'PNG')
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(input_bytes, 'customer')
        
        output_image = Image.open(io.BytesIO(result.image_bytes))
        assert output_image.format == 'JPEG'


# ============================================================================
# Property 5: Aspect Ratio Preservation
# ============================================================================

class TestAspectRatioPreservation:
    """
    Property 5: Aspect Ratio Preservation
    
    For any input image with dimensions (w, h), after preprocessing the output
    image dimensions (w', h') SHALL satisfy: |w/h - w'/h'| < 0.01
    (aspect ratio preserved within 1% tolerance).
    
    Validates: Requirements 2.2
    """
    
    @test_settings
    @given(dimensions=valid_dimensions)
    def test_aspect_ratio_preserved(self, dimensions):
        """
        Feature: face-matching-verification, Property 5: Aspect Ratio Preservation
        Validates: Requirements 2.2
        
        Aspect ratio is preserved within 1% tolerance after preprocessing.
        """
        width, height = dimensions
        input_bytes = create_test_image(width, height, 'JPEG')
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(input_bytes, 'customer')
        
        # Calculate aspect ratios
        input_ratio = width / height
        output_width, output_height = result.dimensions
        output_ratio = output_width / output_height
        
        # Aspect ratio should be preserved within 1%
        assert abs(input_ratio - output_ratio) < 0.01
    
    @test_settings
    @given(
        width=st.integers(min_value=480, max_value=2000),
        height=st.integers(min_value=480, max_value=2000)
    )
    def test_aspect_ratio_for_various_ratios(self, width, height):
        """Aspect ratio preserved for various width/height combinations."""
        input_bytes = create_test_image(width, height, 'JPEG')
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(input_bytes, 'customer')
        
        input_ratio = width / height
        output_ratio = result.dimensions[0] / result.dimensions[1]
        
        assert abs(input_ratio - output_ratio) < 0.01


# ============================================================================
# Property 6: Quality Metrics Completeness
# ============================================================================

class TestQualityMetricsCompleteness:
    """
    Property 6: Quality Metrics Completeness
    
    For any successfully preprocessed image, the returned QualityMetrics SHALL
    contain brightness_score, sharpness_score, and face_confidence, all within
    the range [0, 100].
    
    Validates: Requirements 2.5
    """
    
    @test_settings
    @given(dimensions=valid_dimensions, format=supported_formats)
    def test_quality_metrics_present(self, dimensions, format):
        """
        Feature: face-matching-verification, Property 6: Quality Metrics Completeness
        Validates: Requirements 2.5
        
        All quality metrics are present after preprocessing.
        """
        width, height = dimensions
        input_bytes = create_test_image(width, height, format)
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(input_bytes, 'customer')
        
        metrics = result.quality_metrics
        
        # All required fields present
        assert hasattr(metrics, 'brightness_score')
        assert hasattr(metrics, 'sharpness_score')
        assert hasattr(metrics, 'face_confidence')
    
    @test_settings
    @given(dimensions=valid_dimensions)
    def test_brightness_in_valid_range(self, dimensions):
        """Brightness score is in range [0, 100]."""
        width, height = dimensions
        input_bytes = create_test_image(width, height, 'JPEG')
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(input_bytes, 'customer')
        
        assert 0 <= result.quality_metrics.brightness_score <= 100
    
    @test_settings
    @given(dimensions=valid_dimensions)
    def test_sharpness_in_valid_range(self, dimensions):
        """Sharpness score is in range [0, 100]."""
        width, height = dimensions
        input_bytes = create_test_image(width, height, 'JPEG')
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(input_bytes, 'customer')
        
        assert 0 <= result.quality_metrics.sharpness_score <= 100
    
    @test_settings
    @given(dimensions=valid_dimensions)
    def test_face_confidence_in_valid_range(self, dimensions):
        """Face confidence is in range [0, 100]."""
        width, height = dimensions
        input_bytes = create_test_image(width, height, 'JPEG')
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(input_bytes, 'customer')
        
        # Note: face_confidence is 0 until Rekognition DetectFaces is called
        assert 0 <= result.quality_metrics.face_confidence <= 100


# ============================================================================
# Additional Preprocessor Properties
# ============================================================================

class TestImageSizeValidation:
    """Tests for image size validation."""
    
    @test_settings
    @given(dimensions=small_dimensions)
    def test_small_images_rejected(self, dimensions):
        """Images below minimum size are rejected."""
        width, height = dimensions
        input_bytes = create_test_image(width, height, 'JPEG')
        
        preprocessor = ImagePreprocessor(min_size=480)
        
        with pytest.raises(ImageTooSmallError) as exc_info:
            preprocessor.preprocess(input_bytes, 'customer')
        
        assert exc_info.value.error_code == 'IMAGE_TOO_SMALL'
        assert exc_info.value.failed_source == 'customer'


class TestSourceTypeTracking:
    """Tests for source type tracking."""
    
    @test_settings
    @given(
        dimensions=valid_dimensions,
        source=st.sampled_from(['customer', 'id_document', 'iprs'])
    )
    def test_source_type_preserved(self, dimensions, source):
        """Source type is correctly preserved in result."""
        width, height = dimensions
        input_bytes = create_test_image(width, height, 'JPEG')
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(input_bytes, source)
        
        assert result.source_type.value == source


class TestOriginalFormatTracking:
    """Tests for original format tracking."""
    
    @test_settings
    @given(dimensions=valid_dimensions, format=supported_formats)
    def test_original_format_tracked(self, dimensions, format):
        """Original format is tracked in result."""
        width, height = dimensions
        input_bytes = create_test_image(width, height, format)
        
        preprocessor = ImagePreprocessor()
        result = preprocessor.preprocess(input_bytes, 'customer')
        
        assert result.original_format == format
