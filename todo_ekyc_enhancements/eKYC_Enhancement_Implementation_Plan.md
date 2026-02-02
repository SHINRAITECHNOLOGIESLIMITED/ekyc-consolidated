# eKYC Enhancement Implementation Plan

**Technical Feasibility & Solution Design**

**Jubilee Insurance Company - J-Force Portal**

*Based on Technical Requirements Meeting*

---

**Prepared by:** SHINRAI Technologies Limited  
**Date:** January 19, 2025  
**Version:** 1.0  
**Classification:** Confidential Business Partners

---

## Executive Summary

Following the successful completion of Cycle 1 UAT testing and subsequent technical requirements meeting between Jubilee Insurance and SHINRAI Technologies, this document provides the updated implementation plan for three critical eKYC enhancements. The requirements have been refined based on technical discussions with stakeholders on the meeting held on December 18th, 2025.

### Key Meeting Outcomes

- **Face Matching Threshold:** Agreed at 70% with manual review for matches below threshold
- **Face Matching Scope:** Clarified as 3-way comparison between customer uploaded photo, National ID document photo (National ID, Alien ID, Passport, Military ID) and IPRS photo
- **Serial Number Validation:** IPRS API confirmed to return serial numbers including historical records
- **Gender Validation Source:** Clarified to use IPRS (not LexisNexis) due to historical data quality issues

### Enhanced Requirements

1. **Face Matching with 70% Threshold:** 3-way face comparison between customer upload, ID document and IPRS photo with configurable workflow
2. **Serial Number Validation:** Validation against IPRS latest serial number without support for historical National ID scenarios
3. **Gender Validation via IPRS:** Cross-validation using IPRS API data (not LexisNexis)

### Overall Assessment

**Status: ALL HIGHLY FEASIBLE**

All three enhancement requests are highly feasible with IPRS API capabilities confirmed during technical review. The 3-way face matching leverages existing AWS Rekognition infrastructure. Customer demographics (average age 37 years) favor newer generation IDs with better photo quality, reducing implementation risk.

**Total estimated timeline:** 4 weeks for complete development, testing, and UAT preparation with ESB configuration confirmation.

---

## Background & Context

### Technical Requirements Meeting Summary

**Meeting Participants:**

- **Jubilee Insurance:** Kigunda Kananua, Daniel Kariuki, Sharon Mukonyo, Noel Ongole, Joseph Karanja, Fredrick Boaz
- **SHINRAI Technologies:** Timothy Munyao, Mesfin Githinji

### Key Discussion Points

- **Face Matching Scope:** Requirement clarified as 3-way comparison between customer uploaded photo, National ID document and IPRS photo image
- **Threshold Determination:** 70% match threshold agreed for automatic approval with manual review workflow for lower matches (implemented on the consuming systems)
- **ID Quality Considerations:** Challenge of varying ID photo quality across old and new generation documents discussed with alternative manual photo matching workflows
- **Serial Number Handling:** IPRS API confirmed to return both latest serial number for ID replacement scenarios
- **Gender Validation Source:** Sharon Mukonyo clarified requirement to use IPRS instead of LexisNexis due to past data quality issues

### Customer Demographics & Risk Profile

- **Average Customer Age:** 37 years
- **ID Type Distribution:** High probability of new-generation National IDs with improved photo quality
- **Photo Quality Expectation:** Reduced likelihood of low-quality ID photos compared to older customer demographics
- **Implementation Impact:** Favorable demographics reduce complexity of face matching model training and threshold calibration

---

## Detailed Technical Solution Design

### 1. Face Matching with 70% Threshold

#### Requirement Overview

Implement 3-way face matching verification comparing customer-uploaded photo with photo extracted from National ID document. The system must achieve an 70% similarity threshold for automatic approval, with manual review workflow for matches below 70%. Fail process for manual review if there is no 3-way match.

#### Technical Feasibility

**Status: HIGHLY FEASIBLE**

The 3-way face matching is highly feasible using AWS Rekognition CompareFaces API with a single pairwise comparison. The 70% threshold accommodates varying ID quality as discussed in the technical meeting.

#### Implementation Architecture

**Phase 1: Image Acquisition**
- **Customer Photo:** Captured through consuming portal/platform interface with quality validation (resolution, lighting, face detection)
- **ID Document Photo:** Extracted from National ID using Textract AnalyzeID with custom face region cropping

**Phase 2: Image Preprocessing**
- Standardize resolution and format across both image sources
- Orientation correction and face alignment
- Quality assessment and enhancement (brightness, contrast, sharpness)

**Phase 3: Face Comparison**

Execute single pairwise comparison using AWS Rekognition CompareFaces API:
Customer Upload ↔ ID Document Photo

**Phase 4: Decision Algorithm**

Evaluate similarity score and determine verification outcome:
- **Automatic Approval:** Similarity score ≥ 70%
- **Manual Review Required:** Similarity score 50-69%
- **Automatic Rejection:** Similarity score < 50% (configurable threshold)

#### Technical Specifications

