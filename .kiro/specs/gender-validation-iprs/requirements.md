# Requirements Document

## Introduction

This document specifies the requirements for the Gender Validation via IPRS feature for the Jubilee eKYC system. The feature cross-validates gender information extracted from National ID documents against authoritative gender data returned by the IPRS (Integrated Population Registration System) API.

**Business Context**: A past incident where LexisNexis returned incorrect gender data highlighted the need for validation against the official government source. IPRS is Kenya's authoritative identity data source, making it the appropriate validation endpoint for gender data quality assurance.

**Important**: This is a data quality validation feature, not a fraud detection mechanism. The goal is to catch data quality issues early in the KYC process.

## Glossary

- **IPRS**: Integrated Population Registration System - Kenya's official government identity database
- **Gender_Normalizer**: Component that converts various gender representations to standard M/F codes
- **Gender_Validator**: Component that compares normalized gender values from document and IPRS
- **Document_Validation_Function**: Existing Lambda function that validates National ID documents using AWS Textract
- **Textract**: AWS service for extracting text and data from documents
- **ESB**: Enterprise Service Bus - middleware layer for IPRS API integration
- **Validation_Status**: Result of gender comparison - MATCH, MISMATCH, or INCONCLUSIVE

## Requirements

### Requirement 1: Gender Extraction from Document

**User Story:** As a KYC processor, I want to extract gender information from National ID documents, so that I can validate it against government records.

#### Acceptance Criteria

1. WHEN a National ID document is processed, THE Document_Validation_Function SHALL extract the gender value from the SEX field using Textract AnalyzeID
2. WHEN the extracted gender value contains variations such as "M", "MALE", "m", or "male", THE Gender_Normalizer SHALL convert it to the standard code "M"
3. WHEN the extracted gender value contains variations such as "F", "FEMALE", "f", or "female", THE Gender_Normalizer SHALL convert it to the standard code "F"
4. IF the extracted gender value does not match any known gender pattern, THEN THE Gender_Normalizer SHALL return null and log the unrecognized value
5. IF the SEX field is not found in the document, THEN THE Document_Validation_Function SHALL set the extracted gender to null

### Requirement 2: IPRS Gender Retrieval

**User Story:** As a KYC processor, I want to retrieve gender information from IPRS, so that I have authoritative government data for validation.

#### Acceptance Criteria

1. WHEN validating a National ID, THE Document_Validation_Function SHALL query IPRS using the existing search_generic method with ID_NUMBER identifier
2. WHEN IPRS returns a successful response, THE Document_Validation_Function SHALL extract the gender field from the response data
3. WHEN the IPRS gender value is extracted, THE Gender_Normalizer SHALL normalize it using the same rules as document gender
4. IF IPRS returns an error response, THEN THE Document_Validation_Function SHALL log the error and set IPRS gender to null
5. IF IPRS response does not contain a gender field, THEN THE Document_Validation_Function SHALL set IPRS gender to null

### Requirement 3: Gender Validation Logic

**User Story:** As a KYC processor, I want to compare document gender against IPRS gender, so that I can identify potential data quality issues.

#### Acceptance Criteria

1. WHEN both normalized document gender and IPRS gender are available and equal, THE Gender_Validator SHALL return status MATCH
2. WHEN both normalized document gender and IPRS gender are available but differ, THE Gender_Validator SHALL return status MISMATCH
3. WHEN either document gender or IPRS gender is null or unavailable, THE Gender_Validator SHALL return status INCONCLUSIVE
4. WHEN validation status is MISMATCH, THE Gender_Validator SHALL include a reason explaining the discrepancy
5. WHEN validation status is INCONCLUSIVE, THE Gender_Validator SHALL include a reason indicating which source was unavailable

### Requirement 4: Validation Result Structure

**User Story:** As a KYC system integrator, I want gender validation results in a structured format, so that I can process and display them consistently.

#### Acceptance Criteria

1. THE Gender_Validator SHALL return a genderValidation object containing status, extractedGender, iprsGender, normalizedComparison, and reason fields
2. WHEN validation completes, THE genderValidation.status field SHALL contain one of: "MATCH", "MISMATCH", or "INCONCLUSIVE"
3. THE genderValidation.extractedGender field SHALL contain the normalized gender from the document or null if unavailable
4. THE genderValidation.iprsGender field SHALL contain the normalized gender from IPRS or null if unavailable
5. THE genderValidation.normalizedComparison field SHALL contain true if genders match, false if they differ, or null if comparison was not possible
6. WHEN status is not MATCH, THE genderValidation.reason field SHALL contain a human-readable explanation

### Requirement 5: Integration with Existing Workflow

**User Story:** As a system architect, I want gender validation integrated into the existing document validation workflow, so that it enhances rather than disrupts current functionality.

#### Acceptance Criteria

1. THE Document_Validation_Function SHALL include genderValidation in the matchResults structure returned by validate_nationalid
2. THE gender validation process SHALL complete within 50ms additional overhead beyond existing processing time
3. IF gender validation fails due to an exception, THEN THE Document_Validation_Function SHALL log the error and continue with remaining validations
4. THE gender validation SHALL NOT block or fail the overall KYC process regardless of validation result
5. WHEN gender validation completes, THE Document_Validation_Function SHALL log the validation result for audit purposes

### Requirement 6: Error Handling and Logging

**User Story:** As a system administrator, I want comprehensive error handling and logging for gender validation, so that I can troubleshoot issues and maintain audit trails.

#### Acceptance Criteria

1. WHEN gender normalization encounters an unrecognized value, THE Gender_Normalizer SHALL log the original value at WARNING level
2. WHEN IPRS API call fails, THE Document_Validation_Function SHALL log the error details at ERROR level
3. WHEN gender validation completes, THE Document_Validation_Function SHALL log the validation status and both gender values at INFO level
4. IF an unexpected exception occurs during gender validation, THEN THE Document_Validation_Function SHALL log the exception at ERROR level with stack trace
5. THE logging output SHALL include the ID number (masked) for correlation with other validation steps
