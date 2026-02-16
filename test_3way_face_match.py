"""
E2E National ID Verification + Face Matching with IPRS
=======================================================
Document: Peninah_National_ID.jpeg
Selfie:   Peninah_Face_Liveness_Capture.jpeg
ID:       27681984 | Gender: Female
"""
import boto3
import base64
import io
import json
import requests
from pathlib import Path
from PIL import Image

REGION = "eu-west-1"
PROFILE = "pasha-eu"
ESB_SECRET_NAME = "jubilee-ekyc-dev-jubilee-esb-ApiGateway-credentials"

DOC_PATH = Path("/Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/Peninah_National_ID.jpeg")
SELFIE_PATH = Path("/Users/timothy/KIRO_PROJECTS/ekyc-consolidated/todo_ekyc_enhancements/Peninah_Face_Liveness_Capture.jpeg")
ID_NUMBER = "27681984"
EXPECTED_GENDER = "F"

APPROVE_THRESHOLD = 70.0
REVIEW_THRESHOLD = 50.0


def load_bytes(path: Path) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def get_esb_credentials(session: boto3.Session) -> dict:
    """Load ESB credentials from Secrets Manager at runtime."""
    sm = session.client("secretsmanager")
    resp = sm.get_secret_value(SecretId=ESB_SECRET_NAME)
    return json.loads(resp["SecretString"])


def compare_faces(rek, source: bytes, target: bytes, pair_name: str) -> dict:
    """Compare two face images using Rekognition. Tries both directions."""
    def _compare(src, tgt):
        try:
            resp = rek.compare_faces(
                SourceImage={"Bytes": src},
                TargetImage={"Bytes": tgt},
                SimilarityThreshold=0.0
            )
            matches = resp.get("FaceMatches", [])
            if matches:
                return max(m["Similarity"] for m in matches)
            return 0.0
        except Exception as e:
            return {"error": str(e)}

    result_fwd = _compare(source, target)
    if isinstance(result_fwd, dict):
        return {"pair": pair_name, "similarity": 0.0, "matched": False, "error": result_fwd["error"]}

    best = result_fwd
    if result_fwd == 0.0:
        result_rev = _compare(target, source)
        if not isinstance(result_rev, dict) and result_rev > best:
            best = result_rev

    return {"pair": pair_name, "similarity": round(best, 2), "matched": best >= APPROVE_THRESHOLD}


def esb_authenticate(credentials: dict) -> str:
    """Authenticate with Jubilee ESB and return JWT token."""
    base_url = credentials["baseurl"]
    resp = requests.post(
        f"{base_url}/api/auth/signin",
        json={"username": credentials["username"], "password": credentials["password"]},
        headers={"Content-Type": "application/json"},
        timeout=15
    )
    resp.raise_for_status()
    token_data = resp.json()
    return f"{token_data['tokenType']} {token_data['accessToken']}"


def iprs_search(credentials: dict, jwt_token: str, id_number: str) -> requests.Response:
    """Call IPRS searchV2 directly via ESB."""
    base_url = credentials["baseurl"]
    business = credentials["business"]
    url = f"{base_url}/iprs/searchV2/{business}"
    return requests.post(
        url,
        json={"identifier": "ID_NUMBER", "value": id_number},
        headers={"Authorization": jwt_token, "Content-Type": "application/json"},
        timeout=60
    )


def normalize_gender(raw: str) -> str:
    """Normalize gender value to M or F."""
    if not raw:
        return ""
    val = raw.strip().upper()
    if val in ("M", "MALE"):
        return "M"
    if val in ("F", "FEMALE"):
        return "F"
    return val


