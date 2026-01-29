# IPRS Integration Guide

This guide covers integration patterns for the IPRS (Integrated Population Registration System) API via the Jubilee ESB layer.

---
inclusion: fileMatch
fileMatchPattern: "**/iprs.py,**/government_verification/**,**/document_validation/**"
---

## Overview

IPRS is Kenya's national identity database. The eKYC system queries IPRS to:
1. Verify identity document data against government records
2. Retrieve authoritative personal information (name, DOB, gender)
3. Validate serial numbers to detect replaced/counterfeit IDs
4. (Planned) Retrieve photos for face matching

## ESB Layer Architecture

```
Lambda Function
    └── JubileeESBAPI (jubilee_esb_api.py)
            └── IPRS class (iprs.py)
                    └── JubileeESBUtilities (utilities.py)
                            └── HTTP calls to ESB
```

## Using the IPRS Client

### Import Pattern
```python
from jubilee_esb_api import JubileeESBAPI
from portal import Portal

portal = Portal()
esb_client = JubileeESBAPI(portal)

# Access IPRS methods
response = esb_client.iprs.search_generic(data)
```

### Available Methods

| Method | Endpoint | Use Case |
|--------|----------|----------|
| `search_generic(data)` | `/iprs/searchV2/LIFE_BUSINESS` | National ID lookup |
| `search_passport_number(data)` | `/iprs/searchUsingPassportNumber/LIFE_BUSINESS` | Passport lookup |
| `search_alien_id(data)` | `/iprs/searchUsingAlienId/LIFE_BUSINESS` | Alien ID lookup |
| `search_birth_certificate_number(data)` | `/iprs/searchUsingBirthCertificateNumber/LIFE_BUSINESS` | Birth cert lookup |
| `search_death_certificate_number(data)` | `/iprs/searchUsingDeathCertificateNumber/LIFE_BUSINESS` | Death cert lookup |
| `bulk_iprs_search(data)` | `/iprs/bulk-search/LIFE_BUSINESS` | Batch lookups |
| `ping()` | `/iprs/pingIprs/LIFE_BUSINESS` | Health check |

## National ID Lookup Example

```python
from jubilee_esb_api import JubileeESBAPI
from portal import Portal

portal = Portal()
esb_client = JubileeESBAPI(portal)

# Query IPRS by National ID
response = esb_client.iprs.search_generic({
    "identifier": "ID_NUMBER",
    "value": "12345678"
})

if response.status_code == 200:
    result = response.json()
    if result.get("success") and result.get("data"):
        data = result["data"]
        
        # Available fields for v1.2 features:
        serial_number = data.get("serialNumber")  # For serial validation
        gender = data.get("gender")               # For gender validation
        # photo = data.get("photo")               # For face matching (TBD)
```

## Response Handling Pattern

```python
def handle_iprs_response(response):
    """Standard pattern for handling IPRS responses."""
    
    # Check HTTP status
    if response.status_code >= 400:
        error_msg = extract_error_message(response)
        logger.warning(f"IPRS API error: {error_msg}")
        return None, error_msg
    
    # Parse JSON response
    result = response.json()
    
    # Check success flag
    if result.get("error"):
        return None, result["error"]
    
    if not result.get("success", True):
        return None, "IPRS call unsuccessful"
    
    # Check data presence
    if "data" not in result:
        return None, "Missing data in IPRS response"
    
    return result["data"], None


def extract_error_message(response):
    """Extract error message from IPRS error response."""
    try:
        error_obj = response.json()
        if "errors" in error_obj.get("error", {}):
            return error_obj["error"]["errors"].get("errorMessage", "Unknown error")
        return error_obj.get("message", f"{response.status_code}: API error")
    except:
        return f"{response.status_code}: API error"
```

## Field Extraction for v1.2 Features

