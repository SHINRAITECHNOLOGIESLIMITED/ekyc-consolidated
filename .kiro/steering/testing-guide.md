# Testing Guide

This guide covers testing patterns for the Jubilee eKYC platform, including unit tests and property-based tests.

---
inclusion: always
---

## Testing Philosophy

The eKYC platform uses a dual testing approach:
1. **Unit Tests**: Verify specific examples and edge cases
2. **Property-Based Tests (PBT)**: Verify universal properties across random inputs

Both are required for comprehensive coverage.

## Test Framework

- **Python**: pytest + hypothesis
- **Mocking**: unittest.mock + moto (AWS)
- **Coverage**: pytest-cov

## Directory Structure

```
backend/core/functions/<function>/
├── src/
│   └── app.py
└── tests/
    ├── __init__.py
    ├── conftest.py           # Shared fixtures
    ├── test_app.py           # Unit tests
    └── test_properties.py    # Property-based tests
```

## Unit Testing Patterns

### Basic Test Structure
```python
import pytest
from src.normalizer import normalize_serial_number

class TestNormalizeSerialNumber:
    """Unit tests for normalize_serial_number function."""
    
    def test_removes_spaces(self):
        assert normalize_serial_number("12345 ABC") == "12345ABC"
    
    def test_removes_hyphens(self):
        assert normalize_serial_number("12345-ABC") == "12345ABC"
    
    def test_removes_dots(self):
        assert normalize_serial_number("12345.ABC") == "12345ABC"
    
    def test_converts_to_uppercase(self):
        assert normalize_serial_number("12345abc") == "12345ABC"
    
    def test_returns_none_for_none_input(self):
        assert normalize_serial_number(None) is None
    
    def test_returns_none_for_empty_string(self):
        assert normalize_serial_number("") is None
    
    def test_returns_none_for_only_formatting_chars(self):
        assert normalize_serial_number("- . -") is None
```

### Parameterized Tests
```python
import pytest

@pytest.mark.parametrize("input_serial,expected", [
    ("12345-ABC", "12345ABC"),
    ("12345 ABC", "12345ABC"),
    ("12345.ABC", "12345ABC"),
    ("12345-abc", "12345ABC"),
    ("  12345-ABC  ", "12345ABC"),
    ("", None),
    ("---", None),
    (None, None),
])
def test_normalize_serial_number(input_serial, expected):
    assert normalize_serial_number(input_serial) == expected
```

### Mocking External Services
```python
from unittest.mock import Mock, patch
from src.app import validate_nationalid

def test_validate_nationalid_with_iprs_success():
    """Test validation when IPRS returns valid data."""
    
    # Mock IPRS response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": {
            "serialNumber": "217990310",
            "gender": "M",
            "firstName": "JOHN"
        }
    }
    
    with patch('src.app.esb_client.iprs.search_generic', return_value=mock_response):
        result = validate_nationalid({
            "idNumber": "12345678",
            "serialNumber": "217990310"
        })
    
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["results"]["serialNumber"]["status"] == "Matched"
```

### Mocking AWS Services with Moto
```python
import boto3
import pytest
from moto import mock_dynamodb

@pytest.fixture
def dynamodb_table():
    """Create mock DynamoDB table for testing."""
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.create_table(
            TableName='ValidationResults',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        yield table

def test_stores_validation_result(dynamodb_table):
    """Test that validation results are stored in DynamoDB."""
    # Test implementation
    pass
```

## Property-Based Testing

### What is Property-Based Testing?

Property-based testing verifies that certain properties hold true for ALL valid inputs, not just specific examples. The testing framework generates random inputs to find edge cases.

### Hypothesis Configuration
```python
from hypothesis import settings, Phase, given, strategies as st

# Configure for minimum 100 examples per test
test_settings = settings(
    max_examples=100,
    phases=[Phase.generate, Phase.target, Phase.shrink],
    deadline=None  # Disable deadline for slow tests
)
```

### Property Test Structure
```python
from hypothesis import given, strategies as st
from src.normalizer import normalize_serial_number

@given(st.text())
@settings(max_examples=100)
def test_property_normalization_is_idempotent(serial):
    """
    Feature: serial-number-validation, Property 1: Normalization Idempotence
    Validates: Requirements 1.2, 2.3
    
    For any serial number string, applying normalization twice
    produces the same result as applying it once.
    """
    once = normalize_serial_number(serial)
    twice = normalize_serial_number(once) if once else None
    assert once == twice
```

### Custom Strategies

```python
from hypothesis import strategies as st
import string

# Generate valid serial number characters
serial_chars = string.ascii_uppercase + string.digits

# Generate valid serial numbers (non-empty after normalization)
valid_serial = st.text(
    alphabet=serial_chars,
    min_size=1,
    max_size=15
)

# Generate serial numbers with formatting variations
def add_formatting(base: str) -> str:
    """Add random formatting to a serial number."""
    import random
    result = list(base)
    for _ in range(random.randint(0, 3)):
        pos = random.randint(0, len(result))
        char = random.choice([' ', '-', '.'])
        result.insert(pos, char)
    return ''.join(result)

formatted_serial = st.builds(add_formatting, valid_serial)

# Generate pairs of matching serials (same base, different formatting)
@st.composite
def matching_serial_pair(draw):
    base = draw(valid_serial)
    return (add_formatting(base), add_formatting(base))
```