def main():
    session = boto3.Session(profile_name=PROFILE, region_name=REGION)
    rek = session.client("rekognition")
    textract = session.client("textract")

    doc_bytes = load_bytes(DOC_PATH)
    selfie_bytes = load_bytes(SELFIE_PATH)

    print("=" * 80)
    print("E2E NATIONAL ID VERIFICATION + FACE MATCHING")
    print(f"Document: {DOC_PATH.name} | Selfie: {SELFIE_PATH.name}")
    print(f"ID: {ID_NUMBER} | Expected Gender: {EXPECTED_GENDER}")
    print("=" * 80)

    # ── STEP 1: Textract OCR ──────────────────────────────────────────────
    print("\n[1] TEXTRACT - Document OCR")
    textract_resp = textract.detect_document_text(Document={"Bytes": doc_bytes})
    blocks = textract_resp.get("Blocks", [])
    lines = [b["Text"] for b in blocks if b["BlockType"] == "LINE"]
    print(f"    Lines extracted: {len(lines)}")
    for line in lines:
        print(f"    │ {line}")

    all_text = " ".join(lines).upper()
    id_found = ID_NUMBER in all_text
    print(f"    ID {ID_NUMBER} in text: {'✓' if id_found else '✗'}")

    # Extract serial number and gender from OCR text
    extracted_serial = None
    extracted_gender = None
    for i, line in enumerate(lines):
        upper = line.upper().strip()
        # Serial: "SERIAL NUMBER: 700556489" or "SERIAL NUMBER 700556489"
        if "SERIAL" in upper:
            if ":" in upper:
                extracted_serial = upper.split(":")[-1].strip()
            else:
                # Space-separated: take everything after "SERIAL NUMBER"
                parts = upper.replace("SERIAL NUMBER", "").strip()
                if parts:
                    extracted_serial = parts
        if upper in ("MALE", "FEMALE", "M", "F"):
            extracted_gender = normalize_gender(upper)

    print(f"    Extracted serial: {extracted_serial or 'not found'}")
    print(f"    Extracted gender: {extracted_gender or 'not found'}")

    # ── STEP 2: Face Detection ────────────────────────────────────────────
    print("\n[2] REKOGNITION - Face Detection")

    print("    Document faces...")
    doc_faces = rek.detect_faces(Image={"Bytes": doc_bytes}, Attributes=["DEFAULT"])["FaceDetails"]
    print(f"    Found: {len(doc_faces)}")
    for j, f in enumerate(doc_faces):
        bb = f["BoundingBox"]
        print(f"      Face {j+1}: conf={f['Confidence']:.1f}%, "
              f"bbox=(L={bb['Left']:.3f}, T={bb['Top']:.3f}, W={bb['Width']:.3f}, H={bb['Height']:.3f})")

    print("    Selfie faces...")
    selfie_faces = rek.detect_faces(Image={"Bytes": selfie_bytes}, Attributes=["DEFAULT"])["FaceDetails"]
    print(f"    Found: {len(selfie_faces)}")
    if selfie_faces:
        print(f"      Best confidence: {max(f['Confidence'] for f in selfie_faces):.1f}%")

    # ── STEP 3: IPRS Lookup ───────────────────────────────────────────────
    print(f"\n[3] IPRS - Direct ESB Call (ID: {ID_NUMBER})")
    iprs_photo_bytes = None
    iprs_data = None

    try:
        credentials = get_esb_credentials(session)
        print("    Authenticating...")
        jwt_token = esb_authenticate(credentials)
        print("    ✓ Auth OK")

        iprs_resp = iprs_search(credentials, jwt_token, ID_NUMBER)
        print(f"    IPRS status: {iprs_resp.status_code}")

        if iprs_resp.status_code == 200:
            iprs_result = iprs_resp.json()
            data = iprs_result.get("data", iprs_result)
            iprs_data = data

            # Show identity fields
            for key in ["firstName", "otherName", "surname", "serialNumber",
                        "gender", "dateOfBirth", "citizenship"]:
                if key in data:
                    print(f"    {key}: {data[key]}")

            # Extract photo
            if "photo" in data and data["photo"]:
                try:
                    iprs_photo_bytes = base64.b64decode(data["photo"])
                    print(f"    ✓ IPRS photo: {len(iprs_photo_bytes):,} bytes")
                except Exception as e:
                    print(f"    ✗ Photo decode failed: {e}")
            else:
                print(f"    ⚠ No photo in IPRS (isPhotoNil={data.get('isPhotoNil', '?')})")
        else:
            print(f"    ✗ Error: {iprs_resp.text[:300]}")
    except Exception as e:
        print(f"    ✗ ESB call failed: {e}")

    # ── STEP 4: Serial Number Validation ──────────────────────────────────
    print("\n[4] SERIAL NUMBER VALIDATION")
    iprs_serial = iprs_data.get("serialNumber", "") if iprs_data else ""
    if extracted_serial and iprs_serial:
        norm_ext = extracted_serial.upper().replace(" ", "").replace("-", "").replace(".", "")
        norm_iprs = iprs_serial.upper().replace(" ", "").replace("-", "").replace(".", "")
        serial_match = norm_ext == norm_iprs
        print(f"    Extracted: {extracted_serial} → {norm_ext}")
        print(f"    IPRS:      {iprs_serial} → {norm_iprs}")
        print(f"    Result:    {'✓ MATCH' if serial_match else '✗ MISMATCH'}")
    else:
        serial_match = None
        print(f"    INCONCLUSIVE (extracted={extracted_serial}, iprs={iprs_serial})")

    # ── STEP 5: Gender Validation ─────────────────────────────────────────
    print("\n[5] GENDER VALIDATION")
    iprs_gender = normalize_gender(iprs_data.get("gender", "")) if iprs_data else ""
    if extracted_gender and iprs_gender:
        gender_match = extracted_gender == iprs_gender
        print(f"    Extracted: {extracted_gender}")
        print(f"    IPRS:      {iprs_gender}")
        print(f"    Expected:  {EXPECTED_GENDER}")
        print(f"    Doc↔IPRS:  {'✓ MATCH' if gender_match else '✗ MISMATCH'}")
        print(f"    Doc↔Input: {'✓ MATCH' if extracted_gender == EXPECTED_GENDER else '✗ MISMATCH'}")
    else:
        gender_match = None
        print(f"    INCONCLUSIVE (extracted={extracted_gender}, iprs={iprs_gender})")

    # ── STEP 6: 3-Way Face Matching ──────────────────────────────────────
    iprs_available = iprs_photo_bytes is not None
    mode = "3-way" if iprs_available else "2-way (no IPRS photo)"
    print(f"\n[6] FACE MATCHING ({mode})")

    comparisons = []

    # Comparison 1: Selfie ↔ Document (full image — Rekognition finds face)
    print("    [a] Selfie ↔ Document...")
    c1 = compare_faces(rek, selfie_bytes, doc_bytes, "selfie_vs_document")
    comparisons.append(c1)
    print(f"        Similarity: {c1['similarity']}%")

    if iprs_available:
        print("    [b] Selfie ↔ IPRS photo...")
        c2 = compare_faces(rek, selfie_bytes, iprs_photo_bytes, "selfie_vs_iprs")
        comparisons.append(c2)
        print(f"        Similarity: {c2['similarity']}%")

        print("    [c] Document ↔ IPRS photo...")
        c3 = compare_faces(rek, doc_bytes, iprs_photo_bytes, "document_vs_iprs")
        comparisons.append(c3)
        print(f"        Similarity: {c3['similarity']}%")
    else:
        print("    [b,c] Skipped — no IPRS photo")

    # ── Decision ──────────────────────────────────────────────────────────
    valid = [c for c in comparisons if "error" not in c and c["similarity"] > 0]
    if not valid:
        decision, lowest, review = "ERROR", None, False
    elif not iprs_available and len(valid) == 1:
        s = valid[0]["similarity"]
        if s >= APPROVE_THRESHOLD:
            decision, lowest, review = "PARTIAL_MATCH", s, True
        elif s >= REVIEW_THRESHOLD:
            decision, lowest, review = "MANUAL_REVIEW", s, True
        else:
            decision, lowest, review = "AUTO_REJECTED", s, False
    else:
        lowest = min(c["similarity"] for c in valid)
        if lowest >= APPROVE_THRESHOLD:
            decision, lowest, review = "AUTO_APPROVED", lowest, False
        elif lowest >= REVIEW_THRESHOLD:
            decision, lowest, review = "MANUAL_REVIEW", lowest, True
        else:
            decision, lowest, review = "AUTO_REJECTED", lowest, False

    # ── SUMMARY ──────────────────────────────────────────────────────────
    print(f"\n{'=' * 80}")
    print("E2E RESULTS SUMMARY")
    print(f"{'=' * 80}")
    print(f"  Document:           {DOC_PATH.name} (National ID)")
    print(f"  ID Number:          {ID_NUMBER}")
    print(f"  Textract Lines:     {len(lines)}")
    print(f"  ID in OCR:          {'Yes' if id_found else 'No'}")
    print()
    print(f"  Serial Validation:  ", end="")
    if serial_match is True:
        print(f"MATCH ({extracted_serial} = {iprs_serial})")
    elif serial_match is False:
        print(f"MISMATCH ({extracted_serial} ≠ {iprs_serial})")
    else:
        print("INCONCLUSIVE")
    print(f"  Gender Validation:  ", end="")
    if gender_match is True:
        print(f"MATCH ({extracted_gender} = {iprs_gender})")
    elif gender_match is False:
        print(f"MISMATCH ({extracted_gender} ≠ {iprs_gender})")
    else:
        print("INCONCLUSIVE")
    print()
    print(f"  IPRS Photo:         {'Yes' if iprs_available else 'No'}")
    print(f"  Face Match Mode:    {mode}")
    print()
    print(f"  {'Comparison':<30} {'Similarity':>12} {'Result':>10}")
    print(f"  {'─'*30} {'─'*12} {'─'*10}")
    for c in comparisons:
        st = "MATCH" if c["matched"] else ("ERROR" if "error" in c else "NO MATCH")
        print(f"  {c['pair']:<30} {c['similarity']:>11.2f}% {st:>10}")
    print()
    if lowest is not None:
        print(f"  Lowest Score:       {lowest:.2f}%")
    print(f"  Face Decision:      {decision}")
    print(f"  Manual Review:      {'Yes' if review else 'No'}")
    print(f"  Thresholds:         Approve ≥{APPROVE_THRESHOLD}% | Review ≥{REVIEW_THRESHOLD}%")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
