"""
IPRS Response Schema Validation Module

Validates IPRS API responses against expected schema to detect schema drift early.
Emits CloudWatch metrics for monitoring and alerting.

Requirements: Schema validation for v1.2 features (serial number, gender, photo)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
metrics = Metrics(namespace="JubileeEKYC/IPRS")

# Schema version for tracking compatibility
IPRS_SCHEMA_VERSION = "1.2.0"


class SchemaValidationStatus(Enum):
    """Schema validation outcome status."""
    VALID = "VALID"
    INVALID = "INVALID"
    PARTIAL = "PARTIAL"


@dataclass
class SchemaValidationResult:
    """
    Result of IPRS response schema validation.
    
    Attributes:
        status: Validation outcome (VALID, INVALID, or PARTIAL)
        missing_fields: List of required fields that are missing
        null_fields: List of required fields that are present but null
        extra_fields: List of unexpected fields (informational)
        schema_version: Expected schema version
    """
    status: SchemaValidationStatus
    missing_fields: list[str]
    null_fields: list[str]
    extra_fields: list[str]
    schema_version: str = "1.0.0"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for logging/API response."""
        return {
            "status": self.status.value,
            "missingFields": self.missing_fields,
            "nullFields": self.null_fields,
            "extraFields": self.extra_fields,
            "schemaVersion": self.schema_version,
            "isValid": self.status == SchemaValidationStatus.VALID
        }


# Required fields for National ID IPRS response
NATIONAL_ID_REQUIRED_FIELDS = [
    "idNumber",
    "serialNumber",
    "firstName",
    "surname",
    "gender",
    "dateOfBirth",
    "dateOfIssue",
    "placeOfBirth"
]


# Optional fields (may be present)
NATIONAL_ID_OPTIONAL_FIELDS = [
    "otherName",
    "citizenship",
    "photo"
]

# v1.2 feature-specific required fields
V12_SERIAL_NUMBER_FIELDS = ["serialNumber"]
V12_GENDER_FIELDS = ["gender"]
V12_FACE_MATCHING_FIELDS = ["photo"]

# Passport response required fields
PASSPORT_REQUIRED_FIELDS = [
    "passportNumber",
    "firstName",
    "surname",
    "gender",
    "dateOfBirth",
    "dateOfIssue",
    "dateOfExpiry"
]


def validate_iprs_response_schema(
    response: dict,
    document_type: str = "national_id",
    request_id: Optional[str] = None
) -> SchemaValidationResult:
    """
    Validate IPRS response conforms to expected schema.
    
    Checks for required fields, null values, and unexpected fields.
    Emits CloudWatch metrics for monitoring schema drift.
    
    Args:
        response: Raw IPRS API response dictionary
        document_type: Type of document ("national_id" or "passport")
        request_id: Optional request ID for logging correlation
    
    Returns:
        SchemaValidationResult with validation details
    
    Example:
        >>> response = {"success": True, "data": {"idNumber": "123", ...}}
        >>> result = validate_iprs_response_schema(response)
        >>> result.status
        SchemaValidationStatus.VALID
    """
    # Check top-level response structure
    if not isinstance(response, dict):
        logger.error("IPRS response is not a dictionary", extra={
            "request_id": request_id,
            "response_type": type(response).__name__
        })
        _emit_schema_metric("INVALID", document_type, ["response_not_dict"])
        return SchemaValidationResult(
            status=SchemaValidationStatus.INVALID,
            missing_fields=["response_structure"],
            null_fields=[],
            extra_fields=[]
        )
    
    # Check success flag
    if not response.get("success"):
        error_msg = response.get("error", "Unknown error")
        logger.warning("IPRS response indicates failure", extra={
            "request_id": request_id,
            "error": error_msg
        })
        # This is a valid response structure, just unsuccessful
        return SchemaValidationResult(
            status=SchemaValidationStatus.VALID,
            missing_fields=[],
            null_fields=[],
            extra_fields=[]
        )
    
    # Get data payload
    data = response.get("data")
    if data is None:
        logger.error("IPRS response missing data field", extra={
            "request_id": request_id
        })
        _emit_schema_metric("INVALID", document_type, ["data_missing"])
        return SchemaValidationResult(
            status=SchemaValidationStatus.INVALID,
            missing_fields=["data"],
            null_fields=[],
            extra_fields=[]
        )
    
    # Select required fields based on document type
    if document_type == "passport":
        required_fields = PASSPORT_REQUIRED_FIELDS
        optional_fields = ["otherName", "nationality", "photo"]
    else:
        required_fields = NATIONAL_ID_REQUIRED_FIELDS
        optional_fields = NATIONAL_ID_OPTIONAL_FIELDS
    
    # Check for missing fields
    missing_fields = [f for f in required_fields if f not in data]
    
    # Check for null values in required fields
    null_fields = [
        f for f in required_fields 
        if f in data and data[f] is None
    ]
    
    # Identify extra fields (informational, not an error)
    all_expected = set(required_fields + optional_fields)
    extra_fields = [f for f in data.keys() if f not in all_expected]
    
    # Log validation details
    logger.info("IPRS schema validation completed", extra={
        "request_id": request_id,
        "document_type": document_type,
        "missing_fields": missing_fields,
        "null_fields": null_fields,
        "extra_fields": extra_fields
    })
    
    # Determine status
    if missing_fields or null_fields:
        if len(missing_fields) + len(null_fields) <= 2:
            status = SchemaValidationStatus.PARTIAL
        else:
            status = SchemaValidationStatus.INVALID
    else:
        status = SchemaValidationStatus.VALID
    
    # Emit metrics
    _emit_schema_metric(status.value, document_type, missing_fields + null_fields)
    
    return SchemaValidationResult(
        status=status,
        missing_fields=missing_fields,
        null_fields=null_fields,
        extra_fields=extra_fields
    )



