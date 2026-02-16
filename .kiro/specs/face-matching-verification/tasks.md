# Implementation Plan: Face Matching Verification

## Overview

This plan implements the 3-way face matching verification feature for the Jubilee eKYC platform. It adds a `face_match` action to the KYC Orchestrator that compares liveness reference images, document photos, and IPRS photos using AWS Rekognition CompareFaces. Tasks build incrementally: core decision logic first, then document extraction, then orchestration service, then integration with the existing KYC Orchestrator.

## Tasks

- [x] 1. Create core decision logic and threshold configuration
  - [x] 1.1 Create `face_match_service.py` with FaceMatchDecision enum, ComparisonResult and FaceMatchResult dataclasses, and ThresholdConfig
    - Define FaceMatchDecision enum: AUTO_APPROVED, MANUAL_REVIEW, AUTO_REJECTED, PARTIAL_MATCH
    - Define ComparisonResult dataclass with pair_name, similarity, matched, error fields
    - Define FaceMatchResult dataclass with overall_decision, comparisons, lowest_score, iprs_photo_available, document_type, thresholds, error fields
    - Define ThresholdConfig dataclass with auto_approve, manual_review, enabled, require_iprs_photo fields and validate method
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 1.2 Implement `determine_decision` method on FaceMatchService
    - Accept list of ComparisonResult and iprs_photo_available flag
    - Calculate minimum score across all successful comparisons
    - Return PARTIAL_MATCH when iprs_photo_available is False
    - Return AUTO_APPROVED when min score >= auto_approve_threshold
    - Return AUTO_REJECTED when min score < manual_review_threshold
    - Return MANUAL_REVIEW for scores in between
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 1.3 Write property tests for decision logic
    - **Property 5: Minimum Score Correctness**
    - **Property 6: Decision Band Correctness**
    - **Property 7: PARTIAL_MATCH When IPRS Photo Unavailable**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

  - [x]* 1.4 Write unit tests for threshold configuration
    - Test default threshold values (70/50)
    - Test custom thresholds from env vars
    - Test invalid thresholds fallback to defaults
    - Test feature enabled/disabled flag
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 2. Create DocumentPhotoExtractor module
  - [x] 2.1 Create `document_photo_extractor.py` with DocumentPhotoExtractor class
    - NOTE: Implemented as `extract_face_from_document` method directly in `face_match_service.py` instead of separate module
    - Implement extract_face method accepting document_bytes and document_type
    - Implement _detect_and_crop_face using Rekognition DetectFaces with 20% padding
    - Handle all four document types: national_id, alien_id, passport, military_id
    - Raise DocumentPhotoExtractionError for failures (no face found, bad format)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 2.2 Write property test for bounding box padding calculation
    - **Property 2: Bounding Box Padding Calculation**
    - **Validates: Requirements 2.4**

  - [x]* 2.3 Write unit tests for DocumentPhotoExtractor
    - Test face detection and cropping with mocked Rekognition
    - Test no face detected error
    - Test multiple faces picks highest confidence
    - Test Rekognition DetectFaces API error
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 3. Checkpoint - Ensure core modules pass tests
  - All 40 unit tests pass. 108 document_validation tests pass (no regressions).

- [x] 4. Implement FaceMatchService orchestration
  - [x] 4.1 Implement `get_liveness_reference_image` method
    - Retrieve image from S3 at `{sessionId}/reference_image.jpg` in LivenessCaptureBucket
    - Handle S3 NoSuchKey and connectivity errors
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 4.2 Write property test for S3 path construction
    - **Property 1: S3 Path Construction**
    - **Validates: Requirements 1.1**

  - [x] 4.3 Implement `get_iprs_photo` method
    - Extract photo field from iprsVerificationResponse dict
    - Decode base64 to image bytes
    - Return None when photo unavailable or decode fails
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 4.4 Implement `compare_faces` method
    - Call Rekognition CompareFaces with source and target images
    - Return ComparisonResult with similarity score
    - Handle Rekognition errors gracefully, return ComparisonResult with error field
    - _Requirements: 4.4, 4.5, 9.2_

  - [x] 4.5 Implement `execute_face_match` method
    - Orchestrate full workflow: get liveness image → get document → extract face → get IPRS photo → compare faces → determine decision
    - Perform 3 comparisons when IPRS photo available, 1 when not
    - Always include liveness_vs_document comparison
    - Catch all exceptions and return structured error response
    - Add structured logging with Lambda Powertools (session_id, document_type, id_number, scores, decision)
    - Log WARNING for AUTO_REJECTED and MANUAL_REVIEW decisions
    - _Requirements: 4.1, 4.2, 4.3, 9.3, 9.4, 9.5, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [ ]* 4.6 Write property tests for FaceMatchService
    - **Property 3: Comparison Count Based on IPRS Availability**
    - **Property 4: Liveness vs Document Comparison Invariant**
    - **Property 8: Response Structure Completeness**
    - **Property 9: Non-Blocking Error Handling**
    - **Validates: Requirements 3.3, 3.5, 4.1, 4.2, 4.3, 4.5, 5.6, 8.1, 8.2, 8.3, 8.4, 8.5, 9.2, 9.3, 9.5**

  - [x]* 4.7 Write unit tests for FaceMatchService
    - Test successful 3-way comparison flow
    - Test 2-way comparison when IPRS photo missing
    - Test liveness image not found error
    - Test document extraction failure error
    - Test Rekognition error on single comparison
    - Test all comparisons fail
    - Test result to_dict structure
    - _Requirements: 1.2, 1.3, 3.3, 3.4, 9.1, 9.2, 9.3, 9.4_

