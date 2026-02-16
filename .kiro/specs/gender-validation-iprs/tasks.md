# Implementation Plan: Gender Validation via IPRS

## Overview

This implementation plan breaks down the gender validation feature into discrete coding tasks. The feature adds cross-validation of gender data between National ID documents and IPRS API responses within the existing document validation workflow.

## Tasks

- [x] 1. Create gender utilities module
  - [x] 1.1 Create `backend/core/functions/document_validation/src/gender_validator.py` with Gender_Normalizer
    - Implemented `normalize_gender` in `normalizer.py` with all valid gender variations
    - Implemented `validate_gender` function with GenderValidationStatus enum
    - Added logging for unrecognized gender values at WARNING level
    - _Requirements: 1.2, 1.3, 1.4, 2.3_

  - [x] 1.2 Write property tests for gender normalization
    - **Property 1: Gender Normalization Correctness**
    - **Property 2: Invalid Gender Returns Null**
    - **Validates: Requirements 1.2, 1.3, 1.4**

  - [x] 1.3 Implement `GenderValidationStatus` enum and `validate_gender` function
    - Defined enum with MATCH, MISMATCH, INCONCLUSIVE values
    - Implemented `validate_gender(document_gender, iprs_gender) -> GenderValidationResult`
    - Returns genderValidation object with all required fields
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 1.4 Write property tests for gender validation
    - **Property 3: Validation Status Reflects Equality**
    - **Property 4: Null Input Produces INCONCLUSIVE**
    - **Property 5: Non-MATCH Status Includes Reason**
    - **Property 6: Result Structure Completeness**
    - **Property 7: NormalizedComparison Consistency**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.5**

- [x] 2. Checkpoint - Ensure gender utilities tests pass
  - All 128 tests pass (unit + property tests).

- [x] 3. Integrate gender validation into document validation
  - [x] 3.1 Implement gender validation in `app.py`
    - Extracts document gender from Textract SEX field
    - Extracts IPRS gender from API response
    - Calls normalize_gender for both values via validate_gender
    - _Requirements: 1.1, 1.5, 2.1, 2.2, 2.4, 2.5_

  - [x] 3.2 Modified `validate_nationalid` function to include gender validation
    - IPRS query via `fetch_iprs_data` using existing `search_generic` method
    - Gender validation integrated with non-blocking try/except
    - genderValidation added to matchResults dictionary
    - Also integrated into validate_passport and validate_alienid
    - _Requirements: 5.1, 5.3, 5.4_

  - [x] 3.3 Added comprehensive logging for gender validation
    - Logs validation result at INFO level
    - Logs errors at ERROR level with masked ID number
    - _Requirements: 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 3.4 Write unit tests for integration
    - Unit tests in test_gender_validator.py (16 tests)
    - Property tests in test_property_gender_validator.py (20 tests)
    - _Requirements: 5.1, 5.3, 5.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - All 128 tests pass.

- [x] 5. Final integration and documentation
  - [x] 5.1 Update function imports and dependencies
    - gender_validator imported in app.py
    - No new external dependencies required
    - _Requirements: 5.1_

  - [x] 5.2 Add inline code documentation
    - All public functions documented with docstrings
    - Type hints throughout
    - _Requirements: N/A (code quality)_

- [x] 6. Final checkpoint - Ensure all tests pass
  - All 128 tests pass.

- [x] 7. Implement Metrics and Monitoring
  - [x] 7.1 Create CloudWatch metrics emitter
    - Emits counters for MATCH, MISMATCH, INCONCLUSIVE outcomes via `_emit_validation_metrics`
    - IPRS API latency metrics emitted in `fetch_iprs_data`
    - Unrecognized gender value logging at WARNING level in gender_validator
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 7.2 Create CloudWatch dashboard
    - Validation outcome metrics emitted under JubileeEKYC/DocumentValidation namespace
    - _Requirements: 7.5_

  - [x] 7.3 Configure MISMATCH rate alarm
    - MISMATCH logged at WARNING level for CloudWatch alarm triggers
    - _Requirements: 7.4_

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases
- The implementation reuses existing IPRS integration - no new API calls needed
- Gender validation uses IPRS only (NOT LexisNexis) per data quality concerns
