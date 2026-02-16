# Requirements Document

## Introduction

This document specifies the requirements for adding support for additional document types to the Jubilee eKYC platform. The platform currently supports National ID, Passport, KRA PIN Certificate, and CR12 documents. This enhancement adds support for Alien ID, Military ID, Diplomatic ID, Refugee ID, Work Permit, and Dependant Pass documents to serve a broader range of customers including foreign residents, military personnel, diplomats, and refugees in Kenya.

## Glossary

- **Document_Validation_Service**: The Lambda function that performs OCR extraction using AWS Textract and validates document fields against provided data
- **Government_Verification_Service**: The Lambda function that verifies extracted document data against IPRS (Integrated Population Registration System) via the Jubilee ESB gateway
- **IPRS**: Integrated Population Registration System - Kenya's government database for identity verification
- **ESB**: Enterprise Service Bus - Jubilee's integration gateway for external API calls
- **Textract**: AWS service for OCR (Optical Character Recognition) extraction from documents
- **Alien_ID**: Identity document issued to foreign nationals residing in Kenya
- **Military_ID**: Identity document issued to Kenya Defence Forces personnel
- **Diplomatic_ID**: Identity document issued to diplomatic personnel in Kenya
- **Refugee_ID**: Identity document issued to registered refugees in Kenya
- **Work_Permit**: Document authorizing foreign nationals to work in Kenya
- **Dependant_Pass**: Document issued to dependants of work permit holders
- **Normalization**: The process of standardizing field values by converting to uppercase and removing formatting characters

## Requirements

### Requirement 1: Alien ID Document Validation

**User Story:** As a KYC operator, I want to validate Alien ID documents, so that I can onboard foreign residents in Kenya.

#### Acceptance Criteria

1. WHEN an Alien ID document URL is submitted to the `/document/alienid` endpoint, THE Document_Validation_Service SHALL download the document and extract fields using Textract
2. WHEN extracting Alien ID fields, THE Document_Validation_Service SHALL extract: alien ID number, full names, nationality, date of birth, date of issue, date of expiry, and gender
3. WHEN comparing extracted fields with provided data, THE Document_Validation_Service SHALL normalize both values before comparison
4. WHEN validation completes, THE Document_Validation_Service SHALL return match results with status (Matched/Not Matched/Not Found) for each field
5. IF the document cannot be downloaded or processed, THEN THE Document_Validation_Service SHALL return an appropriate error response with status code 400 or 500

### Requirement 2: Alien ID Government Verification

**User Story:** As a KYC operator, I want to verify Alien ID data against IPRS, so that I can confirm the identity of foreign residents.

#### Acceptance Criteria

1. WHEN an Alien ID verification request is submitted to the `/government/alienid` endpoint, THE Government_Verification_Service SHALL call the IPRS `search_alien_id` API
2. WHEN IPRS returns data, THE Government_Verification_Service SHALL compare provided fields against IPRS response fields
3. WHEN comparing fields, THE Government_Verification_Service SHALL normalize date fields to handle different date formats
4. WHEN verification completes, THE Government_Verification_Service SHALL return match results with validation accuracy percentage
5. IF IPRS returns an error or no data, THEN THE Government_Verification_Service SHALL return an appropriate error response

### Requirement 3: Military ID Document Validation

**User Story:** As a KYC operator, I want to validate Military ID documents, so that I can onboard military personnel.

#### Acceptance Criteria

1. WHEN a Military ID document URL is submitted to the `/document/militaryid` endpoint, THE Document_Validation_Service SHALL download the document and extract fields using Textract
2. WHEN extracting Military ID fields, THE Document_Validation_Service SHALL extract: service number, full names, rank, unit, date of birth, and blood group
3. WHEN comparing extracted fields with provided data, THE Document_Validation_Service SHALL normalize both values before comparison
4. WHEN validation completes, THE Document_Validation_Service SHALL return match results with status for each field
5. IF the document cannot be downloaded or processed, THEN THE Document_Validation_Service SHALL return an appropriate error response

### Requirement 4: Military ID Government Verification

**User Story:** As a KYC operator, I want to verify Military ID data against IPRS using the linked National ID, so that I can confirm military personnel identity.

#### Acceptance Criteria

1. WHEN a Military ID verification request is submitted with a linked National ID number, THE Government_Verification_Service SHALL call the IPRS `search_generic` API using the National ID
2. WHEN IPRS returns data, THE Government_Verification_Service SHALL compare provided name and date of birth fields against IPRS response
3. WHEN verification completes, THE Government_Verification_Service SHALL return match results indicating cross-reference status
4. IF no linked National ID is provided, THEN THE Government_Verification_Service SHALL return validation-only results without IPRS verification

### Requirement 5: Diplomatic ID Document Validation

**User Story:** As a KYC operator, I want to validate Diplomatic ID documents, so that I can onboard diplomatic personnel.

#### Acceptance Criteria

