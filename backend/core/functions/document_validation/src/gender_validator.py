"""
Gender Validator Module

Validates gender by comparing document-extracted values against IPRS API responses.
Uses IPRS as the authoritative source (NOT LexisNexis due to data quality issues).

Requirements: Gender Validation feature - IPRS only
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from aws_lambda_powertools import Logger

from normalizer import normalize_gender

logger = Logger()


class GenderValidationStatus(Enum):
    """Gender validation outcome status."""
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class GenderValidationResult:
    """
    Result of gender validation.
    
    Attributes:
        status: Validation outcome (MATCH, MISMATCH, or INCONCLUSIVE)
        extracted_gender: Normalized gender from document (or None)
        iprs_gender: Normalized gender from IPRS (or None)
        normalized_comparison: True if comparison used normalized values
        reason: Explanation for non-MATCH status (None for MATCH)
    """
    status: GenderValidationStatus
    extracted_gender: Optional[str]
    iprs_gender: Optional[str]
    normalized_comparison: bool
    reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "status": self.status.value,
            "extractedGender": self.extracted_gender,
            "iprsGender": self.iprs_gender,
            "normalizedComparison": self.normalized_comparison,
            "reason": self.reason
        }


def validate_gender(
    extracted_gender: Optional[str],
    iprs_gender: Optional[str],
    request_id: Optional[str] = None
) -> GenderValidationResult:
    """
    Validate gender by comparing document extraction with IPRS data.
    
    Compares the gender extracted from a document against the gender from IPRS.
    Both values are normalized before comparison (M/F format).
    
    Note: Uses IPRS as authoritative source, NOT LexisNexis (per Sharon Mukonyo's
    clarification about data quality issues with LexisNexis gender data).
    
    Args:
        extracted_gender: Gender extracted from document via Textract.
            May be None if extraction failed.
        iprs_gender: Gender from IPRS API response.
            May be None if IPRS lookup failed.
        request_id: Optional request ID for logging correlation.
    
    Returns:
        GenderValidationResult with:
        - status: MATCH, MISMATCH, or INCONCLUSIVE
        - extracted_gender: Normalized extracted gender
        - iprs_gender: Normalized IPRS gender
        - normalized_comparison: True if comparison used normalized values
        - reason: Explanation for non-MATCH status
    
    Example:
        >>> validate_gender("Male", "M")
        GenderValidationResult(status=MATCH, ...)
    """
    try:
        # Normalize both gender values
        normalized_extracted = normalize_gender(extracted_gender)
        normalized_iprs = normalize_gender(iprs_gender)
        
        # Log original and normalized values
        logger.info("Gender validation", extra={
            "request_id": request_id,
            "original_extracted": extracted_gender,
            "original_iprs": iprs_gender,
            "normalized_extracted": normalized_extracted,
            "normalized_iprs": normalized_iprs
        })
        
        # Check for missing extracted gender
        if normalized_extracted is None:
            reason = _get_extraction_failure_reason(extracted_gender)
            logger.info("Gender validation result", extra={
                "request_id": request_id,
                "status": "INCONCLUSIVE",
                "reason": reason
            })
            return GenderValidationResult(
                status=GenderValidationStatus.INCONCLUSIVE,
                extracted_gender=None,
                iprs_gender=normalized_iprs,
                normalized_comparison=False,
                reason=reason
            )
        
        # Check for missing IPRS gender
        if normalized_iprs is None:
            reason = _get_iprs_failure_reason(iprs_gender)
            logger.info("Gender validation result", extra={
                "request_id": request_id,
                "status": "INCONCLUSIVE",
                "reason": reason
            })
            return GenderValidationResult(
                status=GenderValidationStatus.INCONCLUSIVE,
                extracted_gender=normalized_extracted,
                iprs_gender=None,
                normalized_comparison=False,
                reason=reason
            )
        
        # Compare normalized values
        if normalized_extracted == normalized_iprs:
            logger.info("Gender validation result", extra={
                "request_id": request_id,
                "status": "MATCH"
            })
            return GenderValidationResult(
                status=GenderValidationStatus.MATCH,
                extracted_gender=normalized_extracted,
                iprs_gender=normalized_iprs,
                normalized_comparison=True,
                reason=None
            )
        else:
            reason = "Document gender does not match IPRS record"
            logger.warning("Gender mismatch detected", extra={
                "request_id": request_id,
                "status": "MISMATCH",
                "extracted_gender": normalized_extracted,
                "iprs_gender": normalized_iprs,
                "reason": reason
            })
            return GenderValidationResult(
                status=GenderValidationStatus.MISMATCH,
                extracted_gender=normalized_extracted,
                iprs_gender=normalized_iprs,
                normalized_comparison=True,
                reason=reason
            )
    
    except Exception as e:
        # Non-blocking: catch all exceptions and return INCONCLUSIVE
        reason = f"Gender validation error: {str(e)}"
        logger.error("Gender validation failed", extra={
            "request_id": request_id,
            "error": str(e)
        })
        return GenderValidationResult(
            status=GenderValidationStatus.INCONCLUSIVE,
            extracted_gender=None,
            iprs_gender=None,
            normalized_comparison=False,
            reason=reason
        )


def _get_extraction_failure_reason(original_value: Optional[str]) -> str:
    """Get appropriate reason message for extraction failure."""
    if original_value is None:
        return "Gender not found in document"
    elif original_value.strip() == "":
        return "Gender not found in document"
    else:
        return "Invalid gender format in document"


def _get_iprs_failure_reason(original_value: Optional[str]) -> str:
    """Get appropriate reason message for IPRS failure."""
    if original_value is None:
        return "IPRS gender unavailable"
    elif original_value.strip() == "":
        return "IPRS gender unavailable"
    else:
        return "Invalid IPRS gender format"
