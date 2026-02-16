---
inclusion: fileMatch
fileMatchPattern: "**/iprs.py,**/government_verification/**/*.py"
---

# IPRS Integration Patterns

Guidelines for integrating with the IPRS (Integrated Population Registration System) API via the Jubilee ESB layer.

## Architecture Overview

```
Lambda Function → JubileeESBAPI → IPRS Class → ESB Gateway → IPRS Government System
```

## Using the IPRS Client

### Initialization

```python
from jubilee_esb_api import JubileeESBAPI
from portal import Portal

portal = Portal()
esb_client = JubileeESBAPI(portal)

# Access IPRS methods
iprs = esb_client.iprs
```

### Available Methods

| Method | Endpoint | Use Case |
|--------|----------|----------|
| `search_generic(data)` | `/iprs/searchV2/LIFE_BUSINESS` | National ID lookup |
| `search_passport_number(data)` | `/iprs/searchUsingPassportNumber/LIFE_BUSINESS` | Passport verification |
| `search_alien_id(data)` | `/iprs/searchUsingAlienId/LIFE_BUSINESS` | Alien ID lookup |
| `search_birth_certificate_number(data)` | `/iprs/searchUsingBirthCertificateNumber/LIFE_BUSINESS` | Birth cert lookup |
| `search_death_certificate_number(data)` | `/iprs/searchUsingDeathCertificateNumber/LIFE_BUSINESS` | Death cert lookup |
| `bulk_iprs_search(data)` | `/iprs/bulk-search/LIFE_BUSINESS` | Batch lookups |
| `ping()` | `/iprs/pingIprs/LIFE_BUSINESS` | Health check |

---

## National ID Search Pattern

### Request

```python
response = esb_client.iprs.search_generic({
    "identifier": "ID_NUMBER",
    "value": "12345678"  # The national ID number
})
```

### Response Handling

```python
if response.status_code >= 400:
    # Handle API error
    logger.error(f"IPRS API error: {response.status_code}")
    return handle_api_error(response)

api_result = response.json()

# Check for business logic errors
if api_result.get("error"):
    return handle_business_error(api_result["error"])

if not api_result.get("success"):
    return handle_unsuccessful_call()

# Extract data
data = api_result.get("data", {})
```

### Extracting Key Fields

```python
# For Serial Number Validation
serial_number = data.get("serialNumber")

# For Gender Validation  
gender = data.get("gender")  # Returns "M" or "F"

# For Face Matching (pending ESB confirmation)
photo = data.get("photo")  # Base64 or URL - needs confirmation

# For Name Matching
first_name = data.get("firstName", "")
other_name = data.get("otherName", "")
surname = data.get("surname", "")
full_name = f"{first_name} {other_name} {surname}".replace("  ", " ").strip().upper()
```

---

## Field Comparison Pattern

Use the existing `process()` function for field-by-field comparison:

```python
def process(event_name, api_field_name, event, api_result, is_date_field=False):
    """
    Compare a field from user input against IPRS response.
    
    Returns:
        dict with 'status' and 'details' keys
        status: "Matched", "Not Matched", "Not provided", "Not Found", "Error in API response"
    """
```

### Example Usage

```python
# Compare serial numbers
serial_result = process(
    event_name='serialNumber',      # Field name in request
    api_field_name='serialNumber',  # Field name in IPRS response
    event=event_data,               # User's request data
    api_result=api_result           # IPRS response
)

# Compare gender
gender_result = process(
    event_name='gender',
    api_field_name='gender',
    event=event_data,
    api_result=api_result
)

# Compare dates (with date normalization)
dob_result = process(
    event_name='dateOfBirth',
    api_field_name='dateOfBirth',
    event=event_data,
    api_result=api_result,
    is_date_field=True  # Enables date format normalization
)
```

---

## Error Handling

