# eKYC v1.2 Enhancements Overview

This document provides an overview of the three features being developed for eKYC v1.2.

---
inclusion: always
---

## Executive Summary

eKYC v1.2 introduces three fraud detection enhancements:

| Feature | Purpose | Status |
|---------|---------|--------|
| Face Matching | 3-way photo comparison with 70% threshold | Spec complete |
| Serial Number Validation | Detect replaced/counterfeit IDs | Spec complete |
| Gender Validation | Cross-validate gender against IPRS | Spec complete |

**Target Delivery**: ~4 weeks (parallel development)  
**Primary Risk**: ESB confirmation for IPRS photo field

## Feature 1: Face Matching Verification

### Overview
Compares customer selfie against ID document photo and IPRS photo using AWS Rekognition.

### Decision Bands
- **≥70%**: Auto-approve
- **50-69%**: Manual review
- **<50%**: Auto-reject (configurable)

### 3-Way Comparison Logic
```
Selfie ↔ ID Photo      → Score 1
ID Photo ↔ IPRS Photo  → Score 2
Selfie ↔ IPRS Photo    → Score 3

Final Score = min(Score1, Score2, Score3)
```

### Key Requirements
- AWS Rekognition CompareFaces API
- New `FaceMatchingResults` DynamoDB table
- New `FaceMatchingFn` Lambda function
- SSM parameters for configurable thresholds
- Manual review workflow (portal-side)

### Dependencies
- ⚠️ **IPRS photo field** - Pending ESB team confirmation

### Spec Location
`.kiro/specs/face-matching-verification/`

## Feature 2: Serial Number Validation

### Overview
Validates that the serial number extracted from a National ID document matches the latest serial number from IPRS. Detects counterfeit or outdated IDs.

### Validation Logic
```python
extracted_serial = normalize(textract_serial)
iprs_serial = normalize(iprs_response.serialNumber)

if extracted_serial == iprs_serial:
    return MATCH  # Document is current
elif extracted_serial != iprs_serial:
    return MISMATCH  # Potential fraud/outdated
else:
    return INCONCLUSIVE  # Data unavailable
```

### Key Requirements
- Normalization: uppercase, remove spaces/hyphens/dots
- Non-blocking: failures don't stop KYC process
- Audit logging with correlation IDs
- CloudWatch metrics for MATCH/MISMATCH rates

### Dependencies
- ✅ **IPRS serialNumber field** - Confirmed available

### Spec Location
`.kiro/specs/serial-number-validation/`

## Feature 3: Gender Validation

### Overview
Cross-validates gender extracted from document against IPRS authoritative record.

### Important Note
> **Gender validation uses IPRS, NOT LexisNexis**, due to historical data quality issues with LexisNexis gender data. (Per Sharon Mukonyo)

### Validation Logic
```python
extracted_gender = normalize(textract_gender)  # "M" or "F"
iprs_gender = normalize(iprs_response.gender)  # "M" or "F"

if extracted_gender == iprs_gender:
    return MATCH
else:
    return MISMATCH
```

### Key Requirements
- Gender normalization (handle "Male"/"Female" → "M"/"F")
- Non-blocking validation
- Audit logging

### Dependencies
- ✅ **IPRS gender field** - Confirmed available

### Spec Location
`.kiro/specs/gender-validation-iprs/`

## Integration Points

All three features integrate into the existing `validate_nationalid` action:

```python
# In document_validation/src/app.py

def validate_nationalid(data):
    # Existing: Textract extraction
    extracted_fields = extract_with_textract(document_url)
    
    # Existing: Field matching
    match_results = compare_fields(extracted_fields, data)
    
    # NEW: Serial number validation
    serial_validation = validate_serial_number(
        extracted_fields.get("serialNumber"),
        iprs_data.get("serialNumber")
    )
    match_results["serialNumberValidation"] = serial_validation
    
    # NEW: Gender validation
    gender_validation = validate_gender(
        extracted_fields.get("gender"),
        iprs_data.get("gender")
    )
    match_results["genderValidation"] = gender_validation
    
    # NEW: Face matching (separate Lambda)
    # Invoked via KYC Orchestrator
    
    return match_results
```

## Branch Strategy

```
develop (production baseline)
    │
    └── develop_v1.2 (integration branch)
            │
            ├── feature/face-matching-verification
            ├── feature/serial-number-validation
            └── feature/gender-validation-iprs
```

## Timeline

| Week | Activities |
|------|------------|
| 1 | Core modules (normalizer, validators), property tests |
| 2 | Integration with document validation, unit tests |
| 3 | Face matching Lambda, Rekognition integration |
| 4 | Metrics, monitoring, UAT, bug fixes |

## Team Requirements

- 2 Backend Engineers
- 1 QA Engineer
- 1 AWS/Solutions Architect (part-time)

## Risk Matrix

| Risk | Impact | Mitigation |
|------|--------|------------|
| ESB photo field unavailable | High | Escalate within 48 hours |
| Ambiguous 3-way scoring | Medium | Define deterministic aggregation rule |
| Poor selfie quality | Medium | Enforce capture-time quality gates |
| Manual review bottlenecks | Medium | SLA + reviewer queue limits |
| Threshold disputes in UAT | Low-Medium | Log ROC metrics during UAT |

## Action Items

- [ ] **ESB Team**: Confirm IPRS photo field availability (48-hour deadline)
- [ ] **Dev Team**: Implement schema validation with version checking
- [ ] **QA Team**: Prepare test data for all three features
- [ ] **Product**: Define manual review SLAs and escalation paths

## Related Documentation

- `esb-response-schemas.md` - IPRS response field definitions
- `iprs-integration.md` - IPRS API integration patterns
- `testing-guide.md` - Property-based testing patterns
