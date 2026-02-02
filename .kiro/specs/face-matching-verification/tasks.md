# Implementation Plan: Face Matching Verification

## Overview

This implementation plan breaks down the Face Matching Verification feature into discrete coding tasks. The feature adds 3-way face comparison to the Jubilee eKYC system using AWS Rekognition CompareFaces API. Tasks are organized to build incrementally, with each step validating core functionality before proceeding.

## Tasks

- [x] 1. Set up project structure and core interfaces
  - [x] 1.1 Create face matching Lambda function directory structure
    - Create `backend/core/functions/face_matching/src/` directory
    - Create `__init__.py`, `app.py` (main handler), and module files
    - Set up `requirements.txt` with dependencies (boto3, Pillow, aws-lambda-powertools)
    - _Requirements: 6.1, 6.2_
  
  - [x] 1.2 Define data models and type definitions
    - Create `models.py` with dataclasses: `FaceMatchingRequest`, `FaceMatchingResult`, `ComparisonResult`, `QualityMetrics`, `MatchDecision`
    - Define enums: `MatchStatus`, `ComparisonMode`, `ImageSource`
    - Define error classes: `FaceMatchingError`, `NoFaceDetectedError`, `MultipleFacesError`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 1.3 Write unit tests for data models
    - Test dataclass instantiation and validation
    - Test enum value correctness
    - Test error class inheritance and attributes
    - _Requirements: 5.1, 5.2_

- [x] 2. Implement Image Preprocessor module
  - [x] 2.1 Create ImagePreprocessor class with format standardization
    - Implement `preprocess()` method to convert images to JPEG
    - Implement `_convert_to_jpeg()` helper using Pillow
    - Implement `_resize_image()` with aspect ratio preservation
    - _Requirements: 2.1, 2.2_

  - [x] 2.2 Write property test for format standardization
    - **Property 4: Image Format Standardization**
    - **Validates: Requirements 2.1**

  - [x] 2.3 Write property test for aspect ratio preservation
    - **Property 5: Aspect Ratio Preservation**
    - **Validates: Requirements 2.2**

  - [x] 2.4 Implement quality metrics calculation
    - Implement `calculate_quality_metrics()` method
    - Calculate brightness score using image histogram
    - Calculate sharpness score using Laplacian variance
    - Integrate Rekognition DetectFaces for face_confidence
    - _Requirements: 2.5_

  - [x] 2.5 Write property test for quality metrics completeness
    - **Property 6: Quality Metrics Completeness**
    - **Validates: Requirements 2.5**

  - [x] 2.6 Implement orientation correction
    - Implement `_correct_orientation()` using EXIF data
    - Handle images without EXIF data gracefully
    - _Requirements: 2.3_

- [x] 3. Checkpoint - Verify preprocessor functionality
  - Ensure all preprocessor tests pass, ask the user if questions arise.

- [x] 4. Implement Face Comparator module
  - [x] 4.1 Create FaceComparator class with Rekognition integration
    - Implement `__init__()` with Rekognition client initialization
    - Implement `compare_faces()` method calling CompareFaces API
    - Parse Rekognition response to extract similarity and confidence
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 4.2 Implement retry logic with exponential backoff
    - Implement `_execute_with_retry()` helper method
    - Configure retry for ThrottlingException and ServiceUnavailableException
    - Implement exponential backoff with max 1 retry
    - _Requirements: 8.1_

  - [x] 4.3 Write property test for retry behavior
    - **Property 16: Retry Behavior**
    - **Validates: Requirements 8.1**

  - [x] 4.4 Implement parallel comparison execution
    - Implement `compare_faces_parallel()` using concurrent.futures
    - Execute all three comparisons concurrently
    - Aggregate results into dictionary
    - _Requirements: 3.4_

  - [x] 4.5 Write property test for comparison completeness
    - **Property 7: Comparison Completeness**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

  - [x] 4.6 Implement error handling for face detection issues
    - Handle InvalidParameterException for no face detected
    - Handle response with multiple face matches
    - Return appropriate error codes
    - _Requirements: 8.2, 8.3_

  - [x] 4.7 Write property test for error response format
    - **Property 15: Error Response Format**
    - **Validates: Requirements 6.5, 8.2, 8.3, 8.4**

- [x] 5. Checkpoint - Verify comparator functionality
  - Ensure all comparator tests pass, ask the user if questions arise.

