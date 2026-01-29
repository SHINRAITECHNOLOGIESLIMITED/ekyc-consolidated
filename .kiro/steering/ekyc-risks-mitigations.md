# eKYC Enhancement Risks and Mitigations

This document captures key risks identified in the executive review and their mitigations.

## Risk Matrix

| Risk | Impact | Mitigation | Owner |
|------|--------|------------|-------|
| ESB serial number not exposed | **HIGH** | Escalate Action Item 1 before sprint start - confirm within 48 hours | ESB Team |
| Ambiguous 3-way scoring logic | Medium | Defined deterministic aggregation rule (fail-fast minimum score) in design | Dev Team |
| Poor selfie quality | Medium | Enforce capture-time quality gates in portal | Frontend Team |
| Manual review bottlenecks | Medium | SLA + reviewer queue limits configured | Ops Team |
| Threshold disputes in UAT | Low-Medium | Log ROC metrics during UAT for data-driven tuning | QA Team |

## Critical Action Items

### Before Sprint Start (48 hours)

1. **ESB Serial Number Confirmation**
   - Contact: ESB Integration Team
   - Confirm: `serialNumber` field is consistently exposed in IPRS response
   - Document: Expected payload structure and version
   - Risk if delayed: Serial number validation feature blocks

### During Sprint

2. **Manual Review UI Verification**
   - Confirm: Manual review UI exists or is lightweight to implement
   - If not: Add UI tasks to face matching feature branch

3. **Threshold Configuration**
   - Set up: SSM parameters for approval (70%) and rejection (50%) thresholds
   - Enable: Runtime configurability without code deployment

## Timeline Assumptions

The 4-week parallel development timeline assumes:

1. ESB serial confirmation in first 48 hours
2. Manual review UI already exists or is lightweight
3. No major IPRS API changes during development
4. Dedicated team: 2 backend engineers, 1 QA, 1 AWS architect (part-time)

## Hidden Effort Areas

Plan additional time for:

- UAT threshold tuning (may require multiple iterations)
- Reviewer SOPs and audit logging documentation
- Exception handling for edge cases:
  - Missing IPRS fields
  - Poor image quality
  - Network timeouts
  - Schema version mismatches

## Metrics to Track from Day One

| Metric | Purpose | Alert Threshold |
|--------|---------|-----------------|
| Manual Review % | Monitor review queue load | >30% |
| False Accept Rate | UAT threshold tuning | TBD during UAT |
| False Reject Rate | UAT threshold tuning | TBD during UAT |
| IPRS API Latency | Performance monitoring | >2s p95 |
| Schema Mismatch Count | ESB stability | >0 |
| MISMATCH Rate (Serial) | Fraud detection | >5% |
| MISMATCH Rate (Gender) | Data quality | >2% |
