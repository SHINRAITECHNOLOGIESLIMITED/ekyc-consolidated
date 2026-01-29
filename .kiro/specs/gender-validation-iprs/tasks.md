# Implementation Plan: Gender Validation via IPRS

## Overview

This implementation plan breaks down the gender validation feature into discrete coding tasks. The feature adds cross-validation of gender data between National ID documents and IPRS API responses within the existing document validation workflow.

## Tasks

- [ ] 1. Create gender utilities module
  - [ ] 1.1 Create `backend/core/functions/document_validation/src/gender_utils.py` with Gender_Normalizer
    - Implement `GENDER_MAPPINGS` dictionary with all valid gender variations
    - Implement `normalize_gender(gender_value: Optional[str]) -> Optional[str]` function
    - Add logging for unrecognized gender values at WARNING level
    - _Requirements: 1.2, 1.3, 1.4, 2.3_

  - [ ] 1.2 Write property tests for gender normalization
    - **Property 1: Gender Normalization Correctness**
    - **Property 2: Invalid Gender Returns Null**
    - **Validates: Requirements 1.2, 1.3, 1.4**

  - [ ] 1.3 Implement `GenderValidationStatus` enum and `validate_gender` function
    - Define enum with MATCH, MISMATCH, INCONCLUSIVE values
    - Implement `validate_gender(document_gender, iprs_gender) -> Dict[str, Any]`
    - Return genderValidation object with all required fields
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [ ] 1.4 Write property tests for gender validation
    - **Property 3: Validation Status Reflects Equality**
    - **Property 4: Null Input Produces INCONCLUSIVE**
    - **Property 5: Non-MATCH Status Includes Reason**
    - **Property 6: Result Structure Completeness**
    - **Property 7: NormalizedComparison Consistency**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.5**

- [ ] 2. Checkpoint - Ensure gender utilities tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Integrate gender validation into document validation
  - [ ] 3.1 Implement `perform_gender_validation` function in `app.py`
    - Extract document gender from Textract SEX field
    - Extract IPRS gender from API response
    - Call normalize_gender for both values
    - Call validate_gender and return result
    - _Requirements: 1.1, 1.5, 2.1, 2.2, 2.4, 2.5_

  - [ ] 3.2 Modify `validate_nationalid` function to include gender validation
    - Add IPRS query using existing `search_generic` method (if not already called)
    - Call `perform_gender_validation` with extracted_form and iprs_response
    - Wrap in try/except for non-blocking behavior
    - Add genderValidation to matchResults dictionary
    - _Requirements: 5.1, 5.3, 5.4_

  - [ ] 3.3 Add comprehensive logging for gender validation
    - Log validation result at INFO level
    - Log errors at ERROR level with masked ID number
    - _Requirements: 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ] 3.4 Write unit tests for integration
    - Test `perform_gender_validation` with mock Textract and IPRS data
    - Test `validate_nationalid` includes genderValidation in response
    - Test error handling and non-blocking behavior
    - _Requirements: 5.1, 5.3, 5.4_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Final integration and documentation
  - [ ] 5.1 Update function imports and dependencies
    - Add gender_utils to Lambda package
    - Verify no new external dependencies required
    - _Requirements: 5.1_

  - [ ] 5.2 Add inline code documentation
    - Document all public functions with docstrings
    - Add type hints throughout
    - _Requirements: N/A (code quality)_

- [ ] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement Metrics and Monitoring
  - [ ] 7.1 Create CloudWatch metrics emitter
    - Emit counters for MATCH, MISMATCH, INCONCLUSIVE outcomes
    - Emit IPRS API latency metrics
    - Emit unrecognized gender value metrics
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ] 7.2 Create CloudWatch dashboard
    - Add validation outcome charts
    - Add MISMATCH rate monitoring
    - _Requirements: 7.5_

  - [ ] 7.3 Configure MISMATCH rate alarm
    - Set configurable threshold for MISMATCH rate
    - Trigger alarm when threshold exceeded
    - _Requirements: 7.4_

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases
- The implementation reuses existing IPRS integration - no new API calls needed
- Gender validation uses IPRS only (NOT LexisNexis) per data quality concerns
