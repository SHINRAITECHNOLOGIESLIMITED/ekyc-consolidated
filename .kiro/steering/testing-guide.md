# Testing Guide

Guidelines for testing the Jubilee eKYC platform, including property-based testing.

## Testing Philosophy

1. **Unit tests** verify specific examples and edge cases
2. **Property tests** verify universal properties across all inputs
3. **Integration tests** verify component interactions
4. **E2E tests** verify complete user flows

All v1.2 features require both unit tests AND property-based tests.

---

## Property-Based Testing

### What is Property-Based Testing?

Instead of testing specific examples, property-based testing:
1. Defines properties that should ALWAYS hold true
2. Generates random inputs to test those properties
3. Shrinks failing cases to minimal counterexamples

### Library: Hypothesis

```python
from hypothesis import given, strategies as st, settings

@settings(max_examples=100)
@given(st.text(min_size=1, max_size=20))
def test_property_name(input_value):
    """
    Feature: serial-number-validation, Property 1: Normalization Idempotence
    Validates: Requirements 1.2, 2.3
    """
    # Test the property
    result = function_under_test(input_value)
    assert property_holds(result)
```

### Configuration

```python
from hypothesis import settings, Phase

# Standard settings for all property tests
test_settings = settings(
    max_examples=100,           # Minimum 100 iterations
    phases=[Phase.generate, Phase.target, Phase.shrink],
    deadline=None               # No timeout
)
```

### Tagging Convention

Every property test MUST include a docstring tag:

```python
def test_normalization_idempotence():
    """
    Feature: serial-number-validation, Property 1: Normalization Idempotence
    Validates: Requirements 1.2, 2.3
    """
```

---

## Test Generators

### Serial Number Generators

```python
from hypothesis import strategies as st
import string

# Characters allowed in serial numbers
serial_chars = string.ascii_uppercase + string.digits

# Random serial number strings (may include formatting)
serial_number = st.text(
    alphabet=serial_chars + " -.",
    min_size=1,
    max_size=20
)

# Valid serial numbers (non-empty after normalization)
valid_serial = st.text(
    alphabet=serial_chars,
    min_size=1,
    max_size=15
)

# Optional serial (including None)
optional_serial = st.one_of(st.none(), valid_serial)

# Pairs of matching serials (same base, different formatting)
def add_formatting(base: str) -> str:
    """Add random spaces/hyphens to a serial number."""
    import random
    result = list(base)
    for _ in range(random.randint(0, 3)):
        pos = random.randint(0, len(result))
        char = random.choice([' ', '-', '.'])
        result.insert(pos, char)
    return ''.join(result)

matching_pair = st.builds(
    lambda base: (add_formatting(base), add_formatting(base)),
    base=valid_serial
)

# Pairs of non-matching serials
non_matching_pair = st.tuples(valid_serial, valid_serial).filter(
    lambda pair: pair[0] != pair[1]
)
```

### Gender Generators

```python
# Valid gender values
valid_gender = st.sampled_from(['M', 'F', 'Male', 'Female', 'm', 'f'])

# Invalid gender values
invalid_gender = st.text(min_size=1, max_size=10).filter(
    lambda x: x.upper() not in ['M', 'F', 'MALE', 'FEMALE']
)
```

### Face Matching Score Generators

```python
# Similarity scores (0-100)
similarity_score = st.floats(min_value=0.0, max_value=100.0)

# Scores in specific bands
approve_score = st.floats(min_value=70.0, max_value=100.0)
review_score = st.floats(min_value=50.0, max_value=69.99)
reject_score = st.floats(min_value=0.0, max_value=49.99)
```

---

## Mocking External Services

### IPRS API Mock

```python
from unittest.mock import Mock, patch

def create_iprs_mock(serial_number=None, gender=None, photo=None):
    """Create a mock IPRS response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "error": None,
        "data": {
            "idNumber": "12345678",
            "serialNumber": serial_number or "217990310",
            "gender": gender or "M",
            "firstName": "JOHN",
            "surname": "DOE",
            "photo": photo
        }
    }
    return mock_response

@patch('jubilee_esb_api.JubileeESBAPI')
def test_with_iprs_mock(mock_esb):
    mock_esb.return_value.iprs.search_generic.return_value = create_iprs_mock(
        serial_number="12345ABC"
    )
    # Test code here
```

