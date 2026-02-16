# Jubilee eKYC API Testing Guide

Complete guide for testing document validation, government verification, and face matching via the unified `/kyc` endpoint.

## Environment

```
Base URL:  https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage
Auth:      Bearer dummy-token  (Stage auto-approves any token)
Method:    POST
Endpoint:  /kyc
```

All requests use the same envelope:

```json
{
  "action": "<action_name>",
  "data": { ... }
}
```

## Headers (all requests)

```bash
-H "Content-Type: application/json"
-H "Authorization: Bearer dummy-token"
```

---

## S3 Buckets

| Bucket | Purpose |
|--------|---------|
| `maisha-verification-dev-686255958278` | Upload test documents here (uploaded_kyc_docs/) |
| `kyc-raw-documents-jubilee-ekyc-dev-686255958278` | Validated documents stored here after processing |
| `faceliveness-captures-jubilee-ekyc-dev-686255958278` | Face liveness reference images |

Upload a test document before calling validation:

```bash
aws s3 cp /path/to/document.jpg \
  s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/document.jpg \
  --profile pasha-eu
```

---

## 1. National ID

### Step 1: Document Validation

Action: `validate_nationalid`

Runs Textract OCR on the document, compares extracted fields against provided data, and cross-validates serial number + gender against IPRS.

```bash
curl -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "validate_nationalid",
    "data": {
      "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/my_id.jpg",
      "idNumber": "26465570",
      "gender": "Male",
      "fullNames": "TIMOTHY MUGO",
      "serialNumber": "702124691",
      "dateOfBirth": "1990-01-15",
      "dateOfIssue": "2020-06-01",
      "districtOfBirth": "NAIROBI",
      "placeOfIssue": "NAIROBI"
    }
  }'
```

**Required fields:** `uploadedDocumentUrl`, `idNumber`

**Optional fields:** `serialNumber`, `fullNames`, `gender`, `dateOfBirth`, `dateOfIssue`, `districtOfBirth`, `placeOfIssue`

Providing optional fields enables Textract match comparison (Matched/Not Matched). If omitted, those fields show "Not provided".

**Response:**

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
        "details": {"expected": "26465570", "actual": "26465570", "confidence": 95.25, "editdistance": 0}
      },
      "serialNumber": {"status": "Matched", "details": {...}},
      "fullNames": {"status": "Matched", "details": {...}},
      "gender": {"status": "Matched", "details": {...}},
      "dateOfBirth": {"status": "Matched", "details": {...}},
      "dateOfIssue": {"status": "Not provided", "details": null},
      "districtOfBirth": {"status": "Not Found", "details": null},
      "placeOfIssue": {"status": "Not Found", "details": null},
      "serialNumberValidation": {
        "status": "MATCH",
        "extractedSerialNumber": "702124691",
        "iprsSerialNumber": "702124691",
        "normalizedComparison": true,
        "reason": null
      },
      "genderValidation": {
        "status": "MATCH",
        "extractedGender": "M",
        "iprsGender": "M",
        "normalizedComparison": true,
        "reason": null
      }
    }
  }
}
```

**Key fields in response:**
- `matchResults.<field>.status` — "Matched", "Not Matched", "Not provided", or "Not Found"
- `serialNumberValidation.status` — "MATCH", "MISMATCH", or "INCONCLUSIVE" (v1.2 IPRS cross-validation)
- `genderValidation.status` — "MATCH", "MISMATCH", or "INCONCLUSIVE" (v1.2 IPRS cross-validation)
- `s3Path` — Document stored in raw docs bucket (used for face matching)

### Step 2: Government Verification (IPRS)

Action: `government_verify_nationalid`

Verifies the person's identity against IPRS (Kenya's Integrated Population Registration System).

```bash
curl -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "government_verify_nationalid",
    "data": {
      "personalData": {
        "name": "TIMOTHY",
        "idNumber": "26465570"
      }
    }
  }'