- Match threshold: 70% as agreed in technical meeting
- Rekognition CompareFaces API cost: $0.001 per comparison
- Processing time: <500ms per comparison (typically 200-300ms)
- Supported image formats: JPEG, PNG for customer upload; extracted image from PDF ID document

#### Dependencies

- Existing AWS Rekognition integration (operational for liveness detection)
- Existing Textract AnalyzeID capability for ID photo extraction
- Portal interface for customer photo upload and quality guidelines

#### Manual Review Workflow – Implemented on the consumer portal/platform

For matches below 70% threshold (50-69% range), implement manual review process:
- Queue management system for review cases
- Side-by-side image display of customer photo and ID photo
- Display of similarity score percentage
- Reviewer decision options: Approve, Reject, Request Re-submission
- Audit trail of manual review decisions and justifications

#### Enhancement Considerations

As discussed in the technical meeting regarding ID quality variations:
- Monitor match accuracy patterns during UAT to identify threshold adjustments
- Consider separate thresholds for old-generation vs new-generation IDs if data supports
- Leverage customer demographic data (average age 37) indicating predominantly newer IDs

#### Estimated Timeline

**10-20 business days (2.5 weeks)** including 3-way comparison logic development, manual review workflow implementation, and comprehensive testing

---

### 2. Serial Number Validation via IPRS

#### Requirement Overview

Validate that the serial number extracted from the submitted National ID document matches the most recent National ID serial number returned by the IPRS API.

#### Technical Feasibility

**Status: HIGHLY FEASIBLE - Confirmed by Joseph Karanja**

IPRS API capability confirmed during technical meeting. Joseph Karanja demonstrated that IPRS API returns serial number data for a given National ID. This enables comprehensive validation.

#### Implementation Approach

- **Serial Number Extraction:** Extract serial number from National ID document using Textract AnalyzeID
- **IPRS Query:** Retrieve latest serial number from IPRS API response
- **Primary Validation:** Compare extracted serial number against latest IPRS serial number
- **Fallback Validation:** If latest doesn't match, prompt customer to provide most recent National ID or mark invalid
- **Data Normalization:** Standardize serial number formats (remove spaces, hyphens, convert to uppercase)
- **Validation Result:** MATCH, MISMATCH, or INCONCLUSIVE (if IPRS data unavailable)

#### ID Replacement Scenario Handling

As discussed in the technical meeting regarding ID document replacements:
- **Scenario A:** Customer presents latest ID → Serial matches IPRS → APPROVED
- **Scenario C:** Serial does not match IPRS latest serial number → REJECTED (potential fraud/counterfeit)
- **Scenario D:** IPRS returns no serial data → INCONCLUSIVE (proceed with other validations)

#### Critical Dependencies & Action Items

- **ACTION ITEM:** Confirm whether ESB (Enterprise Service Bus) currently exposes serial number data in the payload
- Existing IPRS API integration via ESB (operational)
- Textract AnalyzeID serial number extraction

#### Estimated Timeline

**5-10 business days (1.5 week)** contingent on ESB configuration confirmation, including development, testing, and validation logic for historical serial scenarios

---

### 3. Gender Validation via IPRS (Not LexisNexis)

#### Requirement Overview

Cross-validate gender information extracted from the National ID document against gender data returned by the IPRS API. Critical clarification from Sharon Mukonyo: gender validation must use IPRS data, not LexisNexis, due to historical data quality issues where LexisNexis returned incorrect gender information.

#### Technical Feasibility

**Status: HIGHLY FEASIBLE - Confirmed by Joseph Karanja**

IPRS API confirmed to return gender information as part of the identity verification response. The technical meeting clarified that IPRS is the authoritative source for gender validation, addressing previous concerns about data quality in LexisNexis responses.

#### Business Context: Why IPRS, Not LexisNexis

Sharon Mukonyo explained in the technical meeting:
- Past incident where LexisNexis returned incorrect gender data
- IPRS is the official government source with authoritative identity data
- Gender validation requirement is specifically to catch data quality issues, not fraud detection

#### Implementation Approach

