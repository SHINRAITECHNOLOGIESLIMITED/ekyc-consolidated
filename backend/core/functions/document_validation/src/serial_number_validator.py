"""
Serial Number Validator Module

Validates serial numbers by comparing document-extracted values against IPRS API responses.
Provides three-state validation outcomes: MATCH, MISMATCH, or INCONCLUSIVE.

Requirements: 3.1, 3.2, 3.3, 3.4, 4.4, 5.2, 5.3, 6.1-6.6
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional

from aws_lambda_powertools import Logger

from normalizer import normalize_serial_number

logger = Logger()


class ValidationStatus(Enum):
    """Validation outcome status."""
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class SerialNumberValidationResult:
    """
    Result of serial number validation.
    
    Attributes:
        status: Validation outcome (MATCH, MISMATCH, or INCONCLUSIVE)
        extracted_serial_number: Normalized serial from document (or None)
        iprs_serial_number: Normalized serial from IPRS (or None)
        normalized_comparison: True if comparison used normalized values
        reason: Explanation for non-MATCH status (None for MATCH)
    """
    status: ValidationStatus
    extracted_serial_number: Optional[str]
    iprs_serial_number: Optional[str]
    normalized_comparison: bool
    reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "status": self.status.value,
            "extractedSerialNumber": self.extracted_serial_number,
            "iprsSerialNumber": self.iprs_serial_number,
            "normalizedComparison": self.normalized_comparison,
            "reason": self.reason
        }


def validate_serial_number(
    extracted_serial: Optional[str],
    iprs_serial: Optional[str],
    request_id: Optional[str] = None
) -> SerialNumberValidationResult:
    """
    Validate serial number by comparing document extraction with IPRS data.
    
    Compares the serial number extracted from a National ID document against
    the latest serial number from IPRS. Both values are normalized before
    comparison to handle formatting differences.
    
    Args:
        extracted_serial: Serial number extracted from document via Textract.
            May be None if extraction failed.
        iprs_serial: Serial number from IPRS API response.
            May be None if IPRS lookup failed.
        request_id: Optional request ID for logging correlation.
    
    Returns:
        SerialNumberValidationResult with:
        - status: MATCH, MISMATCH, or INCONCLUSIVE
        - extracted_serial_number: Normalized extracted serial
        - iprs_serial_number: Normalized IPRS serial
        - normalized_comparison: True if comparison used normalized values
        - reason: Explanation for non-MATCH status
    
    Example:
        >>> validate_serial_number("12345-ABC", "12345 ABC")
        SerialNumberValidationResult(status=MATCH, ...)
    """
    try:
        # Normalize both serial numbers
        normalized_extracted = normalize_serial_number(extracted_serial)
        normalized_iprs = normalize_serial_number(iprs_serial)
        
        # Log original and normalized values
        logger.info("Serial number validation", extra={
            "request_id": request_id,
            "original_extracted": extracted_serial,
            "original_iprs": iprs_serial,
            "normalized_extracted": normalized_extracted,
            "normalized_iprs": normalized_iprs
        })
        
        # Check for missing extracted serial
        if normalized_extracted is None:
            reason = _get_extraction_failure_reason(extracted_serial)
            logger.info("Serial number validation result", extra={
                "request_id": request_id,
                "status": "INCONCLUSIVE",
                "reason": reason
            })
            return SerialNumberValidationResult(
                status=ValidationStatus.INCONCLUSIVE,
                extracted_serial_number=None,
                iprs_serial_number=normalized_iprs,
                normalized_comparison=False,
                reason=reason
            )
        
        # Check for missing IPRS serial
        if normalized_iprs is None:
            reason = _get_iprs_failure_reason(iprs_serial)
            logger.info("Serial number validation result", extra={
                "request_id": request_id,
                "status": "INCONCLUSIVE",
                "reason": reason
            })
            return SerialNumberValidationResult(
                status=ValidationStatus.INCONCLUSIVE,
                extracted_serial_number=normalized_extracted,
                iprs_serial_number=None,
                normalized_comparison=False,
                reason=reason
            )
        
        # Compare normalized values
        if normalized_extracted == normalized_iprs:
            logger.info("Serial number validation result", extra={
                "request_id": request_id,
                "status": "MATCH"
            })
            return SerialNumberValidationResult(
                status=ValidationStatus.MATCH,
                extracted_serial_number=normalized_extracted,
                iprs_serial_number=normalized_iprs,
                normalized_comparison=True,
                reason=None
            )
        else:
            reason = "Document serial number does not match IPRS record"
            logger.warning("Serial number mismatch detected", extra={
                "request_id": request_id,
                "status": "MISMATCH",
                "extracted_serial": normalized_extracted,
                "iprs_serial": normalized_iprs,
                "reason": reason
            })
            return SerialNumberValidationResult(
                status=ValidationStatus.MISMATCH,
                extracted_serial_number=normalized_extracted,
                iprs_serial_number=normalized_iprs,
                normalized_comparison=True,
                reason=reason
            )
    
    except Exception as e:
        # Non-blocking: catch all exceptions and return INCONCLUSIVE
        reason = f"Serial number validation error: {str(e)}"
        logger.error("Serial number validation failed", extra={
            "request_id": request_id,
            "error": str(e)
        })
        return SerialNumberValidationResult(
            status=ValidationStatus.INCONCLUSIVE,
            extracted_serial_number=None,
            iprs_serial_number=None,
            normalized_comparison=False,
            reason=reason
        )


def _get_extraction_failure_reason(original_value: Optional[str]) -> str:
    """Get appropriate reason message for extraction failure."""
    if original_value is None:
        return "Serial number not found in document"
    elif original_value.strip() == "":
        return "Serial number not found in document"
    else:
        return "Invalid serial number format"


def _get_iprs_failure_reason(original_value: Optional[str]) -> str:
    """Get appropriate reason message for IPRS failure."""
    if original_value is None:
        return "IPRS serial number unavailable"
    elif original_value.strip() == "":
        return "IPRS serial number unavailable"
    else:
        return "Invalid IPRS serial number format"