### API Error Codes

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 200 | Success | Process response |
| 400 | Bad request | Log and return validation error |
| 401 | Unauthorized | Token expired - auto-refresh handles this |
| 404 | Not found | ID doesn't exist in IPRS |
| 417 | Expectation failed | Passport/ID mismatch |
| 500+ | Server error | Log and return INCONCLUSIVE |

### Graceful Degradation

```python
try:
    response = esb_client.iprs.search_generic(data)
    # ... process response
except JubileeESBError as e:
    logger.error(f"IPRS integration error: {e}")
    return {
        "status": "INCONCLUSIVE",
        "reason": f"IPRS API error: {str(e)}"
    }
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {
        "status": "INCONCLUSIVE", 
        "reason": "Internal error during IPRS validation"
    }
```

---

## Caching Behavior

- **Cache Duration**: 7 days (configured in ESB layer)
- **Cache Key**: Based on identifier type + value
- **Cache Storage**: DynamoDB

IPRS responses are cached to reduce API calls and improve latency. Be aware that cached data may be up to 7 days old.

---

## Token Management

The ESB layer handles token management automatically:
- **Token Validity**: 5 minutes
- **Auto-Refresh**: At 4.5 minutes
- **Storage**: In-memory only (never persisted)

No manual token handling required in Lambda functions.

---

## Logging Best Practices

```python
from aws_lambda_powertools import Logger

logger = Logger()

# Log IPRS requests (without sensitive data)
logger.info("IPRS lookup", extra={
    "identifier_type": "ID_NUMBER",
    "id_number_masked": f"***{id_number[-4:]}"  # Mask sensitive data
})

# Log validation results
logger.info("Serial number validation", extra={
    "status": "MATCH",
    "id_number_masked": f"***{id_number[-4:]}"
})

# Log mismatches at WARNING level
if status == "MISMATCH":
    logger.warning("Serial number mismatch detected", extra={
        "extracted_serial": extracted,
        "iprs_serial": iprs_serial,
        "id_number_masked": f"***{id_number[-4:]}"
    })
```

---

## v1.2 Feature Integration Points

### Serial Number Validation

```python
# In document_validation/src/app.py
from serial_number_validator import validate_serial_number

# After Textract extraction and IPRS lookup
serial_validation = validate_serial_number(
    extracted_serial=textract_serial,
    iprs_serial=data.get("serialNumber")
)

# Add to match results
match_results["serialNumberValidation"] = serial_validation.to_dict()
```

### Gender Validation

```python
# In document_validation/src/app.py
from gender_validator import validate_gender

# After Textract extraction and IPRS lookup
gender_validation = validate_gender(
    extracted_gender=textract_gender,
    iprs_gender=data.get("gender")
)

# Add to match results
match_results["genderValidation"] = gender_validation.to_dict()
```

### Face Matching (Pending ESB Confirmation)

```python
# In face_matching/src/app.py
# Requires confirmation that IPRS returns photo field

iprs_photo = data.get("photo")  # Base64 or URL - TBD
if iprs_photo:
    # Compare with selfie and document photo using Rekognition
    pass
```

---

## Testing IPRS Integration

### Unit Test Mocking

```python
from unittest.mock import Mock, patch

@patch('jubilee_esb_api.JubileeESBAPI')
def test_iprs_lookup(mock_esb):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": {
            "idNumber": "12345678",
            "serialNumber": "217990310",
            "gender": "M",
            # ... other fields
        }
    }
    mock_esb.return_value.iprs.search_generic.return_value = mock_response
    
    # Test your function
```

### E2E Test Data

See `e2e/tests/verification/test_verify_nationalid.py` for real test cases with known ID numbers.

### Note on Async Invocations

For Alien ID and Military ID validation, IPRS calls happen inside an asynchronously invoked Lambda (`InvocationType='Event'`). The orchestrator does not wait for the IPRS response — instead, the DocumentValidationFn writes the final result (including IPRS data) to DynamoDB. Clients poll `get_job_status` to retrieve the result. See `.kiro/steering/lambda-patterns.md` for the async invocation pattern.
