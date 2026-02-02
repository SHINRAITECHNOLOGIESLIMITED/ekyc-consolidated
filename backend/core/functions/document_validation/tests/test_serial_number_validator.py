"""
Unit Tests for Serial Number Validator

Tests specific examples and edge cases for the serial_number_validator module.
"""

import pytest
from serial_number_validator import (
    validate_serial_number,
    ValidationStatus,
    SerialNumberValidationResult
)


class TestValidateSerialNumber:
    """Unit tests for validate_serial_number function."""
    
    def test_match_identical_serials(self):
        """MATCH when serial numbers are identical."""
        result = validate_serial_number("12345ABC", "12345ABC")
        assert result.status == ValidationStatus.MATCH
        assert result.reason is None
    
    def test_match_after_normalization(self):
        """MATCH when serials match after normalization."""
        result = validate_serial_number("12345-ABC", "12345 ABC")
        assert result.status == ValidationStatus.MATCH
    
    def test_match_case_insensitive(self):
        """MATCH when serials differ only in case."""
        result = validate_serial_number("12345abc", "12345ABC")
        assert result.status == ValidationStatus.MATCH
    
    def test_mismatch_different_serials(self):
        """MISMATCH when serial numbers differ."""
        result = validate_serial_number("12345ABC", "67890XYZ")
        assert result.status == ValidationStatus.MISMATCH
        assert result.reason is not None
        assert "does not match" in result.reason
    
    def test_inconclusive_none_extracted(self):
        """INCONCLUSIVE when extracted serial is None."""
        result = validate_serial_number(None, "12345ABC")
        assert result.status == ValidationStatus.INCONCLUSIVE
        assert result.reason is not None
        assert "not found" in result.reason.lower()
    
    def test_inconclusive_none_iprs(self):
        """INCONCLUSIVE when IPRS serial is None."""
        result = validate_serial_number("12345ABC", None)
        assert result.status == ValidationStatus.INCONCLUSIVE
        assert result.reason is not None
        assert "unavailable" in result.reason.lower()
    
    def test_inconclusive_both_none(self):
        """INCONCLUSIVE when both serials are None."""
        result = validate_serial_number(None, None)
        assert result.status == ValidationStatus.INCONCLUSIVE
    
    def test_inconclusive_empty_extracted(self):
        """INCONCLUSIVE when extracted serial is empty."""
        result = validate_serial_number("", "12345ABC")
        assert result.status == ValidationStatus.INCONCLUSIVE
    
    def test_inconclusive_empty_iprs(self):
        """INCONCLUSIVE when IPRS serial is empty."""
        result = validate_serial_number("12345ABC", "")
        assert result.status == ValidationStatus.INCONCLUSIVE
    
    def test_inconclusive_whitespace_only(self):
        """INCONCLUSIVE when serial is whitespace only."""
        result = validate_serial_number("   ", "12345ABC")
        assert result.status == ValidationStatus.INCONCLUSIVE
    
    def test_inconclusive_formatting_only(self):
        """INCONCLUSIVE when serial is formatting chars only."""
        result = validate_serial_number("---", "12345ABC")
        assert result.status == ValidationStatus.INCONCLUSIVE


class TestSerialNumberValidationResultToDict:
    """Tests for SerialNumberValidationResult.to_dict() method."""
    
    def test_to_dict_match(self):
        """to_dict returns correct structure for MATCH."""
        result = validate_serial_number("12345ABC", "12345ABC")
        result_dict = result.to_dict()
        
        assert result_dict['status'] == 'MATCH'
        assert result_dict['extractedSerialNumber'] == '12345ABC'
        assert result_dict['iprsSerialNumber'] == '12345ABC'
        assert result_dict['normalizedComparison'] is True
        assert result_dict['reason'] is None
    
    def test_to_dict_mismatch(self):
        """to_dict returns correct structure for MISMATCH."""
        result = validate_serial_number("12345ABC", "67890XYZ")
        result_dict = result.to_dict()
        
        assert result_dict['status'] == 'MISMATCH'
        assert result_dict['extractedSerialNumber'] == '12345ABC'
        assert result_dict['iprsSerialNumber'] == '67890XYZ'
        assert result_dict['normalizedComparison'] is True
        assert result_dict['reason'] is not None
    
    def test_to_dict_inconclusive(self):
        """to_dict returns correct structure for INCONCLUSIVE."""
        result = validate_serial_number(None, "12345ABC")
        result_dict = result.to_dict()
        
        assert result_dict['status'] == 'INCONCLUSIVE'
        assert result_dict['extractedSerialNumber'] is None
        assert result_dict['iprsSerialNumber'] == '12345ABC'
        assert result_dict['normalizedComparison'] is False
        assert result_dict['reason'] is not None
    
    def test_to_dict_backward_compatible(self):
        """to_dict structure is backward compatible with existing API."""
        result = validate_serial_number("12345ABC", "12345ABC")
        result_dict = result.to_dict()
        
        # All required fields must be present
        required_fields = ['status', 'extractedSerialNumber', 'iprsSerialNumber', 
                          'normalizedComparison', 'reason']
        for field in required_fields:
            assert field in result_dict, f"Missing required field: {field}"


class TestRealWorldSerialNumbers:
    """Tests with real-world serial number formats from test data."""
    
    def test_known_serial_217990310(self):
        """Test with known serial number from test data."""
        result = validate_serial_number("217990310", "217990310")
        assert result.status == ValidationStatus.MATCH
    
    def test_known_serial_702945559(self):
        """Test with known serial number from test data."""
        result = validate_serial_number("702945559", "702945559")
        assert result.status == ValidationStatus.MATCH
    
    def test_known_serial_244772451(self):
        """Test with known serial number from test data."""
        result = validate_serial_number("244772451", "244772451")
        assert result.status == ValidationStatus.MATCH
    
    def test_known_serial_229769449(self):
        """Test with known serial number from test data."""
        result = validate_serial_number("229769449", "229769449")
        assert result.status == ValidationStatus.MATCH
    
    def test_mismatch_replaced_id(self):
        """Test mismatch scenario - old serial vs new serial (replaced ID)."""
        # Simulates a customer presenting an old ID after getting a replacement
        result = validate_serial_number("217990310", "229769449")
        assert result.status == ValidationStatus.MISMATCH
        assert "does not match" in result.reason