- **Gender Extraction:** Extract gender from National ID document using Textract AnalyzeID
- **IPRS Query:** Retrieve gender information from IPRS API response (via ESB)
- **Data Normalization:** Standardize gender values (M/F/Male/Female/etc. → standard M/F codes)
- **Validation Logic:** Compare extracted gender with IPRS gender data
- **Result Categorization:** MATCH, MISMATCH (flag for review), or INCONCLUSIVE (if IPRS doesn't provide or return gender)

#### Dependencies

- Existing IPRS API integration via ESB
- Textract AnalyzeID gender extraction
- IPRS gender data confirmed available in API response

#### Estimated Timeline

**2-5 business days (1 week)**

---

## Implementation Timeline & Resource Plan

### Development Approach

Based on technical meeting outcomes, all three enhancements can be developed in parallel for optimal timeline. This approach accelerates delivery.

### Detailed Timeline Breakdown

| Enhancement | Duration | Dependencies | Key Activities |
|-------------|----------|--------------|----------------|
| Gender Validation (IPRS) | 2-5 days | None (Ready to start) | IPRS response parsing, normalization, validation, testing |
| Serial Number Validation | 5-10 days | ESB serial number confirmation | ESB verification, validation logic, testing |
| Face Matching (70% Threshold) | 5-20 days | None (Ready to start) | 2-way comparison logic, manual review workflow API, testing |

### Parallel Development Strategy

**Week 1: Core Development**
- **Days 1-5:** Gender Validation - Complete development and testing
- **Days 1-10:** Serial Number Validation - Development and testing (contingent on ESB confirmation)
- **Days 1-20:** Face Matching - 3-way comparison development and manual review workflow

**Week 2: Integration & Testing**
- Complete integrated testing of all three enhancements
- Edge case testing (poor photo quality, format variations, missing IPRS data)
- Performance testing under realistic load
- Documentation completion (API specs, user guides, manual review procedures)
- Deployment to staging environment and UAT coordination

### Total Timeline Summary

- **Best Case Scenario:** 30 business days (4 weeks) with ESB serial number confirmation in first 2 days
- **Expected Scenario:** 3-4 weeks (accounting for typical ESB confirmation timelines)
- **Contingency Scenario:** 5 weeks (if ESB configuration requires changes or manual review workflow needs extensive calibration)

---

## Critical Action Items from Technical Meeting

The following action items were identified during the technical requirements meeting and must be completed before full implementation can proceed:

### Priority 1: Immediate Actions (Week 1, Day 1-2)

#### Action Item 1: ESB Serial Number Configuration Check
- **Owner:** Joseph Karanja
- **Task:** Check whether ESB currently exposes serial number data in the IPRS API payload
- **Deliverable:** Confirmation of serial number availability and data format in ESB response
- **Impact:** HIGH - Blocks serial number validation implementation

#### Action Item 2: IPRS Serial Number History Verification
- **Owner:** Joseph Karanja / Fredrick Boaz
- **Task:** Confirm whether IPRS API returns all historical serial numbers or only the latest
- **Deliverable:** Documentation of IPRS serial number response structure
- **Impact:** MEDIUM - Affects ID replacement scenario handling

### Priority 2: Supporting Actions (Week 1, Day 3-5)

#### Action Item 3: Face Matching Threshold Documentation
- **Owner:** SHINRAI Technologies (Timothy Munyao & Mesfin Githinji)
- **Task:** Formalize 70% threshold proposal with fallback workflow documentation
- **Deliverable:** Threshold configuration documentation and manual review process specification
- **Status:** 70% threshold agreed in meeting - formal documentation in progress

---

## Recommendations & Next Steps

### Immediate Actions for Project Initiation

1. **ESB Configuration Check:** Prioritize Action Item 1 completion within first 2 business days
2. **Resource Allocation:** Assign 2 backend developers (one for face matching, one for serial/gender validation), 1 QA engineer and 1 AWS Solutions Architect
3. **Project Kickoff:** Schedule kickoff meeting upon Jubilee approval with clear action item assignments

### Implementation Strategy Recommendations

- **Parallel Development:** Develop all three enhancements simultaneously for 4-week delivery
- **Manual Review Investment:** Develop robust manual review workflow for 50-69% matches with clear reviewer guidelines
- **Threshold Calibration:** Monitor match accuracy during UAT and adjust 70% threshold if needed based on false positive/negative rates
- **Customer Demographics Advantage:** Leverage favorable age profile (average 37 years) by optimizing for new-generation ID quality

---

## Conclusion

The technical requirements meeting provided essential clarifications that enable confident implementation planning. The face matching requirement is a straightforward 3-way comparison between customer uploaded photo and National ID document photo, with a 70% threshold providing clear technical specifications. This simpler scope compared to initial understanding accelerates delivery timeline.

Serial number and gender validation via IPRS are confirmed as highly feasible with Joseph Karanja demonstrating IPRS API capabilities during the meeting. The clarification that gender validation must use IPRS (not LexisNexis) due to Sharon Mukonyo's experience with data quality issues ensures implementation focuses on the authoritative government data source.

**Critical success factors:**
- **ESB configuration confirmation:** Complete within first 2 business days
- **Parallel development:** All three enhancements developed simultaneously
- **Threshold calibration:** 70% starting point with UAT-based adjustment
- **Customer demographics advantage:** Average age 37 years favors new-generation ID quality

SHINRAI Technologies is prepared to commence development immediately upon receipt of approval. The 4-week timeline is achievable with appropriate resource allocation and stakeholder engagement.

These enhancements will significantly strengthen the eKYC solution's fraud detection and data validation capabilities while maintaining customer experience through the configurable 70% threshold and manual review workflows.

---

## Approvals

| Name | Designation | Date |
|------|-------------|------|
| Noel Ongole | Assistant Manager - Underwriting | 23/1/2026 |
| Janet Wamaitha | Senior Manager - Underwriting | 23/1/2026 |
| Kigunda Kananua | Head of Operations - Retail & Group Life | 27/1/2026 |
| Anna Manyara | COO | 23/1/2026 |
| Asman Mugambi | CEO | 23/1/2026 |

---

*Document ID: Docusign Envelope ID: 1AC8F194-0479-421A-AA0F-60388D6DCCA2*
