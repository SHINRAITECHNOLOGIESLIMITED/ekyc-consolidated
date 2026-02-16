# Requirements Document

## Introduction

This document defines the requirements for the Face Matching Verification feature in the Jubilee eKYC platform. The feature performs a 3-way face comparison using AWS Rekognition CompareFaces to verify that the person completing the KYC process matches the identity document and government records. It compares a liveness reference image (captured during face liveness check), a document photo (extracted from the uploaded ID document), and an IPRS photo (government-held photo retrieved via ESB API). The minimum similarity score across all comparisons determines the verification outcome using configurable decision bands.

## Glossary

- **Face_Match_Service**: The component responsible for orchestrating 3-way face comparisons and determining verification outcomes
- **Document_Photo_Extractor**: The component responsible for extracting face photos from different document types (National ID, Alien ID, Passport, Military ID)
- **KYC_Orchestrator**: The existing AWS Lambda function that routes KYC actions via the `/kyc` endpoint
- **Liveness_Reference_Image**: The face image captured during the face liveness session, stored in S3 at `{sessionId}/reference_image.jpg` in the LivenessCaptureBucket
- **Document_Photo**: The face photo extracted from the uploaded identity document (National ID, Alien ID, Passport, or Military ID)
- **IPRS_Photo**: The government-held photo retrieved from the IPRS API response, base64-encoded
- **Similarity_Score**: A float value between 0.0 and 100.0 returned by AWS Rekognition CompareFaces representing the confidence that two faces belong to the same person
- **Overall_Decision**: The final verification outcome: AUTO_APPROVED, MANUAL_REVIEW, AUTO_REJECTED, or PARTIAL_MATCH
- **Auto_Approve_Threshold**: The minimum Similarity_Score (default 70%) at which all comparisons must score for automatic approval
- **Manual_Review_Threshold**: The minimum Similarity_Score (default 50%) below which any comparison triggers automatic rejection
- **Minimum_Score**: The lowest Similarity_Score across all performed comparisons, used to determine the Overall_Decision
- **Comparison_Pair**: A pair of face images submitted to Rekognition CompareFaces for similarity scoring
- **IPRS_API**: The Integrated Population Registration System API accessed via the Jubilee ESB layer
- **LivenessCaptureBucket**: The existing S3 bucket where face liveness session images are stored

## Requirements

### Requirement 1: Liveness Reference Image Retrieval

**User Story:** As a KYC operator, I want the system to retrieve the liveness reference image from the face liveness session, so that it can be used as the trusted baseline for face comparisons.

#### Acceptance Criteria

1. WHEN a face match request is received, THE Face_Match_Service SHALL retrieve the Liveness_Reference_Image from S3 at path `{sessionId}/reference_image.jpg` in the LivenessCaptureBucket
2. IF the Liveness_Reference_Image does not exist in S3, THEN THE Face_Match_Service SHALL return an error response indicating the liveness session image is missing
3. IF the S3 retrieval fails due to a connectivity or permission error, THEN THE Face_Match_Service SHALL return an error response with details of the failure

### Requirement 2: Document Photo Extraction

**User Story:** As a KYC operator, I want the system to extract the face photo from uploaded identity documents, so that it can be compared against the liveness image and government records.

#### Acceptance Criteria

1. THE Document_Photo_Extractor SHALL support extracting face photos from National ID, Alien ID, Passport, and Military ID document types
2. WHEN a PDF document is provided, THE Document_Photo_Extractor SHALL convert the PDF to an image before extraction
3. THE Document_Photo_Extractor SHALL use AWS Rekognition DetectFaces to locate the face bounding box within the document image
4. WHEN a face is detected, THE Document_Photo_Extractor SHALL crop the face region with 20% padding around the detected bounding box
5. IF no face is detected in the document image, THEN THE Document_Photo_Extractor SHALL return an error indicating no face was found in the document
6. IF the document format is unsupported or corrupted, THEN THE Document_Photo_Extractor SHALL return an error with the specific failure reason

### Requirement 3: IPRS Photo Retrieval

**User Story:** As a KYC operator, I want the system to retrieve the government-held photo from IPRS when available, so that a 3-way comparison can be performed for stronger identity verification.

#### Acceptance Criteria