```

**Required fields:** `personalData.name`, `personalData.idNumber`

Save the full response — it contains the IPRS photo (Base64) needed for 3-way face matching.

### Step 3: Face Matching

Action: `face_match`

Compares liveness selfie against document photo and IPRS photo (3-way comparison).

**Prerequisites:**
1. Liveness reference image must exist at `{sessionId}/reference_image.jpg` in the liveness bucket
2. Document image must be JPEG/PNG in the raw docs bucket (Rekognition cannot read PDFs)
3. IPRS verification response from Step 2 (for 3-way match; without it you get PARTIAL_MATCH)

Upload liveness image:
```bash
aws s3 cp /path/to/selfie.jpg \
  s3://faceliveness-captures-jubilee-ekyc-dev-686255958278/test-session-123/reference_image.jpg \
  --profile pasha-eu
```

Upload document as JPEG (if original was PDF):
```bash
aws s3 cp /path/to/id_photo.jpeg \
  s3://kyc-raw-documents-jubilee-ekyc-dev-686255958278/NationalID/26465570.jpeg \
  --profile pasha-eu
```

```bash
curl -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "face_match",
    "data": {
      "sessionId": "test-session-123",
      "documentType": "national_id",
      "documentS3Path": "NationalID/26465570.jpeg",
      "idNumber": "26465570",
      "iprsVerificationResponse": <FULL_RESPONSE_FROM_STEP_2>
    }
  }'
```

**Required fields:** `sessionId`, `documentType`, `documentS3Path`, `idNumber`

**Optional fields:** `iprsVerificationResponse` (enables 3-way match)

**documentType values:** `national_id`, `alien_id`, `passport`, `military_id`

**Response:**

```json
{
  "overall_decision": "AUTO_APPROVED",
  "comparisons": {
    "liveness_vs_document": {"similarity": 99.99, "matched": true},
    "liveness_vs_iprs": {"similarity": 98.50, "matched": true},
    "document_vs_iprs": {"similarity": 97.20, "matched": true}
  },
  "lowest_score": 97.20,
  "iprs_photo_available": true,
  "document_type": "national_id",
  "thresholds": {"auto_approve": 70.0, "manual_review": 50.0},
  "requires_manual_review": false
}
```

**Decision bands:**

| Lowest Score | Decision | Manual Review |
|-------------|----------|---------------|
| ≥ 70% | AUTO_APPROVED | No |
| 50–69% | MANUAL_REVIEW | Yes |
| < 50% | AUTO_REJECTED | No |
| No IPRS photo | PARTIAL_MATCH | Yes |

---

## 2. Passport

### Step 1: Document Validation

Action: `validate_passport`

Uses Textract queries for reliable passport field extraction. Cross-validates gender against IPRS using the passport-specific endpoint.

```bash
curl -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "validate_passport",
    "data": {
      "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/passport.jpg",
      "passportNumber": "BK080411",
      "personalNumber": "27681984",
      "surname": "MAINA",
      "givenNames": "JANE WAIRIMU",
      "gender": "Female",
      "dateOfBirth": "1990-05-20",
      "placeOfBirth": "NAIROBI",
      "dateOfIssue": "2020-01-15",
      "dateOfExpiry": "2030-01-14",
      "nationality": "KENYAN",
      "countryCode": "KEN",
      "issuingAuthority": "DEPARTMENT OF IMMIGRATION"
    }
  }'
