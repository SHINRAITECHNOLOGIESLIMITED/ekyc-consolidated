"""
E2E Test: Military ID Validation + Face Matching

Tests the full v1.2 flow for Military ID:
1. validate_militaryid - OCR extraction + serial number + gender validation via IPRS
2. government_verify_nationalid - IPRS verification (using associated national ID)
3. face_match - 3-way face comparison (liveness vs document vs IPRS)
"""

import json
import requests
import time

BASE_URL = "https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer dummy-token"
}

SERVICE_NUMBER = "94143"
GENDER = "Male"
DOC_S3_URL = "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/ID_Military1.pdf"
LIVENESS_SESSION_ID = "test-military1-session"


def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


# ============================================================
# Step 1: Validate Military ID (Document Validation)
# Tests: Textract OCR, Serial Number Validation, Gender Validation
# ============================================================
print_section("Step 1: Validate Military ID (Document Validation)")
print(f"  Service Number: {SERVICE_NUMBER}")
print(f"  Gender: {GENDER}")
print(f"  Document: {DOC_S3_URL}")

ID_NUMBER = "27140910"

payload = {
    "action": "validate_militaryid",
    "data": {
        "uploadedDocumentUrl": DOC_S3_URL,
        "serviceNumber": SERVICE_NUMBER,
        "idNumber": ID_NUMBER,
        "gender": GENDER
    }
}

print(f"\n  POST {BASE_URL}/kyc")
start = time.time()
resp = requests.post(f"{BASE_URL}/kyc", headers=HEADERS, json=payload, timeout=120)
elapsed = time.time() - start
print(f"\n  Status: {resp.status_code} ({elapsed:.1f}s)")

body = resp.json()
if isinstance(body.get('body'), str):
    body = json.loads(body['body'])

# Navigate orchestrator response
result_data = body
if body.get('result') and isinstance(body['result'], dict):
    inner = body['result']
    if inner.get('body') and isinstance(inner['body'], str):
        result_data = json.loads(inner['body'])
    elif inner.get('body') and isinstance(inner['body'], dict):
        result_data = inner['body']
    else:
        result_data = inner

if 'results' in result_data:
    results = result_data['results']
    match_results = results.get('matchResults', {})

    print("\n  --- Match Results ---")
    for field in ['serviceNumber', 'idNumber', 'serialNumber', 'fullNames', 'gender',
                  'dateOfBirth', 'rank', 'unit', 'dateOfIssue', 'bloodGroup']:
        if field in match_results:
            mr = match_results[field]
            status = mr.get('status', 'N/A')
            details = mr.get('details', {})
            if details:
                expected = details.get('expected', '')
                actual = details.get('actual', '')
                conf = details.get('confidence', '')
                print(f"  {field}: {status} (expected={expected}, actual={actual}, confidence={conf})")
            else:
                print(f"  {field}: {status}")

    print("\n  --- v1.2: Serial Number Validation ---")
    snv = match_results.get('serialNumberValidation', {})
    print(f"  Status: {snv.get('status', 'N/A')}")
    print(f"  Extracted: {snv.get('extractedSerialNumber', 'N/A')}")
    print(f"  IPRS: {snv.get('iprsSerialNumber', 'N/A')}")
    print(f"  Reason: {snv.get('reason', 'None')}")

    print("\n  --- v1.2: Gender Validation ---")
    gv = match_results.get('genderValidation', {})
    print(f"  Status: {gv.get('status', 'N/A')}")
    print(f"  Extracted: {gv.get('extractedGender', 'N/A')}")
    print(f"  IPRS: {gv.get('iprsGender', 'N/A')}")
    print(f"  Reason: {gv.get('reason', 'None')}")

    print("\n  --- Keyword Checks ---")
    for check in results.get('keywords_checks', []):
        print(f"  {check['check']}: {'PASS' if check['result'] else 'FAIL'}")
else:
    print(f"\n  Response: {json.dumps(result_data, indent=2)[:2000]}")

doc_s3_path = result_data.get('s3Path', '')
print(f"\n  Document S3 Path: {doc_s3_path}")


# ============================================================
# Step 2: Government Verification (IPRS via National ID)
# ============================================================
print_section("Step 2: Government Verify National ID (IPRS)")

