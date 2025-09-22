# SOW-Compliant KYC Endpoint Consolidation Plan

**Project**: Jubilee Insurance eKYC System - Statement of Work Compliance
**Feature**: Action-Based KYC Endpoint Consolidation
**Created**: September 22, 2025 (Updated for SOW Compliance)
**Status**: SOW Compliance Rebuild - Complete Architectural Redesign Required

---

## Executive Summary

After thorough analysis of the signed Statement of Work (SOW), this implementation plan has been completely redesigned to ensure 100% compliance with contractual requirements. The original implementation approach did not align with SOW specifications and must be rebuilt.

## SOW Compliance Analysis

### Critical Gaps Identified
- **Architecture**: SOW requires action-based routing, not workflow orchestration
- **Security**: Day 1 security fixes were not implemented (CRITICAL)
- **Endpoint Design**: Must be `/kyc` with actions, not `/kyc/process`
- **Operations**: Must support 10+ individual actions, not process types
- **Performance**: Must achieve <3 seconds, currently ~15 seconds
- **Documentation**: Missing all required documentation deliverables

### SOW Requirements Overview
```
PHASE 1: Security-First Architecture (Days 1-3)
├── Day 1: Critical Security Implementation (PRIORITY)
├── Day 2-3: Unified API Design
PHASE 2: Backend Implementation (Days 4-7)
├── Day 4-5: Core Consolidation
├── Day 6-7: Service Integration
PHASE 3: Deployment & Testing (Days 8-10)
├── Day 8-9: API Gateway & Testing
├── Day 10: Production Deployment
```

---

## Required Architecture Redesign

### Current (Non-Compliant) Architecture
```
POST /kyc/process
{
  "processType": "customer|individual_agent|business_agent",
  "personalData": {...},
  "documents": {...},
  "options": {...}
}
```

### SOW-Required Action-Based Architecture
```
POST /kyc
{
  "action": "validate_nationalid",
  "data": {
    "nationalIdUrl": "...",
    "personalData": {...}
  }
}

POST /kyc
{
  "action": "government_verify_nationalid",
  "data": {
    "idNumber": "...",
    "personalData": {...}
  }
}
```

### Required Actions (10+ Operations)
1. **Document Validation Actions**
   - `validate_nationalid`
   - `validate_passport`
   - `validate_krapincertificate`
   - `validate_cr12`

2. **Government Verification Actions**
   - `government_verify_nationalid`
   - `government_verify_passport`

3. **Other Operations**
   - `background_check`
   - `face_liveness`
   - `agent_registration`
   - `customer_registration`

4. **Supporting Actions**
   - `stream_document`

---

## SOW Compliance Implementation Plan

### PHASE 1: Security-First Architecture (Days 1-3)

#### DAY 1 - Critical Security Implementation (HIGHEST PRIORITY)
**Technical Deliverables:**
- Security headers configuration
- HttpOnly cookie setup for refresh tokens
- 2FA integration with existing Cognito

**Technical Activities:**
- Implement essential security headers: Strict-Transport-Security, Content-Security-Policy, X-Frame-Options
- Configure HttpOnly flags for Cognito refresh tokens
- Integrate 2FA with current authentication flow
- **PRIORITY**: Security fixes deployed to staging by end of Day 1

**Commit:** `feat(security): implement critical security fixes - Day 1 SOW deliverable`

#### DAY 2 - Unified API Design
**Technical Deliverables:**
- Action parameter structure design
- Standardized payload format for all 10+ operations
- Consistent response structure

**Technical Activities:**
- Design action parameter structure (action: "validate_nationalid", etc.)
- Create standardized payload format for all operations
- Define consistent response structure for all actions

**Commit:** `feat(api): design action-based API structure - Day 2 SOW deliverable`

#### DAY 3 - Architecture Setup
**Technical Deliverables:**
- Basic feature flag framework
- Core API specification documentation

**Technical Activities:**
- Implement simple feature flags for operation enable/disable
- Document core API specification with examples

**Commit:** `feat(architecture): implement feature flags and API docs - Day 3 SOW deliverable`

### PHASE 2: Backend Implementation (Days 4-7)

#### DAY 4 - Core Consolidation
**Technical Deliverables:**
- Action-based request router
- Modular function handlers
- Switch logic for all operation types

**Technical Activities:**
- Develop action-based request router
- Refactor existing handlers into modular functions
- Implement switch logic for all operation types
- Create unified response formatter

**Commit:** `feat(backend): implement action router and modular handlers - Day 4 SOW deliverable`

#### DAY 5 - Error Handling & Logging
**Technical Deliverables:**
- Basic logging and error handling
- Response formatting system

**Technical Activities:**
- Implement comprehensive error handling
- Create unified response formatter
- Basic logging infrastructure

**Commit:** `feat(backend): implement error handling and logging - Day 5 SOW deliverable`