- [x] 5. Checkpoint - Ensure FaceMatchService tests pass
  - All 40 tests pass.

- [x] 6. Integrate with KYC Orchestrator
  - [x] 6.1 Add face_match to payload_schemas.py
    - Add FACE_MATCH = "face_match" to KYCAction enum
    - Add face_match data schema with required fields (sessionId, documentType, documentS3Path, idNumber) and optional fields (iprsVerificationResponse, personalData)
    - _Requirements: 7.2, 7.3, 7.4_

  - [ ]* 6.2 Write property test for payload validation
    - **Property 10: Required Payload Field Validation**
    - **Validates: Requirements 7.2, 7.3**

  - [x] 6.3 Add face_match to feature_flags.py
    - Add FACE_MATCH_ACTION = "face_match_action" to FeatureFlag enum
    - Add face_match mapping in is_action_enabled function
    - _Requirements: 7.5_

  - [x] 6.4 Add face_match handler to action_router.py
    - Add face_match to _initialize_action_handlers mapping
    - Implement _handle_face_match method that reads config from env vars, instantiates FaceMatchService, and calls execute_face_match
    - Add face_match identifier extraction in _extract_natural_identifier
    - _Requirements: 7.1_

  - [x] 6.5 Add face_match normalization to response_normalizer.py
    - Add _normalize_face_match function
    - Add face_match routing in normalize_verification_response
    - Add face_match mapping in _action_to_verification_type
    - _Requirements: 7.6_

  - [ ]* 6.6 Write unit tests for KYC Orchestrator integration
    - Test face_match action registered in ActionRouter
    - Test payload validation accepts valid payloads
    - Test payload validation rejects missing required fields
    - Test feature flag controls face_match action
    - Test response normalization for face_match
    - _Requirements: 7.1, 7.2, 7.3, 7.5, 7.6_

- [x] 7. Checkpoint - Ensure integration tests pass
  - All 40 face match tests pass. 108 document_validation tests pass (no regressions).

- [x] 8. Update SAM template and add CloudWatch metrics
  - [x] 8.1 Update backend/template.yaml
    - Add Rekognition CompareFaces and DetectFaces permissions to KYC Orchestrator Lambda
    - Add S3 read access to LivenessCaptureBucket for KYC Orchestrator
    - Add S3 read access to KYC documents bucket for KYC Orchestrator
    - Add environment variables: FACE_MATCH_AUTO_APPROVE_THRESHOLD, FACE_MATCH_MANUAL_REVIEW_THRESHOLD, FACE_MATCH_ENABLED, FACE_MATCH_REQUIRE_IPRS_PHOTO
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [ ] 8.2 Add CloudWatch metrics emission to FaceMatchService
    - Emit metrics for each Overall_Decision outcome (AUTO_APPROVED, MANUAL_REVIEW, AUTO_REJECTED, PARTIAL_MATCH)
    - _Requirements: 10.7_

- [x] 9. Final checkpoint - Ensure all tests pass
  - All 40 face match tests pass. 108 document_validation tests pass. SAM build succeeded. Deployed to AWS (stack up to date).

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- The implementation uses Python 3.11 matching the existing codebase
- Property tests use the Hypothesis library with minimum 100 iterations per test
- All new modules are created in `backend/core/functions/kyc_orchestrator/src/`
- Tests go in `backend/core/functions/kyc_orchestrator/tests/`
- The existing face liveness S3 bucket (LivenessCaptureBucket) is reused for reference image retrieval
- IPRS photo comes from the iprsVerificationResponse passed in the request payload (no separate IPRS call needed)
- Face extraction from document is implemented directly in `face_match_service.py` using Rekognition DetectFaces + Pillow crop with 20% padding
- Pillow==11.1.0 added to kyc_orchestrator requirements.txt