verify_payload = {
    "action": "government_verify_nationalid",
    "data": {
        "personalData": {
            "name": "",
            "idNumber": ID_NUMBER
        }
    }
}

print(f"\n  POST {BASE_URL}/kyc")
start = time.time()
resp2 = requests.post(f"{BASE_URL}/kyc", headers=HEADERS, json=verify_payload, timeout=60)
elapsed2 = time.time() - start
print(f"  Status: {resp2.status_code} ({elapsed2:.1f}s)")

body2 = resp2.json()
if isinstance(body2.get('body'), str):
    body2 = json.loads(body2['body'])

iprs_verification_response = None
if body2.get('success') and body2.get('result'):
    iprs_verification_response = body2['result']
    print(f"\n  IPRS Verification: SUCCESS")
elif 'result' in body2:
    iprs_verification_response = body2.get('result')
    print(f"\n  IPRS Response available")
else:
    print(f"\n  Response: {json.dumps(body2, indent=2)[:500]}")


# ============================================================
# Step 3: Face Matching (3-way comparison)
# ============================================================
print_section("Step 3: Face Matching (3-way Comparison)")

# For face matching, we need the document in the raw docs bucket
# The validate_militaryid step copies it there as MilitaryID/{serviceNumber}.pdf
# But Rekognition can't read PDFs — we need a JPEG/PNG version
# The doc validation converts to PDF, so we'll use the original uploaded image

face_match_payload = {
    "action": "face_match",
    "data": {
        "sessionId": LIVENESS_SESSION_ID,
        "documentType": "military_id",
        "documentS3Path": f"MilitaryID/{SERVICE_NUMBER}.jpeg",
        "idNumber": ID_NUMBER,
        "iprsVerificationResponse": iprs_verification_response
    }
}

print(f"\n  POST {BASE_URL}/kyc")
print(f"  Document S3 Path: {face_match_payload['data']['documentS3Path']}")
print(f"  Session ID: {LIVENESS_SESSION_ID}")
print(f"  Has IPRS Response: {iprs_verification_response is not None}")

start = time.time()
resp3 = requests.post(f"{BASE_URL}/kyc", headers=HEADERS, json=face_match_payload, timeout=90)
elapsed3 = time.time() - start
print(f"\n  Status: {resp3.status_code} ({elapsed3:.1f}s)")

body3 = resp3.json()
if isinstance(body3.get('body'), str):
    body3 = json.loads(body3['body'])

print(f"\n  --- Face Match Result ---")
result3 = body3.get('result', body3)
if isinstance(result3, dict):
    print(f"  Overall Decision: {result3.get('overall_decision', 'N/A')}")
    print(f"  Lowest Score: {result3.get('lowest_score', 'N/A')}")
    print(f"  IPRS Photo Available: {result3.get('iprs_photo_available', 'N/A')}")
    print(f"  Requires Manual Review: {result3.get('requires_manual_review', 'N/A')}")

    comparisons = result3.get('comparisons', {})
    if comparisons:
        print(f"\n  --- Comparisons ---")
        for comp_name, comp_data in comparisons.items():
            if isinstance(comp_data, dict):
                sim = comp_data.get('similarity', 'N/A')
                matched = comp_data.get('matched', 'N/A')
                err = comp_data.get('error', '')
                print(f"  {comp_name}: similarity={sim}, matched={matched}")
                if err:
                    print(f"    error: {err}")
            else:
                print(f"  {comp_name}: {comp_data}")

    thresholds = result3.get('thresholds', {})
    if thresholds:
        print(f"\n  Thresholds: approve={thresholds.get('auto_approve')}, review={thresholds.get('manual_review')}")

    if result3.get('error'):
        print(f"\n  Error: {result3.get('error')}")
else:
    print(f"  Response: {json.dumps(body3, indent=2)[:1000]}")


# ============================================================
# Summary
# ============================================================
print_section("Test Summary")
print(f"  Subject: Military ID {SERVICE_NUMBER} (National ID: {ID_NUMBER})")
print(f"  Document Validation: {resp.status_code} ({elapsed:.1f}s)")
print(f"  Government Verification: {resp2.status_code} ({elapsed2:.1f}s)")
print(f"  Face Matching: {resp3.status_code} ({elapsed3:.1f}s)")
print(f"  Total Time: {elapsed + elapsed2 + elapsed3:.1f}s")
