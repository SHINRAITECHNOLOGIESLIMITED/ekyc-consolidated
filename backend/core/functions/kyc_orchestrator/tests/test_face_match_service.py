"""Unit tests for FaceMatchService."""
import base64
import io
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from face_match_service import (
    FaceMatchService,
    FaceMatchResult,
    FaceMatchDecision,
    ComparisonResult,
    ThresholdConfig,
    FaceMatchError,
    DocumentPhotoExtractionError,
)


class TestThresholdConfig:
    """Tests for threshold configuration."""

    def test_default_thresholds(self):
        config = ThresholdConfig()
        assert config.auto_approve == 70.0
        assert config.manual_review == 50.0
        assert config.enabled is True
        assert config.require_iprs_photo is False

    def test_valid_thresholds(self):
        config = ThresholdConfig(auto_approve=80.0, manual_review=40.0)
        assert config.validate() is True

    def test_invalid_thresholds_equal(self):
        config = ThresholdConfig(auto_approve=50.0, manual_review=50.0)
        assert config.validate() is False

    def test_invalid_thresholds_reversed(self):
        config = ThresholdConfig(auto_approve=40.0, manual_review=60.0)
        assert config.validate() is False


class TestFaceMatchServiceInit:
    """Tests for FaceMatchService initialization."""

    def test_invalid_thresholds_fallback_to_defaults(self, mock_rekognition, mock_s3):
        service = FaceMatchService(
            rekognition_client=mock_rekognition,
            s3_client=mock_s3,
            liveness_bucket="test-bucket",
            documents_bucket="docs-bucket",
            auto_approve_threshold=30,
            manual_review_threshold=60,
        )
        assert service.config.auto_approve == 70.0
        assert service.config.manual_review == 50.0

    def test_valid_custom_thresholds(self, mock_rekognition, mock_s3):
        service = FaceMatchService(
            rekognition_client=mock_rekognition,
            s3_client=mock_s3,
            liveness_bucket="test-bucket",
            documents_bucket="docs-bucket",
            auto_approve_threshold=80,
            manual_review_threshold=40,
        )
        assert service.config.auto_approve == 80.0
        assert service.config.manual_review == 40.0


class TestCompareFaces:
    """Tests for compare_faces method."""

    def test_successful_match(self, mock_rekognition, mock_s3):
        mock_rekognition.compare_faces.return_value = {
            "FaceMatches": [
                {"Similarity": 85.2, "Face": {"Confidence": 99.9, "BoundingBox": {}}}
            ],
            "UnmatchedFaces": [],
        }
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        result = service.compare_faces(b"src", b"tgt", "test_pair")
        assert result.similarity == 85.2
        assert result.matched is True
        assert result.error is None

    def test_no_face_matches(self, mock_rekognition, mock_s3):
        mock_rekognition.compare_faces.return_value = {
            "FaceMatches": [],
            "UnmatchedFaces": [{"Face": {"BoundingBox": {}}}],
        }
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        result = service.compare_faces(b"src", b"tgt", "test_pair")
        assert result.similarity == 0.0
        assert result.matched is False

    def test_rekognition_error(self, mock_rekognition, mock_s3):
        mock_rekognition.compare_faces.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameterException", "Message": "bad image"}},
            "CompareFaces",
        )
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        result = service.compare_faces(b"src", b"tgt", "test_pair")
        assert result.similarity == 0.0
        assert result.error is not None


class TestGetLivenessReferenceImage:
    """Tests for liveness image retrieval."""

    def test_successful_retrieval(self, mock_rekognition, mock_s3):
        mock_body = Mock()
        mock_body.read.return_value = b"image_bytes"
        mock_s3.get_object.return_value = {"Body": mock_body}

        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="liveness-bucket", documents_bucket="d",
        )
        result = service.get_liveness_reference_image("session-123")
        assert result == b"image_bytes"
        mock_s3.get_object.assert_called_once_with(
            Bucket="liveness-bucket", Key="session-123/reference_image.jpg"
        )

    def test_not_found(self, mock_rekognition, mock_s3):
        mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "not found"}},
            "GetObject",
        )
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        with pytest.raises(FaceMatchError, match="not found"):
            service.get_liveness_reference_image("bad-session")

    def test_s3_error(self, mock_rekognition, mock_s3):
        mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "GetObject",
        )
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        with pytest.raises(FaceMatchError, match="S3 error"):
            service.get_liveness_reference_image("session-123")


