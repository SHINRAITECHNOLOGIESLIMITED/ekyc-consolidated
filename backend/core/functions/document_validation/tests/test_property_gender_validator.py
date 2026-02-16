"""
Property-Based Tests for Gender Validator

Uses Hypothesis to verify universal correctness properties across randomly
generated inputs for the gender validation feature.

Feature: gender-validation-iprs
"""

import string

import pytest
from hypothesis import given, strategies as st, settings, Phase

from normalizer import normalize_gender
from gender_validator import (
    validate_gender,
    GenderValidationStatus,
    GenderValidationResult,
)

# Standard settings for all property tests
test_settings = settings(
    max_examples=100,
    phases=[Phase.generate, Phase.target, Phase.shrink],
    deadline=None,
)

# --- Strategies ---

MALE_VARIANTS = ['M', 'MALE', 'm', 'male', 'Male']
FEMALE_VARIANTS = ['F', 'FEMALE', 'f', 'female', 'Female']
ALL_VALID_VARIANTS = MALE_VARIANTS + FEMALE_VARIANTS
VALID_NORMALIZED = ['M', 'F']

valid_gender = st.sampled_from(ALL_VALID_VARIANTS)
valid_normalized_gender = st.sampled_from(VALID_NORMALIZED)

# Strings that are NOT valid gender values after stripping
invalid_gender = st.text(min_size=1, max_size=10).filter(
    lambda x: x.strip() not in ALL_VALID_VARIANTS and x.strip() != ''
)


# --- Property 1: Gender Normalization Correctness ---

class TestGenderNormalizationCorrectness:
    """Property 1: Valid gender strings normalize to correct standard code."""

    @test_settings
    @given(st.sampled_from(MALE_VARIANTS))
    def test_male_variants_normalize_to_m(self, gender_input):
        """
        Feature: gender-validation-iprs, Property 1: Gender Normalization Correctness
        Validates: Requirements 1.2, 1.3, 2.3
        """
        assert normalize_gender(gender_input) == 'M'

    @test_settings
    @given(st.sampled_from(FEMALE_VARIANTS))
    def test_female_variants_normalize_to_f(self, gender_input):
        """
        Feature: gender-validation-iprs, Property 1: Gender Normalization Correctness
        Validates: Requirements 1.2, 1.3, 2.3
        """
        assert normalize_gender(gender_input) == 'F'


# --- Property 2: Invalid Gender Returns Null ---

class TestInvalidGenderReturnsNull:
    """Property 2: Invalid gender strings return None."""

    @test_settings
    @given(invalid_gender)
    def test_invalid_gender_returns_none(self, gender_input):
        """
        Feature: gender-validation-iprs, Property 2: Invalid Gender Returns Null
        Validates: Requirements 1.4
        """
        assert normalize_gender(gender_input) is None

    def test_none_returns_none(self):
        """None input returns None."""
        assert normalize_gender(None) is None

    def test_empty_string_returns_none(self):
        """Empty string returns None."""
        assert normalize_gender('') is None

    def test_whitespace_only_returns_none(self):
        """Whitespace-only string returns None."""
        assert normalize_gender('   ') is None


# --- Property 3: Validation Status Reflects Equality ---

class TestValidationStatusReflectsEquality:
    """Property 3: MATCH iff equal, MISMATCH iff different (both non-null)."""

    @test_settings
    @given(valid_normalized_gender)
    def test_same_gender_is_match(self, gender):
        """
        Feature: gender-validation-iprs, Property 3: Validation Status Reflects Equality
        Validates: Requirements 3.1, 3.2
        """
        result = validate_gender(gender, gender)
        assert result.status == GenderValidationStatus.MATCH

    @test_settings
    @given(
        st.sampled_from(VALID_NORMALIZED),
        st.sampled_from(VALID_NORMALIZED),
    )
    def test_different_gender_is_mismatch(self, g1, g2):
        """
        Feature: gender-validation-iprs, Property 3: Validation Status Reflects Equality
        Validates: Requirements 3.1, 3.2
        """
        # Only test when they actually differ after normalization
        from hypothesis import assume
        assume(g1 != g2)
        result = validate_gender(g1, g2)
        assert result.status == GenderValidationStatus.MISMATCH


# --- Property 4: Null Input Produces INCONCLUSIVE ---

