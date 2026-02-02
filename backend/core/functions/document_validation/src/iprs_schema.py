"""
IPRS Response Schema Definition and Validation

Defines the expected schema for IPRS API responses and provides validation
to detect schema changes that could break validation logic.

Schema Version: 1.0.0
Last Updated: January 2026
"""

import os
from typing import Dict, List, Optional, Tuple
from aws_lambda_powertools import Logger
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()

# Metrics namespace for IPRS validation
METRICS_NAMESPACE = os.environ.get('METRICS_NAMESPACE', 'JubileeEKYC/DocumentValidation')

# Schema version - update when IPRS response structure changes
IPRS_SCHEMA_VERSION = "1.0.0"

# SSM Parameter name for schema version (can be overridden via environment)
IPRS_SCHEMA_VERSION_PARAM = os.environ.get(
    'IPRS_SCHEMA_VERSION_PARAM',
    '/jubilee-ekyc/esb/iprs-schema-version'
)

# Required fields for National ID validation
REQUIRED_FIELDS_NATIONAL_ID = [
    'idNumber',
    'serialNumber',
    'firstName',
    'surname',
    'gender',
    'dateOfBirth',
    'dateOfIssue',
    'placeOfBirth'
]

# Optional fields that may be present
OPTIONAL_FIELDS_NATIONAL_ID = [
    'otherName',
    'citizenship',
    'photo'
]


def validate_iprs_response_schema(
    response: Dict,
    document_type: str = "NATIONAL_ID"
) -> Tuple[bool, List[str], Optional[str]]:
    """
    Validate that an IPRS response conforms to the expected schema.
    
    Args:
        response: The IPRS API response dictionary
        document_type: Type of document being validated (NATIONAL_ID, PASSPORT, etc.)
    
    Returns:
        Tuple of (is_valid, missing_fields, error_message)
        - is_valid: True if schema is valid
        - missing_fields: List of missing required fields
        - error_message: Error description if validation failed
    """
    # Check for success flag
    if not response.get('success'):
        return False, [], "IPRS response indicates failure"
    
    # Check for data object
    data = response.get('data')
    if not data:
        return False, [], "IPRS response missing 'data' field"
    
    if not isinstance(data, dict):
        return False, [], "IPRS response 'data' is not a dictionary"
    
    # Get required fields based on document type
    if document_type == "NATIONAL_ID":
        required_fields = REQUIRED_FIELDS_NATIONAL_ID
    else:
        # Default to National ID fields for now
        required_fields = REQUIRED_FIELDS_NATIONAL_ID
    
    # Check for missing required fields
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        logger.warning("IPRS schema validation - missing fields", extra={
            "missing_fields": missing_fields,
            "document_type": document_type,
            "schema_version": IPRS_SCHEMA_VERSION
        })
        return False, missing_fields, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Check for null values in critical fields
    null_critical_fields = []
    critical_fields = ['serialNumber', 'gender']
    for field in critical_fields:
        if data.get(field) is None:
            null_critical_fields.append(field)
    
    if null_critical_fields:
        logger.warning("IPRS schema validation - null critical fields", extra={
            "null_fields": null_critical_fields,
            "document_type": document_type
        })
        # This is a warning, not a failure - fields exist but are null
    
    logger.info("IPRS schema validation passed", extra={
        "document_type": document_type,
        "schema_version": IPRS_SCHEMA_VERSION,
        "has_serial": data.get('serialNumber') is not None,
        "has_gender": data.get('gender') is not None
    })
    
    return True, [], None


def get_schema_version() -> str:
    """
    Get the current IPRS schema version.
    
    In production, this could be fetched from SSM Parameter Store
    to allow dynamic updates without redeployment.
    
    Returns:
        Schema version string
    """
    # For now, return the hardcoded version
    # TODO: Implement SSM Parameter Store lookup for production
    return IPRS_SCHEMA_VERSION


def check_schema_compatibility(response: Dict) -> Dict:
    """
    Check if the IPRS response is compatible with the current schema version.
    
    Returns a dict with compatibility information for logging/metrics.
    
    Args:
        response: The IPRS API response
    
    Returns:
        Dict with keys: compatible, version, missing_fields, warnings
    """
    is_valid, missing_fields, error = validate_iprs_response_schema(response)
    
    result = {
        "compatible": is_valid,
        "version": IPRS_SCHEMA_VERSION,
        "missing_fields": missing_fields,
        "error": error,
        "warnings": []
    }
    
    # Check for unexpected fields (schema evolution)
    if is_valid:
        data = response.get('data', {})
        known_fields = set(REQUIRED_FIELDS_NATIONAL_ID + OPTIONAL_FIELDS_NATIONAL_ID)
        actual_fields = set(data.keys())
        new_fields = actual_fields - known_fields
        
        if new_fields:
            result["warnings"].append(f"New fields detected: {', '.join(new_fields)}")
            logger.info("IPRS schema - new fields detected", extra={
                "new_fields": list(new_fields),
                "schema_version": IPRS_SCHEMA_VERSION
            })
    
    return result


def emit_schema_validation_metric(metrics, is_valid: bool, missing_fields: List[str] = None):
    """
    Emit CloudWatch metrics for IPRS schema validation.
    
    This function emits metrics that can be used to create CloudWatch alarms
    for schema mismatch detection.
    
    Args:
        metrics: AWS Lambda Powertools Metrics instance
        is_valid: Whether schema validation passed
        missing_fields: List of missing fields (if any)
    """
    try:
        # Emit schema validation result metric
        metrics.add_metric(
            name="IPRSSchemaValidation",
            unit=MetricUnit.Count,
            value=1 if is_valid else 0
        )
        
        # Emit schema mismatch metric (for alarming)
        if not is_valid:
            metrics.add_metric(
                name="IPRSSchemaMismatch",
                unit=MetricUnit.Count,
                value=1
            )
            
            # Add dimension for missing fields count
            metrics.add_dimension(
                name="MissingFieldsCount",
                value=str(len(missing_fields) if missing_fields else 0)
            )
            
            logger.warning("IPRS schema mismatch metric emitted", extra={
                "missing_fields": missing_fields,
                "schema_version": IPRS_SCHEMA_VERSION
            })
        else:
            # Emit zero for mismatch when valid (for consistent metric)
            metrics.add_metric(
                name="IPRSSchemaMismatch",
                unit=MetricUnit.Count,
                value=0
            )
            
    except Exception as e:
        # Don't fail validation due to metrics emission error
        logger.error("Failed to emit schema validation metric", extra={
            "error": str(e)
        })
