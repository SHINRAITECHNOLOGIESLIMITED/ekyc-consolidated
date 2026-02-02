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
