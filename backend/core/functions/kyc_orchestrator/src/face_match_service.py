"""
Face Matching Service for 3-way face comparison using AWS Rekognition.

Compares liveness reference image, document photo, and IPRS photo
to verify identity with configurable decision bands.
"""
import base64
import io
import os
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple

import boto3
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

logger = Logger()


class FaceMatchDecision(Enum):
    """Face matching verification outcomes."""
    AUTO_APPROVED = "AUTO_APPROVED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    AUTO_REJECTED = "AUTO_REJECTED"
    PARTIAL_MATCH = "PARTIAL_MATCH"


class DocumentPhotoExtractionError(Exception):
    """Raised when face extraction from document fails."""
    pass


class FaceMatchError(Exception):
    """Raised when face matching encounters a critical error."""
    pass


@dataclass
class ComparisonResult:
    """Result of a single pairwise face comparison."""
    pair_name: str
    similarity: float = 0.0
    matched: bool = False
    error: Optional[str] = None


@dataclass
class ThresholdConfig:
    """Face matching threshold configuration."""
    auto_approve: float = 70.0
    manual_review: float = 50.0
    enabled: bool = True
    require_iprs_photo: bool = False

    def validate(self) -> bool:
        """Return True if thresholds are valid (auto_approve > manual_review)."""
        return self.auto_approve > self.manual_review


@dataclass
class FaceMatchResult:
    """Complete face matching result."""
    overall_decision: str
    comparisons: Dict[str, Any] = field(default_factory=dict)
    lowest_score: Optional[float] = None
    iprs_photo_available: bool = False
    document_type: str = ""
    thresholds: Dict[str, float] = field(default_factory=dict)
    requires_manual_review: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            "overall_decision": self.overall_decision,
            "comparisons": self.comparisons,
            "lowest_score": self.lowest_score,
            "iprs_photo_available": self.iprs_photo_available,
            "document_type": self.document_type,
            "thresholds": self.thresholds,
            "requires_manual_review": self.requires_manual_review,
        }
        if self.error:
            result["error"] = self.error
        return result


