"""
Property-Based Tests for Serial Number Validator

Tests the serial_number_validator module using Hypothesis for property-based testing.
Each test validates specific correctness properties defined in the design document.
"""

import string
from hypothesis import given, strategies as st, settings, assume

from serial_number_validator import (
    validate_serial_number,
    ValidationStatus,
    SerialNumberValidationResult
)
from normalizer import normalize_serial_number


# Test configuration
test_settings = settings(max_examples=100, deadline=None)


# Strategies for generating test data
serial_chars = string.ascii_uppercase + string.digits
formatting_chars = ' -.'

# Valid serial numbers (non-empty after normalization)
valid_serial = st.text(alphabet=serial_chars, min_size=1, max_size=15)

# Serial numbers with formatting
formatted_serial = st.text(alphabet=serial_chars + formatting_chars, min_size=1, max_size=20)

# Optional serial (including None and empty)
optional_serial = st.one_of(
    st.none(),
    st.just(""),
    st.just("   "),
    st.just("---"),
    valid_serial
)


def add_random_formatting(base: str) -> str:
    """Add random formatting characters to a serial number."""
    import random
    if not base:
        return base
    result = list(base)
    for _ in range(random.randint(0, 3)):
        pos = random.randint(0, len(result))
        char = random.choice([' ', '-', '.'])
        result.insert(pos, char)
    return ''.join(result)


class TestMatchDecisionCorrectness:
    """
    Property 4: MATCH Decision Correctness
    
    For any two non-empty serial numbers where the normalized values are identical,
    the validation function SHALL return status MATCH.
    
    Validates: Requirements 3.1, 3.2
    """
    
    @test_settings
    @given(valid_serial)
    def test_identical_serials_match(self, serial):
        """
        Feature: serial-number-validation, Property 4: MATCH Decision Correctness
        Validates: Requirements 3.1, 3.2
        """
        result = validate_serial_number(serial, serial)
        assert result.status == ValidationStatus.MATCH, \
            f"Expected MATCH for identical serials {serial!r}, got {result.status}"
    
    @test_settings
    @given(valid_serial)
    def test_formatted_serials_match(self, base_serial):
        """
        Feature: serial-number-validation, Property 4: MATCH Decision Correctness (formatted)
        Validates: Requirements 3.1, 3.2
        """
        # Create two versions with different formatting
        version1 = add_random_formatting(base_serial)
        version2 = add_random_formatting(base_serial)
        
        result = validate_serial_number(version1, version2)
        assert result.status == ValidationStatus.MATCH, \
            f"Expected MATCH for {version1!r} vs {version2!r}, got {result.status}"
    
    @test_settings
    @given(valid_serial)
    def test_case_insensitive_match(self, serial):
        """
        Feature: serial-number-validation, Property 4: MATCH Decision Correctness (case)
        Validates: Requirements 3.1, 3.2
        """
        result = validate_serial_number(serial.lower(), serial.upper())
        assert result.status == ValidationStatus.MATCH, \
            f"Expected MATCH for case variants, got {result.status}"


class TestMismatchDecisionCorrectness:
    """
    Property 5: MISMATCH Decision Correctness
    
    For any two non-empty serial numbers where the normalized values differ,
    the validation function SHALL return status MISMATCH with a non-empty reason.
    
    Validates: Requirements 3.3, 6.6
    """
    
    @test_settings
    @given(valid_serial, valid_serial)
    def test_different_serials_mismatch(self, serial1, serial2):
        """
        Feature: serial-number-validation, Property 5: MISMATCH Decision Correctness
        Validates: Requirements 3.3, 6.6
        """
        # Only test if normalized values are actually different
        norm1 = normalize_serial_number(serial1)
        norm2 = normalize_serial_number(serial2)
        assume(norm1 != norm2)
        
        result = validate_serial_number(serial1, serial2)
        assert result.status == ValidationStatus.MISMATCH, \
            f"Expected MISMATCH for {serial1!r} vs {serial2!r}, got {result.status}"
        assert result.reason is not None and result.reason != "", \
            f"MISMATCH should have non-empty reason, got {result.reason!r}"


