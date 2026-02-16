"""E2E Test: Peninah National ID — all 3 steps in one script."""
import json, requests, time

BASE = "https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage"
H = {"Content-Type": "application/json", "Authorization": "Bearer dummy-token"}
ID = "27681984"

def call(payload):
    start = time.time()
    r = requests.post(f"{BASE}/kyc", headers=H, json=payload, timeout=120)
    elapsed = time.time() - start
    body = r.json()
    if isinstance(body.get('body'), str):
        body = json.loads(body['body'])
    return r.status_code, body, elapsed

print("=" * 70)
print("STEP 1: validate_nationalid")
print("=" * 70)
code1, body1, t1 = call({
    "action": "validate_nationalid",
    "data": {
        "uploadedDocumentUrl": f"s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/Peninah_National_ID.jpeg",
        "idNumber": ID,
        "gender": "Female"
    }
})
print(f"Status: {code1} ({t1:.1f}s)")

# Parse inner body
result1 = body1.get('result', body1)
if isinstance(result1, dict) and 'body' in result1:
    result1 = json.loads(result1['body']) if isinstance(result1['body'], str) else result1['body']

if 'results' in result1:
    mr = result1['results'].get('matchResults', {})
    for field in ['idNumber', 'serialNumber', 'fullNames', 'gender']:
        if field in mr:
            d = mr[field].get('details', {})
            status = mr[field]['status']
            if d:
                exp = d.get('expected', '')
                act = d.get('actual', '')
                conf = d.get('confidence', '')
                print(f"  {field}: {status} (exp={exp}, act={act}, conf={conf})")
            else:
                print(f"  {field}: {status}")
    snv = mr.get('serialNumberValidation', {})
    print(f"  Serial Number Validation: {snv.get('status','N/A')} (extracted={snv.get('extractedSerialNumber')}, iprs={snv.get('iprsSerialNumber')})")
    gv = mr.get('genderValidation', {})
    print(f"  Gender Validation: {gv.get('status','N/A')} (extracted={gv.get('extractedGender')}, iprs={gv.get('iprsGender')})")
    for c in result1['results'].get('keywords_checks', []):
        print(f"  {c['check']}: {'PASS' if c['result'] else 'FAIL'}")
else:
    print(f"  Response: {json.dumps(result1, indent=2)[:500]}")

print(f"\n{'=' * 70}")
print("STEP 2: government_verify_nationalid (IPRS)")
print("=" * 70)
code2, body2, t2 = call({
    "action": "government_verify_nationalid",
    "data": {"personalData": {"name": "PENINAH", "idNumber": ID}}
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
    print(f"  Response: {json.dumps(body2, indent=2)[:300]}")

print(f"\n{'=' * 70}")
print("STEP 3: face_match (3-way comparison)")
print("=" * 70)
code3, body3, t3 = call({
    "action": "face_match",
    "data": {
        "sessionId": "test-peninah-session",
        "documentType": "national_id",
        "documentS3Path": "NationalID/27681984.jpeg",
        "idNumber": ID,
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
    if r3.get('error'):
        print(f"  ERROR: {r3['error']}")

print(f"\n{'=' * 70}")
print("SUMMARY")
print("=" * 70)
print(f"  Step 1 (Doc Validation):  {code1} ({t1:.1f}s)")
print(f"  Step 2 (IPRS):            {code2} ({t2:.1f}s)")
print(f"  Step 3 (Face Match):      {code3} ({t3:.1f}s)")
print(f"  Total: {t1+t2+t3:.1f}s")
