"""
Unit Tests for Gender Validator

Tests specific examples and edge cases for the gender_validator module.
"""

import pytest
from gender_validator import (
    validate_gender,
    GenderValidationStatus,
    GenderValidationResult
)


class TestValidateGender:
    """Unit tests for validate_gender function."""
    
    def test_match_same_gender_m(self):
        """MATCH when both genders are M."""
        result = validate_gender("M", "M")
        assert result.status == GenderValidationStatus.MATCH
        assert result.reason is None
    
    def test_match_same_gender_f(self):
        """MATCH when both genders are F."""
        result = validate_gender("F", "F")
        assert result.status == GenderValidationStatus.MATCH
        assert result.reason is None
    
    def test_match_male_variants(self):
        """MATCH when male variants are compared."""
        assert validate_gender("Male", "M").status == GenderValidationStatus.MATCH
        assert validate_gender("M", "Male").status == GenderValidationStatus.MATCH
        assert validate_gender("MALE", "m").status == GenderValidationStatus.MATCH
    
    def test_match_female_variants(self):
        """MATCH when female variants are compared."""
        assert validate_gender("Female", "F").status == GenderValidationStatus.MATCH
        assert validate_gender("F", "Female").status == GenderValidationStatus.MATCH
        assert validate_gender("FEMALE", "f").status == GenderValidationStatus.MATCH
    
    def test_mismatch_different_genders(self):
        """MISMATCH when genders differ."""
        result = validate_gender("M", "F")
        assert result.status == GenderValidationStatus.MISMATCH
        assert result.reason is not None
        assert "does not match" in result.reason
    
    def test_mismatch_male_vs_female(self):
        """MISMATCH when Male vs Female."""
        result = validate_gender("Male", "Female")
        assert result.status == GenderValidationStatus.MISMATCH
    
    def test_inconclusive_none_extracted(self):
        """INCONCLUSIVE when extracted gender is None."""
        result = validate_gender(None, "M")
        assert result.status == GenderValidationStatus.INCONCLUSIVE
        assert result.reason is not None
        assert "not found" in result.reason.lower()
    
    def test_inconclusive_none_iprs(self):
        """INCONCLUSIVE when IPRS gender is None."""
        result = validate_gender("M", None)
        assert result.status == GenderValidationStatus.INCONCLUSIVE
        assert result.reason is not None
        assert "unavailable" in result.reason.lower()
    
    def test_inconclusive_both_none(self):
        """INCONCLUSIVE when both genders are None."""
        result = validate_gender(None, None)
        assert result.status == GenderValidationStatus.INCONCLUSIVE
    
    def test_inconclusive_empty_extracted(self):
        """INCONCLUSIVE when extracted gender is empty."""
        result = validate_gender("", "M")
        assert result.status == GenderValidationStatus.INCONCLUSIVE
    
    def test_inconclusive_empty_iprs(self):
        """INCONCLUSIVE when IPRS gender is empty."""
        result = validate_gender("M", "")
        assert result.status == GenderValidationStatus.INCONCLUSIVE
    
    def test_inconclusive_invalid_extracted(self):
        """INCONCLUSIVE when extracted gender is invalid."""
        result = validate_gender("Unknown", "M")
        assert result.status == GenderValidationStatus.INCONCLUSIVE
        assert "invalid" in result.reason.lower()
    
    def test_inconclusive_invalid_iprs(self):
        """INCONCLUSIVE when IPRS gender is invalid."""
        result = validate_gender("M", "X")
        assert result.status == GenderValidationStatus.INCONCLUSIVE


class TestGenderValidationResultToDict:
    """Tests for GenderValidationResult.to_dict() method."""
    
    def test_to_dict_match(self):
        """to_dict returns correct structure for MATCH."""
        result = validate_gender("M", "M")
        result_dict = result.to_dict()
        
        assert result_dict['status'] == 'MATCH'
        assert result_dict['extractedGender'] == 'M'
        assert result_dict['iprsGender'] == 'M'
        assert result_dict['normalizedComparison'] is True
        assert result_dict['reason'] is None
    
    def test_to_dict_mismatch(self):
        """to_dict returns correct structure for MISMATCH."""
        result = validate_gender("M", "F")
        result_dict = result.to_dict()
        
        assert result_dict['status'] == 'MISMATCH'
        assert result_dict['extractedGender'] == 'M'
        assert result_dict['iprsGender'] == 'F'
        assert result_dict['normalizedComparison'] is True
        assert result_dict['reason'] is not None
    
    def test_to_dict_inconclusive(self):
        """to_dict returns correct structure for INCONCLUSIVE."""
        result = validate_gender(None, "M")
        result_dict = result.to_dict()
        
        assert result_dict['status'] == 'INCONCLUSIVE'
        assert result_dict['extractedGender'] is None
        assert result_dict['iprsGender'] == 'M'
        assert result_dict['normalizedComparison'] is False
        assert result_dict['reason'] is not None