- [x] 6. Implement Decision Calculator module
  - [x] 6.1 Create DecisionCalculator class with threshold configuration
    - Implement `__init__()` accepting approval and rejection thresholds
    - Implement SSM Parameter Store integration for threshold retrieval
    - Implement fallback to default values (70%, 50%)
    - _Requirements: 4.5, 4.6_

  - [x] 6.2 Implement decision algorithm for 3-way comparison
    - Implement `calculate_decision()` method
    - Apply approval logic: all scores >= approval_threshold → APPROVED
    - Apply review logic: any score in [rejection, approval) → MANUAL_REVIEW
    - Apply rejection logic: any score < rejection_threshold → REJECTED
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 6.3 Write property test for approval decision
    - **Property 8: Decision Algorithm - Approval**
    - **Validates: Requirements 4.1**

  - [x] 6.4 Write property test for manual review decision
    - **Property 9: Decision Algorithm - Manual Review**
    - **Validates: Requirements 4.2**

  - [x] 6.5 Write property test for rejection decision
    - **Property 10: Decision Algorithm - Rejection**
    - **Validates: Requirements 4.3**

  - [x] 6.6 Implement 2-way comparison mode handling
    - Detect when only 2 images available
    - Force MANUAL_REVIEW status for 2-way mode (if not rejected)
    - Set comparison_mode field appropriately
    - _Requirements: 4.4_

  - [x] 6.7 Write property test for graceful degradation
    - **Property 3: Graceful Degradation to 2-Way Mode**
    - **Validates: Requirements 1.6, 3.5, 4.4**

  - [x] 6.8 Implement reasons generation for non-approval
    - Generate descriptive reasons for MANUAL_REVIEW status
    - Generate descriptive reasons for REJECTED status
    - Include comparison names and scores in reasons
    - _Requirements: 5.6_

  - [x] 6.9 Write property test for non-approval reasons
    - **Property 12: Reasons for Non-Approval**
    - **Validates: Requirements 5.6**

- [x] 7. Checkpoint - Verify decision calculator functionality
  - Ensure all decision calculator tests pass, ask the user if questions arise.

- [ ] 8. Implement Image Acquisition module
  - [ ] 8.1 Implement customer photo retrieval from S3
    - Create `ImageAcquisition` class
    - Implement `get_customer_photo()` method
    - Validate image meets quality requirements before returning
    - _Requirements: 1.1_

  - [ ] 8.2 Write property test for image validation
    - **Property 1: Image Validation Correctness**
    - **Validates: Requirements 1.1, 1.4**

  - [ ] 8.3 Implement ID document photo extraction
    - Implement `extract_id_document_photo()` method
    - Integrate with existing Textract AnalyzeID functionality
    - Extract face region from document
    - _Requirements: 1.2_

  - [ ] 8.4 Implement IPRS photo retrieval
    - Implement `get_iprs_photo()` method
    - Parse IPRS API response for photo field
    - Handle missing photo gracefully (return None)
    - _Requirements: 1.3_

  - [ ] 8.5 Write property test for IPRS photo extraction
    - **Property 2: IPRS Photo Extraction**
    - **Validates: Requirements 1.3**

- [ ] 9. Implement main Face Matching Lambda handler
  - [ ] 9.1 Create main handler with request parsing
    - Implement `handler()` function in `app.py`
    - Parse and validate incoming request
    - Initialize all component classes
    - _Requirements: 6.1_

  - [ ] 9.2 Write property test for input validation
    - **Property 17: Input Validation**
    - **Validates: Requirements 8.6**

  - [ ] 9.3 Implement orchestration logic
    - Implement `process_face_matching()` function
    - Coordinate image acquisition from all sources
    - Execute preprocessing on all images
    - Execute parallel comparisons
    - Calculate decision and build response
    - _Requirements: 3.4, 4.1, 4.2, 4.3_

  - [ ] 9.4 Write property test for response structure
    - **Property 11: Response Structure Completeness**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

  - [ ] 9.5 Implement DynamoDB result storage
    - Create `ResultStorage` class
    - Implement `store_result()` method
    - Store all required audit fields
    - _Requirements: 6.3, 7.4_

  - [ ] 9.6 Write property test for audit trail storage
    - **Property 13: Audit Trail Storage**
    - **Validates: Requirements 6.3, 7.4**

  - [ ] 9.7 Implement KYC status update
    - Implement `update_kyc_status()` method
    - Map MatchStatus to KYC status values
    - Update customer record in DynamoDB
    - _Requirements: 6.4_

  - [ ] 9.8 Write property test for KYC status update
    - **Property 14: KYC Status Update Consistency**
    - **Validates: Requirements 6.4**

- [ ] 10. Checkpoint - Verify Lambda handler functionality
  - Ensure all handler tests pass, ask the user if questions arise.