class TestInconclusiveForMissingData:
    """
    Property 6: INCONCLUSIVE for Missing Data
    
    For any validation request where either the extracted serial number or IPRS serial number
    is None, empty, or unavailable, the validation function SHALL return status INCONCLUSIVE
    with a non-empty reason.
    
    Validates: Requirements 1.3, 1.4, 2.4, 2.5, 3.4, 8.1, 8.2, 8.5
    """
    
    @test_settings
    @given(valid_serial)
    def test_none_extracted_is_inconclusive(self, iprs_serial):
        """
        Feature: serial-number-validation, Property 6: INCONCLUSIVE for Missing Data (extracted=None)
        Validates: Requirements 1.3, 3.4, 8.1
        """
        result = validate_serial_number(None, iprs_serial)
        assert result.status == ValidationStatus.INCONCLUSIVE, \
            f"Expected INCONCLUSIVE when extracted is None, got {result.status}"
        assert result.reason is not None and result.reason != "", \
            f"INCONCLUSIVE should have non-empty reason"
    
    @test_settings
    @given(valid_serial)
    def test_none_iprs_is_inconclusive(self, extracted_serial):
        """
        Feature: serial-number-validation, Property 6: INCONCLUSIVE for Missing Data (iprs=None)
        Validates: Requirements 2.4, 3.4, 8.2
        """
        result = validate_serial_number(extracted_serial, None)
        assert result.status == ValidationStatus.INCONCLUSIVE, \
            f"Expected INCONCLUSIVE when IPRS is None, got {result.status}"
        assert result.reason is not None and result.reason != "", \
            f"INCONCLUSIVE should have non-empty reason"
    
    def test_both_none_is_inconclusive(self):
        """
        Feature: serial-number-validation, Property 6: INCONCLUSIVE for Missing Data (both=None)
        Validates: Requirements 3.4
        """
        result = validate_serial_number(None, None)
        assert result.status == ValidationStatus.INCONCLUSIVE
        assert result.reason is not None and result.reason != ""
    
    @test_settings
    @given(valid_serial)
    def test_empty_extracted_is_inconclusive(self, iprs_serial):
        """
        Feature: serial-number-validation, Property 6: INCONCLUSIVE for Missing Data (extracted="")
        Validates: Requirements 1.4, 3.4
        """
        result = validate_serial_number("", iprs_serial)
        assert result.status == ValidationStatus.INCONCLUSIVE
        assert result.reason is not None and result.reason != ""
    
    @test_settings
    @given(valid_serial)
    def test_empty_iprs_is_inconclusive(self, extracted_serial):
        """
        Feature: serial-number-validation, Property 6: INCONCLUSIVE for Missing Data (iprs="")
        Validates: Requirements 2.4, 3.4
        """
        result = validate_serial_number(extracted_serial, "")
        assert result.status == ValidationStatus.INCONCLUSIVE
        assert result.reason is not None and result.reason != ""
    
    @test_settings
    @given(valid_serial)
    def test_whitespace_only_extracted_is_inconclusive(self, iprs_serial):
        """
        Feature: serial-number-validation, Property 6: INCONCLUSIVE for Missing Data (extracted=whitespace)
        Validates: Requirements 1.4, 3.4
        """
        result = validate_serial_number("   ", iprs_serial)
        assert result.status == ValidationStatus.INCONCLUSIVE
        assert result.reason is not None and result.reason != ""
    
    @test_settings
    @given(valid_serial)
    def test_formatting_only_extracted_is_inconclusive(self, iprs_serial):
        """
        Feature: serial-number-validation, Property 6: INCONCLUSIVE for Missing Data (extracted=formatting)
        Validates: Requirements 1.4, 3.4
        """
        result = validate_serial_number("---", iprs_serial)
        assert result.status == ValidationStatus.INCONCLUSIVE
        assert result.reason is not None and result.reason != ""



class TestResponseStructureCompleteness:
    """
    Property 7: Response Structure Completeness
    
    For any validation result, the serialNumberValidation object SHALL contain:
    status (one of MATCH, MISMATCH, INCONCLUSIVE), extractedSerialNumber (string or null),
    iprsSerialNumber (string or null), and normalizedComparison (boolean).
    
    Validates: Requirements 5.2, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5
    """
    
    @test_settings
    @given(optional_serial, optional_serial)
    def test_response_has_required_fields(self, extracted, iprs):
        """
        Feature: serial-number-validation, Property 7: Response Structure Completeness
        Validates: Requirements 5.2, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5
        """
        result = validate_serial_number(extracted, iprs)
        
        # Check result object has all required attributes
        assert hasattr(result, 'status')
        assert hasattr(result, 'extracted_serial_number')
        assert hasattr(result, 'iprs_serial_number')
        assert hasattr(result, 'normalized_comparison')
        assert hasattr(result, 'reason')
        
        # Check status is valid enum value
        assert result.status in ValidationStatus
        
        # Check normalized_comparison is boolean
        assert isinstance(result.normalized_comparison, bool)
    
    @test_settings
    @given(optional_serial, optional_serial)
    def test_to_dict_has_required_fields(self, extracted, iprs):
        """
        Feature: serial-number-validation, Property 7: Response Structure Completeness (dict)
        Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5
        """
        result = validate_serial_number(extracted, iprs)
        result_dict = result.to_dict()
        
        # Check all required fields exist
        assert 'status' in result_dict
        assert 'extractedSerialNumber' in result_dict
        assert 'iprsSerialNumber' in result_dict
        assert 'normalizedComparison' in result_dict
        assert 'reason' in result_dict
        
        # Check status is string value
        assert result_dict['status'] in ['MATCH', 'MISMATCH', 'INCONCLUSIVE']
        
        # Check normalizedComparison is boolean
        assert isinstance(result_dict['normalizedComparison'], bool)


