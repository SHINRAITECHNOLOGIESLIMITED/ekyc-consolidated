---
inclusion: fileMatch
fileMatchPattern: "**/jubilee_esb_api_layer/**/*.py,**/government_verification/**/*.py,**/document_validation/**/*.py"
---

# ESB API Schema Documentation

This document defines the expected response schemas for Jubilee ESB API integrations. Schema versioning protects against unexpected payload changes.

## Schema Version

**Current Version**: `1.0.0`
**Last Updated**: January 2026
**SSM Parameter**: `/jubilee-ekyc/esb/schema-version`

---

## IPRS API Response Schema

### National ID Search (`/iprs/searchV2/LIFE_BUSINESS`)

**Request**:
```json
{
  "identifier": "ID_NUMBER",
  "value": "12345678"
}
```

**Response Schema**:
```json
{
  "success": true,
  "error": null,
  "data": {
    "idNumber": "string",
    "serialNumber": "string",
    "firstName": "string",
    "otherName": "string | null",
    "surname": "string",
    "gender": "string",
    "dateOfBirth": "string",
    "dateOfIssue": "string",
    "placeOfBirth": "string",
    "citizenship": "string | null",
    "photo": "string | null"
  }
}
```

### Field Definitions

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `idNumber` | string | Yes | National ID number | "12345678" |
| `serialNumber` | string | Yes | ID card serial number (changes on replacement) | "217990310" |
| `firstName` | string | Yes | First name | "STEPHEN" |
| `otherName` | string | No | Middle name(s) | "BIKO" |
| `surname` | string | Yes | Family name | "NYAMAI" |
| `gender` | string | Yes | Gender (M/F or Male/Female) | "M" |
| `dateOfBirth` | string | Yes | Date of birth (M/D/YYYY format) | "2/19/1984" |
| `dateOfIssue` | string | Yes | ID issue date | "4/1/2003" |
| `placeOfBirth` | string | Yes | District/place of birth | "NAIROBI" |
| `citizenship` | string | No | Citizenship status | "Kenyan" |
| `photo` | string | No | Base64 encoded photo or URL | ⚠️ Needs ESB confirmation |

### Critical Fields for v1.2 Features

| Feature | Required Field | Status |
|---------|---------------|--------|
| Serial Number Validation | `serialNumber` | ✅ Confirmed available |
| Gender Validation | `gender` | ✅ Confirmed available |
| Face Matching | `photo` | ⚠️ Pending ESB confirmation |

---

## Passport Search (`/iprs/searchUsingPassportNumber/LIFE_BUSINESS`)

**Request**:
```json
{
  "identifier": "PASSPORT",
  "value": "A1234567",
  "idNumber": "12345678"
}
```

**Response Schema**:
```json
{
  "success": true,
  "error": null,
  "data": {
    "passportNumber": "string",
    "firstName": "string",
    "otherName": "string | null",
    "surname": "string",
    "gender": "string",
    "dateOfBirth": "string",
    "dateOfIssue": "string",
    "dateOfExpiry": "string"
  }
}
```

---

## KRA API Response Schema

### Tax PIN Validation (`/api/v1/kra/validate-id`)

**Request** (GET with query params):
```
?typeOfTaxpayer=KE&taxpayerID=A123456789B
```

**Response Schema**:
```json
{
  "success": true,
  "error": null,
  "data": {
    "responseCode": "string",
    "pin": "string",
    "taxpayerName": "string"
  }
}
```

### Response Codes

| Code | Meaning |
|------|---------|
| `30000` | Valid ID - success |
| `30001` | Invalid User ID or Password |
| `30002` | Invalid ID |
| `30003` | iPage not Done |

---

## LexisNexis API Response Schema

### Background Check (`/lexis/search/LIFE_BUSINESS`)

**Request**:
```json
{
  "firstName": "JOHN",
  "middleName": "DAVID",
  "lastName": "SMITH",
  "gender": "Male",
  "dob": "1990-05-15",
  "nationalIdentificationNumber": "12345678",
  "countryCode": "KEN",
  "entityType": "Individual",
  "sourceName": "Portals"
}
```

**Response**: Varies based on screening results. See LexisNexis documentation.

---

## Schema Validation Rules

When implementing ESB integrations:

1. **Always check `success` field** before accessing `data`
2. **Handle missing optional fields** gracefully (use `.get()` with defaults)
3. **Log schema mismatches** at WARNING level
4. **Return INCONCLUSIVE** status when expected fields are missing
5. **Emit CloudWatch metric** on schema validation failures

### Example Schema Validation

```python
def validate_iprs_schema(response: dict) -> bool:
    """Validate IPRS response conforms to expected schema."""
    required_fields = ['idNumber', 'serialNumber', 'firstName', 'surname', 'gender']
    
    if not response.get('success'):
        return False
    
    data = response.get('data', {})
    missing = [f for f in required_fields if f not in data]
    
    if missing:
        logger.warning(f"IPRS schema mismatch - missing fields: {missing}")
        return False
    
    return True
```

---

## Date Format Notes

IPRS returns dates in **American format** (M/D/YYYY), not D/M/YYYY:
- `2/19/1984` = February 19, 1984
- `12/24/2009` = December 24, 2009

Always normalize dates before comparison using multiple format parsers.

---

## Action Items

- [ ] **ESB Team**: Confirm `photo` field availability in IPRS response (48-hour deadline)
- [ ] **ESB Team**: Provide sample IPRS response with all fields populated
- [ ] **Dev Team**: Update schema version in SSM when ESB confirms photo field
