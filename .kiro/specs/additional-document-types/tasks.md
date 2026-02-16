# Implementation Plan: Additional Document Types

## Overview

This implementation plan adds support for six new document types to the Jubilee eKYC platform: Alien ID, Military ID, Diplomatic ID, Refugee ID, Work Permit, and Dependant Pass. The implementation follows existing patterns established for National ID and Passport validation/verification.

## Tasks

- [ ] 1. Extend Portal Layer with new document types
  - [ ] 1.1 Add new document type enum values to portal.py
    - Add ALIEN_ID, MILITARY_ID, DIPLOMATIC_ID, REFUGEE_ID, WORK_PERMIT, DEPENDANT_PASS to DOCUMENT_TYPE enum
    - Update SUPPORTED_DOCUMENT_TYPES list
    - _Requirements: 9.1, 9.2, 9.3_

- [ ] 2. Implement Alien ID document validation
  - [ ] 2.1 Add validate_alienid function to document_validation/src/app.py
    - Define request schema with alienIdNumber as required field
    - Implement Textract field extraction for Alien ID fields
    - Add keyword checks for "Republic of Kenya" and "Alien Certificate"
    - Wire up to handler route for `/document/alienid`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ] 2.2 Write property test for text normalization idempotence
    - **Property 1: Text Normalization Idempotence**
    - **Validates: Requirements 1.3, 10.1**
  
  - [ ] 2.3 Write unit tests for validate_alienid
    - Test schema validation (valid/invalid requests)
    - Test field extraction and comparison
    - Test error handling for download failures
    - _Requirements: 1.1, 1.4, 1.5_

- [ ] 3. Implement Alien ID government verification
  - [ ] 3.1 Add verify_alienid function to government_verification/src/app.py
    - Define request schema with alienIdNumber as required field
    - Call IPRS search_alien_id API via ESB layer
    - Compare provided fields against IPRS response
    - Calculate validation accuracy
    - Wire up to handler route for `/government/alienid`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [ ] 3.2 Write property test for date normalization equivalence
    - **Property 2: Date Normalization Equivalence**
    - **Validates: Requirements 2.3, 10.2**
  
  - [ ] 3.3 Write unit tests for verify_alienid
    - Test IPRS API call with mock responses
    - Test field comparison logic
    - Test error handling for IPRS failures
    - _Requirements: 2.1, 2.2, 2.5_

- [ ] 4. Checkpoint - Alien ID validation and verification
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement Military ID document validation
  - [ ] 5.1 Add validate_militaryid function to document_validation/src/app.py
    - Define request schema with serviceNumber as required field
    - Implement Textract field extraction for Military ID fields (service number, rank, unit, blood group)
    - Add keyword checks for military-specific terms
    - Wire up to handler route for `/document/militaryid`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  
  - [ ] 5.2 Write unit tests for validate_militaryid
    - Test schema validation
    - Test field extraction and comparison
    - _Requirements: 3.1, 3.4_

- [ ] 6. Implement Military ID government verification
  - [ ] 6.1 Add verify_militaryid function to government_verification/src/app.py
    - Define request schema with serviceNumber required, linkedIdNumber optional
    - If linkedIdNumber provided, call IPRS search_generic API
    - Compare name and date of birth fields
    - Return cross-reference status
    - Wire up to handler route for `/government/militaryid`
    - _Requirements: 4.1, 4.2, 4.3, 4.4_
  
  - [ ] 6.2 Write unit tests for verify_militaryid
    - Test with and without linkedIdNumber
    - Test IPRS cross-reference logic
    - _Requirements: 4.1, 4.4_

- [ ] 7. Checkpoint - Military ID validation and verification
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement Diplomatic ID document validation
  - [ ] 8.1 Add validate_diplomaticid function to document_validation/src/app.py
    - Define request schema with diplomaticIdNumber as required field
    - Implement Textract field extraction for Diplomatic ID fields (mission, nationality)
    - Add keyword checks for diplomatic-specific terms
    - Wire up to handler route for `/document/diplomaticid`
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [ ] 8.2 Write unit tests for validate_diplomaticid
    - Test schema validation and field extraction
    - _Requirements: 5.1, 5.4_

- [ ] 9. Implement Refugee ID document validation
  - [ ] 9.1 Add validate_refugeeid function to document_validation/src/app.py
    - Define request schema with refugeeIdNumber as required field
    - Implement Textract field extraction for Refugee ID fields (country of origin, camp/settlement)
    - Add keyword checks for refugee-specific terms
    - Wire up to handler route for `/document/refugeeid`
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [ ] 9.2 Write unit tests for validate_refugeeid
    - Test schema validation and field extraction
    - _Requirements: 6.1, 6.4_

- [ ] 10. Implement Work Permit document validation
  - [ ] 10.1 Add validate_workpermit function to document_validation/src/app.py
    - Define request schema with permitNumber as required field
    - Implement Textract field extraction for Work Permit fields (employer, occupation)
    - Add keyword checks for work permit-specific terms
    - Wire up to handler route for `/document/workpermit`
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [ ] 10.2 Write unit tests for validate_workpermit
    - Test schema validation and field extraction
    - _Requirements: 7.1, 7.4_

- [ ] 11. Implement Dependant Pass document validation
  - [ ] 11.1 Add validate_dependantpass function to document_validation/src/app.py
    - Define request schema with passNumber as required field
    - Implement Textract field extraction for Dependant Pass fields (relationship, principal permit number)
    - Add keyword checks for dependant pass-specific terms
    - Wire up to handler route for `/document/dependantpass`
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  
  - [ ] 11.2 Write unit tests for validate_dependantpass
    - Test schema validation and field extraction
    - _Requirements: 8.1, 8.4_

- [ ] 12. Checkpoint - All validation endpoints complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement shared correctness property tests
  - [ ] 13.1 Write property test for field comparison consistency
    - **Property 3: Field Comparison Consistency**
    - **Validates: Requirements 2.2, 4.2**
  
  - [ ] 13.2 Write property test for validation accuracy calculation
    - **Property 4: Validation Accuracy Calculation**
    - **Validates: Requirements 2.4**
  
  - [ ] 13.3 Write property test for edit distance correctness
    - **Property 5: Edit Distance Correctness**
    - **Validates: Requirements 10.3**
  
  - [ ] 13.4 Write property test for response structure consistency
    - **Property 6: Response Structure Consistency**
    - **Validates: Requirements 1.4, 3.4, 11.1, 11.2**
  
  - [ ] 13.5 Write property test for error response structure
    - **Property 7: Error Response Structure**
    - **Validates: Requirements 11.3**
  
  - [ ] 13.6 Write property test for CORS headers presence
    - **Property 8: CORS Headers Presence**
    - **Validates: Requirements 11.4**

- [ ] 14. Integrate v1.2 features for applicable document types
  - [ ] 14.1 Add IPRS validation to Alien ID validation
    - Fetch IPRS data using alienIdNumber
    - Perform serial number validation if available
    - Perform gender validation against IPRS
    - Return INCONCLUSIVE if IPRS unavailable
    - _Requirements: 12.1, 12.2, 12.3_
  
  - [ ] 14.2 Write unit tests for v1.2 feature integration
    - Test serial number validation with Alien ID
    - Test gender validation with IPRS data
    - Test INCONCLUSIVE fallback
    - _Requirements: 12.1, 12.2, 12.3_

- [ ] 15. Final checkpoint - All features complete
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks including tests are required for comprehensive coverage
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Textract field mappings may need adjustment based on actual document extraction results
- Sample documents are available in `design and requirements/sample-kyc-documents/` for testing
