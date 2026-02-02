"""
Property-Based Tests for Serial Number Normalizer

Tests the normalizer module using Hypothesis for property-based testing.
Each test validates specific correctness properties defined in the design document.
"""

import string
from hypothesis import given, strategies as st, settings, assume

from normalizer import normalize_serial_number, normalize_gender


# Test configuration
test_settings = settings(max_examples=100, deadline=None)


# Strategies for generating test data
serial_chars = string.ascii_uppercase + string.digits
formatting_chars = ' -.'

# Valid serial numbers (non-empty after normalization)
valid_serial = st.text(alphabet=serial_chars, min_size=1, max_size=15)

# Serial numbers with formatting (may include spaces, hyphens, dots)
formatted_serial = st.text(alphabet=serial_chars + formatting_chars, min_size=1, max_size=20)

# Any text including lowercase
any_serial = st.text(alphabet=string.ascii_letters + string.digits + formatting_chars, min_size=0, max_size=20)


def add_random_formatting(base: str) -> str:
    """Add random formatting characters to a serial number."""
    import random
    if not base:
        return base
    result = list(base)
    # Add 0-3 random formatting characters
    for _ in range(random.randint(0, 3)):
        pos = random.randint(0, len(result))
        char = random.choice([' ', '-', '.'])
        result.insert(pos, char)
    return ''.join(result)


class TestNormalizationIdempotence:
    """
    Property 1: Normalization Idempotence
    
    For any serial number string, applying the normalization function twice
    SHALL produce the same result as applying it once.
    
    normalize(normalize(x)) == normalize(x)
    
    Validates: Requirements 1.2, 2.3
    """
    
    @test_settings
    @given(any_serial)
    def test_normalization_idempotence(self, serial):
        """
        Feature: serial-number-validation, Property 1: Normalization Idempotence
        Validates: Requirements 1.2, 2.3
        """
        first_normalization = normalize_serial_number(serial)
        if first_normalization is not None:
            second_normalization = normalize_serial_number(first_normalization)
            assert second_normalization == first_normalization, \
                f"Idempotence failed: normalize({first_normalization!r}) = {second_normalization!r}"


class TestNormalizationConsistency:
    """
    Property 2: Normalization Consistency
    
    For any two serial numbers that differ only in formatting (spaces, hyphens, dots, case),
    the normalization function SHALL produce identical output strings.
    
    Validates: Requirements 1.2, 2.3
    """
    
    @test_settings
    @given(valid_serial)
    def test_normalization_consistency_with_formatting(self, base_serial):
        """
        Feature: serial-number-validation, Property 2: Normalization Consistency
        Validates: Requirements 1.2, 2.3
        """
        # Create two versions with different formatting
        version1 = add_random_formatting(base_serial)
        version2 = add_random_formatting(base_serial)
        
        normalized1 = normalize_serial_number(version1)
        normalized2 = normalize_serial_number(version2)
        
        assert normalized1 == normalized2, \
            f"Consistency failed: {version1!r} -> {normalized1!r}, {version2!r} -> {normalized2!r}"
    
    @test_settings
    @given(valid_serial)
    def test_normalization_case_insensitive(self, serial):
        """
        Feature: serial-number-validation, Property 2: Normalization Consistency (case)
        Validates: Requirements 1.2, 2.3
        """
        upper = normalize_serial_number(serial.upper())
        lower = normalize_serial_number(serial.lower())
        mixed = normalize_serial_number(serial.swapcase())
        
        assert upper == lower == mixed, \
            f"Case consistency failed: upper={upper!r}, lower={lower!r}, mixed={mixed!r}"


class TestCharacterRemoval:
    """
    Property 3: Normalization Character Removal
    
    For any input string, the normalized output SHALL contain no spaces, hyphens, or dots,
    and SHALL be entirely uppercase.
    
    Validates: Requirements 1.2, 2.3, 8.3
    """
    
    @test_settings
    @given(formatted_serial)
    def test_no_spaces_in_output(self, serial):
        """
        Feature: serial-number-validation, Property 3: Character Removal (spaces)
        Validates: Requirements 1.2, 2.3, 8.3
        """
        result = normalize_serial_number(serial)
        if result is not None:
            assert ' ' not in result, f"Space found in normalized output: {result!r}"
    
    @test_settings
    @given(formatted_serial)
    def test_no_hyphens_in_output(self, serial):
        """
        Feature: serial-number-validation, Property 3: Character Removal (hyphens)
        Validates: Requirements 1.2, 2.3, 8.3
        """
        result = normalize_serial_number(serial)
        if result is not None:
            assert '-' not in result, f"Hyphen found in normalized output: {result!r}"
    
    @test_settings
    @given(formatted_serial)
    def test_no_dots_in_output(self, serial):
        """
        Feature: serial-number-validation, Property 3: Character Removal (dots)
        Validates: Requirements 1.2, 2.3, 8.3
        """
        result = normalize_serial_number(serial)
        if result is not None:
            assert '.' not in result, f"Dot found in normalized output: {result!r}"
    
    @test_settings
    @given(any_serial)
    def test_output_is_uppercase(self, serial):
        """
        Feature: serial-number-validation, Property 3: Character Removal (uppercase)
        Validates: Requirements 1.2, 2.3, 8.3
        """
        result = normalize_serial_number(serial)
        if result is not None:
            assert result == result.upper(), f"Output not uppercase: {result!r}"


class TestGenderNormalization:
    """
    Property tests for gender normalization (for Gender Validation feature).
    """
    
    @test_settings
    @given(st.sampled_from(['M', 'm', 'Male', 'MALE', 'male']))
    def test_male_variants_normalize_to_m(self, gender):
        """Male variants should normalize to 'M'."""
        assert normalize_gender(gender) == 'M'
    
    @test_settings
    @given(st.sampled_from(['F', 'f', 'Female', 'FEMALE', 'female']))
    def test_female_variants_normalize_to_f(self, gender):
        """Female variants should normalize to 'F'."""
        assert normalize_gender(gender) == 'F'
    
    @test_settings
    @given(st.text(min_size=1, max_size=10).filter(
        lambda x: x.strip().upper() not in ['M', 'F', 'MALE', 'FEMALE', '']
    ))
    def test_invalid_gender_returns_none(self, gender):
        """Invalid gender values should return None."""
        result = normalize_gender(gender)
        assert result is None, f"Expected None for invalid gender {gender!r}, got {result!r}"