### Textract Mock

```python
def create_textract_mock(serial_number=None, gender=None):
    """Create a mock Textract extraction result."""
    return {
        "SERIAL_NUMBER": serial_number or "12345-ABC",
        "GENDER": gender or "M",
        "ID_NUMBER": "12345678",
        "FIRST_NAME": "JOHN",
        "LAST_NAME": "DOE"
    }
```

### Rekognition Mock

```python
def create_rekognition_mock(similarity=85.0):
    """Create a mock Rekognition CompareFaces result."""
    return {
        "FaceMatches": [{
            "Similarity": similarity,
            "Face": {
                "BoundingBox": {...},
                "Confidence": 99.9
            }
        }],
        "UnmatchedFaces": []
    }
```

---

## Test File Structure

```
backend/core/functions/document_validation/
├── src/
│   ├── app.py
│   ├── normalizer.py
│   └── serial_number_validator.py
└── tests/
    ├── __init__.py
    ├── conftest.py              # Shared fixtures
    ├── test_normalizer.py       # Unit tests
    ├── test_property_normalizer.py  # Property tests
    ├── test_serial_number_validator.py
    └── test_property_serial_number_validator.py
```

---

## Running Tests

### Unit Tests

```bash
cd backend/core/functions/document_validation/tests
pytest -v

# With coverage
pytest --cov=src --cov-report=html
```

### Property Tests Only

```bash
pytest -v -k "property"
```

### E2E Tests

```bash
cd e2e
pytest tests/verification/test_verify_nationalid.py -v
```

### E2E Tests for Async Endpoints (Alien ID / Military ID)

`validate_alienid` and `validate_militaryid` use an async job pattern (202 → poll `get_job_status` → COMPLETED). E2E tests for these endpoints must implement polling logic:

```python
# 1. Submit validation request — expect 202 with jobId
response = requests.post(url, json=payload, headers=headers)
assert response.status_code == 202
job_id = response.json()["jobId"]

# 2. Poll get_job_status every 5s until COMPLETED or timeout
for _ in range(max_polls):
    time.sleep(5)
    poll_response = requests.post(url, json={
        "action": "get_job_status",
        "data": {"jobId": job_id}
    }, headers=headers)
    status = poll_response.json().get("status")
    if status == "COMPLETED":
        result = poll_response.json()["result"]
        break
else:
    raise TimeoutError("Job did not complete in time")

# 3. Validate the result payload as usual
assert result["success"] is True
```

See `test_alien1_e2e.py` in the project root for a working example.

### All Tests with Verbose Output

```bash
pytest -v --tb=short
```

---

## Coverage Requirements

| Module | Minimum Coverage |
|--------|-----------------|
| normalizer.py | 95% |
| serial_number_validator.py | 90% |
| gender_validator.py | 90% |
| face_matching.py | 85% |

### Checking Coverage

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=90
```

---

## Triaging Property Test Failures

When a property test fails, you get a counterexample. Determine:

1. **Test is incorrect** → Fix the test
2. **Code has a bug** → Fix the code
3. **Specification is incomplete** → Ask user to clarify requirements

```python
# Example failure output
Falsifying example: test_normalization_idempotence(
    serial='\x00'  # Null character
)

# Analysis: Should null characters be stripped?
# Action: Ask user or update spec
```

---

## Test Data

### Known Test IDs

From `e2e/tests/verification/test_verify_nationalid.py`:

| ID Number | Serial Number | Name | Gender |
|-----------|---------------|------|--------|
| 23667272 | 217934147 | JANE WAIRIMU MAINA | F |
| 32140017 | 702945559 | EFFIE NJOKI NYAMBURA | F |
| 36296352 | 244772451 | JOEL MUUO | M |
| 23224868 | 229769449 | STEPHEN BIKO NYAMAI | M |

### Test Documents

Located in `design and requirements/sample-kyc-documents/`:
- Sample_Kenyan National ID.pdf
- Sample_Kenyan Passport.pdf
- Sample KRA PIN.pdf