class FaceMatchService:
    """3-way face matching service using AWS Rekognition."""

    VALID_DOCUMENT_TYPES = ["national_id", "alien_id", "passport", "military_id"]

    def __init__(
        self,
        rekognition_client=None,
        s3_client=None,
        liveness_bucket: Optional[str] = None,
        documents_bucket: Optional[str] = None,
        auto_approve_threshold: float = 70.0,
        manual_review_threshold: float = 50.0,
    ):
        self.rekognition = rekognition_client or boto3.client("rekognition")
        self.s3 = s3_client or boto3.client("s3")
        self.liveness_bucket = liveness_bucket or os.environ.get("LIVENESSCAPTUREBUCKET_BUCKET_NAME", "")
        self.documents_bucket = documents_bucket or os.environ.get("KYCDOCUMENTSBUCKET_NAME", "")

        # Validate thresholds
        if auto_approve_threshold <= manual_review_threshold:
            logger.error(
                "Invalid thresholds: auto_approve must be > manual_review. Using defaults.",
                extra={"auto_approve": auto_approve_threshold, "manual_review": manual_review_threshold}
            )
            auto_approve_threshold = 70.0
            manual_review_threshold = 50.0

        self.config = ThresholdConfig(
            auto_approve=auto_approve_threshold,
            manual_review=manual_review_threshold,
        )

    def compare_faces(
        self, source_image: bytes, target_image: bytes, pair_name: str
    ) -> ComparisonResult:
        """
        Compare two face images using Rekognition CompareFaces.

        Args:
            source_image: Source face image bytes.
            target_image: Target face image bytes.
            pair_name: Identifier for this comparison pair.

        Returns:
            ComparisonResult with similarity score.
        """
        try:
            response = self.rekognition.compare_faces(
                SourceImage={"Bytes": source_image},
                TargetImage={"Bytes": target_image},
                SimilarityThreshold=0,
                QualityFilter="AUTO",
            )
            if response.get("FaceMatches"):
                best = max(response["FaceMatches"], key=lambda m: m["Similarity"])
                similarity = best["Similarity"]
                return ComparisonResult(
                    pair_name=pair_name,
                    similarity=similarity,
                    matched=similarity >= self.config.auto_approve,
                )
            return ComparisonResult(pair_name=pair_name, similarity=0.0, matched=False)
        except ClientError as e:
            logger.error(f"Rekognition CompareFaces error for {pair_name}: {e}")
            return ComparisonResult(
                pair_name=pair_name, similarity=0.0, matched=False, error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error in compare_faces for {pair_name}: {e}")
            return ComparisonResult(
                pair_name=pair_name, similarity=0.0, matched=False, error=str(e)
            )

    def get_liveness_reference_image(self, session_id: str) -> bytes:
        """
        Retrieve liveness reference image from S3.

        Args:
            session_id: The face liveness session ID.

        Returns:
            Image bytes.

        Raises:
            FaceMatchError: If image cannot be retrieved.
        """
        key = f"{session_id}/reference_image.jpg"
        try:
            response = self.s3.get_object(Bucket=self.liveness_bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise FaceMatchError(f"Liveness session image not found: {key}")
            raise FaceMatchError(f"S3 error retrieving liveness image: {e}")
        except Exception as e:
            raise FaceMatchError(f"Failed to retrieve liveness image: {e}")

    def get_document_image(self, document_s3_path: str) -> bytes:
        """
        Retrieve document image from S3.

        Args:
            document_s3_path: S3 key for the document.

        Returns:
            Document image bytes.

        Raises:
            FaceMatchError: If document cannot be retrieved.
        """
        try:
            response = self.s3.get_object(Bucket=self.documents_bucket, Key=document_s3_path)
            return response["Body"].read()
        except ClientError as e:
            raise FaceMatchError(f"S3 error retrieving document: {e}")
        except Exception as e:
            raise FaceMatchError(f"Failed to retrieve document: {e}")

    def extract_face_from_document(self, document_bytes: bytes, document_type: str) -> bytes:
        """
        Extract face region from a document image using Rekognition DetectFaces.

        Detects the largest face in the document and crops it with 20% padding.

        Args:
            document_bytes: Raw document image bytes (JPEG/PNG).
            document_type: One of national_id, alien_id, passport, military_id.

        Returns:
            Cropped face image bytes (JPEG).

        Raises:
            DocumentPhotoExtractionError: If no face is found or extraction fails.
        """
        try:
            # Detect faces in the document image
            response = self.rekognition.detect_faces(
                Image={"Bytes": document_bytes},
                Attributes=["DEFAULT"],
            )
            face_details = response.get("FaceDetails", [])
            if not face_details:
                raise DocumentPhotoExtractionError(
                    f"No face found in {document_type} document"
                )

            # Use the face with highest confidence
            best_face = max(face_details, key=lambda f: f.get("Confidence", 0))
            bbox = best_face["BoundingBox"]

            # Crop face with 20% padding using Pillow
            from PIL import Image as PILImage

            image = PILImage.open(io.BytesIO(document_bytes))
            img_width, img_height = image.size

            # Convert fractional bounding box to pixel coordinates
            left = bbox["Left"] * img_width
            top = bbox["Top"] * img_height
            width = bbox["Width"] * img_width
            height = bbox["Height"] * img_height

            # Add 20% padding
            pad_w = width * 0.20
            pad_h = height * 0.20

            crop_left = max(0, left - pad_w)
            crop_top = max(0, top - pad_h)
            crop_right = min(img_width, left + width + pad_w)
            crop_bottom = min(img_height, top + height + pad_h)

            cropped = image.crop((crop_left, crop_top, crop_right, crop_bottom))

            # Convert to JPEG bytes
            buffer = io.BytesIO()
            cropped.save(buffer, format="JPEG", quality=95)
            buffer.seek(0)
            return buffer.read()

        except DocumentPhotoExtractionError:
            raise
        except Exception as e:
            raise DocumentPhotoExtractionError(
                f"Failed to extract face from {document_type} document: {e}"
            )

    def get_iprs_photo(
        self, iprs_verification_response: Optional[Dict[str, Any]]
    ) -> Optional[bytes]:
        """
        Extract and decode IPRS photo from verification response.

        Args:
            iprs_verification_response: Previous IPRS verification result dict.

        Returns:
            Decoded photo bytes, or None if unavailable.
        """
        if not iprs_verification_response:
            return None

        # Navigate nested response structures to find photo
        data = iprs_verification_response
        # Try common response structures
        if "data" in data:
            data = data["data"]
        if "result" in data:
            data = data["result"]
        if "data" in data:
            data = data["data"]

        photo_b64 = data.get("photo")
        if not photo_b64:
            logger.info("IPRS response does not contain a photo field")
            return None

        try:
            return base64.b64decode(photo_b64)
        except Exception as e:
            logger.warning(f"Failed to decode IPRS photo from base64: {e}")
            return None

    def determine_decision(
        self,
        comparisons: List[ComparisonResult],
        iprs_photo_available: bool,
    ) -> Tuple[FaceMatchDecision, Optional[float], bool]:
        """
        Apply decision algorithm based on minimum score across comparisons.

        Args:
            comparisons: List of comparison results.
            iprs_photo_available: Whether IPRS photo was available.

        Returns:
            Tuple of (decision, lowest_score, requires_manual_review).
        """
        # Filter out failed comparisons
        successful = [c for c in comparisons if c.error is None]
        if not successful:
            return FaceMatchDecision.AUTO_REJECTED, None, False

        scores = [c.similarity for c in successful]
        lowest = min(scores)

        # PARTIAL_MATCH when IPRS photo unavailable — always requires manual review
        if not iprs_photo_available:
            return FaceMatchDecision.PARTIAL_MATCH, lowest, True

        if lowest >= self.config.auto_approve:
            return FaceMatchDecision.AUTO_APPROVED, lowest, False
        elif lowest < self.config.manual_review:
            return FaceMatchDecision.AUTO_REJECTED, lowest, False
        else:
            return FaceMatchDecision.MANUAL_REVIEW, lowest, True

    def execute_face_match(
        self,
        session_id: str,
        document_type: str,
        document_s3_path: str,
        id_number: str,
        iprs_verification_response: Optional[Dict[str, Any]] = None,
    ) -> FaceMatchResult:
        """
        Execute the full 3-way face matching pipeline.

        Args:
            session_id: Liveness session ID.
            document_type: One of national_id, alien_id, passport, military_id.
            document_s3_path: S3 key for the uploaded document.
            id_number: Customer ID number.
            iprs_verification_response: Previous IPRS verification result.

        Returns:
            FaceMatchResult with overall decision and comparison details.
        """
        logger.info(
            "Starting face match",
            extra={
                "session_id": session_id,
                "document_type": document_type,
                "id_number": id_number[:4] + "****" if id_number else "N/A",
            },
        )

        thresholds = {
            "auto_approve": self.config.auto_approve,
            "manual_review": self.config.manual_review,
        }

        try:
            # Step 1: Get liveness reference image
            liveness_bytes = self.get_liveness_reference_image(session_id)

            # Step 2: Get document image and validate it contains a face
            document_bytes = self.get_document_image(document_s3_path)
            # Validate a face exists (raises DocumentPhotoExtractionError if not)
            self.extract_face_from_document(document_bytes, document_type)
            # Use full document image for CompareFaces — Rekognition detects
            # faces within larger images and this avoids quality loss from
            # cropping small ID photos (e.g. national ID face is ~17% of image)

            # Step 3: Get IPRS photo (may be None)
            iprs_bytes = self.get_iprs_photo(iprs_verification_response)
            iprs_photo_available = iprs_bytes is not None

            # Step 4: Perform comparisons using full document image
            comparisons_list: List[ComparisonResult] = []

            # Comparison 1: Liveness vs Document (ALWAYS)
            comp1 = self.compare_faces(
                liveness_bytes, document_bytes, "liveness_vs_document"
            )
            comparisons_list.append(comp1)

            # Comparisons 2 & 3: Only if IPRS photo available
            if iprs_bytes:
                comp2 = self.compare_faces(
                    liveness_bytes, iprs_bytes, "liveness_vs_iprs"
                )
                comparisons_list.append(comp2)

                comp3 = self.compare_faces(
                    document_bytes, iprs_bytes, "document_vs_iprs"
                )
                comparisons_list.append(comp3)

            # Step 5: Determine decision
            decision, lowest_score, requires_review = self.determine_decision(
                comparisons_list, iprs_photo_available
            )

            # Build comparisons dict for response
            comparisons_dict = {}
            for comp in comparisons_list:
                entry = {"similarity": round(comp.similarity, 2), "matched": comp.matched}
                if comp.error:
                    entry["error"] = comp.error
                comparisons_dict[comp.pair_name] = entry

            result = FaceMatchResult(
                overall_decision=decision.value,
                comparisons=comparisons_dict,
                lowest_score=round(lowest_score, 2) if lowest_score is not None else None,
                iprs_photo_available=iprs_photo_available,
                document_type=document_type,
                thresholds=thresholds,
                requires_manual_review=requires_review,
            )

            # Log decision
            log_level = "warning" if decision in (
                FaceMatchDecision.AUTO_REJECTED, FaceMatchDecision.MANUAL_REVIEW
            ) else "info"
            getattr(logger, log_level)(
                f"Face match completed: {decision.value}",
                extra={
                    "session_id": session_id,
                    "document_type": document_type,
                    "overall_decision": decision.value,
                    "lowest_score": lowest_score,
                    "iprs_photo_available": iprs_photo_available,
                    "requires_manual_review": requires_review,
                },
            )

            return result

        except (FaceMatchError, DocumentPhotoExtractionError) as e:
            logger.error(f"Face match failed: {e}", extra={"session_id": session_id})
            return FaceMatchResult(
                overall_decision="ERROR",
                document_type=document_type,
                thresholds=thresholds,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected face match error: {e}", extra={"session_id": session_id})
            return FaceMatchResult(
                overall_decision="ERROR",
                document_type=document_type,
                thresholds=thresholds,
                error=f"Unexpected error: {str(e)}",
            )
