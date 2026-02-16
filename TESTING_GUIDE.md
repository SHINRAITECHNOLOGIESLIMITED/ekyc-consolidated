# Jubilee eKYC API Testing Guide

## Environment Details

**API Base URL (Stage - No Auth Required):**
```
https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage
```

**AWS Account:** 686255958278  
**Region:** eu-west-1

---

## Quick Start

All Stage endpoints accept any Bearer token for testing:

```bash
export API_URL="https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage"
export AUTH="Authorization: Bearer test-token"
```

---

## 1. Document Validation Tests

### 1.1 Validate National ID

Validates a National ID document using Textract OCR and compares against IPRS.

**v1.2 Features:** Includes Serial Number Validation and Gender Validation.

```bash
curl -X POST "$API_URL/document/nationalid" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/TIM.jpg",
    "idNumber": "26465570"
  }' | jq
```

**Expected Response:**
```json
{
  "message": "Validation successfull",
  "s3Path": "NationalID/26465570.pdf",
  "results": {
    "keywords_checks": [
      {"check": "Contains the words \"Jamhuri ya Kenya\"", "result": true},
      {"check": "Contains the words \"Republic of Kenya\"", "result": true}
    ],
    "matchResults": {
      "idNumber": {
        "status": "Matched",
        "details": {"expected": "26465570", "actual": "26465570", "ocr_confidence": 95.25, "match_score": 100.0}
      },
      "serialNumberValidation": {
        "status": "MATCH",
        "extractedSerialNumber": "702124691",
        "iprsSerialNumber": "702124691",
        "normalizedComparison": true
      },
      "genderValidation": {
        "status": "MATCH",
        "extractedGender": "M",
        "iprsGender": "M",
        "normalizedComparison": true
      }
    }
  }
}
```

### 1.2 Validate Passport

```bash
curl -X POST "$API_URL/document/passport" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/passport.pdf",
    "passportNumber": "AB1234567"
  }' | jq
```

### 1.3 Validate KRA PIN Certificate

```bash
curl -X POST "$API_URL/document/krapincertificate" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/kra_pin.pdf",
    "pinNumber": "A001234567X"
  }' | jq
```

---

## 2. Government Verification Tests

### 2.1 Verify National ID against IPRS

```bash
curl -X POST "$API_URL/government/nationalid" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "idNumber": "26465570"
  }' | jq
```

**Expected Response:**
```json
{
  "message": "Verification successful",
  "results": {
    "matchResults": {
      "firstName": {"status": "Matched", "details": {"expected": "TIMOTHY", "actual": "TIMOTHY"}},
      "lastName": {"status": "Matched", "details": {"expected": "...", "actual": "..."}},
      "gender": {"status": "Matched", "details": {"expected": "M", "actual": "M"}},
      "dateOfBirth": {"status": "Matched", "details": {...}}
    }
  }
}
```

### 2.2 Verify Passport against IPRS

```bash
curl -X POST "$API_URL/government/passport" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "passportNumber": "AB1234567",
    "idNumber": "26465570"
  }' | jq
```

### 2.3 Verify KRA PIN

```bash
curl -X POST "$API_URL/government/kra" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "pinNumber": "A001234567X",
    "idNumber": "26465570"
  }' | jq
```

---

## 3. Background Check Tests

### 3.1 LexisNexis Background Check

```bash
curl -X POST "$API_URL/backgroundcheck" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "firstName": "TIMOTHY",
    "lastName": "MWANGI",
    "middleName": "",
    "gender": "M",
    "dob": "1990-01-15",
    "nationalIdentificationNumber": "26465570",
    "countryCode": "KE"
  }' | jq
```

---

## 4. Face Liveness Tests

### 4.1 Create Liveness Session

```bash
curl -X POST "$API_URL/faceliveness" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "action": "create_session"
  }' | jq
```

**Response:**
```json
{
  "sessionId": "abc123-def456-...",
  "message": "Liveness session created"
}
```

### 4.2 Get Liveness Results

```bash
curl -X POST "$API_URL/faceliveness" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "action": "get_results",
    "sessionId": "abc123-def456-..."
  }' | jq
```

---

## 5. Unified KYC Endpoint Tests

The `/kyc` endpoint supports all actions via a single endpoint.

### 5.1 Validate National ID (via /kyc)

```bash
curl -X POST "$API_URL/kyc" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "action": "validate_nationalid",
    "data": {
      "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/TIM.jpg",
      "idNumber": "26465570"
    }
  }' | jq
```

### 5.2 Verify National ID (via /kyc)

```bash
curl -X POST "$API_URL/kyc" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "action": "verify_nationalid",
    "data": {
      "idNumber": "26465570"
    }
  }' | jq
```

### 5.3 Available Actions

| Action | Description |
|--------|-------------|
| `validate_nationalid` | Validate National ID document |
| `validate_passport` | Validate Passport document |
| `validate_krapincertificate` | Validate KRA PIN certificate |
| `validate_cr12` | Validate Company CR12 |
| `verify_nationalid` | Verify ID against IPRS |
| `verify_passport` | Verify Passport against IPRS |
| `verify_kra` | Verify KRA PIN |
| `background_check` | LexisNexis screening |
| `create_liveness_session` | Start face liveness |
| `get_liveness_results` | Get liveness results |

