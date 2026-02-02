# v1.2 eKYC Enhancements

Overview of the three features being developed for v1.2 release.

## Feature Summary

| Feature | Purpose | Status | Branch |
|---------|---------|--------|--------|
| Face Matching | 3-way photo comparison with 70% threshold | Spec complete | `feature/face-matching-verification` |
| Serial Number Validation | Detect outdated/counterfeit IDs | Spec complete | `feature/serial-number-validation` |
| Gender Validation | Cross-validate gender against IPRS | Spec complete | `feature/gender-validation-iprs` |

**Integration Branch**: `develop_v1.2`

---

## 1. Face Matching (70% Threshold)

### Purpose
Compare customer selfie against ID document photo AND IPRS photo to verify identity.

### Decision Bands
| Score Range | Decision | Action |
|-------------|----------|--------|
| ≥70% | APPROVE | Auto-approve |
| 50-69% | REVIEW | Route to manual review |
| <50% | REJECT | Auto-reject |

### 3-Way Comparison Logic
1. Selfie ↔ ID Document Photo
2. ID Document Photo ↔ IPRS Photo
3. Selfie ↔ IPRS Photo

**Aggregation**: Minimum score across all comparisons determines outcome.

### Key Requirements
- Uses AWS Rekognition CompareFaces
- Thresholds configurable via SSM Parameter Store
- Manual review workflow for 50-69% scores
- Metrics: false accept rate, false reject rate, review rate

### ESB Dependency
⚠️ **Pending**: Confirm IPRS returns `photo` field (Base64 or URL)

---

## 2. Serial Number Validation

### Purpose
Validate that the serial number on a submitted National ID matches the latest serial number in IPRS. Detects:
- Counterfeit IDs (fake serial numbers)
- Outdated IDs (old serial from replaced ID)

### Validation Logic
```
Extracted Serial (Textract) → Normalize → Compare → IPRS Serial (API)
```

### Normalization Rules
- Convert to uppercase
- Remove spaces, hyphens, dots
- Strip whitespace

### Outcomes
| Status | Meaning |
|--------|---------|
| MATCH | Document is the latest issued ID |
| MISMATCH | Document may be fraudulent or outdated |
| INCONCLUSIVE | Unable to compare (missing data) |

### Key Requirements
- Non-blocking: INCONCLUSIVE doesn't fail overall validation
- Audit trail: Log both original and normalized values
- Metrics: MATCH/MISMATCH/INCONCLUSIVE rates

### ESB Status
✅ **Confirmed**: IPRS `serialNumber` field is available

---

## 3. Gender Validation (IPRS Only)

### Purpose
Cross-validate gender extracted from document against IPRS authoritative record.

### Why IPRS Only?
Sharon Mukonyo confirmed: Use IPRS for gender validation, NOT LexisNexis, due to historical data quality issues with LexisNexis gender data.

### Validation Logic
```
Extracted Gender (Textract) → Normalize → Compare → IPRS Gender (API)
```

### Gender Normalization
| Input | Normalized |
|-------|------------|
| M, m, Male, MALE | M |
| F, f, Female, FEMALE | F |

### Outcomes
| Status | Meaning |
|--------|---------|
| MATCH | Gender matches IPRS record |
| MISMATCH | Gender doesn't match (data entry error or fraud) |
| INCONCLUSIVE | Unable to compare (missing data) |

### Key Requirements
- Non-blocking: INCONCLUSIVE doesn't fail overall validation
- Metrics: MATCH/MISMATCH/INCONCLUSIVE rates

### ESB Status
✅ **Confirmed**: IPRS `gender` field is available

---

## Implementation Priority

1. **Serial Number Validation** - No ESB dependencies, can start immediately
2. **Gender Validation** - No ESB dependencies, can start immediately
3. **Face Matching** - Blocked on ESB confirmation for photo field

---

## Risk Matrix

| Risk | Impact | Mitigation |
|------|--------|------------|
| ESB photo field not available | High | Escalate to ESB team immediately |
| Ambiguous 3-way scoring logic | Medium | Define deterministic aggregation rule |
| Poor selfie quality | Medium | Enforce capture-time quality gates |
| Manual review bottlenecks | Medium | SLA + reviewer queue limits |
| Threshold disputes in UAT | Low-Medium | Log ROC metrics during UAT |

---

## Action Items

| Item | Owner | Deadline |
|------|-------|----------|
| Confirm IPRS photo field availability | ESB Team | 48 hours from sprint start |
| Define 3-way face matching aggregation rule | Dev Team | Before implementation |
| Set up CloudWatch dashboards | Dev Team | Sprint 1 |
| Create manual review SOP | Product Team | Before UAT |

---

## Specs Location

All specs are in `.kiro/specs/`:
- `serial-number-validation/` - requirements.md, design.md, tasks.md
- `face-matching-verification/` - requirements.md, design.md, tasks.md (on feature branch)
- `gender-validation-iprs/` - requirements.md, design.md, tasks.md (on feature branch)