```

**Required fields:** `uploadedDocumentUrl`, `passportNumber`

**Optional fields:** `personalNumber`, `surname`, `givenNames`, `gender`, `dateOfBirth`, `placeOfBirth`, `dateOfIssue`, `dateOfExpiry`, `nationality`, `countryCode`, `issuingAuthority`, `documentType`

**Notes:**
- `personalNumber` is the national ID number printed on the passport. Providing it enables IPRS gender validation.
- Gender validation uses the passport-specific IPRS endpoint (`/iprs/searchUsingPassportNumber`), not the national ID endpoint.
- Response includes `extractedData` showing raw Textract output and `extractionMethod` ("queries" or "forms").

**Response includes:**

```json
{
  "message": "Validation successful",
  "s3Path": "Passport/BK080411.pdf",
  "results": {
    "keywords_checks": [
      {"check": "Contains the words \"Jamhuri ya Kenya\"", "result": true},
      {"check": "Contains the words \"Republic of Kenya\"", "result": true},
      {"check": "Contains the words \"Republique de Kenya\"", "result": true},
      {"check": "Contains the word \"PASSPORT\"", "result": true}
    ],
    "matchResults": {
      "passportNumber": {"status": "Matched", "details": {...}},
      "surname": {"status": "Matched", "details": {...}},
      "givenNames": {"status": "Matched", "details": {...}},
      "gender": {"status": "Matched", "details": {...}},
      "genderValidation": {
        "status": "MATCH",
        "extractedGender": "F",
        "iprsGender": "F",
        "normalizedComparison": true,
        "reason": null
      }
    },
    "extractedData": {
      "PASSPORT_NUMBER": "BK080411",
      "SURNAME": "MAINA",
      "GIVEN_NAMES": "JANE WAIRIMU",
      "SEX": "F",
      "DATE_OF_BIRTH": "20/05/1990"
    },
    "extractionMethod": "queries"
  }
}
```

### Step 2: Government Verification (IPRS)

Action: `government_verify_nationalid`

Passport holders are verified via their national ID number in IPRS.

```bash
curl -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "government_verify_nationalid",
    "data": {
      "personalData": {
        "name": "JANE WAIRIMU MAINA",
        "idNumber": "27681984"
      }
    }
  }'
```

### Step 3: Face Matching

Same as National ID face matching, but use `"documentType": "passport"`:

```bash
curl -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "face_match",
    "data": {
      "sessionId": "test-passport-session",
      "documentType": "passport",
      "documentS3Path": "Passport/BK080411.jpeg",
      "idNumber": "27681984",
      "iprsVerificationResponse": <FULL_RESPONSE_FROM_STEP_2>
    }
  }'
```

Document must be JPEG/PNG in the raw docs bucket (not PDF).

---

## 3. Alien ID (Foreigner Certificate)

### Step 1: Document Validation (Async)

Action: `validate_alienid`

Validates Alien ID documents issued to foreign nationals in Kenya. Uses the dedicated Alien ID IPRS endpoint for serial number and gender cross-validation.

> **Async Pattern**: Alien ID validation uses an async job pattern because PDF processing can exceed API Gateway's 29s timeout. The API returns `202 Accepted` with a `jobId`. Poll `get_job_status` to retrieve the result.

```bash
# Submit validation — returns 202 with jobId
curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "validate_alienid",
    "data": {
      "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/alien_id.jpg",
      "alienIdNumber": "123456",
      "serialNumber": "A12345678",
      "fullNames": "JOHN DOE",
      "gender": "Male",
      "dateOfBirth": "1985-03-10",
      "nationality": "BRITISH",
      "placeOfBirth": "LONDON",
      "placeOfIssue": "NAIROBI",
      "dateOfIssue": "2022-01-01",
      "dateOfExpiry": "2027-01-01",
      "indivNumber": "9876543"
    }
  }' | python3 -m json.tool

# Response (202):
# {
#   "result": {
#     "jobId": "8c7d9b38-0503-4ca6-a0fc-1847c4b81bb7",
#     "status": "PROCESSING",
#     "message": "Alien ID validation submitted. Poll get_job_status with this jobId.",
#     "pollAction": "get_job_status"
#   }
# }

# Poll for result (repeat every 5s until status is COMPLETED or FAILED)
curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "get_job_status",
    "data": {
      "jobId": "<JOB_ID_FROM_ABOVE>"
    }
  }' | python3 -m json.tool
