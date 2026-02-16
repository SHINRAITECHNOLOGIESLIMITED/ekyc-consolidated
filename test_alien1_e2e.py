"""
E2E Test: Alien ID 1 — all 3 steps (async flow).

Subject: PATHI VENKATA SRAVAN KUMAR
Alien ID (INDIV. Number): 814409
Gender: Male
Nationality: Indian

Step 1 now uses async pattern:
  - POST validate_alienid → 202 with jobId
  - Poll get_job_status until COMPLETED/FAILED
This avoids the API Gateway 29s timeout for PDF-heavy alien ID validation.
"""
import json, requests, time

BASE = "https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage"
H = {"Content-Type": "application/json", "Authorization": "Bearer dummy-token"}
ALIEN_ID = "814409"
GENDER = "Male"
SESSION_ID = "test-alien1-session"

# Polling config
POLL_INTERVAL = 5   # seconds between polls
POLL_TIMEOUT = 120  # max seconds to wait


def call(payload, timeout=120):
    start = time.time()
    r = requests.post(f"{BASE}/kyc", headers=H, json=payload, timeout=timeout)
    elapsed = time.time() - start
    body = r.json()
    if isinstance(body.get('body'), str):
        body = json.loads(body['body'])
    return r.status_code, body, elapsed


def parse_inner(body):
    result = body.get('result', body)
    if isinstance(result, dict) and 'body' in result:
        b = result['body']
        result = json.loads(b) if isinstance(b, str) else b
    return result


def poll_job(job_id):
    """Poll get_job_status until COMPLETED or FAILED, or timeout."""
    start = time.time()
    while time.time() - start < POLL_TIMEOUT:
        code, body, _ = call({
            "action": "get_job_status",
            "data": {"jobId": job_id}
        })
        result = body.get('result', body)
        status = result.get('status', 'UNKNOWN')
        print(f"  Poll: status={status} ({time.time() - start:.0f}s elapsed)")

        if status == 'COMPLETED':
            return result.get('result', result)
        elif status == 'FAILED':
            print(f"  Job FAILED: {result.get('errorMessage', 'unknown error')}")
            return None

        time.sleep(POLL_INTERVAL)

    print(f"  TIMEOUT after {POLL_TIMEOUT}s")
    return None


print("=" * 70)
print("STEP 1: validate_alienid (async)")
print("=" * 70)
step1_start = time.time()
code1, body1, t1 = call({
    "action": "validate_alienid",
    "data": {
        "uploadedDocumentUrl": "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/ALIEN_ID1.pdf",
        "alienIdNumber": ALIEN_ID,
        "gender": GENDER
    }
}, timeout=120)
print(f"Initial response: {code1} ({t1:.1f}s)")

r1 = None
if code1 == 202:
    # Async flow — extract jobId and poll
    result_data = body1.get('result', body1)
    job_id = result_data.get('jobId')
    print(f"  Job submitted: {job_id}")
    print(f"  Polling for completion...")
    time.sleep(3)  # brief initial wait before first poll
    job_result = poll_job(job_id)
    step1_elapsed = time.time() - step1_start

    if job_result:
        # job_result is the Lambda response stored in DynamoDB
        r1 = job_result
        if isinstance(r1, dict) and 'body' in r1:
            r1 = json.loads(r1['body']) if isinstance(r1['body'], str) else r1['body']
        code1 = r1.get('statusCode', 200) if isinstance(r1, dict) else 200
        print(f"  Job completed in {step1_elapsed:.1f}s total")
    else:
        step1_elapsed = time.time() - step1_start
        print(f"  Job did not complete. Elapsed: {step1_elapsed:.1f}s")
else:
    # Sync fallback (shouldn't happen, but handle gracefully)
    step1_elapsed = t1
    r1 = parse_inner(body1)
    print(f"  Got sync response (unexpected for alienid)")

# Print validation results
if r1:
    inner = r1
    if isinstance(inner, dict) and 'results' in inner:
        mr = inner['results'].get('matchResults', {})
        for field in ['serialNumber', 'fullNames', 'gender', 'nationality',
                      'dateOfBirth', 'placeOfBirth', 'indivNumber']:
            if field in mr:
                d = mr[field].get('details', {})
                status = mr[field]['status']
                if d:
                    print(f"  {field}: {status} (exp={d.get('expected')}, act={d.get('actual')})")
                else:
                    print(f"  {field}: {status}")
        snv = mr.get('serialNumberValidation', {})
        print(f"  Serial Number Validation: {snv.get('status','N/A')} "
              f"(extracted={snv.get('extractedSerialNumber')}, iprs={snv.get('iprsSerialNumber')})")
        gv = mr.get('genderValidation', {})
        print(f"  Gender Validation: {gv.get('status','N/A')} "
              f"(extracted={gv.get('extractedGender')}, iprs={gv.get('iprsGender')})")
        for c in inner['results'].get('keywords_checks', []):
            print(f"  {c['check']}: {'PASS' if c['result'] else 'FAIL'}")
    else:
        print(f"  Response: {json.dumps(r1, indent=2)[:800]}")

print(f"\n{'=' * 70}")
print("STEP 2: government_verify_alienid (IPRS)")
print("=" * 70)
code2, body2, t2 = call({
    "action": "government_verify_alienid",
    "data": {
        "personalData": {
            "alienIdNumber": ALIEN_ID
        }
    }
})
print(f"Status: {code2} ({t2:.1f}s)")

iprs_resp = None
if body2.get('success') and body2.get('result'):
    iprs_resp = body2['result']
    print("  IPRS Verification: SUCCESS")
elif 'result' in body2:
    iprs_resp = body2.get('result')
    print("  IPRS Response available")
else:
    print(f"  Response: {json.dumps(body2, indent=2)[:500]}")

print(f"\n{'=' * 70}")
print("STEP 3: face_match (3-way comparison)")
print("=" * 70)
code3, body3, t3 = call({
    "action": "face_match",
    "data": {
        "sessionId": SESSION_ID,
        "documentType": "alien_id",
        "documentS3Path": f"AlienID/{ALIEN_ID}.jpeg",
        "idNumber": ALIEN_ID,
        "iprsVerificationResponse": iprs_resp
    }
})
print(f"Status: {code3} ({t3:.1f}s)")

r3 = body3.get('result', body3)
if isinstance(r3, dict):
    print(f"  Decision: {r3.get('overall_decision','N/A')}")
    print(f"  Lowest Score: {r3.get('lowest_score','N/A')}")
    print(f"  IPRS Photo: {r3.get('iprs_photo_available','N/A')}")
    print(f"  Manual Review: {r3.get('requires_manual_review','N/A')}")
    for name, comp in r3.get('comparisons', {}).items():
        if isinstance(comp, dict):
            print(f"  {name}: similarity={comp.get('similarity')}, matched={comp.get('matched')}")
            if comp.get('error'):
                print(f"    error: {comp['error']}")
    if r3.get('error'):
        print(f"  ERROR: {r3['error']}")

print(f"\n{'=' * 70}")
print("SUMMARY")
print("=" * 70)
print(f"  Alien ID: {ALIEN_ID} | Gender: {GENDER}")
print(f"  Step 1 (Doc Validation):  {code1} ({step1_elapsed:.1f}s)")
print(f"  Step 2 (IPRS):            {code2} ({t2:.1f}s)")
print(f"  Step 3 (Face Match):      {code3} ({t3:.1f}s)")
print(f"  Total: {step1_elapsed+t2+t3:.1f}s")