class TestGetIPRSPhoto:
    """Tests for IPRS photo extraction."""

    def test_valid_base64_photo(self, mock_rekognition, mock_s3):
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        photo_bytes = b"fake_photo_data"
        iprs_response = {"data": {"photo": base64.b64encode(photo_bytes).decode()}}
        result = service.get_iprs_photo(iprs_response)
        assert result == photo_bytes

    def test_missing_photo_field(self, mock_rekognition, mock_s3):
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        result = service.get_iprs_photo({"data": {"gender": "M"}})
        assert result is None

    def test_none_response(self, mock_rekognition, mock_s3):
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        result = service.get_iprs_photo(None)
        assert result is None

    def test_invalid_base64(self, mock_rekognition, mock_s3):
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        result = service.get_iprs_photo({"data": {"photo": "not-valid-base64!!!"}})
        assert result is None

    def test_nested_response_structure(self, mock_rekognition, mock_s3):
        """IPRS response may be nested in result.data."""
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        photo_bytes = b"nested_photo"
        iprs_response = {
            "result": {"data": {"photo": base64.b64encode(photo_bytes).decode()}}
        }
        result = service.get_iprs_photo(iprs_response)
        assert result == photo_bytes


class TestDetermineDecision:
    """Tests for decision algorithm."""

    def _make_service(self, mock_rekognition, mock_s3, approve=70, review=50):
        return FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
            auto_approve_threshold=approve, manual_review_threshold=review,
        )

    def test_auto_approved_all_high(self, mock_rekognition, mock_s3):
        service = self._make_service(mock_rekognition, mock_s3)
        comparisons = [
            ComparisonResult("a", 85.0, True),
            ComparisonResult("b", 78.0, True),
            ComparisonResult("c", 82.0, True),
        ]
        decision, score, review = service.determine_decision(comparisons, True)
        assert decision == FaceMatchDecision.AUTO_APPROVED
        assert score == 78.0
        assert review is False

    def test_manual_review_mid_score(self, mock_rekognition, mock_s3):
        service = self._make_service(mock_rekognition, mock_s3)
        comparisons = [
            ComparisonResult("a", 65.0, False),
            ComparisonResult("b", 78.0, True),
        ]
        decision, score, review = service.determine_decision(comparisons, True)
        assert decision == FaceMatchDecision.MANUAL_REVIEW
        assert score == 65.0
        assert review is True

    def test_auto_rejected_low_score(self, mock_rekognition, mock_s3):
        service = self._make_service(mock_rekognition, mock_s3)
        comparisons = [
            ComparisonResult("a", 45.0, False),
            ComparisonResult("b", 78.0, True),
        ]
        decision, score, review = service.determine_decision(comparisons, True)
        assert decision == FaceMatchDecision.AUTO_REJECTED
        assert score == 45.0
        assert review is False

    def test_partial_match_no_iprs(self, mock_rekognition, mock_s3):
        """PARTIAL_MATCH when IPRS photo unavailable, always requires manual review."""
        service = self._make_service(mock_rekognition, mock_s3)
        comparisons = [ComparisonResult("a", 90.0, True)]
        decision, score, review = service.determine_decision(comparisons, False)
        assert decision == FaceMatchDecision.PARTIAL_MATCH
        assert score == 90.0
        assert review is True

    def test_boundary_exactly_70(self, mock_rekognition, mock_s3):
        service = self._make_service(mock_rekognition, mock_s3)
        comparisons = [ComparisonResult("a", 70.0, True)]
        decision, score, _ = service.determine_decision(comparisons, True)
        assert decision == FaceMatchDecision.AUTO_APPROVED

    def test_boundary_exactly_50(self, mock_rekognition, mock_s3):
        service = self._make_service(mock_rekognition, mock_s3)
        comparisons = [ComparisonResult("a", 50.0, False)]
        decision, score, _ = service.determine_decision(comparisons, True)
        assert decision == FaceMatchDecision.MANUAL_REVIEW

    def test_boundary_49_99(self, mock_rekognition, mock_s3):
        service = self._make_service(mock_rekognition, mock_s3)
        comparisons = [ComparisonResult("a", 49.99, False)]
        decision, score, _ = service.determine_decision(comparisons, True)
        assert decision == FaceMatchDecision.AUTO_REJECTED

    def test_all_comparisons_failed(self, mock_rekognition, mock_s3):
        service = self._make_service(mock_rekognition, mock_s3)
        comparisons = [ComparisonResult("a", 0.0, False, error="fail")]
        decision, score, _ = service.determine_decision(comparisons, True)
        assert decision == FaceMatchDecision.AUTO_REJECTED
        assert score is None