### Serial Number Validation
```python
def get_iprs_serial_number(iprs_data: dict) -> tuple[str | None, str | None]:
    """Extract serial number from IPRS response for validation."""
    if not iprs_data:
        return None, "IPRS data unavailable"
    
    serial = iprs_data.get("serialNumber")
    if not serial:
        return None, "IPRS serial number unavailable"
    
    return serial, None
```

### Gender Validation
```python
def get_iprs_gender(iprs_data: dict) -> tuple[str | None, str | None]:
    """Extract gender from IPRS response for validation."""
    if not iprs_data:
        return None, "IPRS data unavailable"
    
    gender = iprs_data.get("gender")
    if not gender:
        return None, "IPRS gender unavailable"
    
    # Normalize: IPRS returns "M" or "F"
    return gender.upper().strip(), None
```

### Face Matching (Pending)
```python
def get_iprs_photo(iprs_data: dict) -> tuple[str | None, str | None]:
    """Extract photo from IPRS response for face matching.
    
    NOTE: Photo field availability pending ESB team confirmation.
    """
    if not iprs_data:
        return None, "IPRS data unavailable"
    
    photo = iprs_data.get("photo")
    if not photo:
        return None, "IPRS photo unavailable"
    
    # TODO: Determine if photo is Base64 or URL
    return photo, None
```

## Error Handling Best Practices

### Non-Blocking Validation
```python
def validate_with_iprs(id_number: str, extracted_data: dict) -> dict:
    """Validate document data against IPRS - non-blocking pattern."""
    
    validation_result = {
        "status": "INCONCLUSIVE",
        "reason": None,
        "iprs_data": None
    }
    
    try:
        response = esb_client.iprs.search_generic({
            "identifier": "ID_NUMBER",
            "value": id_number
        })
        
        iprs_data, error = handle_iprs_response(response)
        
        if error:
            validation_result["reason"] = f"IPRS error: {error}"
            return validation_result
        
        validation_result["iprs_data"] = iprs_data
        # Perform validation...
        
    except Exception as e:
        logger.error(f"IPRS validation failed: {e}")
        validation_result["reason"] = f"IPRS exception: {str(e)}"
    
    return validation_result
```

### Graceful Degradation
- IPRS failures should NOT block the overall KYC process
- Return `INCONCLUSIVE` status, not errors
- Log issues for monitoring
- Continue with other validations

## Caching

IPRS responses are cached for 7 days in DynamoDB. The caching is handled by the ESB layer automatically.

## Timeouts

- Default timeout: 240 seconds (4 minutes)
- No automatic retries (KYC operations are not idempotent)

## Logging

Use AWS Lambda Powertools for structured logging:

```python
from aws_lambda_powertools import Logger

logger = Logger()

@logger.inject_lambda_context
def handler(event, context):
    logger.info("IPRS lookup", extra={
        "id_number": id_number,
        "operation": "search_generic"
    })
```

## Metrics

Emit CloudWatch metrics for monitoring:

```python
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

metrics = Metrics()

@metrics.log_metrics
def handler(event, context):
    # Track IPRS call outcomes
    metrics.add_metric(
        name="IPRSCallSuccess",
        unit=MetricUnit.Count,
        value=1
    )
```

## Testing

### Mocking IPRS Responses
```python
from unittest.mock import Mock, patch

def test_serial_number_validation():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "data": {
            "serialNumber": "217990310",
            "gender": "M"
        }
    }
    
    with patch.object(esb_client.iprs, 'search_generic', return_value=mock_response):
        result = validate_serial_number(...)
```

## Known Issues

1. **Date Format Inconsistency**: IPRS returns dates in various formats (US, ISO, European). Always normalize before comparison.

2. **Photo Field**: Availability pending ESB team confirmation. Do not assume this field exists.

3. **Gender Values**: IPRS returns "M" or "F". Document extraction may return "Male"/"Female". Normalize before comparison.

## Related Documentation

- See `esb-response-schemas.md` for complete response schemas
- See `testing-guide.md` for property-based testing patterns