---

## 6. Test IDs (Known Working)

| ID Number | Serial Number | Name | Gender |
|-----------|---------------|------|--------|
| 26465570 | 702124691 | TIMOTHY | M |
| 23667272 | 217934147 | JANE WAIRIMU MAINA | F |
| 32140017 | 702945559 | EFFIE NJOKI NYAMBURA | F |
| 36296352 | 244772451 | JOEL MUUO | M |
| 23224868 | 229769449 | STEPHEN BIKO NYAMAI | M |

---

## 7. v1.2 Feature Tests

### 7.1 Serial Number Validation

Tests that the serial number on the ID matches IPRS records.

**MATCH Case:**
```bash
# Use TIM.jpg which has matching serial number
curl -X POST "$API_URL/document/nationalid" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/TIM.jpg",
    "idNumber": "26465570"
  }' | jq '.results.matchResults.serialNumberValidation'
```

**Expected:**
```json
{
  "status": "MATCH",
  "extractedSerialNumber": "702124691",
  "iprsSerialNumber": "702124691",
  "normalizedComparison": true,
  "reason": null
}
```

### 7.2 Gender Validation

Tests that gender on the ID matches IPRS records.

```bash
curl -X POST "$API_URL/document/nationalid" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/TIM.jpg",
    "idNumber": "26465570"
  }' | jq '.results.matchResults.genderValidation'
```

**Expected:**
```json
{
  "status": "MATCH",
  "extractedGender": "M",
  "iprsGender": "M",
  "normalizedComparison": true,
  "reason": null
}
```

---

## 8. Error Handling Tests

### 8.1 Missing Required Field

```bash
curl -X POST "$API_URL/document/nationalid" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "uploadedDocumentUrl": "s3://bucket/doc.jpg"
  }' | jq
```

**Expected:** 400 Bad Request with validation error

### 8.2 Invalid Document URL

```bash
curl -X POST "$API_URL/document/nationalid" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "uploadedDocumentUrl": "invalid-url",
    "idNumber": "12345678"
  }' | jq
```

### 8.3 Non-existent ID Number

```bash
curl -X POST "$API_URL/government/nationalid" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "idNumber": "99999999"
  }' | jq
```

---

## 9. Batch Testing Script

Save as `test_all.sh`:

```bash
#!/bin/bash

API_URL="https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage"
AUTH="Authorization: Bearer test-token"

echo "=== Testing Document Validation ==="
curl -s -X POST "$API_URL/document/nationalid" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/TIM.jpg",
    "idNumber": "26465570"
  }' | jq '.message, .results.matchResults.serialNumberValidation.status, .results.matchResults.genderValidation.status'

echo ""
echo "=== Testing Government Verification ==="
curl -s -X POST "$API_URL/government/nationalid" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{"idNumber": "26465570"}' | jq '.message'

echo ""
echo "=== Testing Background Check ==="
curl -s -X POST "$API_URL/backgroundcheck" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "firstName": "TIMOTHY",
    "lastName": "TEST",
    "gender": "M",
    "dob": "1990-01-15",
    "nationalIdentificationNumber": "26465570",
    "countryCode": "KE"
  }' | jq '.message'

echo ""
echo "=== All tests complete ==="
```

Run with:
```bash
chmod +x test_all.sh
./test_all.sh
```

---

## 10. Upload Test Document to S3

Before testing document validation, upload a test document:

```bash
# Upload a test image
aws s3 cp /path/to/your/id.jpg \
  s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/test_id.jpg \
  --profile pasha-eu

# Then use in validation
curl -X POST "$API_URL/document/nationalid" \
  -H "Content-Type: application/json" \
  -H "$AUTH" \
  -d '{
    "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/test_id.jpg",
    "idNumber": "YOUR_ID_NUMBER"
  }' | jq
```

---

## 11. CloudWatch Logs

View Lambda logs for debugging:

```bash
# Document Validation logs
aws logs tail /aws/lambda/jubilee-ekyc-dev-DocumentValidationFn-F5iNea5fWItr \
  --follow --profile pasha-eu --region eu-west-1

# Government Verification logs
aws logs tail /aws/lambda/jubilee-ekyc-dev-GovernmentVerificationFn-w15xzu1elQpk \
  --follow --profile pasha-eu --region eu-west-1
```

---

## 12. Response Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid/missing token |
| 404 | Not Found - Invalid endpoint |
| 500 | Internal Server Error |

---

## 13. Validation Status Values

### Serial Number Validation
- `MATCH` - Serial numbers match (document is current)
- `MISMATCH` - Serial numbers differ (outdated/fraudulent)
- `INCONCLUSIVE` - Unable to compare (missing data)

### Gender Validation
- `MATCH` - Gender matches IPRS record
- `MISMATCH` - Gender doesn't match
- `INCONCLUSIVE` - Unable to compare (missing data)
