# Requirements Document

## Introduction

This document defines the requirements for the Face Matching Verification feature in the Jubilee eKYC system. The feature implements 3-way face matching verification comparing customer-uploaded photos, photos extracted from National ID documents, and photos retrieved from the IPRS (Integrated Population Registration System) API. The system uses AWS Rekognition CompareFaces API to perform pairwise comparisons and applies configurable thresholds to determine automatic approval, manual review, or rejection outcomes.

## Glossary

- **Face_Matching_Service**: The AWS Lambda function responsible for orchestrating face comparison operations and determining match outcomes
- **Rekognition_Client**: AWS Rekognition service client used for face comparison operations via the CompareFaces API
- **Customer_Photo**: A photograph uploaded by the customer through the portal interface, typically a passport-style photo
- **ID_Document_Photo**: A photograph extracted from the customer's National ID document using AWS Textract AnalyzeID
- **IPRS_Photo**: A photograph retrieved from the IPRS API response for the customer
- **Similarity_Score**: A percentage value (0-100) returned by Rekognition CompareFaces indicating how similar two faces are
- **Match_Status**: The overall verification outcome: APPROVED, MANUAL_REVIEW, or REJECTED
- **Approval_Threshold**: The minimum similarity score (default 70%) required for automatic approval
- **Review_Threshold**: The minimum similarity score (default 50%) below which automatic rejection occurs
- **Image_Preprocessor**: Component responsible for standardizing images before comparison (resolution, format, orientation)
- **Quality_Metrics**: Measurements of image quality including brightness, sharpness, and face detection confidence

## Requirements

### Requirement 1: Image Acquisition

**User Story:** As a KYC operator, I want the system to acquire face images from multiple sources, so that I can perform comprehensive identity verification.

#### Acceptance Criteria

1. WHEN a customer uploads a photo through the portal, THE Face_Matching_Service SHALL validate the image meets quality requirements (minimum 480x480 resolution, JPEG or PNG format, single face detected)
2. WHEN processing a National ID document, THE Face_Matching_Service SHALL extract the face photo region from the document using Textract AnalyzeID
3. WHEN an IPRS verification is completed, THE Face_Matching_Service SHALL retrieve the photo field from the IPRS API response
4. IF a customer photo fails quality validation, THEN THE Face_Matching_Service SHALL return an error with specific quality issues identified
5. IF the ID document photo cannot be extracted, THEN THE Face_Matching_Service SHALL return an error indicating document photo extraction failed
6. IF the IPRS photo is unavailable, THEN THE Face_Matching_Service SHALL proceed with 2-way comparison (Customer ↔ ID Document) and flag the result for manual review

### Requirement 2: Image Preprocessing

**User Story:** As a system architect, I want images to be standardized before comparison, so that comparison accuracy is maximized across different image sources.

#### Acceptance Criteria

1. THE Image_Preprocessor SHALL convert all images to a standardized format (JPEG) before comparison
2. THE Image_Preprocessor SHALL resize images to a consistent resolution while maintaining aspect ratio
3. WHEN an image has incorrect orientation, THE Image_Preprocessor SHALL apply orientation correction based on EXIF data
4. THE Image_Preprocessor SHALL perform face alignment to normalize face position within the image
5. THE Image_Preprocessor SHALL calculate and return Quality_Metrics for each processed image (brightness score, sharpness score, face detection confidence)
6. IF image preprocessing fails for any source, THEN THE Face_Matching_Service SHALL log the failure and return an appropriate error

### Requirement 3: Face Comparison Execution

**User Story:** As a KYC operator, I want the system to compare faces across all image sources, so that I can verify the customer's identity with high confidence.

#### Acceptance Criteria

1. THE Face_Matching_Service SHALL execute pairwise comparison between Customer_Photo and ID_Document_Photo using Rekognition CompareFaces API
2. THE Face_Matching_Service SHALL execute pairwise comparison between Customer_Photo and IPRS_Photo using Rekognition CompareFaces API
3. THE Face_Matching_Service SHALL execute pairwise comparison between ID_Document_Photo and IPRS_Photo using Rekognition CompareFaces API
4. WHEN all three images are available, THE Face_Matching_Service SHALL complete all three comparisons
5. WHEN only two images are available (IPRS unavailable), THE Face_Matching_Service SHALL execute only the Customer_Photo ↔ ID_Document_Photo comparison
6. THE Face_Matching_Service SHALL complete each individual comparison within 500ms

### Requirement 4: Decision Algorithm