```

**Required fields:** `uploadedDocumentUrl`, `alienIdNumber`

**Optional fields:** `serialNumber`, `fullNames`, `gender`, `dateOfBirth`, `nationality`, `placeOfBirth`, `placeOfIssue`, `dateOfIssue`, `dateOfExpiry`, `indivNumber`

**Notes:**
- Returns 202 (not 200) — use `get_job_status` to poll for the result
- Typical completion time: 15-25 seconds
- Uses `/iprs/searchUsingAlienId` endpoint (separate from national ID IPRS)
- Response includes `extractedData` with raw Textract values
- Textract field `INDIV._NUMBER` maps to `indivNumber` (note the dot in the Textract key)

**Response includes:**

```json
{
  "message": "Validation successful",
  "s3Path": "AlienID/123456.pdf",
  "results": {
    "keywords_checks": [
      {"check": "Contains \"FOREIGNER CERTIFICATE\" or \"ALIEN\"", "result": true},
      {"check": "Contains \"REPUBLIC OF KENYA\"", "result": true}
    ],
    "matchResults": {
      "serialNumber": {"status": "Matched", "details": {...}},
      "fullNames": {"status": "Matched", "details": {...}},
      "gender": {"status": "Matched", "details": {...}},
      "nationality": {"status": "Matched", "details": {...}},
      "serialNumberValidation": {
        "status": "MATCH",
        "extractedSerialNumber": "A12345678",
        "iprsSerialNumber": "A12345678"
      },
      "genderValidation": {
        "status": "MATCH",
        "extractedGender": "M",
        "iprsGender": "M"
      }
    },
    "extractedData": {
      "SERIAL_NUMBER": "A12345678",
      "FULL_NAMES": "JOHN DOE",
      "SEX": "MALE"
    }
  }
}
```

### Step 2: Government Verification

Action: `government_verify_alienid`

```bash
curl -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "government_verify_alienid",
    "data": {
      "personalData": {
        "alienIdNumber": "123456",
        "fullNames": "JOHN DOE",
        "dateOfBirth": "1985-03-10"
      }
    }
  }'
```

**Required fields:** `personalData.alienIdNumber`

### Step 3: Face Matching

```bash
curl -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "face_match",
    "data": {
      "sessionId": "test-alien-session",
      "documentType": "alien_id",
      "documentS3Path": "AlienID/123456.jpeg",
      "idNumber": "123456",
      "iprsVerificationResponse": <FULL_RESPONSE_FROM_STEP_2>
    }
  }'
```

---

## 4. Military ID

### Step 1: Document Validation (Async)

Action: `validate_militaryid`

Validates Kenya Defence Forces military ID. IPRS lookup uses the associated national ID number (not the service number).

> **Async Pattern**: Military ID validation uses the same async job pattern as Alien ID. Returns `202 Accepted` with a `jobId`. Poll `get_job_status` to retrieve the result.

```bash
# Submit validation — returns 202 with jobId
curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "validate_militaryid",
    "data": {
      "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/ID_Military1.pdf",
      "serviceNumber": "94143",
      "idNumber": "27140910",
      "gender": "Male",
      "fullNames": "JOHN DOE",
      "dateOfBirth": "1988-07-22",
      "rank": "CORPORAL",
      "unit": "KDF",
      "dateOfIssue": "2019-05-01",
      "bloodGroup": "O+",
      "serialNumber": "MIL123456"
    }
  }' | python3 -m json.tool

# Poll for result (repeat every 5s until COMPLETED or FAILED)
curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "get_job_status",
    "data": {
      "jobId": "<JOB_ID_FROM_ABOVE>"
    }
  }' | python3 -m json.tool
```

**Required fields:** `uploadedDocumentUrl`, `serviceNumber`

**Optional fields:** `idNumber`, `gender`, `fullNames`, `dateOfBirth`, `rank`, `unit`, `dateOfIssue`, `bloodGroup`, `serialNumber`

**Important notes:**
- `idNumber` is the person's national ID number. Without it, IPRS lookup falls back to `serviceNumber` which will likely fail (no military ID search endpoint in IPRS).
- Gender extraction checks both `SEX` and `GENDER` Textract fields, then falls back to the `gender` field in the request payload. Always provide `gender` in the payload for military IDs.
- IPRS may return `null` for `serialNumber` for some individuals — this results in serial number validation INCONCLUSIVE.

**Response includes:**

```json
{
  "message": "Validation successful",
  "s3Path": "MilitaryID/94143.pdf",
  "results": {
    "keywords_checks": [
      {"check": "Contains the words \"Kenya Defence Forces\"", "result": true},
      {"check": "Contains the words \"Military\"", "result": true}
    ],
    "matchResults": {
      "serviceNumber": {"status": "Matched", "details": {...}},
      "idNumber": {"status": "Matched", "details": {...}},
      "gender": {"status": "Matched", "details": {...}},
      "rank": {"status": "Not Found", "details": null},
      "serialNumberValidation": {
        "status": "INCONCLUSIVE",
        "extractedSerialNumber": null,
        "iprsSerialNumber": null,
        "reason": "IPRS serial number not available"
      },
      "genderValidation": {
        "status": "MATCH",
        "extractedGender": "M",
        "iprsGender": "M"
      }
    }
  }
}
```

### Step 2: Government Verification (IPRS via National ID)

Military IDs are verified through the person's national ID number:

```bash
curl -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "government_verify_nationalid",
    "data": {
      "personalData": {
        "name": "JOHN DOE",
        "idNumber": "27140910"
      }
    }
  }'
