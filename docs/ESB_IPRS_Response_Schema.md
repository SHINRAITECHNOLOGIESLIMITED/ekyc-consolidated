# ESB IPRS Response Schema Documentation

**Version**: 1.0.0  
**Last Updated**: January 2026  
**Status**: Confirmed from production code analysis

---

## Overview

This document defines the confirmed IPRS API response schema based on analysis of the production codebase. The schema is used by the Jubilee eKYC platform for government verification.

---

## National ID Search Response

**Endpoint**: `POST /iprs/searchV2/LIFE_BUSINESS`

### Request
```json
{
  "identifier": "ID_NUMBER",
  "value": "12345678"
}
```

### Response Structure
```json
{
  "success": true,
  "error": null,
  "data": {
    "idNumber": "12345678",
    "serialNumber": "217990310",
    "firstName": "STEPHEN",
    "otherName": "BIKO",
    "surname": "NYAMAI",
    "gender": "M",
    "dateOfBirth": "2/19/1984",
    "dateOfIssue": "4/1/2003",
    "placeOfBirth": "NAIROBI",
    "citizenship": "Kenyan",
    "photo": "..."
  }
}
```

---

## Field Definitions

### Confirmed Fields (Used in Production)

| Field | Type | Required | Source | Description |
|-------|------|----------|--------|-------------|
| `idNumber` | string | Yes | `government_verification/app.py:215` | National ID number |
| `serialNumber` | string | Yes | `government_verification/app.py:213` | ID card serial number |
| `firstName` | string | Yes | `government_verification/app.py:225` | First name |
| `otherName` | string | No | `government_verification/app.py:226` | Middle name(s) |
| `surname` | string | Yes | `government_verification/app.py:227` | Family name |
| `gender` | string | Yes | `government_verification/app.py:219` | Gender (M/F) |
| `dateOfBirth` | string | Yes | `government_verification/app.py:217` | Date of birth |
| `dateOfIssue` | string | Yes | `government_verification/app.py:218` | ID issue date |
| `placeOfBirth` | string | Yes | `government_verification/app.py:220` | District of birth |

### Pending Confirmation

| Field | Type | Status | Notes |
|-------|------|--------|-------|
| `photo` | string | ⚠️ Pending | Base64 or URL - needs ESB team confirmation |
| `citizenship` | string | Unknown | May be available |

---

## v1.2 Feature Field Requirements

### Serial Number Validation
- **Required Field**: `serialNumber`
- **Status**: ✅ Confirmed available
- **Evidence**: Used in `government_verification/app.py` line 213

### Gender Validation
- **Required Field**: `gender`
- **Status**: ✅ Confirmed available
- **Evidence**: Used in `government_verification/app.py` line 219

### Face Matching
- **Required Field**: `photo`
- **Status**: ⚠️ Pending ESB confirmation
- **Action**: ESB team to confirm within 48 hours

---

## Date Format

IPRS returns dates in **American format** (M/D/YYYY):
- `2/19/1984` = February 19, 1984
- `12/24/2009` = December 24, 2009

The codebase handles multiple date formats for comparison:
```python
date_formats = [
    '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d',
    '%m/%d/%Y', '%Y/%d/%m',
    '%d %b %Y', '%d %B %Y',
    '%Y-%b-%d', '%Y-%B-%d',
    '%d- %m- %Y',
    '%m-%d-%Y',
]
```

---

## Error Response Structure

### API Error (HTTP 4xx/5xx)
```json
{
  "error": {
    "errors": {
      "errorMessage": "Detailed error message"
    }
  },
  "message": "Error summary"
}
```

### Business Logic Error
```json
{
  "success": false,
  "error": "Error description",
  "data": null
}
```

---

## Passport Search Response

**Endpoint**: `POST /iprs/searchUsingPassportNumber/LIFE_BUSINESS`

### Request
```json
{
  "identifier": "PASSPORT",
  "value": "A1234567",
  "idNumber": "12345678"
}
```

### Response Structure
```json
{
  "success": true,
  "error": null,
  "data": {
    "passportNumber": "A1234567",
    "firstName": "STEPHEN",
    "otherName": "BIKO",
    "surname": "NYAMAI",
    "gender": "M",
    "dateOfBirth": "2/19/1984",
    "dateOfIssue": "1/15/2020",
    "dateOfExpiry": "1/14/2030"
  }
}
```

---

## Test Data Reference

From E2E tests (`e2e/tests/verification/test_verify_nationalid.py`):

| ID Number | Serial Number | Name | Gender | DOB |
|-----------|---------------|------|--------|-----|
| 23667272 | 217934147 | JANE WAIRIMU MAINA | F | - |
| 32140017 | 702945559 | EFFIE NJOKI NYAMBURA | F | 12/19/1994 |
| 36296352 | 244772451 | JOEL MUUO | M | 8/30/1998 |
| 23224868 | 229769449 | STEPHEN BIKO NYAMAI | M | 2/19/1984 |

---

## Schema Validation Code

```python
def validate_iprs_response_schema(response: dict) -> tuple[bool, list[str]]:
    """
    Validate IPRS response conforms to expected schema.
    
    Returns:
        (is_valid, missing_fields)
    """
    required_fields = [
        'idNumber',
        'serialNumber', 
        'firstName',
        'surname',
        'gender',
        'dateOfBirth',
        'dateOfIssue',
        'placeOfBirth'
    ]
    
    if not response.get('success'):
        return False, ['success=false']
    
    data = response.get('data', {})
    if not data:
        return False, ['data missing']
    
    missing = [f for f in required_fields if f not in data or data[f] is None]
    
    return len(missing) == 0, missing
```

---

## Action Items

- [ ] **ESB Team**: Confirm `photo` field availability and format (Base64 vs URL)
- [ ] **ESB Team**: Provide sample response with all fields populated
- [ ] **Dev Team**: Store schema version in SSM Parameter Store
- [ ] **Dev Team**: Implement schema validation with CloudWatch alerting