- [ ] 11. Integrate with KYC Orchestrator
  - [ ] 11.1 Add face_matching action to ActionRouter
    - Add `'face_matching': self._handle_face_matching` to action_handlers dict
    - Implement `_handle_face_matching()` method
    - Route request to Face Matching Lambda
    - _Requirements: 6.1, 6.2_

  - [ ] 11.2 Add face_matching schema to PayloadValidator
    - Define JSON schema for face_matching action data
    - Add schema to PayloadValidator schemas dict
    - _Requirements: 8.6_

  - [ ] 11.3 Implement error response handling
    - Map Face Matching errors to standardized responses
    - Ensure error_code and message are included
    - _Requirements: 6.5_

  - [ ] 11.4 Write integration tests for action routing
    - Test face_matching action is recognized
    - Test request is routed to correct handler
    - Test error responses are properly formatted
    - _Requirements: 6.1, 6.2, 6.5_

- [ ] 12. Configure infrastructure
  - [ ] 12.1 Create SSM parameters for thresholds
    - Create `/ekyc/face-matching/approval-threshold` parameter (default: 70)
    - Create `/ekyc/face-matching/rejection-threshold` parameter (default: 50)
    - _Requirements: 4.5_

  - [ ] 12.2 Create DynamoDB table for results
    - Create FaceMatchingResults table with request_id as partition key
    - Create GSI on customer_id with timestamp as sort key
    - Configure TTL for 30-day retention
    - _Requirements: 6.3_

  - [ ] 12.3 Update Lambda IAM permissions
    - Add Rekognition CompareFaces permission
    - Add SSM GetParameter permission
    - Add DynamoDB read/write permissions for results table
    - Add S3 read permission for customer photos bucket
    - _Requirements: 3.1, 4.5, 6.3_

- [ ] 13. Final checkpoint - End-to-end verification
  - Ensure all tests pass, ask the user if questions arise.
  - Verify face_matching action works through KYC Orchestrator
  - Verify results are stored in DynamoDB
  - Verify KYC status is updated correctly

- [ ] 14. Implement Metrics and Observability
  - [ ] 14.1 Create CloudWatch metrics emitter
    - Implement `MetricsEmitter` class using aws-lambda-powertools
    - Emit counters for APPROVED, MANUAL_REVIEW, REJECTED outcomes
    - Calculate and emit manual review percentage
    - _Requirements: 9.1, 9.2_

  - [ ] 14.2 Implement latency metrics
    - Add timing instrumentation around each comparison
    - Emit `FaceMatching.ComparisonLatency` metric
    - _Requirements: 9.4_

  - [ ] 14.3 Implement quality gate metrics
    - Emit metrics for image quality failures
    - Track poor selfie quality, low resolution rejections
    - _Requirements: 9.5_

  - [ ] 14.4 Create CloudWatch dashboard
    - Create dashboard with approval/rejection rates
    - Add manual review queue depth widget
    - Add latency percentile charts
    - _Requirements: 9.6_

  - [ ] 14.5 Implement ROC metrics logging for UAT
    - Log false accept/reject indicators during UAT
    - Enable threshold tuning based on metrics
    - _Requirements: 9.3_

- [ ] 15. Implement Feature Flags
  - [ ] 15.1 Create feature flag configuration
    - Set up AWS AppConfig or SSM Parameter Store for feature flags
    - Create flags for threshold values
    - Create flag for aggregation rule selection
    - _Requirements: 10.1, 10.2, 10.3_

  - [ ] 15.2 Implement aggregation rule selector
    - Support fail-fast, minimum score, and weighted average rules
    - Read aggregation rule from feature flag
    - _Requirements: 10.5_

  - [ ] 15.3 Implement third comparison toggle
    - Add feature flag to enable/disable ID ↔ IPRS comparison
    - Default to enabled
    - _Requirements: 10.4_

  - [ ] 15.4 Implement configuration change logging
    - Log threshold changes with timestamp and previous values
    - _Requirements: 10.6_

- [ ] 16. Implement Manual Review Workflow
  - [ ] 16.1 Create review task queue integration
    - Create review task when Match_Status is MANUAL_REVIEW
    - Include all scores, image references, quality metrics
    - _Requirements: 11.1, 11.2_

  - [ ] 16.2 Implement SLA tracking
    - Configure SLA thresholds for review completion
    - Emit metrics for queue depth and resolution time
    - _Requirements: 11.3, 11.4_

  - [ ] 16.3 Implement reviewer audit logging
    - Log manual review decisions with reviewer ID
    - Include timestamp and decision rationale
    - _Requirements: 11.6_

- [ ] 17. Final integration checkpoint
  - Verify metrics are emitting to CloudWatch
  - Verify feature flags are working
  - Verify manual review workflow integration
  - Run full end-to-end test with all new features

## Notes

- All tasks including tests are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- The implementation follows existing patterns from face_liveness and document_validation functions
- Metrics instrumentation is required from day one per executive recommendations
- Feature flags enable runtime threshold tuning without code deployment