```

There is no dedicated military ID government verification endpoint. Always use `government_verify_nationalid` with the person's national ID number.

### Step 3: Face Matching

```bash
curl -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "face_match",
    "data": {
      "sessionId": "test-military-session",
      "documentType": "military_id",
      "documentS3Path": "MilitaryID/94143.jpeg",
      "idNumber": "27140910",
      "iprsVerificationResponse": <FULL_RESPONSE_FROM_STEP_2>
    }
  }'
```

Document must be JPEG/PNG. If the original is PDF, convert and upload:

```bash
# Convert PDF to JPEG (requires Python + PyMuPDF)
python3 -c "
import fitz
doc = fitz.open('/path/to/military_id.pdf')
page = doc[0]
pix = page.get_pixmap(matrix=fitz.Matrix(200/72, 200/72))
pix.save('/tmp/military_id.jpeg')
"

aws s3 cp /tmp/military_id.jpeg \
  s3://kyc-raw-documents-jubilee-ekyc-dev-686255958278/MilitaryID/94143.jpeg \
  --profile pasha-eu
```

---

## Quick Reference: All Actions

| Action | Required Data Fields | IPRS Endpoint |
|--------|---------------------|---------------|
| `validate_nationalid` | `uploadedDocumentUrl`, `idNumber` | `/iprs/searchV2` (by ID number) |
| `validate_passport` | `uploadedDocumentUrl`, `passportNumber` | `/iprs/searchUsingPassportNumber` |
| `validate_alienid` | `uploadedDocumentUrl`, `alienIdNumber` | `/iprs/searchUsingAlienId` |
| `validate_militaryid` | `uploadedDocumentUrl`, `serviceNumber` | `/iprs/searchV2` (by national ID) |
| `government_verify_nationalid` | `personalData.name`, `personalData.idNumber` | `/iprs/searchV2` |
| `government_verify_alienid` | `personalData.alienIdNumber` | `/iprs/searchUsingAlienId` |
| `face_match` | `sessionId`, `documentType`, `documentS3Path`, `idNumber` | N/A (uses Rekognition) |
| `get_job_status` | `jobId` | N/A (reads from DynamoDB) |

### Async Actions

`validate_alienid` and `validate_militaryid` use an async pattern to avoid API Gateway's 29s timeout:

1. Client sends the validation request → API returns **202 Accepted** with `{ "jobId": "...", "status": "PROCESSING" }`
2. Client polls `get_job_status` with the `jobId` every 5 seconds
3. When `status` is `COMPLETED`, the `result` field contains the full validation response
4. If `status` is `FAILED`, the `errorMessage` field explains what went wrong
5. Jobs expire after 24 hours

All other actions (`validate_nationalid`, `validate_passport`, `government_verify_*`, `face_match`) remain synchronous and return results immediately.

## v1.2 Validation Statuses

| Status | Meaning |
|--------|---------|
| MATCH | Extracted value matches IPRS record |
| MISMATCH | Values differ — possible fraud or outdated document |
| INCONCLUSIVE | Cannot compare — missing data from Textract or IPRS |

## Test IDs (Known Working)

| ID Number | Serial Number | Name | Gender | Document Types Tested |
|-----------|---------------|------|--------|-----------------------|
| 26465570 | 702124691 | TIMOTHY | M | National ID |
| 27681984 | — | PENINAH | F | National ID |
| 27140910 | — | — | M | Military ID (service# 94143) |
| 23667272 | 217934147 | JANE WAIRIMU MAINA | F | National ID |
| 32140017 | 702945559 | EFFIE NJOKI NYAMBURA | F | National ID |
| 36296352 | 244772451 | JOEL MUUO | M | National ID |

---

## Curl E2E Examples (Copy-Paste Ready)

### Peninah — National ID (ID: 27681984, Female)

**Pre-requisites: Upload documents to S3**

```bash
# Upload National ID to uploads bucket
aws s3 cp /Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/Peninah_National_ID.jpeg \
  s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/Peninah_National_ID.jpeg \
  --profile pasha-eu

