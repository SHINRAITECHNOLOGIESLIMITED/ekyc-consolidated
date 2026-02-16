"""
Tests for IPRS Response Schema Validation Module

Unit tests and property-based tests for schema validation.
"""

import sys
from unittest.mock import MagicMock

# Mock aws_lambda_powertools before importing iprs_schema
mock_logger = MagicMock()
mock_metrics = MagicMock()
sys.modules['aws_lambda_powertools'] = MagicMock()
sys.modules['aws_lambda_powertools'].Logger = MagicMock(return_value=mock_logger)
sys.modules['aws_lambda_powertools'].Metrics = MagicMock(return_value=mock_metrics)
sys.modules['aws_lambda_powertools.metrics'] = MagicMock()
sys.modules['aws_lambda_powertools.metrics'].MetricUnit = MagicMock()

import pytest

from iprs_schema import (
    validate_iprs_response_schema,
    validate_v12_fields,
    extract_validated_field,
    SchemaValidationStatus,
    SchemaValidationResult,
    NATIONAL_ID_REQUIRED_FIELDS
)


class TestValidateIPRSResponseSchema:
    """Tests for validate_iprs_response_schema function."""
    
    def test_valid_complete_response(self):
        """VALID when all required fields present."""
        response = {
            "success": True,
            "error": None,
            "data": {
                "idNumber": "23224868",
                "serialNumber": "229769449",
                "firstName": "STEPHEN",
                "otherName": "BIKO",
                "surname": "NYAMAI",
                "gender": "M",
                "dateOfBirth": "2/19/1984",
                "dateOfIssue": "4/1/2003",
                "placeOfBirth": "NAIROBI"
            }
        }
        
        result = validate_iprs_response_schema(response)
        
        assert result.status == SchemaValidationStatus.VALID
        assert result.missing_fields == []
        assert result.null_fields == []
    
    def test_invalid_missing_required_fields(self):
        """INVALID when multiple required fields missing."""
        response = {
            "success": True,
            "data": {
                "idNumber": "23224868",
                "firstName": "STEPHEN"
            }
        }
        
        result = validate_iprs_response_schema(response)
        
        assert result.status == SchemaValidationStatus.INVALID
        assert "serialNumber" in result.missing_fields
        assert "surname" in result.missing_fields
        assert "gender" in result.missing_fields
    
    def test_partial_few_missing_fields(self):
        """PARTIAL when only 1-2 fields missing."""
        response = {
            "success": True,
            "data": {
                "idNumber": "23224868",
                "serialNumber": "229769449",
                "firstName": "STEPHEN",
                "surname": "NYAMAI",
                "gender": "M",
                "dateOfBirth": "2/19/1984",
                "dateOfIssue": "4/1/2003"
                # Missing: placeOfBirth
            }
        }
        
        result = validate_iprs_response_schema(response)
        
        assert result.status == SchemaValidationStatus.PARTIAL
        assert "placeOfBirth" in result.missing_fields
    
    def test_null_required_field(self):
        """Detects null values in required fields."""
        response = {
            "success": True,
            "data": {
                "idNumber": "23224868",
                "serialNumber": None,  # Null value
                "firstName": "STEPHEN",
                "surname": "NYAMAI",
                "gender": "M",
                "dateOfBirth": "2/19/1984",
                "dateOfIssue": "4/1/2003",
                "placeOfBirth": "NAIROBI"
            }
        }
        
        result = validate_iprs_response_schema(response)
        
        assert "serialNumber" in result.null_fields
    
    def test_unsuccessful_response_is_valid_structure(self):
        """Unsuccessful IPRS response is still valid schema."""
        response = {
            "success": False,
            "error": "ID number not found",
            "data": None
        }
        
        result = validate_iprs_response_schema(response)
        
        assert result.status == SchemaValidationStatus.VALID
    
    def test_missing_data_field(self):
        """INVALID when data field is missing entirely."""
        response = {
            "success": True
        }
        
        result = validate_iprs_response_schema(response)
        
        assert result.status == SchemaValidationStatus.INVALID
        assert "data" in result.missing_fields
    
    def test_extra_fields_detected(self):
        """Extra fields are detected but don't cause failure."""
        response = {
            "success": True,
            "data": {
                "idNumber": "23224868",
                "serialNumber": "229769449",
                "firstName": "STEPHEN",
                "surname": "NYAMAI",
                "gender": "M",
                "dateOfBirth": "2/19/1984",
                "dateOfIssue": "4/1/2003",
                "placeOfBirth": "NAIROBI",
                "unexpectedField": "some value"
            }
        }
        
        result = validate_iprs_response_schema(response)
        
        assert result.status == SchemaValidationStatus.VALID
        assert "unexpectedField" in result.extra_fields
    
    def test_passport_document_type(self):
        """Validates passport-specific required fields."""
        response = {
            "success": True,
            "data": {
                "passportNumber": "AK1577133",
                "firstName": "STEPHEN",
                "surname": "NYAMAI",
                "gender": "M",
                "dateOfBirth": "2/19/1984",
                "dateOfIssue": "1/15/2020",
                "dateOfExpiry": "1/14/2030"
            }
        }
        
        result = validate_iprs_response_schema(response, document_type="passport")
        
        assert result.status == SchemaValidationStatus.VALID



