"""
Unit tests for Face Matching data models.

Tests dataclass instantiation, validation, enum values, and error classes.
"""

import pytest
from datetime import datetime

from models import (
    # Enums
    ImageSource,
    MatchStatus,
    ComparisonMode,
    # Request models
    FaceMatchingRequest,
    QualityMetrics,
    PreprocessedImage,
    # Response models
    ComparisonResult,
    MatchDecision,
    FaceMatchingResult,
    # Error classes
    FaceMatchingError,
    NoFaceDetectedError,
    MultipleFacesError,
    ImageTooSmallError,
    UnsupportedFormatError,
    PreprocessingError,
    ComparisonError,
    ValidationError,
)


class TestEnums:
    """Tests for enum definitions."""
    
    def test_image_source_values(self):
        """ImageSource enum has correct values."""
        assert ImageSource.CUSTOMER.value == "customer"
        assert ImageSource.ID_DOCUMENT.value == "id_document"
        assert ImageSource.IPRS.value == "iprs"
    
    def test_match_status_values(self):
        """MatchStatus enum has correct values."""
        assert MatchStatus.APPROVED.value == "APPROVED"
        assert MatchStatus.MANUAL_REVIEW.value == "MANUAL_REVIEW"
        assert MatchStatus.REJECTED.value == "REJECTED"
    
    def test_comparison_mode_values(self):
        """ComparisonMode enum has correct values."""
        assert ComparisonMode.THREE_WAY.value == "3-way"
        assert ComparisonMode.TWO_WAY.value == "2-way"


class TestFaceMatchingRequest:
    """Tests for FaceMatchingRequest dataclass."""
    
    def test_create_request_with_all_fields(self):
        """Create request with all required fields."""
        request = FaceMatchingRequest(
            customer_id="cust-123",
            customer_photo_key="photos/selfie.jpg",
            id_document_key="docs/id.pdf",
            iprs_id_number="12345678",
            request_id="req-456"
        )
        
        assert request.customer_id == "cust-123"
        assert request.customer_photo_key == "photos/selfie.jpg"
        assert request.id_document_key == "docs/id.pdf"
        assert request.iprs_id_number == "12345678"
        assert request.request_id == "req-456"
    
    def test_auto_generate_request_id(self):
        """Request ID is auto-generated if not provided."""
        request = FaceMatchingRequest(
            customer_id="cust-123",
            customer_photo_key="photos/selfie.jpg",
            id_document_key="docs/id.pdf",
            iprs_id_number="12345678"
        )
        
        assert request.request_id is not None
        assert len(request.request_id) == 36  # UUID format


class TestQualityMetrics:
    """Tests for QualityMetrics dataclass."""
    
    def test_create_quality_metrics(self):
        """Create quality metrics with all fields."""
        metrics = QualityMetrics(
            brightness_score=75.5,
            sharpness_score=82.3,
            face_confidence=99.1,
            face_bounding_box={'left': 0.1, 'top': 0.2, 'width': 0.5, 'height': 0.6}
        )
        
        assert metrics.brightness_score == 75.5
        assert metrics.sharpness_score == 82.3
        assert metrics.face_confidence == 99.1
        assert metrics.face_bounding_box is not None
    
    def test_to_dict(self):
        """QualityMetrics converts to dict correctly."""
        metrics = QualityMetrics(
            brightness_score=75.5,
            sharpness_score=82.3,
            face_confidence=99.1
        )
        
        result = metrics.to_dict()
        
        assert result['brightness_score'] == 75.5
        assert result['sharpness_score'] == 82.3
        assert result['face_confidence'] == 99.1


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""
    
    def test_create_comparison_result(self):
        """Create comparison result with all fields."""
        result = ComparisonResult(
            comparison_name="customer_vs_id_document",
            similarity_score=85.5,
            confidence=99.2,
            source_face_confidence=99.5,
            target_face_confidence=98.8
        )
        
        assert result.comparison_name == "customer_vs_id_document"
        assert result.similarity_score == 85.5
        assert result.confidence == 99.2
    
    def test_to_dict_rounds_scores(self):
        """ComparisonResult.to_dict rounds scores to 2 decimal places."""
        result = ComparisonResult(
            comparison_name="test",
            similarity_score=85.5678,
            confidence=99.2345
        )
        
        d = result.to_dict()
        
        assert d['similarity_score'] == 85.57
        assert d['confidence'] == 99.23


class TestMatchDecision:
    """Tests for MatchDecision dataclass."""
    
    def test_approved_decision(self):
        """Create approved decision with empty reasons."""
        decision = MatchDecision(
            status=MatchStatus.APPROVED,
            reasons=[],
            comparison_breakdown={
                'customer_vs_id_document': 'PASS',
                'customer_vs_iprs': 'PASS',
                'id_document_vs_iprs': 'PASS'
            }
        )
        
        assert decision.status == MatchStatus.APPROVED
        assert len(decision.reasons) == 0
    
    def test_rejected_decision_has_reasons(self):
        """Rejected decision includes reasons."""
        decision = MatchDecision(
            status=MatchStatus.REJECTED,
            reasons=['customer_vs_id_document: score 45.0% is below rejection threshold'],
            comparison_breakdown={'customer_vs_id_document': 'FAIL'}
        )
        
        assert decision.status == MatchStatus.REJECTED
        assert len(decision.reasons) > 0
    
    def test_to_dict(self):
        """MatchDecision converts to dict correctly."""
        decision = MatchDecision(
            status=MatchStatus.MANUAL_REVIEW,
            reasons=['Score in review range'],
            comparison_breakdown={'test': 'REVIEW'}
        )
        
        d = decision.to_dict()
        
        assert d['status'] == 'MANUAL_REVIEW'
        assert 'Score in review range' in d['reasons']


