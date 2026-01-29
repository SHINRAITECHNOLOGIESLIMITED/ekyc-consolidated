# ESB Response Schemas

This document defines the expected response schemas from the Jubilee ESB (Enterprise Service Bus) APIs. These schemas are critical for the eKYC v1.2 features and should be version-controlled.

---
inclusion: fileMatch
fileMatchPattern: "**/iprs.py,**/kra.py,**/lexisnexis.py,**/government_verification/**,**/document_validation/**"
---

## Schema Version

**Current Version**: 1.0.0  
**Last Updated**: 2026-01-29  
**ESB Base URL**: `https://jubipay.jubileeinsurance.com`  
**Business Unit**: `LIFE_BUSINESS`

## IPRS National ID Response Schema

**Endpoint**: `POST /iprs/searchV2/LIFE_BUSINESS`

### Request
```json
{
  "identifier": "ID_NUMBER",
  "value": "12345678"
}
```

### Response
```json
{
  "success": true,
  "error": null,
  "data": {
    "idNumber": "12345678",
    "serialNumber": "217990310",
    "firstName": "JOHN",
    "otherName": "DAVID",
    "surname": "SMITH",
    "gender": "M",
    "dateOfBirth": "1990-05-15",
    "dateOfIssue": "2020-03-15",
    "placeOfBirth": "NAIROBI",
    "citizenship": "KENYAN",
    "photo": null
  }
}
```

### Field Definitions

| Field | Type | Required | Description | Used By |
|-------|------|----------|-------------|---------|
| `idNumber` | string | Yes | National ID number | All validations |
| `serialNumber` | string | Yes | ID card serial number (changes on replacement) | Serial Number Validation |
| `firstName` | string | Yes | First name | Name matching |
| `otherName` | string | No | Middle name(s) | Name matching |
| `surname` | string | Yes | Last name / family name | Name matching |
| `gender` | string | Yes | Gender code: "M" or "F" | Gender Validation |
| `dateOfBirth` | string | Yes | Date of birth (format varies) | DOB validation |
| `dateOfIssue` | string | Yes | ID issue date | Document validation |
| `placeOfBirth` | string | Yes | District/place of birth | Document validation |
| `citizenship` | string | No | Citizenship status | Informational |
| `photo` | string | No | Base64 photo or URL (TBD) | Face Matching (pending confirmation) |

### Critical Fields for v1.2 Features

#### Serial Number Validation
- **Field**: `data.serialNumber`
- **Status**: ✅ Confirmed available
- **Format**: Numeric string, 9 digits typical
- **Notes**: Changes when ID is replaced - used to detect outdated/counterfeit IDs

#### Gender Validation  
- **Field**: `data.gender`
- **Status**: ✅ Confirmed available
- **Format**: Single character - "M" (Male) or "F" (Female)
- **Notes**: Authoritative source per Sharon Mukonyo (NOT LexisNexis)

#### Face Matching
- **Field**: `data.photo`
- **Status**: ⚠️ Pending ESB team confirmation
- **Format**: TBD (Base64 string or URL)
- **Action Required**: ESB team must confirm within 48 hours of sprint start

## IPRS Passport Response Schema

**Endpoint**: `POST /iprs/searchUsingPassportNumber/LIFE_BUSINESS`

### Request
```json
{
  "identifier": "PASSPORT",
  "value": "A1234567",
  "idNumber": "12345678"
}
```

### Response
```json
{
  "success": true,
  "error": null,
  "data": {
    "passportNumber": "A1234567",
    "firstName": "JOHN",
    "otherName": "DAVID", 
    "surname": "SMITH",
    "gender": "M",
    "dateOfBirth": "1990-05-15",
    "dateOfIssue": "2020-01-15",
    "dateOfExpiry": "2030-01-14",
    "placeOfIssue": "NAIROBI"
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `passportNumber` | string | Yes | Passport number |
| `firstName` | string | Yes | First name |
| `otherName` | string | No | Middle name(s) |
| `surname` | string | Yes | Last name |
| `gender` | string | Yes | Gender code: "M" or "F" |
| `dateOfBirth` | string | Yes | Date of birth |
| `dateOfIssue` | string | Yes | Passport issue date |
| `dateOfExpiry` | string | Yes | Passport expiry date |
| `placeOfIssue` | string | No | Place of issue |

## KRA Tax PIN Response Schema

**Endpoint**: `GET /api/v1/kra/validate-id`

### Request Parameters
- `typeOfTaxpayer`: KE | NKE | NKENR | COMP
- `taxpayerID`: KRA PIN number

### Response
```json
{
  "success": true,
  "error": null,
  "data": {
    "responseCode": "30000",
    "pin": "A123456789B",
    "taxpayerName": "JOHN DAVID SMITH"
  }
}
```

### Response Codes

| Code | Meaning |
|------|---------|
| 30000 | Valid ID - success |
| 30001 | Invalid User ID or Password |
| 30002 | Invalid ID |
| 30003 | iPage not Done |

## LexisNexis Background Check Response Schema

**Endpoint**: `POST /lexis/search/LIFE_BUSINESS`

### Request
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

### Response
```json
{
  "success": true,
  "error": null,
  "data": {
    "matchStatus": "NO_MATCH",
    "riskScore": 0,
    "sanctions": [],
    "pep": false,
    "adverseMedia": []
  }
}
```

> **Note**: Gender validation uses IPRS, NOT LexisNexis, due to historical data quality issues with LexisNexis gender data.

## Error Response Schema

All ESB endpoints return errors in this format:

```json
{
  "success": false,
  "error": {
    "errors": {
      "errorMessage": "Detailed error message"
    }
  },
  "data": null
}
```

## Date Format Notes

IPRS returns dates in various formats. The system handles:
- `YYYY-MM-DD` (ISO format)
- `M/D/YYYY` (US format)
- `DD-MM-YYYY` (European format)
- `DD MMM YYYY` (e.g., "18 May 1987")

Always normalize dates before comparison.

## Schema Versioning Strategy

1. **SSM Parameter**: Store schema version in `/ekyc/esb/schema-version`
2. **Validation**: Validate required fields exist before processing
3. **Alerting**: Emit CloudWatch metric on schema mismatch
4. **Graceful Degradation**: Return INCONCLUSIVE on schema issues, don't fail

## Action Items

- [ ] **ESB Team**: Confirm `photo` field availability in IPRS response (48-hour deadline)
- [ ] **ESB Team**: Provide sample IPRS response with all fields populated
- [ ] **Dev Team**: Implement schema validation with version checking
- [ ] **Dev Team**: Create CloudWatch alarm for schema mismatches