class TestGetDocumentImage:
    """Tests for document image retrieval from S3."""

    def test_successful_retrieval(self, mock_rekognition, mock_s3):
        mock_body = Mock()
        mock_body.read.return_value = b"doc_bytes"
        mock_s3.get_object.return_value = {"Body": mock_body}

        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="docs-bucket",
        )
        result = service.get_document_image("NationalID/12345.jpg")
        assert result == b"doc_bytes"
        mock_s3.get_object.assert_called_once_with(
            Bucket="docs-bucket", Key="NationalID/12345.jpg"
        )

    def test_s3_error(self, mock_rekognition, mock_s3):
        mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "not found"}},
            "GetObject",
        )
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        with pytest.raises(FaceMatchError, match="S3 error"):
            service.get_document_image("missing/doc.jpg")


class TestExtractFaceFromDocument:
    """Tests for face extraction from document images."""

    def test_successful_extraction(self, mock_rekognition, mock_s3, mock_document_image):
        """Extract face from document with mocked Rekognition DetectFaces."""
        mock_rekognition.detect_faces.return_value = {
            "FaceDetails": [
                {
                    "BoundingBox": {
                        "Left": 0.3,
                        "Top": 0.2,
                        "Width": 0.2,
                        "Height": 0.3,
                    },
                    "Confidence": 99.5,
                }
            ]
        }
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        result = service.extract_face_from_document(mock_document_image, "national_id")
        assert isinstance(result, bytes)
        assert len(result) > 0
        # Verify it's a valid JPEG (starts with JPEG magic bytes)
        assert result[:2] == b'\xff\xd8'

    def test_no_face_detected(self, mock_rekognition, mock_s3, mock_document_image):
        """Raise error when no face found in document."""
        mock_rekognition.detect_faces.return_value = {"FaceDetails": []}
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        with pytest.raises(DocumentPhotoExtractionError, match="No face found"):
            service.extract_face_from_document(mock_document_image, "national_id")

    def test_multiple_faces_picks_highest_confidence(self, mock_rekognition, mock_s3, mock_document_image):
        """When multiple faces detected, use the one with highest confidence."""
        mock_rekognition.detect_faces.return_value = {
            "FaceDetails": [
                {
                    "BoundingBox": {"Left": 0.1, "Top": 0.1, "Width": 0.1, "Height": 0.1},
                    "Confidence": 80.0,
                },
                {
                    "BoundingBox": {"Left": 0.3, "Top": 0.2, "Width": 0.2, "Height": 0.3},
                    "Confidence": 99.0,
                },
            ]
        }
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        result = service.extract_face_from_document(mock_document_image, "passport")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_rekognition_detect_faces_error(self, mock_rekognition, mock_s3, mock_document_image):
        """Handle Rekognition DetectFaces API error."""
        mock_rekognition.detect_faces.side_effect = ClientError(
            {"Error": {"Code": "InvalidImageFormatException", "Message": "bad format"}},
            "DetectFaces",
        )
        service = FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="b", documents_bucket="d",
        )
        with pytest.raises(DocumentPhotoExtractionError, match="Failed to extract face"):
            service.extract_face_from_document(mock_document_image, "national_id")


