# Jubilee eKYC Platform Overview

This document provides essential context for working on the Jubilee eKYC platform.

## Project Summary

A serverless AWS-based Know Your Customer (KYC) solution for Jubilee Insurance Company (Kenya). The platform validates customer identity documents, performs government verification, and conducts background checks.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | AWS SAM, Python 3.11, Lambda |
| Frontend | AWS Amplify Gen 2, Next.js 14, React, TypeScript |
| Database | DynamoDB, S3 |
| AI/ML | AWS Textract (OCR), Rekognition (Face) |
| External APIs | IPRS, KRA, LexisNexis via ESB |
| Auth | AWS Cognito |

## Architecture

```
Portal (Next.js) → API Gateway → KYC Orchestrator → Feature Lambdas
                                       ↓
                              [Document Validation]
                              [Government Verification]
                              [Face Liveness]
                              [Background Check]
                              [Certification]
```

## Key Directories

```
backend/
├── core/
│   ├── functions/           # Lambda functions
│   │   ├── document_validation/   # Textract-based doc validation
│   │   ├── government_verification/  # IPRS/KRA verification
│   │   ├── face_liveness/         # Rekognition face liveness
│   │   ├── background_check/      # LexisNexis screening
│   │   ├── certification/         # Final KYC certification
│   │   └── kyc_orchestrator/      # Unified /kyc endpoint
│   └── layers/              # Shared Lambda layers
│       ├── jubilee_esb_api_layer/  # ESB integration
│       └── document_textract/      # Textract utilities
├── shared/
│   ├── functions/authorizer/      # API Gateway authorizer
│   └── layers/portal_project/     # Portal GraphQL client
└── template.yaml            # SAM template

portal/                      # Next.js frontend
├── amplify/                 # Amplify Gen 2 config
└── src/
    ├── app/                 # Next.js app router pages
    ├── components/          # React components
    └── services/            # API clients
```

## KYC Orchestrator Actions

The `/kyc` endpoint routes requests based on `action` field:

| Action | Lambda | Description | Response |
|--------|--------|-------------|----------|
| `validate_nationalid` | DocumentValidationFn | Validate National ID via Textract | Sync (200) |
| `validate_passport` | DocumentValidationFn | Validate Passport via Textract | Sync (200) |
| `validate_krapincertificate` | DocumentValidationFn | Validate KRA PIN certificate | Sync (200) |
| `validate_alienid` | DocumentValidationFn | Validate Alien ID via Textract + IPRS | Async (202 → poll) |
| `validate_militaryid` | DocumentValidationFn | Validate Military ID via Textract + IPRS | Async (202 → poll) |
| `get_job_status` | KYCOrchestratorFn | Poll async job result | Sync (200) |
| `verify_nationalid` | GovernmentVerificationFn | Verify ID against IPRS | Sync (200) |
| `verify_passport` | GovernmentVerificationFn | Verify passport against IPRS | Sync (200) |
| `verify_kra` | GovernmentVerificationFn | Verify KRA PIN | Sync (200) |
| `background_check` | BackgroundCheckFn | LexisNexis screening | Sync (200) |
| `create_liveness_session` | FaceLivenessFn | Start face liveness check | Sync (200) |
| `get_liveness_results` | FaceLivenessFn | Get liveness results | Sync (200) |
| `face_match` | FaceMatchingFn | 3-way face comparison | Sync (200) |

### Async Job Pattern

`validate_alienid` and `validate_militaryid` use an async pattern to avoid API Gateway's 29s timeout (PDF processing + IPRS cross-validation can exceed this). The flow:

1. Client sends request → Orchestrator creates job in DynamoDB (PROCESSING), invokes Lambda async, returns 202 with `jobId`
2. Client polls `get_job_status` with `jobId` every 5s
3. When status is `COMPLETED`, the `result` field contains the full validation response
4. Jobs expire after 24 hours (DynamoDB TTL)

Infrastructure: `AsyncJobsTable` (DynamoDB, PAY_PER_REQUEST, TTL enabled)

## v1.2 Features (In Development)

| Feature | Status | Branch |
|---------|--------|--------|
| Face Matching (70% threshold) | Spec complete | `feature/face-matching-verification` |
| Serial Number Validation | Spec complete | `feature/serial-number-validation` |
| Gender Validation (IPRS) | Spec complete | `feature/gender-validation-iprs` |

### Integration Branch

All v1.2 features merge to `develop_v1.2` before final merge to `develop`.

## External API Dependencies

| Service | Provider | Purpose |
|---------|----------|---------|
| IPRS | Kenya Government | National ID/Passport verification |
| KRA | Kenya Revenue Authority | Tax PIN validation |
| LexisNexis | LexisNexis Risk Solutions | Background/sanctions screening |

All external APIs accessed via Jubilee ESB gateway at `https://jubipay.jubileeinsurance.com`.

## Environment Variables

Key Lambda environment variables:
- `JUBILEE_ESB_API_SECRET_ARN` - ESB credentials in Secrets Manager
- `PORTAL_SECRET_ARN` - Portal GraphQL credentials
- `DOCUMENT_VALIDATION_FN_ARN` - Document validation Lambda ARN
- `GOVERNMENT_VERIFICATION_FN_ARN` - Government verification Lambda ARN
- `ASYNC_JOBS_TABLE_NAME` - DynamoDB table for async job tracking (used by KYCOrchestratorFn and DocumentValidationFn)

## Testing

```bash
# Unit tests
cd backend/core/functions/<function>/tests
pytest

# E2E tests
cd e2e
pytest tests/
```

## Deployment

```bash
cd backend
sam build
sam deploy --guided
```

See `backend/samconfig.toml` for deployment configuration.
