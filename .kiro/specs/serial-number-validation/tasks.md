# Implementation Plan: Serial Number Validation

## Overview

This implementation plan breaks down the Serial Number Validation feature into discrete coding tasks. The feature enhances the existing `validate_nationalid` function to compare document serial numbers against IPRS records. Tasks are ordered to build incrementally, with testing tasks marked as optional.

## Tasks

- [ ] 1. Create Serial Number Normalizer Module
  - [ ] 1.1 Create normalizer.py with normalize_serial_number function
    - Implement normalization rules: uppercase, remove spaces/hyphens/dots
    - Handle None and empty string inputs
    - Return None for invalid inputs (empty after normalization)
    - _Requirements: 1.2, 2.3, 8.3_
  
  - [ ] 1.2 Write property tests for normalizer
    - **Property 1: Normalization Idempotence**
    - **Property 2: Normalization Consistency**
    - **Property 3: Character Removal**
    - **Validates: Requirements 1.2, 2.3, 8.3**

- [ ] 2. Create Serial Number Validator Module
  - [ ] 2.1 Create serial_number_validator.py with core validation logic
    - Define ValidationStatus enum (MATCH, MISMATCH, INCONCLUSIVE)
    - Define SerialNumberValidationResult dataclass
    - Implement validate_serial_number function
    - Use normalizer module for serial number normalization
    - _Requirements: 3.1, 3.2, 3.3, 3.4_
  
  - [ ] 2.2 Write property tests for validation decisions
    - **Property 4: MATCH Decision Correctness**
    - **Property 5: MISMATCH Decision Correctness**
    - **Property 6: INCONCLUSIVE for Missing Data**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 6.6**
  
  - [ ] 2.3 Write property tests for response structure
    - **Property 7: Response Structure Completeness**
    - **Property 9: Reason Presence for Non-MATCH**
    - **Property 10: Audit Data Completeness**
    - **Validates: Requirements 4.4, 5.2, 5.3, 6.1-6.6**

- [ ] 3. Checkpoint - Ensure core modules pass tests
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Integrate with Document Validation Function
  - [ ] 4.1 Add IPRS serial number retrieval to validate_nationalid
    - Import IPRS client from jubilee_esb_api_layer
    - Call search_generic with ID_NUMBER identifier
    - Extract serialNumber field from response
    - Handle IPRS API errors gracefully
    - _Requirements: 2.1, 2.2, 2.4, 2.5_
  
  - [ ] 4.2 Integrate serial number validator into validate_nationalid
    - Import serial_number_validator module
    - Extract serial number from Textract response
    - Call validate_serial_number with both serial numbers
    - Add serialNumberValidation to matchResults
    - Ensure validation errors don't block overall validation
    - _Requirements: 1.1, 1.3, 5.1, 5.2, 5.4_
  
  - [ ] 4.3 Write property test for non-blocking behavior
    - **Property 8: Non-Blocking Behavior**
    - **Validates: Requirements 4.3, 5.4, 8.1, 8.2, 8.5**

- [ ] 5. Add Logging and Audit Trail
  - [ ] 5.1 Add structured logging to serial_number_validator
    - Log validation requests with request context
    - Log original and normalized serial numbers
    - Log validation status and reason
    - Use WARNING level for MISMATCH status
    - Use AWS Lambda Powertools logger
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 6. Checkpoint - Ensure integration tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Update Response Structure
  - [ ] 7.1 Update validate_nationalid response to include serialNumberValidation
    - Add serialNumberValidation object to response
    - Include status, extractedSerialNumber, iprsSerialNumber, normalizedComparison, reason
    - Ensure backward compatibility with existing response structure
    - _Requirements: 5.3, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_
  
  - [ ] 7.2 Write unit tests for response structure
    - Test MATCH response structure
    - Test MISMATCH response structure
    - Test INCONCLUSIVE response structure
    - Test backward compatibility
    - _Requirements: 5.3, 6.1-6.6_

- [ ] 8. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required including property-based tests for comprehensive coverage
- The implementation uses Python as the existing codebase is Python-based
- Property tests use the Hypothesis library for property-based testing
- All new modules are created in `backend/core/functions/document_validation/src/`
- The existing IPRS integration in `jubilee_esb_api_layer` is reused without modification
