# Context Transfer — Jubilee eKYC v1.2

## TASK 1: Fix Confidence Calculation Logic
- **STATUS**: done
- **DETAILS**: `confidence` field in document validation responses was Textract's OCR confidence, NOT a match/similarity score. Fixed by:
  - Renamed `confidence` → `ocr_confidence` in `process()` function
  - Added `match_score` field: `round((1 - editdistance / max_len) * 100, 2)` — actual similarity percentage
  - Updated `rate()` to compute averages for both `ocr_confidence` and `match_score`, returning 5 values
  - Updated all 6 call sites (national ID, passport, KRA PIN, CR12, alien ID, military ID)
  - Portal's `overall_confidence` now receives `match_score` instead of OCR confidence
  - E2E tests confirmed: `ocr_confidence: 95.03, match_score: 100.0` for matching fields
- **FILEPATHS**: `backend/core/functions/document_validation/src/app.py`

## TASK 2: Git Commit/Push Confidence Fix to All Branches
- **STATUS**: done
- **DETAILS**: Committed, pushed to `feature/serial-number-validation`, merged (fast-forward) to `feature/face-matching-verification`, `feature/gender-validation-iprs`, and `develop_v1.2`. All clean.

## TASK 3: Analyze QA Claim — Details Mismatch / No Overall Verdict
- **STATUS**: done
- **DETAILS**: QA finding valid — users can't determine success/failure. HTTP 200 with "Validation successfull" regardless of mismatches. No top-level `overall_status`. `rate()` computes accuracy but only sends to portal, not in API response. Response normalizer computes VERIFIED/FAILED but only for DynamoDB.
- **FILEPATHS**: `backend/core/functions/document_validation/src/app.py`, `backend/core/functions/government_verification/src/app.py`, `backend/core/functions/kyc_orchestrator/src/response_normalizer.py`

## TASK 4: Implement Summary Block in Document Validation Responses
- **STATUS**: done
- **DETAILS**: Updated `rate()` to return a 5th value — `summary` dict:
  - `overall_status`: PASS (no mismatches) / FAIL (any mismatch) / INCONCLUSIVE (no comparisons)
  - `matched`, `mismatched`, `not_provided`, `not_found` counts
  - `validation_accuracy`, `match_score` (rounded), `mismatched_fields` array
  - Updated all 6 call sites. Built, deployed, E2E tested.
- **FILEPATHS**: `backend/core/functions/document_validation/src/app.py`

## TASK 5: Git Commit/Push Summary Block + All Branches
- **STATUS**: done
- **DETAILS**: Committed, pushed to all 3 feature branches + `develop_v1.2`. All clean merges.

## TASK 6: Update All Documentation
- **STATUS**: done
- **DETAILS**: Updated 5 files with renamed `ocr_confidence`/`match_score` fields and new `summary` block in all response examples:
  - `EKYC_TESTING_GUIDE.md` — All response examples updated, added field descriptions for `ocr_confidence`, `match_score`, `summary.*`
  - `TESTING_GUIDE.md` — Section 1.1 response example updated
  - `API_ENDPOINTS.md` — Response example updated, added "Validation Summary Block" section documenting `summary` and field details
  - `.kiro/specs/additional-document-types/design.md` — Response schema example updated with `ocr_confidence`, `match_score`, `summary` block; mock fixture `ocr_confidence` renamed (left raw Textract `phrases.confidence` as-is)
  - `.kiro/steering/ekyc-enhancements.md` — Added "Response Fields (v1.2 Updates)" section
  - Verified no stale `"confidence"` references remain in any updated file
  - Committed, pushed to `feature/serial-number-validation`, merged to `feature/face-matching-verification` (fast-forward), `feature/gender-validation-iprs`, `develop_v1.2`. All clean.
- **FILEPATHS**: `EKYC_TESTING_GUIDE.md`, `TESTING_GUIDE.md`, `API_ENDPOINTS.md`, `.kiro/specs/additional-document-types/design.md`, `.kiro/steering/ekyc-enhancements.md`

## KEY ENVIRONMENT DETAILS
- **AWS Profile**: `pasha-eu`
- **Region**: `eu-west-1`
- **Stack**: `jubilee-ekyc-dev`
- **API Base URL**: `https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage`
- **Auth**: Stage endpoint accepts `Bearer dummy-token`
- **Current branch**: `feature/serial-number-validation`
- **S3 Buckets**:
  - Uploads: `maisha-verification-dev-686255958278`
  - Raw docs: `kyc-raw-documents-jubilee-ekyc-dev-686255958278`
  - Liveness: `faceliveness-captures-jubilee-ekyc-dev-686255958278`

## USER CORRECTIONS AND INSTRUCTIONS
- Use `--profile pasha-eu` for all AWS CLI commands
- Stage endpoint requires no real auth (dummy-token works)
- Always do full `sam build` before `sam deploy` (partial builds break other functions)
- Use `rm -rf .aws-sam` if build directory gets corrupted
- When running E2E tests, use Python scripts (not individual curl commands)
- API Gateway REST API has a hard 29s timeout limit
- IPRS returns only the latest/newest serial number as a single string field
- The two changes made to `document_validation/src/app.py`:
  1. `process()` returns `ocr_confidence` and `match_score` instead of `confidence`
  2. `rate()` returns 5 values (added `summary` dict) with `overall_status`, field counts, `mismatched_fields`