def validate_v12_fields(
    response: dict,
    features: list[str],
    request_id: Optional[str] = None
) -> dict[str, SchemaValidationResult]:
    """
    Validate v1.2 feature-specific fields in IPRS response.
    
    Checks availability of fields required for specific v1.2 features:
    - serial_number: Requires serialNumber field
    - gender: Requires gender field
    - face_matching: Requires photo field
    
    Args:
        response: Raw IPRS API response dictionary
        features: List of features to validate ("serial_number", "gender", "face_matching")
        request_id: Optional request ID for logging correlation
    
    Returns:
        Dictionary mapping feature name to validation result
    
    Example:
        >>> result = validate_v12_fields(response, ["serial_number", "gender"])
        >>> result["serial_number"].status
        SchemaValidationStatus.VALID
    """
    results = {}
    data = response.get("data", {}) if response.get("success") else {}
    
    feature_field_map = {
        "serial_number": V12_SERIAL_NUMBER_FIELDS,
        "gender": V12_GENDER_FIELDS,
        "face_matching": V12_FACE_MATCHING_FIELDS
    }
    
    for feature in features:
        required = feature_field_map.get(feature, [])
        missing = [f for f in required if f not in data]
        null_fields = [f for f in required if f in data and data[f] is None]
        
        if missing or null_fields:
            status = SchemaValidationStatus.INVALID
        else:
            status = SchemaValidationStatus.VALID
        
        results[feature] = SchemaValidationResult(
            status=status,
            missing_fields=missing,
            null_fields=null_fields,
            extra_fields=[]
        )
        
        # Log feature-specific validation
        logger.info(f"v1.2 {feature} field validation", extra={
            "request_id": request_id,
            "feature": feature,
            "status": status.value,
            "missing": missing,
            "null": null_fields
        })
        
        # Emit feature-specific metric
        _emit_feature_metric(feature, status.value)
    
    return results


def extract_validated_field(
    response: dict,
    field_name: str,
    default: Optional[str] = None
) -> Optional[str]:
    """
    Safely extract a field from IPRS response with validation.
    
    Args:
        response: Raw IPRS API response dictionary
        field_name: Name of field to extract
        default: Default value if field is missing or null
    
    Returns:
        Field value or default
    """
    if not response.get("success"):
        return default
    
    data = response.get("data", {})
    value = data.get(field_name)
    
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return default
    
    return value


def _emit_schema_metric(
    status: str,
    document_type: str,
    problem_fields: list[str]
) -> None:
    """Emit CloudWatch metric for schema validation."""
    try:
        metrics.add_metric(
            name="SchemaValidation",
            unit=MetricUnit.Count,
            value=1
        )
        metrics.add_dimension(name="Status", value=status)
        metrics.add_dimension(name="DocumentType", value=document_type)
        
        # Emit specific metric for schema drift detection
        if status != "VALID":
            metrics.add_metric(
                name="SchemaDrift",
                unit=MetricUnit.Count,
                value=1
            )
            logger.warning("Schema drift detected", extra={
                "status": status,
                "document_type": document_type,
                "problem_fields": problem_fields
            })
    except Exception as e:
        logger.error(f"Failed to emit schema metric: {e}")


def _emit_feature_metric(feature: str, status: str) -> None:
    """Emit CloudWatch metric for v1.2 feature field availability."""
    try:
        metrics.add_metric(
            name=f"V12FieldAvailability_{feature}",
            unit=MetricUnit.Count,
            value=1 if status == "VALID" else 0
        )
        
        if status != "VALID":
            metrics.add_metric(
                name=f"V12FieldMissing_{feature}",
                unit=MetricUnit.Count,
                value=1
            )
    except Exception as e:
        logger.error(f"Failed to emit feature metric: {e}")



def emit_schema_validation_metric(
    metrics_instance,
    schema_valid: bool,
    missing_fields: list[str]
) -> None:
    """
    Emit CloudWatch metric for schema validation result.
    
    Args:
        metrics_instance: AWS Lambda Powertools Metrics instance
        schema_valid: Whether schema validation passed
        missing_fields: List of missing field names
    """
    try:
        metrics_instance.add_metric(
            name="IPRSSchemaValidation",
            unit=MetricUnit.Count,
            value=1 if schema_valid else 0
        )
        
        if not schema_valid and missing_fields:
            metrics_instance.add_metric(
                name="IPRSSchemaMissingFields",
                unit=MetricUnit.Count,
                value=len(missing_fields)
            )
    except Exception as e:
        logger.error(f"Failed to emit schema validation metric: {e}")


def check_schema_compatibility(
    response: dict,
    required_features: list[str] = None
) -> tuple[bool, list[str], str]:
    """
    Check if IPRS response schema is compatible with required features.
    
    Args:
        response: Raw IPRS API response dictionary
        required_features: List of features requiring validation
    
    Returns:
        Tuple of (is_valid, missing_fields, error_message)
    """
    if required_features is None:
        required_features = ["serial_number", "gender"]
    
    if not isinstance(response, dict):
        return False, [], "Response is not a dictionary"
    
    if not response.get("success"):
        return True, [], ""  # Unsuccessful response is valid structure
    
    data = response.get("data", {})
    if not data:
        return False, ["data"], "Missing data field"
    
    missing = []
    for feature in required_features:
        if feature == "serial_number" and "serialNumber" not in data:
            missing.append("serialNumber")
        elif feature == "gender" and "gender" not in data:
            missing.append("gender")
        elif feature == "face_matching" and "photo" not in data:
            missing.append("photo")
    
    if missing:
        return False, missing, f"Missing fields: {', '.join(missing)}"
    
    return True, [], ""
