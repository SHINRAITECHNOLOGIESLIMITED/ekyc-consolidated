# Testing Guide

This document provides guidance for testing in the Jubilee eKYC project.

## Test Structure

```
backend/core/functions/{function_name}/
├── src/
│   └── app.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── pytest.ini
    ├── requirements.txt
    ├── test_app.py
    └── test_properties.py
```

## Running Tests

```bash
# Run all tests for a function
cd backend/core/functions/{function_name}/tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test file
python -m pytest test_app.py

# Run tests matching pattern
python -m pytest -k "test_validation"
```

## Unit Tests

### Basic Structure

```python
import pytest
from unittest.mock import Mock, patch

def test_validate_nationalid_success():
    """Test successful national ID validation."""
    data = {
        'uploadedDocumentUrl': 's3://bucket/doc.pdf',
        'idNumber': '12345678'
    }
    
    with patch('app.extract') as mock_extract:
        mock_extract.return_value = {'form': {'ID_NUMBER': {'value': '12345678'}}}
        result = validate_nationalid(data)
    
    assert result['statusCode'] == 200
    body = json.loads(result['body'])
    assert 'matchResults' in body['results']
```

### Fixtures

```python
# conftest.py
import pytest

@pytest.fixture
def sample_nationalid_data():
    return {
        'uploadedDocumentUrl': 's3://test-bucket/test.pdf',
        'idNumber': '12345678',
        'fullNames': 'John Doe',
        'dateOfBirth': '1990-01-01'
    }

@pytest.fixture
def mock_textract_response():
    return {
        'form': {
            'ID_NUMBER': {'value': '12345678', 'confidence': 99.5},
            'FULL_NAMES': {'value': 'John Doe', 'confidence': 98.2}
        }
    }
```

## Property-Based Tests

### Setup

```python
from hypothesis import given, strategies as st, settings

# Configure Hypothesis
settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=10)
settings.load_profile("dev")  # Use "ci" in CI/CD
```

### Writing Properties

```python
from hypothesis import given, strategies as st, settings

# Property 1: Normalization Idempotence
@settings(max_examples=100)
@given(st.text(min_size=0, max_size=50))
def test_normalization_idempotent(input_str):
    """
    Feature: serial-number-validation, Property 1: Normalization Idempotence
    Validates: Requirements 1.2, 2.3
    """
    result1 = normalize_serial_number(input_str)
    result2 = normalize_serial_number(result1) if result1 else None
    assert result1 == result2

# Property 2: Character Removal
@settings(max_examples=100)
@given(st.text(alphabet=st.characters(whitelist_categories=['L', 'N', 'P', 'Z'])))
def test_normalization_removes_special_chars(input_str):
    """
    Feature: serial-number-validation, Property 3: Character Removal
    Validates: Requirements 1.2, 2.3, 8.3
    """
    result = normalize_serial_number(input_str)
    if result:
        assert ' ' not in result
        assert '-' not in result
        assert '.' not in result
        assert result == result.upper()
```

### Custom Strategies

```python
from hypothesis import strategies as st

# Generate valid serial numbers
valid_serial = st.text(
    alphabet=st.characters(whitelist_categories=['L', 'N']),
    min_size=1,
    max_size=15
)

# Generate serial numbers with formatting
formatted_serial = st.builds(
    lambda base, sep: sep.join([base[i:i+4] for i in range(0, len(base), 4)]),
    base=valid_serial,
    sep=st.sampled_from([' ', '-', '.', ''])
)

# Generate gender values
valid_gender = st.sampled_from(['M', 'MALE', 'm', 'male', 'F', 'FEMALE', 'f', 'female'])
invalid_gender = st.text().filter(lambda x: x.strip().upper() not in ['M', 'MALE', 'F', 'FEMALE'])
```

## Mocking External Services

### AWS Services

```python
from moto import mock_dynamodb, mock_s3
import boto3

@mock_dynamodb
def test_dynamodb_operation():
    # Create mock table
    dynamodb = boto3.client('dynamodb', region_name='eu-west-1')
    dynamodb.create_table(
        TableName='TestTable',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Run test
    result = my_function()
    assert result['statusCode'] == 200
```

### External APIs

```python
from unittest.mock import patch, Mock

@patch('iprs.IPRS.search_generic')
def test_iprs_integration(mock_search):
    mock_search.return_value = {
        'success': True,
        'data': {
            'firstName': 'John',
            'surname': 'Doe',
            'gender': 'M',
            'serialNumber': '12345ABC'
        }
    }
    
    result = verify_nationalid({'idNumber': '12345678'})
    assert result['status'] == 'MATCH'
```

## Test Coverage Requirements

| Component | Target |
|-----------|--------|
| Core validation logic | 90%+ |
| Error handling paths | 100% |
| Property tests | All properties defined in design.md |
| Integration points | 80%+ |

## CI/CD Integration

```yaml
# Example GitHub Actions workflow
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: |
        cd backend/core/functions/document_validation/tests
        python -m pytest --cov=src --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```
