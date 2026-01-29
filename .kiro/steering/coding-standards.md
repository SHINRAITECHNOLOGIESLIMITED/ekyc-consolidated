# Coding Standards

This document defines coding standards for the Jubilee eKYC platform.

---
inclusion: always
---

## Python Standards

### Style Guide
- Follow PEP 8 style guide
- Use type hints for function signatures
- Maximum line length: 120 characters
- Use f-strings for string formatting

### Imports
```python
# Standard library
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

# Third-party
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.validation import validate

# Local
from serial_number_validator import validate_serial_number
from normalizer import normalize_serial_number
```

### Type Hints
```python
def validate_serial_number(
    extracted_serial: Optional[str],
    iprs_serial: Optional[str]
) -> SerialNumberValidationResult:
    """Validate serial number with proper type hints."""
    pass
```

### Dataclasses for Models
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SerialNumberValidationResult:
    status: str
    extracted_serial_number: Optional[str]
    iprs_serial_number: Optional[str]
    normalized_comparison: bool
    reason: Optional[str] = None
```

### Enums for Constants
```python
from enum import Enum

class ValidationStatus(Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    INCONCLUSIVE = "INCONCLUSIVE"
```

### Error Handling
```python
# Good: Specific exception handling with logging
try:
    result = external_api_call()
except ConnectionError as e:
    logger.warning(f"API connection failed: {e}")
    return fallback_result()
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# Bad: Bare except
try:
    result = external_api_call()
except:
    pass
```

### Logging
```python
from aws_lambda_powertools import Logger

logger = Logger()

# Good: Structured logging with context
logger.info("Validation complete", extra={
    "id_number": id_number,
    "status": result.status,
    "duration_ms": duration
})

# Bad: Unstructured logging
print(f"Validation complete for {id_number}")
```

## Lambda Function Patterns

### Handler Structure
```python
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
tracer = Tracer()

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler with proper decorators."""
    logger.info("Processing request", extra={"event": event})
    
    try:
        result = process_request(event)
        return make_response(200, result)
    except ValidationError as e:
        logger.warning(f"Validation failed: {e}")
        return make_response(400, {"error": str(e)})
    except Exception as e:
        logger.error(f"Handler failed: {e}")
        return make_response(500, {"error": "Internal server error"})
```

### Response Format
```python
def make_response(status_code: int, body: dict) -> dict:
    """Standard API Gateway response format."""
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
- Use interfaces for object shapes
- Use async/await over raw promises

### Component Structure
```typescript
// Good: Typed props with interface
interface ValidationResultProps {
  status: 'MATCH' | 'MISMATCH' | 'INCONCLUSIVE';
  reason?: string;
  extractedValue: string | null;
  iprsValue: string | null;
}

export function ValidationResult({ 
  status, 
  reason, 
  extractedValue, 
  iprsValue 
}: ValidationResultProps) {
  return (
    <div className="validation-result">
      {/* Component content */}
    </div>
  );
}
```

### API Calls
```typescript
// Good: Typed API response
interface SerialNumberValidation {
  status: 'MATCH' | 'MISMATCH' | 'INCONCLUSIVE';
  extractedSerialNumber: string | null;
  iprsSerialNumber: string | null;
  normalizedComparison: boolean;
  reason?: string;
}

async function validateDocument(data: DocumentData): Promise<SerialNumberValidation> {
  const response = await api.post('/kyc', {
    action: 'validate_nationalid',
    data
  });
  return response.data.serialNumberValidation;
}
```

## Documentation Standards

### Function Docstrings
```python
def validate_serial_number(
    extracted_serial: Optional[str],
    iprs_serial: Optional[str]
) -> SerialNumberValidationResult:
    """
    Validate serial number by comparing document extraction with IPRS data.
    
    Compares the serial number extracted from a document via Textract against
    the serial number returned by the IPRS API. Both values are normalized
    before comparison.
    
    Args:
        extracted_serial: Serial number extracted from document via Textract.
            May be None if extraction failed.
        iprs_serial: Serial number from IPRS API response.
            May be None if IPRS lookup failed.
    
    Returns:
        SerialNumberValidationResult containing:
        - status: MATCH, MISMATCH, or INCONCLUSIVE
        - extracted_serial_number: Normalized extracted serial
        - iprs_serial_number: Normalized IPRS serial
        - normalized_comparison: True if comparison used normalized values
        - reason: Explanation for non-MATCH status
    
    Example:
        >>> result = validate_serial_number("12345-ABC", "12345 ABC")
        >>> result.status
        ValidationStatus.MATCH
    """
    pass
```

### Module Docstrings
```python
"""
Serial Number Validator Module

This module provides functionality for validating National ID serial numbers
by comparing document-extracted values against IPRS government records.

Key Components:
    - ValidationStatus: Enum for validation outcomes
    - SerialNumberValidationResult: Dataclass for validation results
    - validate_serial_number: Main validation function

Usage:
    from serial_number_validator import validate_serial_number
    
    result = validate_serial_number(extracted_serial, iprs_serial)
    if result.status == ValidationStatus.MISMATCH:
        logger.warning("Potential fraud detected")

Requirements:
    - Requirements 1.2, 2.3, 3.1-3.4 from serial-number-validation spec
"""
```

## Naming Conventions

### Python
- **Functions**: `snake_case` - `validate_serial_number()`
- **Variables**: `snake_case` - `extracted_serial`
- **Classes**: `PascalCase` - `SerialNumberValidator`
- **Constants**: `UPPER_SNAKE_CASE` - `MAX_RETRIES`
- **Private**: `_leading_underscore` - `_internal_method()`

### TypeScript
- **Functions**: `camelCase` - `validateSerialNumber()`
- **Variables**: `camelCase` - `extractedSerial`
- **Interfaces**: `PascalCase` - `SerialNumberValidation`
- **Constants**: `UPPER_SNAKE_CASE` - `MAX_RETRIES`
- **Components**: `PascalCase` - `ValidationResult`

## Testing Standards

### Test File Naming
- Python: `test_<module_name>.py`
- TypeScript: `<component>.test.tsx`

### Test Function Naming
```python
# Good: Descriptive test names
def test_normalize_removes_spaces_and_hyphens():
    pass

def test_validate_returns_match_for_identical_normalized_serials():
    pass

def test_validate_returns_inconclusive_when_iprs_unavailable():
    pass

# Bad: Vague test names
def test_normalize():
    pass

def test_validate():
    pass
```

### Property Test Naming
```python
def test_property_normalization_is_idempotent():
    """
    Feature: serial-number-validation, Property 1: Normalization Idempotence
    Validates: Requirements 1.2, 2.3
    """
    pass
```

## Git Commit Standards

### Commit Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

### Examples
```
feat(serial-validation): add serial number normalizer module

Implements normalize_serial_number function that:
- Converts to uppercase
- Removes spaces, hyphens, dots
- Returns None for empty inputs

Requirements: 1.2, 2.3, 8.3

fix(iprs): handle missing serialNumber field gracefully

Return INCONCLUSIVE status instead of raising exception
when IPRS response is missing the serialNumber field.

Fixes #123
```