# Upload liveness selfie to liveness bucket
aws s3 cp /Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/Peninah_Face_Liveness_Capture.jpeg \
  s3://faceliveness-captures-jubilee-ekyc-dev-686255958278/test-peninah-session/reference_image.jpg \
  --profile pasha-eu

# Upload National ID as JPEG to raw docs bucket (Rekognition needs JPEG, not PDF)
aws s3 cp /Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/Peninah_National_ID.jpeg \
  s3://kyc-raw-documents-jubilee-ekyc-dev-686255958278/NationalID/27681984.jpeg \
  --profile pasha-eu
```

**Step 1: Document Validation**

```bash
curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "validate_nationalid",
    "data": {
      "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/Peninah_National_ID.jpeg",
      "idNumber": "27681984",
      "gender": "Female"
    }
  }' | python3 -m json.tool
```

**Step 2: Government Verification (IPRS)**

```bash
# Save response to file (needed for Step 3)
curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "government_verify_nationalid",
    "data": {
      "personalData": {
        "name": "PENINAH",
        "idNumber": "27681984"
      }
    }
  }' -o /tmp/peninah_iprs.json

# View response
python3 -m json.tool /tmp/peninah_iprs.json
```

**Step 3: Face Matching (3-way)**

```bash
# Extract the IPRS result and build face_match payload
python3 -c "
import json
with open('/tmp/peninah_iprs.json') as f:
    iprs = json.load(f)
iprs_result = iprs.get('result', iprs)
payload = {
    'action': 'face_match',
    'data': {
        'sessionId': 'test-peninah-session',
        'documentType': 'national_id',
        'documentS3Path': 'NationalID/27681984.jpeg',
        'idNumber': '27681984',
        'iprsVerificationResponse': iprs_result
    }
}
with open('/tmp/peninah_face_match_payload.json', 'w') as f:
    json.dump(payload, f)
print('Payload written to /tmp/peninah_face_match_payload.json')
"

curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d @/tmp/peninah_face_match_payload.json | python3 -m json.tool
```

### Timothy — National ID (ID: 26465570, Male)

**Pre-requisites: Upload documents to S3**

```bash
aws s3 cp /Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/TIM.jpg \
  s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/TIM.jpg --profile pasha-eu

aws s3 cp /Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/TIM-extracted-face.jpg \
  s3://faceliveness-captures-jubilee-ekyc-dev-686255958278/test-timothy-session/reference_image.jpg --profile pasha-eu

aws s3 cp /Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/TIM.jpg \
  s3://kyc-raw-documents-jubilee-ekyc-dev-686255958278/NationalID/26465570.jpeg --profile pasha-eu
```

**Step 1: Document Validation**

```bash
curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "validate_nationalid",
    "data": {
      "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/TIM.jpg",
      "idNumber": "26465570",
      "gender": "Male"
    }
  }' | python3 -m json.tool
```

**Step 2: Government Verification**

```bash
curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "government_verify_nationalid",
    "data": {
      "personalData": {
        "name": "TIMOTHY",
        "idNumber": "26465570"
      }
    }
  }' -o /tmp/timothy_iprs.json

python3 -m json.tool /tmp/timothy_iprs.json
```

**Step 3: Face Matching**

```bash
python3 -c "
import json
with open('/tmp/timothy_iprs.json') as f:
    iprs = json.load(f)