class TestReasonPresenceForNonMatch:
    """
    Property 9: Reason Presence for Non-MATCH
    
    For any validation result where status is MISMATCH or INCONCLUSIVE,
    the reason field SHALL be non-null and non-empty.
    
    Validates: Requirements 6.6
    """
    
    @test_settings
    @given(optional_serial, optional_serial)
    def test_non_match_has_reason(self, extracted, iprs):
        """
        Feature: serial-number-validation, Property 9: Reason Presence for Non-MATCH
        Validates: Requirements 6.6
        """
        result = validate_serial_number(extracted, iprs)
        
        if result.status in (ValidationStatus.MISMATCH, ValidationStatus.INCONCLUSIVE):
            assert result.reason is not None, \
                f"Non-MATCH status {result.status} should have reason, got None"
            assert result.reason != "", \
                f"Non-MATCH status {result.status} should have non-empty reason"
    
    @test_settings
    @given(valid_serial)
    def test_match_has_no_reason(self, serial):
        """
        Feature: serial-number-validation, Property 9: Reason Presence (MATCH has no reason)
        Validates: Requirements 6.6
        """
        result = validate_serial_number(serial, serial)
        
        if result.status == ValidationStatus.MATCH:
            assert result.reason is None, \
                f"MATCH status should have no reason, got {result.reason!r}"


class TestAuditDataCompleteness:
    """
    Property 10: Audit Data Completeness
    
    For any validation result, both extractedSerialNumber and iprsSerialNumber fields
    SHALL be present in the response (may be null if unavailable, but field must exist).
    
    Validates: Requirements 4.4
    """
    
    @test_settings
    @given(optional_serial, optional_serial)
    def test_audit_fields_always_present(self, extracted, iprs):
        """
        Feature: serial-number-validation, Property 10: Audit Data Completeness
        Validates: Requirements 4.4
        """
        result = validate_serial_number(extracted, iprs)
        result_dict = result.to_dict()
        
        # Fields must exist (even if None)
        assert 'extractedSerialNumber' in result_dict, \
            "extractedSerialNumber field must be present"
        assert 'iprsSerialNumber' in result_dict, \
            "iprsSerialNumber field must be present"
    
    @test_settings
    @given(valid_serial, valid_serial)
    def test_audit_fields_contain_normalized_values(self, extracted, iprs):
        """
        Feature: serial-number-validation, Property 10: Audit Data Completeness (values)
        Validates: Requirements 4.4
        """
        result = validate_serial_number(extracted, iprs)
        
        # When inputs are valid, outputs should be normalized versions
        if result.extracted_serial_number is not None:
            assert result.extracted_serial_number == result.extracted_serial_number.upper()
            assert ' ' not in result.extracted_serial_number
            assert '-' not in result.extracted_serial_number
            assert '.' not in result.extracted_serial_number
        
        if result.iprs_serial_number is not None:
            assert result.iprs_serial_number == result.iprs_serial_number.upper()
            assert ' ' not in result.iprs_serial_number
            assert '-' not in result.iprs_serial_number
            assert '.' not in result.iprs_serial_number



class TestNonBlockingBehavior:
    """
    Property 8: Non-Blocking Behavior
    
    For any error condition during serial number validation (extraction failure, API error,
    normalization error), the validation function SHALL return a valid SerialNumberValidationResult
    with INCONCLUSIVE status rather than raising an exception.
    
    Validates: Requirements 4.3, 5.4, 8.1, 8.2, 8.5
    """
    
    @test_settings
    @given(st.text(min_size=0, max_size=50))
    def test_never_raises_exception(self, extracted):
        """
        Feature: serial-number-validation, Property 8: Non-Blocking Behavior
        Validates: Requirements 4.3, 5.4, 8.1, 8.2, 8.5
        """
        # Test with various IPRS values including None
        for iprs in [None, "", "   ", "---", "VALID123", extracted]:
            try:
                result = validate_serial_number(extracted, iprs)
                # Should always return a valid result
                assert isinstance(result, SerialNumberValidationResult)
                assert result.status in ValidationStatus
            except Exception as e:
                # Should never raise an exception
                assert False, f"validate_serial_number raised exception: {e}"
    
    @test_settings
    @given(st.text(min_size=0, max_size=50), st.text(min_size=0, max_size=50))
    def test_always_returns_valid_result(self, extracted, iprs):
        """
        Feature: serial-number-validation, Property 8: Non-Blocking Behavior (valid result)
        Validates: Requirements 4.3, 5.4, 8.5
        """
        result = validate_serial_number(extracted, iprs)
        
        # Result should always be valid
        assert isinstance(result, SerialNumberValidationResult)
        assert result.status in ValidationStatus
        assert isinstance(result.normalized_comparison, bool)
        
        # to_dict should always work
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert 'status' in result_dict