class TestNullInputProducesInconclusive:
    """Property 4: At least one null input -> INCONCLUSIVE."""

    @test_settings
    @given(valid_gender)
    def test_none_extracted_is_inconclusive(self, iprs_gender):
        """
        Feature: gender-validation-iprs, Property 4: Null Input Produces INCONCLUSIVE
        Validates: Requirements 3.3
        """
        result = validate_gender(None, iprs_gender)
        assert result.status == GenderValidationStatus.INCONCLUSIVE

    @test_settings
    @given(valid_gender)
    def test_none_iprs_is_inconclusive(self, extracted_gender):
        """
        Feature: gender-validation-iprs, Property 4: Null Input Produces INCONCLUSIVE
        Validates: Requirements 3.3
        """
        result = validate_gender(extracted_gender, None)
        assert result.status == GenderValidationStatus.INCONCLUSIVE

    def test_both_none_is_inconclusive(self):
        """Both None -> INCONCLUSIVE."""
        result = validate_gender(None, None)
        assert result.status == GenderValidationStatus.INCONCLUSIVE

    @test_settings
    @given(invalid_gender)
    def test_invalid_extracted_is_inconclusive(self, bad_gender):
        """Invalid extracted gender (normalizes to None) -> INCONCLUSIVE."""
        result = validate_gender(bad_gender, "M")
        assert result.status == GenderValidationStatus.INCONCLUSIVE

    @test_settings
    @given(invalid_gender)
    def test_invalid_iprs_is_inconclusive(self, bad_gender):
        """Invalid IPRS gender (normalizes to None) -> INCONCLUSIVE."""
        result = validate_gender("F", bad_gender)
        assert result.status == GenderValidationStatus.INCONCLUSIVE


# --- Property 5: Non-MATCH Status Includes Reason ---

class TestNonMatchStatusIncludesReason:
    """Property 5: MISMATCH and INCONCLUSIVE always have a non-empty reason."""

    @test_settings
    @given(
        st.sampled_from(VALID_NORMALIZED),
        st.sampled_from(VALID_NORMALIZED),
    )
    def test_mismatch_has_reason(self, g1, g2):
        """
        Feature: gender-validation-iprs, Property 5: Non-MATCH Status Includes Reason
        Validates: Requirements 3.4, 3.5, 4.6
        """
        from hypothesis import assume
        assume(g1 != g2)
        result = validate_gender(g1, g2)
        assert result.reason is not None
        assert len(result.reason) > 0

    @test_settings
    @given(st.one_of(st.none(), valid_gender))
    def test_inconclusive_has_reason(self, extracted):
        """
        Feature: gender-validation-iprs, Property 5: Non-MATCH Status Includes Reason
        Validates: Requirements 3.4, 3.5, 4.6
        """
        # Force INCONCLUSIVE by making IPRS None
        result = validate_gender(extracted, None)
        assert result.status == GenderValidationStatus.INCONCLUSIVE
        assert result.reason is not None
        assert len(result.reason) > 0

    @test_settings
    @given(valid_normalized_gender)
    def test_match_has_no_reason(self, gender):
        """MATCH status has reason=None."""
        result = validate_gender(gender, gender)
        assert result.reason is None


# --- Property 6: Result Structure Completeness ---

class TestResultStructureCompleteness:
    """Property 6: All results contain required fields."""

    @test_settings
    @given(
        st.one_of(st.none(), valid_gender, invalid_gender),
        st.one_of(st.none(), valid_gender, invalid_gender),
    )
    def test_result_has_all_fields(self, extracted, iprs):
        """
        Feature: gender-validation-iprs, Property 6: Result Structure Completeness
        Validates: Requirements 4.1, 4.3, 4.4
        """
        result = validate_gender(extracted, iprs)

        # Result is a GenderValidationResult
        assert isinstance(result, GenderValidationResult)
        assert isinstance(result.status, GenderValidationStatus)

        # to_dict has all required keys
        d = result.to_dict()
        assert 'status' in d
        assert 'extractedGender' in d
        assert 'iprsGender' in d
        assert 'normalizedComparison' in d
        assert 'reason' in d

        # Status is one of the valid values
        assert d['status'] in ('MATCH', 'MISMATCH', 'INCONCLUSIVE')


# --- Property 7: NormalizedComparison Consistency ---

class TestNormalizedComparisonConsistency:
    """Property 7: normalizedComparison aligns with status."""

    @test_settings
    @given(valid_normalized_gender)
    def test_match_has_true_comparison(self, gender):
        """
        Feature: gender-validation-iprs, Property 7: NormalizedComparison Consistency
        Validates: Requirements 4.5
        """
        result = validate_gender(gender, gender)
        assert result.normalized_comparison is True

    @test_settings
    @given(
        st.sampled_from(VALID_NORMALIZED),
        st.sampled_from(VALID_NORMALIZED),
    )
    def test_mismatch_has_true_comparison(self, g1, g2):
        """
        Feature: gender-validation-iprs, Property 7: NormalizedComparison Consistency
        Validates: Requirements 4.5
        """
        from hypothesis import assume
        assume(g1 != g2)
        result = validate_gender(g1, g2)
        # MISMATCH still used normalized values for comparison
        assert result.normalized_comparison is True

    @test_settings
    @given(valid_gender)
    def test_inconclusive_has_false_comparison(self, gender):
        """
        Feature: gender-validation-iprs, Property 7: NormalizedComparison Consistency
        Validates: Requirements 4.5
        """
        result = validate_gender(None, gender)
        assert result.normalized_comparison is False
