# Coding Standards

Guidelines for writing code in the Jubilee eKYC platform.

## Python Standards

### Style Guide

- Follow PEP 8
- Use type hints for function signatures
- Maximum line length: 120 characters
- Use `snake_case` for functions and variables
- Use `PascalCase` for classes
- Use `UPPER_CASE` for constants

### Lambda Handler Pattern

```python
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate

logger = Logger()
tracer = Tracer()

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    """Lambda handler with Powertools instrumentation."""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Parse and validate input
        data = parse_request(event)
        
        # Business logic
        result = process(data)
        
        # Return response
        return make_response(200, result)
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return make_response(400, {"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return make_response(500, {"error": "Internal server error"})
```

### Response Format

```python
def make_response(status_code: int, body: dict) -> dict:
    """Standard API Gateway response format."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(body)
    }
```

### Error Handling

```python
# Use specific exception types
class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class ExternalAPIError(Exception):
    """Raised when external API call fails."""
    pass

# Catch and handle gracefully
try:
    result = external_api_call()
except ExternalAPIError as e:
    logger.warning(f"External API error: {e}")
    return {"status": "INCONCLUSIVE", "reason": str(e)}
```

### Logging

```python
from aws_lambda_powertools import Logger

logger = Logger()

# Structured logging
logger.info("Processing request", extra={
    "action": action,
    "request_id": context.aws_request_id
})

# Log levels
logger.debug("Detailed debug info")
logger.info("Normal operation")
logger.warning("Potential issue - MISMATCH detected")
logger.error("Error occurred")
```

---

## TypeScript Standards (Portal)

### Style Guide

- Use TypeScript strict mode
- Use `camelCase` for functions and variables
- Use `PascalCase` for components and types
- Use `UPPER_CASE` for constants
- Prefer `const` over `let`

### Component Pattern

```typescript
'use client';

import { useState, useEffect } from 'react';

interface Props {
  documentId: string;
  onValidate: (result: ValidationResult) => void;
}

export default function DocumentValidator({ documentId, onValidate }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Effect logic
  }, [documentId]);

  return (
    <div className="p-4">
      {loading && <Spinner />}
      {error && <ErrorAlert message={error} />}
      {/* Component content */}
    </div>
  );
}
```

### API Calls

```typescript
import { API_BASE_URL } from '@/constants/api';

export async function validateDocument(data: ValidationRequest): Promise<ValidationResponse> {
  const response = await fetch(`${API_BASE_URL}/kyc`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      action: 'validate_nationalid',
      data
    })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}
```

---

## Testing Standards

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch

class TestSerialNumberValidator:
    """Tests for serial number validation."""
    
    def test_match_identical_serials(self):
        """MATCH when serial numbers are identical."""
        result = validate_serial_number("12345ABC", "12345ABC")
        assert result.status == ValidationStatus.MATCH
    
    def test_match_after_normalization(self):
        """MATCH when serials match after normalization."""
        result = validate_serial_number("12345-ABC", "12345 ABC")
        assert result.status == ValidationStatus.MATCH
    
    def test_mismatch_different_serials(self):
        """MISMATCH when serial numbers differ."""
        result = validate_serial_number("12345ABC", "67890XYZ")
        assert result.status == ValidationStatus.MISMATCH
        assert result.reason is not None
```

### Property-Based Tests

```python
from hypothesis import given, strategies as st, settings

@settings(max_examples=100)
@given(st.text(min_size=1, max_size=20))
def test_normalization_idempotence(serial):
    """
    Property 1: Normalization Idempotence
    Validates: Requirements 1.2, 2.3
    """
    normalized = normalize_serial_number(serial)
    if normalized is not None:
        assert normalize_serial_number(normalized) == normalized
```

### Test File Location

- Unit tests: `backend/core/functions/<function>/tests/`
- E2E tests: `e2e/tests/`
- Property tests: Same directory as unit tests, prefixed with `test_property_`

---

## Documentation

### Docstrings

```python
def validate_serial_number(
    extracted_serial: Optional[str],
    iprs_serial: Optional[str]
) -> SerialNumberValidationResult:
    """
    Validate serial number by comparing document extraction with IPRS data.
    
    Compares the serial number extracted from a National ID document against
    the latest serial number from IPRS. Both values are normalized before
    comparison to handle formatting differences.
    
    Args:
        extracted_serial: Serial number extracted from document via Textract.
            May be None if extraction failed.
        iprs_serial: Serial number from IPRS API response.
            May be None if IPRS lookup failed.
    
    Returns:
        SerialNumberValidationResult with:
        - status: MATCH, MISMATCH, or INCONCLUSIVE
        - extracted_serial_number: Normalized extracted serial
        - iprs_serial_number: Normalized IPRS serial
        - normalized_comparison: True if comparison used normalized values
        - reason: Explanation for non-MATCH status
    
    Example:
        >>> validate_serial_number("12345-ABC", "12345 ABC")
        SerialNumberValidationResult(status=MATCH, ...)
    """
```

### Comments

```python
# Good: Explains WHY
# IPRS returns dates in American format (M/D/YYYY), not D/M/YYYY
date_formats = ['%m/%d/%Y', '%d/%m/%Y', ...]

# Bad: Explains WHAT (obvious from code)
# Loop through the list
for item in items:
```