payload = {
    'action': 'face_match',
    'data': {
        'sessionId': 'test-timothy-session',
        'documentType': 'national_id',
        'documentS3Path': 'NationalID/26465570.jpeg',
        'idNumber': '26465570',
        'iprsVerificationResponse': iprs.get('result', iprs)
    }
}
with open('/tmp/timothy_face_match_payload.json', 'w') as f:
    json.dump(payload, f)
"

curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d @/tmp/timothy_face_match_payload.json | python3 -m json.tool
```

### Military ID — Service# 94143 (National ID: 27140910, Male)

**Pre-requisites: Upload documents to S3**

```bash
aws s3 cp "/Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/Samples eKYC/MilitaryIDs/ID Military1.pdf" \
  s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/ID_Military1.pdf --profile pasha-eu

aws s3 cp /Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/Military_ID_Liveness_face.png \
  s3://faceliveness-captures-jubilee-ekyc-dev-686255958278/test-military1-session/reference_image.jpg --profile pasha-eu

# Convert PDF to JPEG for Rekognition, then upload
python3 -c "
import fitz
doc = fitz.open('/Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/Samples eKYC/MilitaryIDs/ID Military1.pdf')
pix = doc[0].get_pixmap(matrix=fitz.Matrix(200/72, 200/72))
pix.save('/tmp/military_94143.jpeg')
print('Converted to /tmp/military_94143.jpeg')
"

aws s3 cp /tmp/military_94143.jpeg \
  s3://kyc-raw-documents-jubilee-ekyc-dev-686255958278/MilitaryID/94143.jpeg --profile pasha-eu
```

**Step 1: Document Validation**

```bash
curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "validate_militaryid",
    "data": {
      "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/ID_Military1.pdf",
      "serviceNumber": "94143",
      "idNumber": "27140910",
      "gender": "Male"
    }
  }' | python3 -m json.tool
```

**Step 2: Government Verification (via National ID)**

```bash
curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "action": "government_verify_nationalid",
    "data": {
      "personalData": {
        "name": "",
        "idNumber": "27140910"
      }
    }
  }' -o /tmp/military_iprs.json

python3 -m json.tool /tmp/military_iprs.json
```

**Step 3: Face Matching**

```bash
python3 -c "
import json
with open('/tmp/military_iprs.json') as f:
    iprs = json.load(f)
payload = {
    'action': 'face_match',
    'data': {
        'sessionId': 'test-military1-session',
        'documentType': 'military_id',
        'documentS3Path': 'MilitaryID/94143.jpeg',
        'idNumber': '27140910',
        'iprsVerificationResponse': iprs.get('result', iprs)
    }
}
with open('/tmp/military_face_match_payload.json', 'w') as f:
    json.dump(payload, f)
"

curl -s -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/kyc \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d @/tmp/military_face_match_payload.json | python3 -m json.tool
```

---

## Common Issues

1. **Face match returns "Liveness session image not found"** — Upload the selfie to `s3://faceliveness-captures-jubilee-ekyc-dev-686255958278/{sessionId}/reference_image.jpg`

2. **Face match returns "InvalidImageFormatException"** — Rekognition cannot read PDFs. Upload a JPEG/PNG version of the document to the raw docs bucket.

3. **Serial number / gender INCONCLUSIVE** — Either Textract couldn't extract the field, or IPRS returned null. For military IDs, always provide `idNumber` (national ID) and `gender` in the request payload as fallbacks.

4. **Government verification fails for military ID** — There is no military ID IPRS endpoint. Use `government_verify_nationalid` with the person's national ID number.

5. **Passport gender validation INCONCLUSIVE** — Provide `personalNumber` (national ID number) in the passport validation payload to enable IPRS lookup.

6. **Alien ID / Military ID returns 202 instead of 200** — This is expected. These actions now use async processing. Extract the `jobId` from the response and poll `get_job_status` until the status is `COMPLETED`. See the Python E2E test scripts (`test_alien1_e2e.py`) for a working polling implementation.

7. **get_job_status returns PROCESSING for a long time** — The Lambda has a 60s timeout. If the job is still PROCESSING after 90s, it likely failed silently. Check CloudWatch logs for the DocumentValidationFn.