**User Story:** As a compliance officer, I want the system to apply consistent decision rules, so that verification outcomes are fair and auditable.

#### Acceptance Criteria

1. WHEN all Similarity_Scores are greater than or equal to the Approval_Threshold (default 70%), THE Face_Matching_Service SHALL set Match_Status to APPROVED
2. WHEN any Similarity_Score is between the Review_Threshold (default 50%) and Approval_Threshold, THE Face_Matching_Service SHALL set Match_Status to MANUAL_REVIEW
3. WHEN any Similarity_Score is below the Review_Threshold (default 50%), THE Face_Matching_Service SHALL set Match_Status to REJECTED
4. WHEN operating in 2-way comparison mode (IPRS unavailable), THE Face_Matching_Service SHALL set Match_Status to MANUAL_REVIEW regardless of score if the single comparison passes
5. THE Face_Matching_Service SHALL read Approval_Threshold and Review_Threshold from SSM Parameter Store
6. IF SSM Parameter Store is unavailable, THEN THE Face_Matching_Service SHALL use default threshold values (70% approval, 50% rejection)

### Requirement 5: API Response Structure

**User Story:** As a portal developer, I want detailed comparison results, so that I can display meaningful information to operators and customers.

#### Acceptance Criteria

1. THE Face_Matching_Service SHALL return individual Similarity_Scores for each pairwise comparison performed
2. THE Face_Matching_Service SHALL return the overall Match_Status (APPROVED, MANUAL_REVIEW, or REJECTED)
3. THE Face_Matching_Service SHALL return confidence levels from Rekognition for each comparison
4. THE Face_Matching_Service SHALL return Quality_Metrics for each input image
5. THE Face_Matching_Service SHALL return a comparison_mode field indicating whether 3-way or 2-way comparison was performed
6. WHEN Match_Status is MANUAL_REVIEW or REJECTED, THE Face_Matching_Service SHALL return a reasons array explaining which comparisons failed or triggered review

### Requirement 6: Integration with KYC Orchestrator

**User Story:** As a system integrator, I want face matching to be accessible through the unified KYC endpoint, so that it integrates seamlessly with existing workflows.

#### Acceptance Criteria

1. THE KYC_Orchestrator SHALL support a new action `face_matching` for face verification requests
2. WHEN the `face_matching` action is invoked, THE KYC_Orchestrator SHALL route the request to the Face_Matching_Service
3. THE Face_Matching_Service SHALL store verification results in DynamoDB with full audit trail (timestamp, request_id, all scores, decision, image references)
4. THE Face_Matching_Service SHALL update the customer's KYC status based on the Match_Status outcome
5. IF the Face_Matching_Service encounters an error, THEN THE KYC_Orchestrator SHALL return a standardized error response with error_code and message

### Requirement 7: Audit and Logging

**User Story:** As a compliance auditor, I want comprehensive logging of all face matching operations, so that I can review verification decisions and investigate disputes.

#### Acceptance Criteria

1. THE Face_Matching_Service SHALL log all comparison requests with request_id, customer_id, and timestamp
2. THE Face_Matching_Service SHALL log all Similarity_Scores and the resulting Match_Status for each request
3. THE Face_Matching_Service SHALL log image quality metrics for audit purposes
4. THE Face_Matching_Service SHALL store S3 references to all images used in comparison (not the images themselves in logs)
5. WHEN an error occurs, THE Face_Matching_Service SHALL log the error details including error_code, message, and stack trace
6. THE Face_Matching_Service SHALL use AWS Lambda Powertools for structured logging with correlation IDs

### Requirement 8: Error Handling

**User Story:** As a system operator, I want graceful error handling, so that the system remains stable and provides meaningful feedback when issues occur.

#### Acceptance Criteria

1. IF Rekognition CompareFaces API returns an error, THEN THE Face_Matching_Service SHALL retry once with exponential backoff before failing
2. IF no face is detected in any source image, THEN THE Face_Matching_Service SHALL return an error with code NO_FACE_DETECTED and identify which image failed
3. IF multiple faces are detected in a source image, THEN THE Face_Matching_Service SHALL return an error with code MULTIPLE_FACES_DETECTED
4. IF image format is unsupported, THEN THE Face_Matching_Service SHALL return an error with code UNSUPPORTED_FORMAT
5. IF the request times out, THEN THE Face_Matching_Service SHALL return a partial result with completed comparisons and indicate which comparisons timed out
6. THE Face_Matching_Service SHALL validate all input parameters and return validation errors with specific field-level details
