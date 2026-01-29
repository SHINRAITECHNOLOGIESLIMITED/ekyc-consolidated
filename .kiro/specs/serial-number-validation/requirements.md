# Requirements Document

## Introduction

This document defines the requirements for the Serial Number Validation feature in the Jubilee eKYC system. The feature validates that the serial number extracted from a submitted National ID document matches the most recent National ID serial number returned by the IPRS (Integrated Population Registration System) API. This validation helps detect counterfeit or outdated ID documents by ensuring the physical document presented corresponds to the latest official record.

## Glossary

- **Serial_Number_Validator**: The component responsible for comparing serial numbers from document extraction and IPRS API
- **Document_Validation_Service**: The existing AWS Lambda function that validates National ID documents using Textract
- **IPRS_API**: The Integrated Population Registration System API accessed via the Jubilee ESB layer
- **Extracted_Serial_Number**: The serial number extracted from the National ID document using AWS Textract AnalyzeID
- **IPRS_Serial_Number**: The serial number returned by the IPRS API for a given ID number
- **Normalization**: The process of standardizing serial number format by removing spaces, hyphens, dots, and converting to uppercase
- **Validation_Status**: The outcome of serial number comparison: MATCH, MISMATCH, or INCONCLUSIVE
- **Match_Results**: The existing data structure in document validation that stores field-by-field comparison results

## Requirements

### Requirement 1: Serial Number Extraction from Document

**User Story:** As a KYC operator, I want the system to extract the serial number from National ID documents, so that I can verify the document's authenticity against government records.

#### Acceptance Criteria

1. WHEN processing a National ID document, THE Document_Validation_Service SHALL extract the serial number using the existing SERIAL_NUMBER field from Textract AnalyzeID
2. THE Serial_Number_Validator SHALL normalize the Extracted_Serial_Number by removing spaces, hyphens, and dots, and converting to uppercase
3. IF the serial number cannot be extracted from the document, THEN THE Serial_Number_Validator SHALL set Validation_Status to INCONCLUSIVE with reason "Serial number not found in document"
4. IF the extracted serial number is empty after normalization, THEN THE Serial_Number_Validator SHALL set Validation_Status to INCONCLUSIVE with reason "Invalid serial number format"

### Requirement 2: IPRS Serial Number Retrieval

**User Story:** As a KYC operator, I want the system to retrieve the latest serial number from IPRS, so that I can compare it against the document serial number.

#### Acceptance Criteria

1. WHEN validating a National ID, THE Serial_Number_Validator SHALL query the IPRS API using the existing `search_generic` method with ID_NUMBER identifier
2. THE Serial_Number_Validator SHALL extract the `serialNumber` field from the IPRS API response data
3. THE Serial_Number_Validator SHALL normalize the IPRS_Serial_Number using the same normalization rules as the Extracted_Serial_Number
4. IF the IPRS API does not return a serial number field, THEN THE Serial_Number_Validator SHALL set Validation_Status to INCONCLUSIVE with reason "IPRS serial number unavailable"
5. IF the IPRS API returns an error, THEN THE Serial_Number_Validator SHALL set Validation_Status to INCONCLUSIVE with reason containing the error details

### Requirement 3: Serial Number Comparison

**User Story:** As a compliance officer, I want the system to compare serial numbers using consistent rules, so that validation outcomes are accurate and auditable.

#### Acceptance Criteria

1. THE Serial_Number_Validator SHALL compare the normalized Extracted_Serial_Number against the normalized IPRS_Serial_Number
2. WHEN the normalized serial numbers are identical, THE Serial_Number_Validator SHALL set Validation_Status to MATCH
3. WHEN the normalized serial numbers differ, THE Serial_Number_Validator SHALL set Validation_Status to MISMATCH
4. WHEN either serial number is unavailable, THE Serial_Number_Validator SHALL set Validation_Status to INCONCLUSIVE
5. THE Serial_Number_Validator SHALL complete the comparison within 100ms additional processing time