### Property Tests for Serial Number Validation

```python
from hypothesis import given, strategies as st, assume
from src.serial_number_validator import validate_serial_number, ValidationStatus
from src.normalizer import normalize_serial_number

@given(st.text(alphabet=string.ascii_uppercase + string.digits, min_size=1))
def test_property_match_for_identical_normalized(serial):
    """
    Feature: serial-number-validation, Property 4: MATCH Decision Correctness
    Validates: Requirements 3.1, 3.2
    
    For any two non-empty serial numbers where normalized values are identical,
    validation returns MATCH.
    """
    # Same serial with different formatting should match
    formatted1 = add_formatting(serial)
    formatted2 = add_formatting(serial)
    
    result = validate_serial_number(formatted1, formatted2)
    assert result.status == ValidationStatus.MATCH


@given(
    st.text(alphabet=string.ascii_uppercase + string.digits, min_size=1),
    st.text(alphabet=string.ascii_uppercase + string.digits, min_size=1)
)
def test_property_mismatch_for_different_normalized(serial1, serial2):
    """
    Feature: serial-number-validation, Property 5: MISMATCH Decision Correctness
    Validates: Requirements 3.3, 6.6
    
    For any two non-empty serial numbers where normalized values differ,
    validation returns MISMATCH with a non-empty reason.
    """
    # Skip if they happen to be the same
    assume(serial1 != serial2)
    
    result = validate_serial_number(serial1, serial2)
    assert result.status == ValidationStatus.MISMATCH
    assert result.reason is not None
    assert len(result.reason) > 0


@given(st.one_of(st.none(), st.just(""), st.just("   ")))
def test_property_inconclusive_for_missing_extracted(empty_value):
    """
    Feature: serial-number-validation, Property 6: INCONCLUSIVE for Missing Data
    Validates: Requirements 1.3, 1.4, 3.4
    
    When extracted serial is None or empty, validation returns INCONCLUSIVE.
    """
    result = validate_serial_number(empty_value, "12345ABC")
    assert result.status == ValidationStatus.INCONCLUSIVE
    assert result.reason is not None
```

### Property Test Tagging Convention

Every property test MUST include a docstring with:
```python
"""
Feature: <feature-name>, Property N: <Property Title>
Validates: Requirements X.Y, X.Z
"""
```

This enables traceability from tests to requirements.

## Test Fixtures

### conftest.py
```python
import pytest
import os
from unittest.mock import Mock

@pytest.fixture(autouse=True)
def set_env_vars():
    """Set required environment variables for tests."""
    os.environ['AWS_REGION'] = 'eu-west-1'
    os.environ['POWERTOOLS_SERVICE_NAME'] = 'test-service'
    yield
    # Cleanup if needed

@pytest.fixture
def mock_iprs_response():
    """Create a mock IPRS API response."""
    def _create_response(data=None, status_code=200, success=True):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = {
            "success": success,
            "error": None,
            "data": data or {
                "serialNumber": "217990310",
                "gender": "M",
                "firstName": "JOHN",
                "surname": "SMITH"
            }
        }
        return response
    return _create_response

@pytest.fixture
def mock_esb_client(mock_iprs_response):
    """Create a mock ESB client."""
    client = Mock()
    client.iprs.search_generic.return_value = mock_iprs_response()
    return client
```

## Running Tests

### Run All Tests
```bash
cd backend/core/functions/document_validation
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_normalizer.py -v
```

### Run Property Tests Only
```bash
pytest tests/test_properties.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Run with Verbose Hypothesis Output
```bash
pytest tests/test_properties.py -v --hypothesis-show-statistics
```

## Coverage Requirements

| Module | Minimum Coverage |
|--------|-----------------|
| normalizer.py | 95% |
| serial_number_validator.py | 90% |
| Integration code | 80% |

## Debugging Failed Property Tests

When a property test fails, Hypothesis provides a counterexample:

```
Falsifying example: test_property_normalization_is_idempotent(
    serial='\x00'
)
```

Steps to debug:
1. Add the counterexample as a unit test
2. Investigate why the property doesn't hold
3. Either fix the code or refine the property/strategy

```python
def test_counterexample_null_character():
    """Regression test for null character handling."""
    result = normalize_serial_number('\x00')
    # Decide expected behavior and assert
```

## Best Practices

1. **Test behavior, not implementation** - Focus on what the function does, not how
2. **Use descriptive test names** - `test_returns_inconclusive_when_iprs_unavailable`
3. **One assertion per test** - Makes failures easier to diagnose
4. **Don't mock what you don't own** - Use integration tests for external services
5. **Property tests complement unit tests** - Use both for comprehensive coverage
6. **Keep tests fast** - Mock slow external calls
7. **Test edge cases explicitly** - Empty strings, None, special characters