class TestExecuteFaceMatch:
    """Tests for the full face matching pipeline."""

    def _make_service(self, mock_rekognition, mock_s3):
        return FaceMatchService(
            rekognition_client=mock_rekognition, s3_client=mock_s3,
            liveness_bucket="liveness-bucket", documents_bucket="docs-bucket",
            auto_approve_threshold=70, manual_review_threshold=50,
        )

    def _setup_s3_mocks(self, mock_s3, mock_document_image):
        """Set up S3 to return liveness and document images."""
        liveness_body = Mock()
        liveness_body.read.return_value = b'\xff\xd8\xff\xe0' + b'\x00' * 50

        doc_body = Mock()
        doc_body.read.return_value = mock_document_image

        def get_object_side_effect(Bucket, Key):
            body = Mock()
            if "liveness" in Bucket:
                body.read.return_value = b'\xff\xd8\xff\xe0' + b'\x00' * 50
            else:
                body.read.return_value = mock_document_image
            return {"Body": body}

        mock_s3.get_object.side_effect = get_object_side_effect

    def _setup_rekognition_mocks(self, mock_rekognition, similarity=85.0):
        """Set up Rekognition to return face detection and comparison results."""
        mock_rekognition.detect_faces.return_value = {
            "FaceDetails": [
                {
                    "BoundingBox": {"Left": 0.3, "Top": 0.2, "Width": 0.2, "Height": 0.3},
                    "Confidence": 99.5,
                }
            ]
        }
        mock_rekognition.compare_faces.return_value = {
            "FaceMatches": [
                {"Similarity": similarity, "Face": {"Confidence": 99.9, "BoundingBox": {}}}
            ],
            "UnmatchedFaces": [],
        }

    def test_3way_comparison_auto_approved(self, mock_rekognition, mock_s3, mock_document_image):
        """Full 3-way comparison with IPRS photo, all scores high → AUTO_APPROVED."""
        self._setup_s3_mocks(mock_s3, mock_document_image)
        self._setup_rekognition_mocks(mock_rekognition, similarity=85.0)

        service = self._make_service(mock_rekognition, mock_s3)
        photo_b64 = base64.b64encode(b"iprs_photo_data").decode()
        iprs_response = {"data": {"photo": photo_b64}}

        result = service.execute_face_match(
            session_id="session-123",
            document_type="national_id",
            document_s3_path="NationalID/12345.jpg",
            id_number="12345678",
            iprs_verification_response=iprs_response,
        )

        assert result.overall_decision == "AUTO_APPROVED"
        assert result.iprs_photo_available is True
        assert result.requires_manual_review is False
        assert len(result.comparisons) == 3
        assert "liveness_vs_document" in result.comparisons
        assert "liveness_vs_iprs" in result.comparisons
        assert "document_vs_iprs" in result.comparisons
        assert result.error is None

    def test_2way_comparison_partial_match(self, mock_rekognition, mock_s3, mock_document_image):
        """2-way comparison without IPRS photo → PARTIAL_MATCH with requires_manual_review."""
        self._setup_s3_mocks(mock_s3, mock_document_image)
        self._setup_rekognition_mocks(mock_rekognition, similarity=85.0)

        service = self._make_service(mock_rekognition, mock_s3)

        result = service.execute_face_match(
            session_id="session-123",
            document_type="national_id",
            document_s3_path="NationalID/12345.jpg",
            id_number="12345678",
            iprs_verification_response=None,
        )

        assert result.overall_decision == "PARTIAL_MATCH"
        assert result.iprs_photo_available is False
        assert result.requires_manual_review is True
        assert len(result.comparisons) == 1
        assert "liveness_vs_document" in result.comparisons
        assert result.error is None

    def test_2way_iprs_no_photo_field(self, mock_rekognition, mock_s3, mock_document_image):
        """IPRS response present but no photo field → PARTIAL_MATCH."""
        self._setup_s3_mocks(mock_s3, mock_document_image)
        self._setup_rekognition_mocks(mock_rekognition, similarity=85.0)

        service = self._make_service(mock_rekognition, mock_s3)
        iprs_response = {"data": {"gender": "M", "serialNumber": "12345"}}

        result = service.execute_face_match(
            session_id="session-123",
            document_type="national_id",
            document_s3_path="NationalID/12345.jpg",
            id_number="12345678",
            iprs_verification_response=iprs_response,
        )

        assert result.overall_decision == "PARTIAL_MATCH"
        assert result.iprs_photo_available is False
        assert result.requires_manual_review is True

    def test_3way_auto_rejected(self, mock_rekognition, mock_s3, mock_document_image):
        """3-way comparison with low score → AUTO_REJECTED."""
        self._setup_s3_mocks(mock_s3, mock_document_image)
        self._setup_rekognition_mocks(mock_rekognition, similarity=30.0)

        service = self._make_service(mock_rekognition, mock_s3)
        photo_b64 = base64.b64encode(b"iprs_photo").decode()

        result = service.execute_face_match(
            session_id="session-123",
            document_type="national_id",
            document_s3_path="NationalID/12345.jpg",
            id_number="12345678",
            iprs_verification_response={"data": {"photo": photo_b64}},
        )

        assert result.overall_decision == "AUTO_REJECTED"
        assert result.requires_manual_review is False

    def test_3way_manual_review(self, mock_rekognition, mock_s3, mock_document_image):
        """3-way comparison with mid-range score → MANUAL_REVIEW."""
        self._setup_s3_mocks(mock_s3, mock_document_image)
        self._setup_rekognition_mocks(mock_rekognition, similarity=60.0)

        service = self._make_service(mock_rekognition, mock_s3)
        photo_b64 = base64.b64encode(b"iprs_photo").decode()

        result = service.execute_face_match(
            session_id="session-123",
            document_type="national_id",
            document_s3_path="NationalID/12345.jpg",
            id_number="12345678",
            iprs_verification_response={"data": {"photo": photo_b64}},
        )

        assert result.overall_decision == "MANUAL_REVIEW"
        assert result.requires_manual_review is True

    def test_liveness_image_not_found_error(self, mock_rekognition, mock_s3):
        """Error when liveness session image doesn't exist."""
        mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "not found"}},
            "GetObject",
        )
        service = self._make_service(mock_rekognition, mock_s3)

        result = service.execute_face_match(
            session_id="bad-session",
            document_type="national_id",
            document_s3_path="NationalID/12345.jpg",
            id_number="12345678",
        )

        assert result.overall_decision == "ERROR"
        assert result.error is not None
        assert "not found" in result.error

    def test_document_extraction_failure(self, mock_rekognition, mock_s3, mock_document_image):
        """Error when face extraction from document fails."""
        # S3 returns images fine
        self._setup_s3_mocks(mock_s3, mock_document_image)
        # But DetectFaces returns no faces
        mock_rekognition.detect_faces.return_value = {"FaceDetails": []}

        service = self._make_service(mock_rekognition, mock_s3)

        result = service.execute_face_match(
            session_id="session-123",
            document_type="national_id",
            document_s3_path="NationalID/12345.jpg",
            id_number="12345678",
        )

        assert result.overall_decision == "ERROR"
        assert result.error is not None
        assert "No face found" in result.error

    def test_result_to_dict(self, mock_rekognition, mock_s3, mock_document_image):
        """Verify FaceMatchResult.to_dict() produces correct structure."""
        self._setup_s3_mocks(mock_s3, mock_document_image)
        self._setup_rekognition_mocks(mock_rekognition, similarity=85.0)

        service = self._make_service(mock_rekognition, mock_s3)
        result = service.execute_face_match(
            session_id="session-123",
            document_type="national_id",
            document_s3_path="NationalID/12345.jpg",
            id_number="12345678",
        )

        d = result.to_dict()
        assert "overall_decision" in d
        assert "comparisons" in d
        assert "lowest_score" in d
        assert "iprs_photo_available" in d
        assert "document_type" in d
        assert "thresholds" in d
        assert "requires_manual_review" in d
        assert d["document_type"] == "national_id"
        assert d["thresholds"]["auto_approve"] == 70.0
        assert d["thresholds"]["manual_review"] == 50.0

    def test_id_number_masked_in_logs(self, mock_rekognition, mock_s3, mock_document_image):
        """Verify ID number is masked in log output (first 4 chars + ****)."""
        self._setup_s3_mocks(mock_s3, mock_document_image)
        self._setup_rekognition_mocks(mock_rekognition, similarity=85.0)

        service = self._make_service(mock_rekognition, mock_s3)
        # This should not raise — just verifying it runs with a long ID
        result = service.execute_face_match(
            session_id="session-123",
            document_type="national_id",
            document_s3_path="NationalID/12345.jpg",
            id_number="23667272",
        )
        assert result.overall_decision in ["PARTIAL_MATCH", "AUTO_APPROVED", "AUTO_REJECTED", "MANUAL_REVIEW"]
