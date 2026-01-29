# Jubilee eKYC Project Overview

This document provides technical context for the Jubilee eKYC platform.

## Architecture Summary

The Jubilee eKYC platform is a serverless AWS-based Know Your Customer (KYC) solution for Jubilee Insurance Company in Kenya.

### Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | AWS SAM, Python 3.11, Lambda |
| Frontend | AWS Amplify Gen 2, Next.js, React, TypeScript |
| Database | DynamoDB |
| Storage | S3 |
| Auth | Cognito |
| Document Processing | AWS Textract |
| Face Detection | AWS Rekognition |
| External APIs | IPRS, KRA, LexisNexis via ESB |

### Project Structure

```
├── backend/                    # AWS SAM serverless backend
│   ├── core/                   # Core KYC functions
│   │   ├── functions/          # Lambda functions
│   │   └── layers/             # Shared Lambda layers
│   ├── process/                # Workflow functions
│   │   ├── functions/          # Registration handlers
│   │   └── state_machines/     # Step Functions definitions
│   └── shared/                 # Shared utilities
├── portal/                     # Next.js admin portal
│   ├── amplify/                # Amplify Gen 2 config
│   └── src/                    # React application
├── e2e/                        # End-to-end tests
└── .kiro/                      # Kiro specs and steering
    ├── specs/                  # Feature specifications
    └── steering/               # Technical guidance
```

## Core Lambda Functions

| Function | Purpose | Endpoint |
|----------|---------|----------|
| KYCOrchestratorFn | Unified KYC endpoint | `/kyc` |
| DocumentValidationFn | Document OCR validation | `/document/*` |
| GovernmentVerificationFn | IPRS/KRA verification | `/government/*` |
| BackgroundChecksFn | LexisNexis checks | `/backgroundcheck` |
| FaceLivenessFn | Face liveness detection | `/faceliveness` |
| CertificationFn | PDF certificate generation | - |
| RegistrationFn | Customer/Agent registration | `/agent-registration`, `/customer-registration` |
| DocumentStreamingFn | S3 document streaming | `/stream/*` |

## KYC Orchestrator Actions

The unified `/kyc` endpoint uses action-based routing:

```python
# Document Validation Actions
'validate_nationalid'
'validate_passport'
'validate_krapincertificate'
'validate_cr12'

# Government Verification Actions
'government_verify_nationalid'
'government_verify_passport'
'government_verify_kra'

# Other KYC Operations
'background_check'
'face_liveness'
'agent_registration'
'customer_registration'
'stream_document'
'get_certificate'
'generate_certificate'
'get_kyc_status'
```

## External API Integrations

### IPRS (Integrated Population Registration System)
- Kenya's official government identity database
- Accessed via Jubilee ESB layer
- Methods: `search_generic`, `search_passport_number`, `search_alien_id`

### KRA (Kenya Revenue Authority)
- Tax PIN verification
- Accessed via Jubilee ESB layer

### LexisNexis
- Background checks and sanctions screening
- Accessed via Jubilee ESB layer

## Development Commands

```bash
# Build
sam build

# Local testing
sam local invoke FunctionName -e event.json
sam local start-api

# Deploy
sam validate --lint
sam build
sam deploy

# Tests
cd backend/core/functions/*/tests
python -m pytest
```
