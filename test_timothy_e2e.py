"""
E2E Test: Timothy National ID Validation + Face Matching

Tests the full v1.2 flow:
1. validate_nationalid - OCR extraction + serial number + gender validation via IPRS
2. government_verify_nationalid - IPRS verification
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

ID_NUMBER = "26465570"
GENDER = "Male"
DOC_S3_URL = "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/TIM.jpg"
LIVENESS_SESSION_ID = "test-timothy-session"


def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_result(key, value, indent=2):
    prefix = " " * indent
    if isinstance(value, dict):
        print(f"{prefix}{key}:")
        for k, v in value.items():
            print_result(k, v, indent + 2)
    elif isinstance(value, list):
        print(f"{prefix}{key}: [{len(value)} items]")
        for item in value:
            if isinstance(item, dict):
                for k, v in item.items():
                    print_result(k, v, indent + 2)
                print()
    else:
        print(f"{prefix}{key}: {value}")


# ============================================================
# Step 1: Validate National ID (Document Validation)
# Tests: Textract OCR, Serial Number Validation, Gender Validation
# ============================================================
print_section("Step 1: Validate National ID (Document Validation)")
print(f"  ID Number: {ID_NUMBER}")
print(f"  Gender: {GENDER}")
print(f"  Document: {DOC_S3_URL}")

payload = {
    "action": "validate_nationalid",
    "data": {
        "uploadedDocumentUrl": DOC_S3_URL,
        "idNumber": ID_NUMBER,
        "gender": GENDER
    }
}

print(f"\n  POST {BASE_URL}/kyc")
start = time.time()
resp = requests.post(f"{BASE_URL}/kyc", headers=HEADERS, json=payload, timeout=60)
elapsed = time.time() - start
print(f"\n  Status: {resp.status_code} ({elapsed:.1f}s)")

body = resp.json()
if isinstance(body.get('body'), str):
    body = json.loads(body['body'])

if 'results' in body:
    results = body['results']
    match_results = results.get('matchResults', {})

    print("\n  --- Match Results ---")
    for field in ['idNumber', 'serialNumber', 'fullNames', 'gender', 'dateOfBirth']:
        if field in match_results:
            mr = match_results[field]
            status = mr.get('status', 'N/A')
            details = mr.get('details', {})
            expected = details.get('expected', '')
            actual = details.get('actual', '')
            conf = details.get('confidence', '')
            print(f"  {field}: {status} (expected={expected}, actual={actual}, confidence={conf})")

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
    print(f"\n  Response: {json.dumps(body, indent=2)}")

doc_s3_path = body.get('s3Path', '')
print(f"\n  Document S3 Path: {doc_s3_path}")


# ============================================================
# Step 2: Government Verification (IPRS)
# ============================================================
print_section("Step 2: Government Verify National ID (IPRS)")

verify_payload = {
    "action": "government_verify_nationalid",
    "data": {
        "personalData": {
            "name": "TIMOTHY",
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
    if isinstance(iprs_verification_response, dict):
        iprs_data = iprs_verification_response
        if 'body' in iprs_data:
            try:
                inner = json.loads(iprs_data['body']) if isinstance(iprs_data['body'], str) else iprs_data['body']
                iprs_data = inner
            except Exception:
                pass
        print(f"  Response keys: {list(iprs_data.keys()) if isinstance(iprs_data, dict) else 'N/A'}")
elif 'result' in body2:
    iprs_verification_response = body2.get('result')
    print(f"\n  IPRS Response available")
else:
    print(f"\n  Response: {json.dumps(body2, indent=2)[:500]}")


# ============================================================
# Step 3: Face Matching (3-way comparison)
# ============================================================
print_section("Step 3: Face Matching (3-way Comparison)")

face_match_payload = {
    "action": "face_match",
    "data": {
        "sessionId": LIVENESS_SESSION_ID,
        "documentType": "national_id",
        "documentS3Path": "NationalID/26465570.jpeg",
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
                print(f"  {comp_name}: similarity={sim}, matched={matched}")
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
print(f"  Subject: TIMOTHY (ID: {ID_NUMBER})")
print(f"  Document Validation: {resp.status_code} ({elapsed:.1f}s)")
print(f"  Government Verification: {resp2.status_code} ({elapsed2:.1f}s)")
print(f"  Face Matching: {resp3.status_code} ({elapsed3:.1f}s)")
print(f"  Total Time: {elapsed + elapsed2 + elapsed3:.1f}s")