class TestValidateV12Fields:
    """Tests for v1.2 feature-specific field validation."""
    
    def test_serial_number_field_present(self):
        """VALID when serialNumber field is present."""
        response = {
            "success": True,
            "data": {"serialNumber": "229769449"}
        }
        
        results = validate_v12_fields(response, ["serial_number"])
        
        assert results["serial_number"].status == SchemaValidationStatus.VALID
    
    def test_serial_number_field_missing(self):
        """INVALID when serialNumber field is missing."""
        response = {
            "success": True,
            "data": {"idNumber": "23224868"}
        }
        
        results = validate_v12_fields(response, ["serial_number"])
        
        assert results["serial_number"].status == SchemaValidationStatus.INVALID
        assert "serialNumber" in results["serial_number"].missing_fields
    
    def test_gender_field_present(self):
        """VALID when gender field is present."""
        response = {
            "success": True,
            "data": {"gender": "M"}
        }
        
        results = validate_v12_fields(response, ["gender"])
        
        assert results["gender"].status == SchemaValidationStatus.VALID
    
    def test_gender_field_null(self):
        """INVALID when gender field is null."""
        response = {
            "success": True,
            "data": {"gender": None}
        }
        
        results = validate_v12_fields(response, ["gender"])
        
        assert results["gender"].status == SchemaValidationStatus.INVALID
        assert "gender" in results["gender"].null_fields
    
    def test_face_matching_photo_present(self):
        """VALID when photo field is present."""
        response = {
            "success": True,
            "data": {"photo": "base64encodedstring"}
        }
        
        results = validate_v12_fields(response, ["face_matching"])
        
        assert results["face_matching"].status == SchemaValidationStatus.VALID
    
    def test_face_matching_photo_missing(self):
        """INVALID when photo field is missing."""
        response = {
            "success": True,
            "data": {"idNumber": "23224868"}
        }
        
        results = validate_v12_fields(response, ["face_matching"])
        
        assert results["face_matching"].status == SchemaValidationStatus.INVALID
        assert "photo" in results["face_matching"].missing_fields
    
    def test_multiple_features(self):
        """Validates multiple features at once."""
        response = {
            "success": True,
            "data": {
                "serialNumber": "229769449",
                "gender": "M"
                # photo missing
            }
        }
        
        results = validate_v12_fields(
            response, 
            ["serial_number", "gender", "face_matching"]
        )
        
        assert results["serial_number"].status == SchemaValidationStatus.VALID
        assert results["gender"].status == SchemaValidationStatus.VALID
        assert results["face_matching"].status == SchemaValidationStatus.INVALID
    
    def test_unsuccessful_response(self):
        """All features INVALID when response unsuccessful."""
        response = {
            "success": False,
            "error": "Not found",
            "data": None
        }
        
        results = validate_v12_fields(
            response, 
            ["serial_number", "gender", "face_matching"]
        )
        
        assert results["serial_number"].status == SchemaValidationStatus.INVALID
        assert results["gender"].status == SchemaValidationStatus.INVALID
        assert results["face_matching"].status == SchemaValidationStatus.INVALID


class TestExtractValidatedField:
    """Tests for extract_validated_field helper."""
    
    def test_extract_existing_field(self):
        """Returns field value when present."""
        response = {
            "success": True,
            "data": {"serialNumber": "229769449"}
        }
        
        value = extract_validated_field(response, "serialNumber")
        
        assert value == "229769449"
    
    def test_extract_missing_field_returns_default(self):
        """Returns default when field missing."""
        response = {
            "success": True,
            "data": {"idNumber": "23224868"}
        }
        
        value = extract_validated_field(response, "serialNumber", default="N/A")
        
        assert value == "N/A"
    
    def test_extract_null_field_returns_default(self):
        """Returns default when field is null."""
        response = {
            "success": True,
            "data": {"serialNumber": None}
        }
        
        value = extract_validated_field(response, "serialNumber", default="N/A")
        
        assert value == "N/A"
    
    def test_extract_empty_string_returns_default(self):
        """Returns default when field is empty string."""
        response = {
            "success": True,
            "data": {"serialNumber": "   "}
        }
        
        value = extract_validated_field(response, "serialNumber", default="N/A")
        
        assert value == "N/A"
    
    def test_extract_from_unsuccessful_response(self):
        """Returns default when response unsuccessful."""
        response = {
            "success": False,
            "data": {"serialNumber": "229769449"}
        }
        
        value = extract_validated_field(response, "serialNumber", default="N/A")
        
        assert value == "N/A"


class TestSchemaValidationResult:
    """Tests for SchemaValidationResult dataclass."""
    
    def test_to_dict(self):
        """Converts to dictionary correctly."""
        result = SchemaValidationResult(
            status=SchemaValidationStatus.PARTIAL,
            missing_fields=["photo"],
            null_fields=["citizenship"],
            extra_fields=["newField"]
        )
        
        d = result.to_dict()
        
        assert d["status"] == "PARTIAL"
        assert d["missingFields"] == ["photo"]
        assert d["nullFields"] == ["citizenship"]
        assert d["extraFields"] == ["newField"]
        assert d["isValid"] is False
    
    def test_is_valid_true_for_valid_status(self):
        """isValid is True only for VALID status."""
        valid_result = SchemaValidationResult(
            status=SchemaValidationStatus.VALID,
            missing_fields=[],
            null_fields=[],
            extra_fields=[]
        )
        
        assert valid_result.to_dict()["isValid"] is True