class TestFaceMatchingResult:
    """Tests for FaceMatchingResult dataclass."""
    
    def test_create_full_result(self):
        """Create complete face matching result."""
        result = FaceMatchingResult(
            request_id="req-123",
            customer_id="cust-456",
            match_status=MatchStatus.APPROVED,
            comparison_mode=ComparisonMode.THREE_WAY,
            comparisons=[
                ComparisonResult("customer_vs_id_document", 85.0, 99.0),
                ComparisonResult("customer_vs_iprs", 82.0, 98.0),
                ComparisonResult("id_document_vs_iprs", 88.0, 99.0)
            ],
            quality_metrics={
                'customer': QualityMetrics(75.0, 80.0, 99.0)
            },
            decision=MatchDecision(MatchStatus.APPROVED, [], {}),
            thresholds_used={'approval': 70.0, 'rejection': 50.0},
            processing_time_ms=1250.5
        )
        
        assert result.request_id == "req-123"
        assert result.match_status == MatchStatus.APPROVED
        assert len(result.comparisons) == 3
    
    def test_to_dict_structure(self):
        """FaceMatchingResult.to_dict has correct structure."""
        result = FaceMatchingResult(
            request_id="req-123",
            customer_id="cust-456",
            match_status=MatchStatus.APPROVED,
            comparison_mode=ComparisonMode.THREE_WAY,
            comparisons=[],
            quality_metrics={},
            decision=MatchDecision(MatchStatus.APPROVED, [], {}),
            thresholds_used={'approval': 70.0, 'rejection': 50.0},
            processing_time_ms=1000.0
        )
        
        d = result.to_dict()
        
        assert 'request_id' in d
        assert 'match_status' in d
        assert 'comparison_mode' in d
        assert 'comparisons' in d
        assert 'quality_metrics' in d
        assert 'decision' in d
        assert 'thresholds_used' in d
        assert 'processing_time_ms' in d
        assert 'timestamp' in d


class TestErrorClasses:
    """Tests for error classes."""
    
    def test_face_matching_error_base(self):
        """FaceMatchingError base class works correctly."""
        error = FaceMatchingError(
            error_code="TEST_ERROR",
            message="Test error message",
            details={'key': 'value'},
            failed_source="customer"
        )
        
        assert error.error_code == "TEST_ERROR"
        assert error.message == "Test error message"
        assert error.details == {'key': 'value'}
        assert error.failed_source == "customer"
    
    def test_face_matching_error_to_dict(self):
        """FaceMatchingError converts to dict correctly."""
        error = FaceMatchingError(
            error_code="TEST_ERROR",
            message="Test message",
            failed_source="customer"
        )
        
        d = error.to_dict()
        
        assert d['error_code'] == "TEST_ERROR"
        assert d['message'] == "Test message"
        assert d['failed_source'] == "customer"
    
    def test_no_face_detected_error(self):
        """NoFaceDetectedError has correct attributes."""
        error = NoFaceDetectedError("customer")
        
        assert error.error_code == "NO_FACE_DETECTED"
        assert "customer" in error.message
        assert error.failed_source == "customer"
        assert 'suggestion' in error.details
    
    def test_multiple_faces_error(self):
        """MultipleFacesError has correct attributes."""
        error = MultipleFacesError("id_document", 3)
        
        assert error.error_code == "MULTIPLE_FACES_DETECTED"
        assert "3" in error.message
        assert error.failed_source == "id_document"
        assert error.details['face_count'] == 3
    
    def test_image_too_small_error(self):
        """ImageTooSmallError has correct attributes."""
        error = ImageTooSmallError("customer", (320, 240), 480)
        
        assert error.error_code == "IMAGE_TOO_SMALL"
        assert "320x240" in error.message
        assert error.details['actual_dimensions']['width'] == 320
        assert error.details['minimum_dimensions']['width'] == 480
    
    def test_unsupported_format_error(self):
        """UnsupportedFormatError has correct attributes."""
        error = UnsupportedFormatError("customer", "GIF")
        
        assert error.error_code == "UNSUPPORTED_FORMAT"
        assert "GIF" in error.message
        assert error.details['actual_format'] == "GIF"
        assert 'JPEG' in error.details['supported_formats']
    
    def test_preprocessing_error(self):
        """PreprocessingError has correct attributes."""
        error = PreprocessingError("customer", "Corrupt image data")
        
        assert error.error_code == "PREPROCESSING_FAILED"
        assert "customer" in error.message
        assert error.failed_source == "customer"
    
    def test_comparison_error(self):
        """ComparisonError has correct attributes."""
        error = ComparisonError("customer_vs_id_document", "API timeout")
        
        assert error.error_code == "COMPARISON_FAILED"
        assert "customer_vs_id_document" in error.message
        assert error.details['comparison'] == "customer_vs_id_document"
    
    def test_validation_error(self):
        """ValidationError has correct attributes."""
        error = ValidationError(
            "Missing required fields",
            field_errors={'customer_id': 'required'}
        )
        
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details['field_errors']['customer_id'] == 'required'
    
    def test_error_inheritance(self):
        """All error classes inherit from FaceMatchingError."""
        errors = [
            NoFaceDetectedError("test"),
            MultipleFacesError("test", 2),
            ImageTooSmallError("test", (100, 100)),
            UnsupportedFormatError("test", "BMP"),
            PreprocessingError("test", "error"),
            ComparisonError("test", "error"),
            ValidationError("error")
        ]
        
        for error in errors:
            assert isinstance(error, FaceMatchingError)
            assert isinstance(error, Exception)