1. WHEN processing a National ID or Passport document, THE Face_Match_Service SHALL attempt to retrieve the IPRS_Photo from the IPRS verification response data
2. THE Face_Match_Service SHALL decode the base64-encoded IPRS_Photo into image bytes for comparison
3. IF the IPRS verification response does not contain a photo field, THEN THE Face_Match_Service SHALL proceed with 2-way comparison only
4. IF the IPRS_Photo cannot be decoded from base64, THEN THE Face_Match_Service SHALL log a warning and proceed with 2-way comparison only
5. WHEN processing an Alien ID or Military ID document, THE Face_Match_Service SHALL not require an IPRS_Photo and SHALL proceed with 2-way comparison

### Requirement 4: 3-Way Face Comparison

**User Story:** As a fraud prevention analyst, I want the system to perform a 3-way face comparison when all three images are available, so that identity fraud is detected with high confidence.

#### Acceptance Criteria

1. WHEN all three images are available (Liveness_Reference_Image, Document_Photo, IPRS_Photo), THE Face_Match_Service SHALL perform three comparisons: Liveness_Reference_Image vs Document_Photo, Liveness_Reference_Image vs IPRS_Photo, and Document_Photo vs IPRS_Photo
2. WHEN only the Liveness_Reference_Image and Document_Photo are available, THE Face_Match_Service SHALL perform one comparison: Liveness_Reference_Image vs Document_Photo
3. THE Face_Match_Service SHALL always perform the Liveness_Reference_Image vs Document_Photo comparison regardless of IPRS_Photo availability
4. THE Face_Match_Service SHALL use AWS Rekognition CompareFaces for each Comparison_Pair
5. THE Face_Match_Service SHALL record the Similarity_Score for each performed comparison

### Requirement 5: Decision Algorithm

**User Story:** As a compliance officer, I want the system to apply consistent decision rules based on configurable thresholds, so that verification outcomes are deterministic and auditable.

#### Acceptance Criteria

1. THE Face_Match_Service SHALL determine the Minimum_Score as the lowest Similarity_Score across all performed comparisons
2. WHEN the Minimum_Score is greater than or equal to the Auto_Approve_Threshold, THE Face_Match_Service SHALL set Overall_Decision to AUTO_APPROVED
3. WHEN the Minimum_Score is less than the Manual_Review_Threshold, THE Face_Match_Service SHALL set Overall_Decision to AUTO_REJECTED
4. WHEN the Minimum_Score is greater than or equal to the Manual_Review_Threshold and less than the Auto_Approve_Threshold, THE Face_Match_Service SHALL set Overall_Decision to MANUAL_REVIEW
5. WHEN the IPRS_Photo is unavailable and only 2-way comparison is performed, THE Face_Match_Service SHALL set Overall_Decision to PARTIAL_MATCH with `requires_manual_review` set to true, indicating the verification is inconclusive without the government photo and must be routed to manual review
6. THE Face_Match_Service SHALL include the configured threshold values in the response for audit purposes

### Requirement 6: Threshold Configuration

**User Story:** As a system administrator, I want face matching thresholds to be configurable without code deployment, so that thresholds can be tuned during UAT and production.

#### Acceptance Criteria

1. THE Face_Match_Service SHALL read the Auto_Approve_Threshold from the FACE_MATCH_AUTO_APPROVE_THRESHOLD environment variable with a default value of 70
2. THE Face_Match_Service SHALL read the Manual_Review_Threshold from the FACE_MATCH_MANUAL_REVIEW_THRESHOLD environment variable with a default value of 50
3. THE Face_Match_Service SHALL read the feature enabled state from the FACE_MATCH_ENABLED environment variable with a default value of true
4. THE Face_Match_Service SHALL read the IPRS photo requirement from the FACE_MATCH_REQUIRE_IPRS_PHOTO environment variable with a default value of false
5. IF the Auto_Approve_Threshold is less than or equal to the Manual_Review_Threshold, THEN THE Face_Match_Service SHALL log an error and use default threshold values

### Requirement 7: Integration with KYC Orchestrator

**User Story:** As a system integrator, I want face matching integrated into the KYC Orchestrator as a new action, so that it works seamlessly with the existing KYC workflow.

#### Acceptance Criteria