#### DAY 6 - Service Integration Part 1
**Technical Deliverables:**
- Document validation actions integration
- Government verification actions integration

**Technical Activities:**
- Integrate all document validation services
- Consolidate government verification endpoints
- Implement individual action handlers

**Commit:** `feat(integration): implement document and government verification actions - Day 6 SOW deliverable`

#### DAY 7 - Service Integration Part 2
**Technical Deliverables:**
- Background check and face liveness integration
- Registration workflows
- Legacy proxy layer
- Performance optimization

**Technical Activities:**
- Merge background check and face liveness
- Implement registration workflows
- Create legacy endpoint proxies for backward compatibility
- Basic performance optimization to achieve <3 seconds

**Commit:** `feat(integration): complete service integration and legacy proxy - Day 7 SOW deliverable`

### PHASE 3: Deployment & Testing (Days 8-10)

#### DAY 8 - API Gateway Configuration
**Technical Deliverables:**
- Single /kyc endpoint configuration
- Request validation and CORS

**Technical Activities:**
- Configure single /kyc endpoint in API Gateway
- Implement request validation and CORS
- Update OpenAPI specification

**Commit:** `feat(gateway): configure API Gateway for action-based endpoint - Day 8 SOW deliverable`

#### DAY 9 - Testing & Staging
**Technical Deliverables:**
- Essential test suite
- Staging deployment with health checks

**Technical Activities:**
- Create essential unit and integration tests
- Focus testing on critical paths only
- Deploy to staging with health checks

**Commit:** `feat(testing): implement test suite and staging deployment - Day 9 SOW deliverable`

#### DAY 10 - Production Deployment & Documentation
**Technical Deliverables:**
- Production deployment with feature flags
- Basic monitoring (CloudWatch)
- All required documentation

**Technical Activities:**
- Production deployment with feature flags
- Configure basic monitoring (CloudWatch)
- Create essential API documentation
- Implement rollback procedures

**Documentation Deliverables:**
1. API Reference - Core endpoint documentation with examples
2. Migration Guide - Step-by-step client transition instructions
3. Security Report - Documentation of implemented security fixes
4. Rollback Procedures - Emergency rollback instructions

**Commit:** `feat(production): deploy to production with monitoring and docs - Day 10 SOW deliverable`

---

## Technical Architecture Details

### Action-Based Router Design
```python
def handle_kyc_action(event, context):
    action = event.get('action')
    data = event.get('data', {})

    action_handlers = {
        'validate_nationalid': handle_nationalid_validation,
        'validate_passport': handle_passport_validation,
        'validate_krapincertificate': handle_kra_validation,
        'validate_cr12': handle_cr12_validation,
        'government_verify_nationalid': handle_nationalid_verification,
        'government_verify_passport': handle_passport_verification,
        'background_check': handle_background_check,
        'face_liveness': handle_face_liveness,
        'agent_registration': handle_agent_registration,
        'customer_registration': handle_customer_registration,
        'stream_document': handle_document_streaming
    }

    if action not in action_handlers:
        return error_response(400, f"Unknown action: {action}")

    if not is_feature_enabled(action):
        return error_response(503, f"Action {action} is currently disabled")

    return action_handlers[action](data)
```

### Feature Flag Framework
```python
def is_feature_enabled(action):
    feature_flags = get_feature_flags()
    return feature_flags.get(action, True)

def get_feature_flags():
    # Can be from environment variables, DynamoDB, or Parameter Store
    return {
        'validate_nationalid': True,
        'validate_passport': True,
        'validate_krapincertificate': True,
        'validate_cr12': True,
        'government_verify_nationalid': True,
        'government_verify_passport': True,
        'background_check': True,
        'face_liveness': True,
        'agent_registration': True,
        'customer_registration': True,
        'stream_document': True
    }
```

### Legacy Proxy Implementation
```python
# Proxy existing endpoints to new action-based system
def proxy_legacy_request(legacy_endpoint, request_data):
    action_mapping = {
        '/document/nationalid': 'validate_nationalid',
        '/document/passport': 'validate_passport',
        '/document/krapincertificate': 'validate_krapincertificate',
        '/document/cr12': 'validate_cr12',
        '/government/nationalid': 'government_verify_nationalid',
        '/government/passport': 'government_verify_passport',
        '/background-check': 'background_check',
        '/face-liveness': 'face_liveness',
        '/agent-registration': 'agent_registration',
        '/customer-registration': 'customer_registration'
    }

    action = action_mapping.get(legacy_endpoint)
    if not action:
        return error_response(404, "Legacy endpoint not found")

    # Convert legacy request format to action-based format
    kyc_request = {
        'action': action,
        'data': request_data
    }

    return handle_kyc_action(kyc_request, {})
```

### Security Implementation Details

