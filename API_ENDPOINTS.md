# Jubilee eKYC API Endpoints (v1.2)

## Environment: pasha-eu (Development)

**AWS Account**: 686255958278  
**Region**: eu-west-1  
**Stack Name**: jubilee-ekyc-dev

---

## Frontend Portal

### Hosted URL (AWS Amplify)
```
URL: https://main.d1qtrnpa9trvjj.amplifyapp.com
```

Note: This is a static deployment. For full SSR support, connect to Git repository.

### Local Development
```
URL: http://localhost:3000
```

Run locally with:
```bash
cd portal
npm run dev
```

### Amplify Sandbox (pasha-eu)
The Amplify backend is deployed to pasha-eu with:
- **Cognito User Pool**: `eu-west-1_81h5Vhkvx`
- **AppSync API**: `https://dwx47oyx7nahjdo2gakplo7c3a.appsync-api.eu-west-1.amazonaws.com/graphql`
- **S3 Bucket**: `amplify-jubileeekycportal-kycdocumentsbucketa4bf11-ic5wfd1bnnw8`
- **Identity Pool**: `eu-west-1:7b93dc1d-757f-413b-8797-dc94dda877c6`

To keep the sandbox running:
```bash
cd portal
npx ampx sandbox --profile pasha-eu --identifier ekyc-pasha
```

---

## API Gateway URLs

### Stage Environment (No Auth Required - For Testing)
```
Base URL: https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage
```

The Stage endpoint auto-approves all requests with any Bearer token. Use this for testing:
```bash
curl -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/document/nationalid \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{"uploadedDocumentUrl": "s3://bucket/path/to/document.jpg", "idNumber": "12345678"}'
```

### Production Environment (Auth Required)
```
Base URL: https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Prod
```

Requires valid JWT Bearer token from Jubilee ESB.

---

## Available Endpoints

### Document Validation
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/document/nationalid` | POST | Validate National ID document |
| `/document/passport` | POST | Validate Passport document |
| `/document/krapincertificate` | POST | Validate KRA PIN certificate |
| `/document/cr12` | POST | Validate Company CR12 document |

### Government Verification
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/government/nationalid` | POST | Verify National ID against IPRS |
| `/government/passport` | POST | Verify Passport against IPRS |
| `/government/kra` | POST | Verify KRA PIN |

### Other Services
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/backgroundcheck` | POST | LexisNexis background check |
| `/faceliveness` | POST | Face liveness verification |
| `/kyc` | POST | Unified KYC endpoint (action-based) |
| `/stream/{bucketType}/{documentKey}` | GET | Stream documents from S3 |

---

## v1.2 Features

### Serial Number Validation
Validates that the serial number on a National ID matches the latest serial number in IPRS.

**Response includes:**
```json
{
  "serialNumberValidation": {
    "status": "MATCH",
    "extractedSerialNumber": "702124691",
    "iprsSerialNumber": "702124691",
    "normalizedComparison": true,
    "reason": null
  }
}
```

**Status values:**
- `MATCH` - Serial numbers match (document is current)
- `MISMATCH` - Serial numbers differ (document may be outdated or fraudulent)
- `INCONCLUSIVE` - Unable to compare (missing data)

### Gender Validation
Cross-validates gender extracted from document against IPRS authoritative record.

**Response includes:**
```json
{
  "genderValidation": {
    "status": "MATCH",
    "extractedGender": "M",
    "iprsGender": "M",
    "normalizedComparison": true,
    "reason": null
  }
}
```

**Status values:**
- `MATCH` - Gender matches IPRS record
- `MISMATCH` - Gender doesn't match (data entry error or fraud)
- `INCONCLUSIVE` - Unable to compare (missing data)

---

## Example: National ID Validation

### Request
```bash
curl -X POST https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage/document/nationalid \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-token" \
  -d '{
    "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/test.jpg",
    "idNumber": "26465570"
  }'
```

### Response
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
        "details": {"expected": "26465570", "actual": "26465570", "confidence": 95.25}
      },
      "serialNumberValidation": {
        "status": "MATCH",
        "extractedSerialNumber": "702124691",
        "iprsSerialNumber": "702124691"
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

---

## S3 Buckets

| Bucket | Purpose |
|--------|---------|
| `maisha-verification-dev-686255958278` | Upload test documents here |
| `kyc-raw-documents-jubilee-ekyc-dev-686255958278` | Validated documents stored here |
| `certification-bucket-jubilee-ekyc-dev-686255958278` | KYC certificates |
| `faceliveness-captures-jubilee-ekyc-dev-686255958278` | Face liveness captures |

---

## Test IDs

| ID Number | Serial Number | Name | Gender |
|-----------|---------------|------|--------|
| 26465570 | 702124691 | TIMOTHY | M |
| 23667272 | 217934147 | JANE WAIRIMU MAINA | F |
| 32140017 | 702945559 | EFFIE NJOKI NYAMBURA | F |
| 36296352 | 244772451 | JOEL MUUO | M |

---

## Running E2E Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run National ID validation test
python3 backend/test_e2e_nationalid.py

# Run all e2e tests
cd e2e
pytest tests/ -v
```

---

## CloudWatch Logs

| Function | Log Group |
|----------|-----------|
| Document Validation | `/aws/lambda/jubilee-ekyc-dev-DocumentValidationFn-F5iNea5fWItr` |
| Government Verification | `/aws/lambda/jubilee-ekyc-dev-GovernmentVerificationFn-w15xzu1elQpk` |
| Background Check | `/aws/lambda/jubilee-ekyc-dev-BackgroundChecksFn-wUCVlI9Cz5V7` |
| Face Liveness | `/aws/lambda/jubilee-ekyc-dev-FaceLivenessFn-DtZJtwAw26d8` |
| KYC Orchestrator | `/aws/lambda/jubilee-ekyc-dev-KYCOrchestratorFn-1oY0O0atKeCJ` |
| Authorizer | `/aws/lambda/jubilee-ekyc-dev-AuthorizerFn-Edp6MIEHJ8bx` |
