# Coding Standards

This document defines coding standards for the Jubilee eKYC project.

## Python Standards

### Style Guide
- Follow PEP 8
- Maximum line length: 100 characters
- Use type hints for all function signatures
- Document all public functions with docstrings

### Import Order
```python
# Standard library
import json
import os
from typing import Dict, Any, Optional

# Third-party
import boto3
from aws_lambda_powertools import Logger, Tracer
from hypothesis import given, strategies as st

# Local
from iprs import IPRS
from portal import Portal
```

### Logging
Use AWS Lambda Powertools for structured logging:

```python
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    logger.info("Processing request", extra={"request_id": event.get("requestId")})
```

### Error Handling
```python
try:
    result = process_data(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    return make_response(400, {"message": "Validation failed", "error": str(e)})
except ExternalAPIError as e:
    logger.error(f"External API error: {e}")
    return make_response(503, {"message": "Service unavailable", "error": str(e)})
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    return make_response(500, {"message": "Internal server error", "error": str(e)})
```

### Response Format
All Lambda responses must follow this structure:

```python
def make_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Methods": "POST, OPTIONS"
        },
        "body": json.dumps(body)
    }
```

## TypeScript Standards (Portal)

### Style Guide
- Use TypeScript strict mode
- Prefer `const` over `let`
- Use interfaces for object types
- Use async/await over raw promises

### Component Structure
```typescript
// imports
import { useState, useEffect } from 'react';

// types
interface Props {
  customerId: string;
}

// component
export const CustomerDetails: React.FC<Props> = ({ customerId }) => {
  const [data, setData] = useState<Customer | null>(null);
  
  useEffect(() => {
    // fetch data
  }, [customerId]);
  
  return (
    // JSX
  );
};
```

## Testing Standards

### Unit Tests
- Test file naming: `test_*.py` or `*_test.py`
- Use pytest as the test framework
- Aim for 80%+ code coverage

### Property-Based Tests
Use Hypothesis for property-based testing:

```python
from hypothesis import given, strategies as st, settings

@settings(max_examples=100)
@given(st.text(min_size=1, max_size=20))
def test_normalization_idempotent(input_str):
    """Property: normalize(normalize(x)) == normalize(x)"""
    result1 = normalize(input_str)
    result2 = normalize(result1) if result1 else None
    assert result1 == result2
```

### Test Tagging
Tag property tests with feature and requirement references:

```python
def test_property_name():
    """
    Feature: feature-name, Property N: Property Title
    Validates: Requirements X.Y
    """
    pass
```

## Git Conventions

### Branch Naming
- Feature branches: `feature/feature-name`
- Bug fixes: `fix/bug-description`
- Hotfixes: `hotfix/issue-description`

### Commit Messages
```
type(scope): subject

body (optional)

footer (optional)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(kyc): add face matching verification
fix(iprs): handle timeout errors gracefully
docs(steering): add coding standards
```