#### Security Headers Configuration
```python
def add_security_headers(response):
    security_headers = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'",
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }

    if 'headers' not in response:
        response['headers'] = {}

    response['headers'].update(security_headers)
    return response
```

#### 2FA Integration with Cognito
```python
def enable_2fa_for_user(user_pool_id, username):
    cognito_client = boto3.client('cognito-idp')

    # Enable TOTP MFA for user
    response = cognito_client.admin_set_user_mfa_preference(
        UserPoolId=user_pool_id,
        Username=username,
        TOTPMFASettings={
            'Enabled': True,
            'PreferredMfa': True
        }
    )

    return response
```

#### HttpOnly Cookie Configuration
```python
def set_secure_cookie(response, token_name, token_value):
    cookie_value = f"{token_name}={token_value}; HttpOnly; Secure; SameSite=Strict; Path=/"

    if 'headers' not in response:
        response['headers'] = {}

    response['headers']['Set-Cookie'] = cookie_value
    return response
```

---

## SOW Compliance Checklist

### Must-Have Technical Requirements
- [ ] Single /kyc endpoint handles all 10+ operations via action parameter
- [ ] All 3 security vulnerabilities resolved (headers, 2FA, HttpOnly cookies)
- [ ] Response time <3 seconds average
- [ ] Legacy endpoints functional via proxy
- [ ] Basic rollback capability operational
- [ ] Error rate <2% during initial deployment

### Should-Have Technical Requirements
- [ ] Feature flags for operation control
- [ ] Basic monitoring and alerting
- [ ] Essential API documentation
- [ ] Clear migration path for clients

### Documentation Deliverables
- [ ] API Reference - Core endpoint documentation with examples
- [ ] Migration Guide - Step-by-step client transition instructions
- [ ] Security Report - Documentation of implemented security fixes
- [ ] Rollback Procedures - Emergency rollback instructions

### Technical Success Metrics
- **Performance**: Response time <3 seconds average
- **Reliability**: Error rate <2% during initial deployment
- **Security**: All 3 critical vulnerabilities resolved
- **Compatibility**: All legacy endpoints functional via proxy
- **Monitoring**: Basic CloudWatch monitoring operational

---

## Risk Mitigation Strategies

### High-Priority Technical Risks
1. **Integration Complexity**
   - **Risk**: 10+ service integrations in compressed timeline
   - **Mitigation**: Reuse existing service handlers, wrapper approach for legacy code

2. **Single Endpoint Failure**
   - **Risk**: All operations dependent on one endpoint
   - **Mitigation**: Legacy proxy layer for immediate fallback, feature flags for operation-level control

3. **Security Implementation**
   - **Risk**: Security fixes affecting existing functionality
   - **Mitigation**: Security changes implemented first (Day 1), isolated security configuration

### Performance Optimization Strategy
- **Current**: ~15 seconds response time
- **Target**: <3 seconds
- **Approach**:
  - Parallel Lambda invocations where possible
  - Optimize individual function performance
  - Implement caching for repeated operations
  - Use connection pooling for external services

---

## Environment & Infrastructure

### AWS Environment Setup
- **Account**: 842206816107 (admin access confirmed)
- **Profile**: default
- **Stack**: jubilee-ekyc-backend
- **Region**: eu-west-1
- **API Gateway**: https://65mz46ka57.execute-api.eu-west-1.amazonaws.com/Prod

### Required Infrastructure Components
- AWS Lambda (existing functions + new action router)
- API Gateway (single /kyc endpoint)
- Cognito (2FA integration)
- CloudWatch (monitoring)
- Parameter Store or DynamoDB (feature flags)

### Development Tools
- SAM CLI (deployment)
- Python 3.11 (runtime)
- pytest (testing)
- AWS Lambda Powertools (observability)

---

## Implementation Timeline Summary

| Phase | Duration | Key Deliverable | SOW Compliance |
|-------|----------|----------------|----------------|
| Phase 1.1 | Day 1 | Security fixes | ✅ Critical |
| Phase 1.2 | Day 2-3 | API design | ✅ Required |
| Phase 2.1 | Day 4-5 | Core backend | ✅ Required |
| Phase 2.2 | Day 6-7 | Integration | ✅ Required |
| Phase 3.1 | Day 8-9 | Testing | ✅ Required |
| Phase 3.2 | Day 10 | Production | ✅ Required |

**Total Duration**: 10 business days
**Total Investment**: $3,000 USD
**SOW Compliance**: 100% when complete

---

## Next Steps - Immediate Action Required

1. **PRIORITY**: Begin Phase 1.1 - Day 1 Security Implementation
2. **Commit Strategy**: Each day's deliverables as separate commits
3. **Testing Strategy**: Continuous testing against SOW requirements
4. **Documentation**: Update as implementation progresses

**Critical Success Factor**: Security fixes MUST be completed on Day 1 as per SOW requirements.