### Requirement 4: ID Replacement Scenario Handling

**User Story:** As a fraud prevention analyst, I want the system to detect outdated or counterfeit IDs, so that fraudulent applications are rejected.

#### Acceptance Criteria

1. WHEN Validation_Status is MATCH, THE Serial_Number_Validator SHALL indicate the document is the latest issued ID for the customer
2. WHEN Validation_Status is MISMATCH, THE Serial_Number_Validator SHALL flag the document as potentially fraudulent or outdated
3. WHEN Validation_Status is INCONCLUSIVE, THE Serial_Number_Validator SHALL allow the KYC process to continue with other validations
4. THE Serial_Number_Validator SHALL include both the Extracted_Serial_Number and IPRS_Serial_Number in the response for audit purposes

### Requirement 5: Integration with Document Validation

**User Story:** As a system integrator, I want serial number validation integrated into the existing document validation flow, so that it works seamlessly with current processes.

#### Acceptance Criteria

1. THE Document_Validation_Service SHALL invoke the Serial_Number_Validator as part of the `validate_nationalid` action
2. THE Serial_Number_Validator SHALL add a `serialNumberValidation` field to the existing Match_Results structure
3. THE `serialNumberValidation` field SHALL contain: status, extractedSerialNumber, iprsSerialNumber, normalizedComparison, and reason (when applicable)
4. THE Serial_Number_Validator SHALL not block the overall document validation if serial number validation fails
5. WHEN serial number validation completes, THE Document_Validation_Service SHALL include the result in the portal GraphQL response

### Requirement 6: API Response Enhancement

**User Story:** As a portal developer, I want detailed serial number validation results, so that I can display meaningful information to operators.

#### Acceptance Criteria

1. THE Serial_Number_Validator SHALL return a `serialNumberValidation` object in the API response
2. THE `serialNumberValidation` object SHALL contain a `status` field with value MATCH, MISMATCH, or INCONCLUSIVE
3. THE `serialNumberValidation` object SHALL contain an `extractedSerialNumber` field with the normalized serial number from the document
4. THE `serialNumberValidation` object SHALL contain an `iprsSerialNumber` field with the normalized serial number from IPRS (or null if unavailable)
5. THE `serialNumberValidation` object SHALL contain a `normalizedComparison` boolean indicating whether the comparison was performed on normalized values
6. WHEN Validation_Status is not MATCH, THE `serialNumberValidation` object SHALL contain a `reason` field explaining the outcome

### Requirement 7: Audit and Logging

**User Story:** As a compliance auditor, I want comprehensive logging of serial number validations, so that I can review decisions and investigate discrepancies.

#### Acceptance Criteria

1. THE Serial_Number_Validator SHALL log all validation requests with request_id, id_number, and timestamp
2. THE Serial_Number_Validator SHALL log both the original and normalized serial numbers from document and IPRS
3. THE Serial_Number_Validator SHALL log the Validation_Status and reason for each validation
4. WHEN Validation_Status is MISMATCH, THE Serial_Number_Validator SHALL log at WARNING level for fraud monitoring
5. THE Serial_Number_Validator SHALL use AWS Lambda Powertools for structured logging with correlation IDs

### Requirement 8: Error Handling

**User Story:** As a system operator, I want graceful error handling, so that serial number validation failures do not block the KYC process.

#### Acceptance Criteria

1. IF Textract fails to extract the serial number field, THEN THE Serial_Number_Validator SHALL return INCONCLUSIVE status without failing the overall validation
2. IF IPRS API is unavailable, THEN THE Serial_Number_Validator SHALL return INCONCLUSIVE status and log the connectivity issue
3. IF normalization encounters unexpected characters, THEN THE Serial_Number_Validator SHALL handle them gracefully and proceed with comparison
4. THE Serial_Number_Validator SHALL validate input parameters and return appropriate error details for invalid inputs
5. IF an unexpected error occurs, THEN THE Serial_Number_Validator SHALL log the error and return INCONCLUSIVE status with error details
