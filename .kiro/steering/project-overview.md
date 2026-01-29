# Jubilee eKYC Platform Overview

This document provides an overview of the Jubilee eKYC platform architecture and technology stack.

---
inclusion: always
---

## Project Summary

The Jubilee eKYC platform is a serverless Know Your Customer (KYC) solution built on AWS for Jubilee Insurance Company (Kenya). It automates identity verification for insurance customers and agents.

## Technology Stack

### Backend
- **Runtime**: Python 3.11+
- **Framework**: AWS SAM (Serverless Application Model)
- **Compute**: AWS Lambda
- **API**: Amazon API Gateway (REST)
- **Database**: Amazon DynamoDB
- **Storage**: Amazon S3
- **Secrets**: AWS Secrets Manager
- **Parameters**: AWS SSM Parameter Store

### Frontend
- **Framework**: Next.js 14+ with React
- **Platform**: AWS Amplify Gen 2
- **Auth**: Amazon Cognito
- **API Client**: AWS Amplify client libraries

### External Integrations
- **IPRS**: Kenya's Integrated Population Registration System (via ESB)
- **KRA**: Kenya Revenue Authority tax PIN validation (via ESB)
- **LexisNexis**: Background checks and sanctions screening (via ESB)
- **AWS Textract**: Document OCR and field extraction
- **AWS Rekognition**: Face liveness detection and comparison

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Portal (Next.js)                         │
│                      AWS Amplify Gen 2                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (REST)                         │
│                    /kyc unified endpoint                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     KYC Orchestrator Lambda                     │
│              Action-based routing to services                   │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Document    │     │  Government   │     │    Face       │
│  Validation   │     │ Verification  │     │  Liveness     │
│    Lambda     │     │    Lambda     │     │   Lambda      │
└───────────────┘     └───────────────┘     └───────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Textract    │     │   ESB Layer   │     │  Rekognition  │
│   (AWS)       │     │ (IPRS/KRA)    │     │    (AWS)      │
└───────────────┘     └───────────────┘     └───────────────┘
```

## Key Components

### KYC Orchestrator
- **Location**: `backend/core/functions/kyc_orchestrator/`
- **Purpose**: Unified `/kyc` endpoint with action-based routing
- **Actions**: `validate_nationalid`, `validate_passport`, `verify_nationalid`, etc.

### Document Validation
- **Location**: `backend/core/functions/document_validation/`
- **Purpose**: Extract and validate document fields using Textract
- **Supports**: National ID, Passport, KRA PIN Certificate, CR12

### Government Verification
- **Location**: `backend/core/functions/government_verification/`
- **Purpose**: Verify extracted data against IPRS/KRA government records

### Face Liveness
- **Location**: `backend/core/functions/face_liveness/`
- **Purpose**: Detect live faces and prevent spoofing attacks

### Background Check
- **Location**: `backend/core/functions/background_check/`
- **Purpose**: Sanctions screening via LexisNexis

### ESB Layer
- **Location**: `backend/core/layers/jubilee_esb_api_layer/`
- **Purpose**: Shared layer for ESB API integration (IPRS, KRA, LexisNexis)

## Directory Structure

```
backend/
├── core/
│   ├── functions/
│   │   ├── document_validation/    # Textract-based validation
│   │   ├── government_verification/ # IPRS/KRA verification
│   │   ├── face_liveness/          # Rekognition liveness
│   │   ├── background_check/       # LexisNexis screening
│   │   ├── kyc_orchestrator/       # Unified API router
│   │   └── certification/          # Certificate generation
│   └── layers/
│       ├── jubilee_esb_api_layer/  # ESB integration
│       └── document_textract/      # Textract utilities
├── shared/
│   ├── functions/
│   │   └── authorizer/             # API authorization
│   └── layers/
│       └── portal_project/         # Portal integration
└── template.yaml                   # SAM template
```

## v1.2 Features (In Development)

### 1. Face Matching Verification
- 3-way comparison: Selfie ↔ ID Photo ↔ IPRS Photo
- 70% auto-approval threshold
- Manual review workflow for borderline cases

### 2. Serial Number Validation
- Compare document serial against IPRS latest serial
- Detect replaced/counterfeit IDs
- Non-blocking validation

### 3. Gender Validation
- Cross-validate gender from document against IPRS
- Uses IPRS as authoritative source (NOT LexisNexis)

## Development Workflow

1. **Feature Branches**: `feature/<feature-name>` from `develop`
2. **Integration Branch**: `develop_v1.2` for v1.2 features
3. **Production**: `main` branch
4. **Specs**: `.kiro/specs/<feature-name>/` for requirements, design, tasks

## Deployment

```bash
# Build and deploy
cd backend
sam build
sam deploy --guided

# Deploy specific stack
sam deploy --config-env dev
```

## Testing

- **Unit Tests**: pytest with moto for AWS mocking
- **Property Tests**: Hypothesis library
- **E2E Tests**: `e2e/tests/` directory
- **Run Tests**: `pytest backend/core/functions/<function>/tests/`

## Related Documentation

- `esb-response-schemas.md` - ESB API response schemas
- `iprs-integration.md` - IPRS integration patterns
- `coding-standards.md` - Python/TypeScript style guide
- `testing-guide.md` - Testing patterns and PBT guide