1. THE KYC_Orchestrator SHALL register a `face_match` action handler in the ActionRouter
2. THE KYC_Orchestrator SHALL validate the face_match request payload against the defined schema before processing
3. THE face_match action payload SHALL require: sessionId, documentType, documentS3Path, and idNumber fields
4. THE face_match action payload SHALL accept optional fields: iprsVerificationResponse and personalData
5. THE KYC_Orchestrator SHALL add the FACE_MATCH_ACTION feature flag to the feature flags module
6. THE KYC_Orchestrator SHALL add face_match response normalization to the response normalizer

### Requirement 8: API Response Structure

**User Story:** As a portal developer, I want detailed face matching results in a consistent format, so that I can display meaningful verification information to operators.

#### Acceptance Criteria

1. THE Face_Match_Service SHALL return a response containing: overall_decision, comparisons object, lowest_score, iprs_photo_available flag, document_type, and thresholds object
2. THE comparisons object SHALL contain an entry for each performed comparison with similarity score and matched boolean
3. THE thresholds object SHALL contain the auto_approve and manual_review threshold values used for the decision
4. WHEN a comparison is not performed (IPRS_Photo unavailable), THE comparisons object SHALL omit that comparison entry
5. THE Face_Match_Service SHALL include the document_type in the response to indicate which document was processed

### Requirement 9: Error Handling and Non-Blocking Behavior

**User Story:** As a system operator, I want graceful error handling, so that face matching failures do not block the overall KYC verification process.

#### Acceptance Criteria

1. IF the face match feature is disabled via FACE_MATCH_ENABLED, THEN THE Face_Match_Service SHALL return a response indicating the feature is disabled without performing any comparisons
2. IF AWS Rekognition CompareFaces returns an error for a Comparison_Pair, THEN THE Face_Match_Service SHALL log the error and mark that comparison as failed in the response
3. IF all comparisons fail due to Rekognition errors, THEN THE Face_Match_Service SHALL return an error response without crashing the KYC process
4. IF the document photo extraction fails, THEN THE Face_Match_Service SHALL return an error response indicating the extraction failure reason
5. THE Face_Match_Service SHALL catch all unexpected exceptions and return a structured error response with details

### Requirement 10: Audit Logging and Metrics

**User Story:** As a compliance auditor, I want comprehensive logging and metrics for face matching operations, so that I can review decisions and monitor system performance.

#### Acceptance Criteria

1. THE Face_Match_Service SHALL log each face match request with session_id, document_type, id_number, and timestamp
2. THE Face_Match_Service SHALL log each comparison result with the Comparison_Pair identifier and Similarity_Score
3. THE Face_Match_Service SHALL log the Overall_Decision and Minimum_Score for each request
4. WHEN Overall_Decision is AUTO_REJECTED, THE Face_Match_Service SHALL log at WARNING level for fraud monitoring
5. WHEN Overall_Decision is MANUAL_REVIEW, THE Face_Match_Service SHALL log at WARNING level for review queue monitoring
6. THE Face_Match_Service SHALL use AWS Lambda Powertools for structured logging with correlation IDs
7. THE Face_Match_Service SHALL emit CloudWatch metrics for each Overall_Decision outcome (AUTO_APPROVED, MANUAL_REVIEW, AUTO_REJECTED, PARTIAL_MATCH)

### Requirement 11: SAM Template and Infrastructure

**User Story:** As a DevOps engineer, I want the necessary AWS permissions and configuration added to the SAM template, so that the face matching feature can access required services.

#### Acceptance Criteria

1. THE SAM template SHALL grant the KYC_Orchestrator Lambda permission to call Rekognition CompareFaces and DetectFaces
2. THE SAM template SHALL grant the KYC_Orchestrator Lambda read access to the LivenessCaptureBucket S3 bucket
3. THE SAM template SHALL include environment variables for FACE_MATCH_AUTO_APPROVE_THRESHOLD, FACE_MATCH_MANUAL_REVIEW_THRESHOLD, FACE_MATCH_ENABLED, and FACE_MATCH_REQUIRE_IPRS_PHOTO
4. THE SAM template SHALL grant the KYC_Orchestrator Lambda read access to the KYC documents S3 bucket for document photo retrieval
