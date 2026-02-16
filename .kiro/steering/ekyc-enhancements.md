# eKYC Enhancement Guidelines

This document provides guidance for implementing the three eKYC enhancement features.

## Feature Branches

| Feature | Branch | Spec Location |
|---------|--------|---------------|
| Face Matching Verification | `feature/face-matching-verification` | `.kiro/specs/face-matching-verification/` |
| Serial Number Validation | `feature/serial-number-validation` | `.kiro/specs/serial-number-validation/` |
| Gender Validation via IPRS | `feature/gender-validation-iprs` | `.kiro/specs/gender-validation-iprs/` |

## Architecture Principles

### Integration Points
- All enhancements integrate with the existing KYC Orchestrator (`/kyc` endpoint)
- New actions are added to `action_router.py` following the existing pattern
- IPRS API calls go through `backend/core/layers/jubilee_esb_api_layer/src/iprs.py`

### Response Format
All responses must follow the existing schema:
```python
{
    "statusCode": int,
    "body": {
        "success": bool,
        "message": str,
        "data": dict  # Feature-specific results
    }
}
```

### Async Job Pattern (Alien ID / Military ID)
`validate_alienid` and `validate_militaryid` use an async pattern because PDF processing + IPRS cross-validation can exceed API Gateway's 29s timeout:

1. Orchestrator creates a job record in `AsyncJobsTable` (DynamoDB) with status PROCESSING
2. Invokes DocumentValidationFn asynchronously (`InvocationType='Event'`) with `asyncJobId` in `requestContext`
3. Returns 202 Accepted with `jobId` to the client
4. DocumentValidationFn completes work and writes result to DynamoDB (COMPLETED or FAILED)
5. Client polls `get_job_status` action with `jobId` to retrieve the result

Key files:
- `backend/core/functions/kyc_orchestrator/src/async_job_service.py` — AsyncJobService class
- `backend/core/functions/kyc_orchestrator/src/action_router.py` — `_handle_alienid_validation`, `_handle_militaryid_validation`, `_handle_get_job_status`
- `backend/core/functions/document_validation/src/app.py` — async result writing (`_write_async_result`, `_fail_async_job`)
- `backend/template.yaml` — `AsyncJobsTable` DynamoDB resource

### Response Fields (v1.2 Updates)
Document validation responses now include:
- `matchResults.<field>.details.ocr_confidence` — Textract OCR confidence (how sure Textract read the text)
- `matchResults.<field>.details.match_score` — Similarity percentage between expected and actual values (0-100%), based on Levenshtein edit distance
- `summary` block with `overall_status` (PASS/FAIL/INCONCLUSIVE), field counts (`matched`, `mismatched`, `not_provided`, `not_found`), aggregate `match_score`, and `mismatched_fields` array

Note: The old `confidence` field has been renamed to `ocr_confidence` to avoid confusion. The new `match_score` field provides the actual similarity metric.

### Error Handling
- Use consistent error codes across all features
- Log all errors with correlation IDs
- Return user-friendly messages while logging technical details

## Testing Requirements

### Property-Based Testing
All features require property-based tests using Hypothesis:
```python
from hypothesis import given, strategies as st

@given(st.text())
def test_property_name(input_data):
    # Property assertion
    pass
```

### Test Coverage
- Unit tests for all new functions
- Integration tests for API endpoints
- Property-based tests for correctness properties defined in design.md

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Maximum line length: 100 characters

### Imports
```python
# Standard library
import json
import logging

# Third-party
import boto3
from hypothesis import given

# Local
from iprs import verify_national_id
```

## Deployment

### SAM Template Updates
New Lambda functions should be added to `backend/template.yaml` following existing patterns:
- Use shared layers for common dependencies
- Configure appropriate IAM permissions
- Set environment variables for API endpoints

### Feature Flags
Consider using feature flags for gradual rollout via `feature_flags.py`.
