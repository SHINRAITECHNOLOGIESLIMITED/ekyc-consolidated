"""
Unit Tests for Serial Number Normalizer

Tests specific examples and edge cases for the normalizer module.
"""

import pytest
from normalizer import normalize_serial_number, normalize_gender


class TestNormalizeSerialNumber:
    """Unit tests for normalize_serial_number function."""
    
    def test_removes_hyphens(self):
        """Hyphens should be removed."""
        assert normalize_serial_number("12345-ABC") == "12345ABC"
    
    def test_removes_spaces(self):
        """Spaces should be removed."""
        assert normalize_serial_number("12345 ABC") == "12345ABC"
    
    def test_removes_dots(self):
        """Dots should be removed."""
        assert normalize_serial_number("12345.ABC") == "12345ABC"
    
    def test_converts_to_uppercase(self):
        """Lowercase should be converted to uppercase."""
        assert normalize_serial_number("12345-abc") == "12345ABC"
    
    def test_strips_whitespace(self):
        """Leading and trailing whitespace should be stripped."""
        assert normalize_serial_number("  12345-ABC  ") == "12345ABC"
    
    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        assert normalize_serial_number("") is None
    
    def test_only_formatting_chars_returns_none(self):
        """String with only formatting characters should return None."""
        assert normalize_serial_number("---") is None
        assert normalize_serial_number("   ") is None
        assert normalize_serial_number("...") is None
        assert normalize_serial_number("- . -") is None
    
    def test_none_returns_none(self):
        """None input should return None."""
        assert normalize_serial_number(None) is None
    
    def test_mixed_formatting(self):
        """Mixed formatting should be handled."""
        assert normalize_serial_number("12-345.ABC DEF") == "12345ABCDEF"
    
    def test_real_serial_numbers(self):
        """Test with real-world serial number formats."""
        # From test data
        assert normalize_serial_number("217990310") == "217990310"
        assert normalize_serial_number("702945559") == "702945559"
        assert normalize_serial_number("244772451") == "244772451"
        assert normalize_serial_number("229769449") == "229769449"


class TestNormalizeGender:
    """Unit tests for normalize_gender function."""
    
    def test_uppercase_m(self):
        """'M' should return 'M'."""
        assert normalize_gender("M") == "M"
    
    def test_lowercase_m(self):
        """'m' should return 'M'."""
        assert normalize_gender("m") == "M"
    
    def test_male_word(self):
        """'Male' should return 'M'."""
        assert normalize_gender("Male") == "M"
        assert normalize_gender("MALE") == "M"
        assert normalize_gender("male") == "M"
    
    def test_uppercase_f(self):
        """'F' should return 'F'."""
        assert normalize_gender("F") == "F"
    
    def test_lowercase_f(self):
        """'f' should return 'F'."""
        assert normalize_gender("f") == "F"
    
    def test_female_word(self):
        """'Female' should return 'F'."""
        assert normalize_gender("Female") == "F"
        assert normalize_gender("FEMALE") == "F"
        assert normalize_gender("female") == "F"
    
    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        assert normalize_gender("") is None
    
    def test_none_returns_none(self):
        """None input should return None."""
        assert normalize_gender(None) is None
    
    def test_invalid_gender_returns_none(self):
        """Invalid gender values should return None."""
        assert normalize_gender("Unknown") is None
        assert normalize_gender("X") is None
        assert normalize_gender("Other") is None
    
    def test_strips_whitespace(self):
        """Whitespace should be stripped."""
        assert normalize_gender("  M  ") == "M"
        assert normalize_gender("  Female  ") == "F"
