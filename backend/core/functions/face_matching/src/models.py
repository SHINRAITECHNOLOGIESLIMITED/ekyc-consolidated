"""
Data Models for Face Matching Service

Defines request/response models, enums, and error classes for face matching operations.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime
import uuid


class ImageSource(Enum):
    """Source types for face images."""
    CUSTOMER = "customer"
    ID_DOCUMENT = "id_document"
    IPRS = "iprs"


class MatchStatus(Enum):
    """Overall verification outcome."""
    APPROVED = "APPROVED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    REJECTED = "REJECTED"


class ComparisonMode(Enum):
    """Comparison mode based on available images."""
    THREE_WAY = "3-way"
    TWO_WAY = "2-way"


# ============================================================================
# Request Models
# ============================================================================

@dataclass
class FaceMatchingRequest:
    """Request payload for face matching verification."""
    customer_id: str
    customer_photo_key: str  # S3 key for customer uploaded photo
    id_document_key: str     # S3 key for ID document
    iprs_id_number: str      # ID number for IPRS lookup
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.request_id is None:
            self.request_id = str(uuid.uuid4())


@dataclass
class QualityMetrics:
    """Image quality measurements."""
    brightness_score: float      # 0-100
    sharpness_score: float       # 0-100
    face_confidence: float       # 0-100 from Rekognition
    face_bounding_box: Optional[dict] = None  # {left, top, width, height}
    
    def to_dict(self) -> dict:
        return {
            'brightness_score': self.brightness_score,
            'sharpness_score': self.sharpness_score,
            'face_confidence': self.face_confidence,
            'face_bounding_box': self.face_bounding_box
        }


@dataclass
class PreprocessedImage:
    """Preprocessed image ready for comparison."""
    image_bytes: bytes
    source_type: ImageSource
    quality_metrics: QualityMetrics
    original_format: str
    dimensions: tuple[int, int]


# ============================================================================
# Response Models
# ============================================================================

@dataclass
class ComparisonResult:
    """Result of a single face comparison."""
    comparison_name: str         # e.g., "customer_vs_id_document"
    similarity_score: float      # 0-100
    confidence: float            # 0-100
    source_face_confidence: float = 0.0
    target_face_confidence: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            'comparison_name': self.comparison_name,
            'similarity_score': round(self.similarity_score, 2),
            'confidence': round(self.confidence, 2),
            'source_face_confidence': round(self.source_face_confidence, 2),
            'target_face_confidence': round(self.target_face_confidence, 2)
        }


@dataclass
class MatchDecision:
    """Overall match decision with reasoning."""
    status: MatchStatus
    reasons: list[str] = field(default_factory=list)  # Empty for APPROVED
    comparison_breakdown: dict[str, str] = field(default_factory=dict)  # comparison_name -> "PASS"/"FAIL"/"REVIEW"
    
    def to_dict(self) -> dict:
        return {
            'status': self.status.value,
            'reasons': self.reasons,
            'comparison_breakdown': self.comparison_breakdown
        }


@dataclass
class FaceMatchingResult:
    """Complete face matching verification result."""
    request_id: str
    customer_id: str
    match_status: MatchStatus
    comparison_mode: ComparisonMode
    comparisons: list[ComparisonResult]
    quality_metrics: dict[str, QualityMetrics]  # source_type -> metrics
    decision: MatchDecision
    thresholds_used: dict[str, float]  # approval, rejection thresholds
    processing_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            'request_id': self.request_id,
            'customer_id': self.customer_id,
            'match_status': self.match_status.value,
            'comparison_mode': self.comparison_mode.value,
            'comparisons': [c.to_dict() for c in self.comparisons],
            'quality_metrics': {k: v.to_dict() for k, v in self.quality_metrics.items()},
            'decision': self.decision.to_dict(),
            'thresholds_used': self.thresholds_used,
            'processing_time_ms': round(self.processing_time_ms, 2),
            'timestamp': self.timestamp.isoformat()
        }


# ============================================================================
# Error Classes
# ============================================================================

class FaceMatchingError(Exception):
    """Base error for face matching operations."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[dict] = None,
        failed_source: Optional[str] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.failed_source = failed_source
    
    def to_dict(self) -> dict:
        result = {
            'error_code': self.error_code,
            'message': self.message
        }
        if self.details:
            result['details'] = self.details
        if self.failed_source:
            result['failed_source'] = self.failed_source
        return result


class NoFaceDetectedError(FaceMatchingError):
    """Raised when no face is detected in an image."""
    
    def __init__(self, source: str, message: Optional[str] = None):
        super().__init__(
            error_code='NO_FACE_DETECTED',
            message=message or f'No face detected in {source} image',
            failed_source=source,
            details={'suggestion': 'Please upload a clear photo with your face visible'}
        )


class MultipleFacesError(FaceMatchingError):
    """Raised when multiple faces are detected in an image."""
    
    def __init__(self, source: str, face_count: int):
        super().__init__(
            error_code='MULTIPLE_FACES_DETECTED',
            message=f'Multiple faces ({face_count}) detected in {source} image',
            failed_source=source,
            details={
                'face_count': face_count,
                'suggestion': 'Please upload a photo with only one face'
            }
        )


class ImageTooSmallError(FaceMatchingError):
    """Raised when image resolution is below minimum."""
    
    def __init__(self, source: str, dimensions: tuple[int, int], min_size: int = 480):
        super().__init__(
            error_code='IMAGE_TOO_SMALL',
            message=f'Image resolution {dimensions[0]}x{dimensions[1]} is below minimum {min_size}x{min_size}',
            failed_source=source,
            details={
                'actual_dimensions': {'width': dimensions[0], 'height': dimensions[1]},
                'minimum_dimensions': {'width': min_size, 'height': min_size}
            }
        )


class UnsupportedFormatError(FaceMatchingError):
    """Raised when image format is not supported."""
    
    def __init__(self, source: str, format: str):
        super().__init__(
            error_code='UNSUPPORTED_FORMAT',
            message=f'Image format "{format}" is not supported',
            failed_source=source,
            details={
                'actual_format': format,
                'supported_formats': ['JPEG', 'PNG']
            }
        )


class PreprocessingError(FaceMatchingError):
    """Raised when image preprocessing fails."""
    
    def __init__(self, source: str, reason: str):
        super().__init__(
            error_code='PREPROCESSING_FAILED',
            message=f'Failed to preprocess {source} image: {reason}',
            failed_source=source
        )


class ComparisonError(FaceMatchingError):
    """Raised when Rekognition comparison fails."""
    
    def __init__(self, comparison_name: str, reason: str):
        super().__init__(
            error_code='COMPARISON_FAILED',
            message=f'Face comparison failed for {comparison_name}: {reason}',
            details={'comparison': comparison_name}
        )


class ValidationError(FaceMatchingError):
    """Raised when request validation fails."""
    
    def __init__(self, message: str, field_errors: Optional[dict] = None):
        super().__init__(
            error_code='VALIDATION_ERROR',
            message=message,
            details={'field_errors': field_errors} if field_errors else None
        )