1. WHEN a Diplomatic ID document URL is submitted to the `/document/diplomaticid` endpoint, THE Document_Validation_Service SHALL download the document and extract fields using Textract
2. WHEN extracting Diplomatic ID fields, THE Document_Validation_Service SHALL extract: diplomatic ID number, full names, nationality, mission/embassy, date of birth, date of issue, and date of expiry
3. WHEN comparing extracted fields with provided data, THE Document_Validation_Service SHALL normalize both values before comparison
4. WHEN validation completes, THE Document_Validation_Service SHALL return match results with status for each field

### Requirement 6: Refugee ID Document Validation

**User Story:** As a KYC operator, I want to validate Refugee ID documents, so that I can onboard registered refugees.

#### Acceptance Criteria

1. WHEN a Refugee ID document URL is submitted to the `/document/refugeeid` endpoint, THE Document_Validation_Service SHALL download the document and extract fields using Textract
2. WHEN extracting Refugee ID fields, THE Document_Validation_Service SHALL extract: refugee ID number, full names, country of origin, date of birth, date of issue, and camp/settlement
3. WHEN comparing extracted fields with provided data, THE Document_Validation_Service SHALL normalize both values before comparison
4. WHEN validation completes, THE Document_Validation_Service SHALL return match results with status for each field

### Requirement 7: Work Permit Document Validation

**User Story:** As a KYC operator, I want to validate Work Permit documents, so that I can onboard foreign workers.

#### Acceptance Criteria

1. WHEN a Work Permit document URL is submitted to the `/document/workpermit` endpoint, THE Document_Validation_Service SHALL download the document and extract fields using Textract
2. WHEN extracting Work Permit fields, THE Document_Validation_Service SHALL extract: permit number, full names, nationality, employer, occupation, date of issue, and date of expiry
3. WHEN comparing extracted fields with provided data, THE Document_Validation_Service SHALL normalize both values before comparison
4. WHEN validation completes, THE Document_Validation_Service SHALL return match results with status for each field

### Requirement 8: Dependant Pass Document Validation

**User Story:** As a KYC operator, I want to validate Dependant Pass documents, so that I can onboard dependants of work permit holders.

#### Acceptance Criteria

1. WHEN a Dependant Pass document URL is submitted to the `/document/dependantpass` endpoint, THE Document_Validation_Service SHALL download the document and extract fields using Textract
2. WHEN extracting Dependant Pass fields, THE Document_Validation_Service SHALL extract: pass number, full names, relationship to principal, principal's permit number, date of birth, date of issue, and date of expiry
3. WHEN comparing extracted fields with provided data, THE Document_Validation_Service SHALL normalize both values before comparison
4. WHEN validation completes, THE Document_Validation_Service SHALL return match results with status for each field

### Requirement 9: Document Type Registry

**User Story:** As a system administrator, I want all new document types registered in the portal layer, so that validation and verification records are properly categorized.

#### Acceptance Criteria

1. THE Portal_Layer SHALL include ALIEN_ID, MILITARY_ID, DIPLOMATIC_ID, REFUGEE_ID, WORK_PERMIT, and DEPENDANT_PASS in the DOCUMENT_TYPE enum
2. WHEN capturing document validation results, THE Portal_Layer SHALL accept any of the new document types
3. WHEN capturing document verification results, THE Portal_Layer SHALL accept any of the new document types

### Requirement 10: Field Normalization Consistency

**User Story:** As a developer, I want consistent field normalization across all document types, so that comparisons are reliable.

#### Acceptance Criteria

1. WHEN normalizing text fields, THE Document_Validation_Service SHALL convert to uppercase and trim whitespace
2. WHEN normalizing date fields, THE Document_Validation_Service SHALL parse multiple date formats including DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY, and textual formats like "18 May 1987"
3. WHEN calculating edit distance for non-matching fields, THE Document_Validation_Service SHALL use Levenshtein distance algorithm
4. FOR ALL document types, THE Document_Validation_Service SHALL apply the same normalization rules consistently

### Requirement 11: API Response Consistency

**User Story:** As an API consumer, I want consistent response formats across all document type endpoints, so that I can handle responses uniformly.

#### Acceptance Criteria

1. FOR ALL validation endpoints, THE Document_Validation_Service SHALL return responses with statusCode, message, s3Path, and results fields
2. FOR ALL verification endpoints, THE Government_Verification_Service SHALL return responses with statusCode, message, and results fields
3. WHEN validation or verification fails, THE Services SHALL return error responses with message and error fields
4. FOR ALL endpoints, THE Services SHALL include CORS headers in responses

### Requirement 12: v1.2 Feature Integration

**User Story:** As a product owner, I want v1.2 features (serial number validation, gender validation) applied to applicable new document types, so that fraud detection is comprehensive.

#### Acceptance Criteria

1. WHERE Alien ID documents contain serial numbers, THE Document_Validation_Service SHALL perform serial number validation against IPRS
2. WHERE document types include gender fields, THE Document_Validation_Service SHALL perform gender validation against IPRS when IPRS data is available
3. WHEN IPRS validation is not available for a document type, THE Document_Validation_Service SHALL return INCONCLUSIVE status for those validations
