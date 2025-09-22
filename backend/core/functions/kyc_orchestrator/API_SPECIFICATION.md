# Jubilee eKYC Unified API Specification
## SOW Day 2 Deliverable: Action-Based Endpoint Design

### Overview
This document defines the unified KYC API that consolidates 10+ operations into a single `/kyc` endpoint with action-based routing, as required by the Statement of Work.

### Base URL
```
https://api.jubilee-insurance.co.ke/kyc
```

### Authentication
All requests require authentication via:
- **API Key**: `X-Api-Key` header
- **JWT Token**: `Authorization: Bearer {token}` header
- **2FA Verification**: Required for sensitive operations

### Request Format

#### Base Request Structure
```json
{
  "action": "string",           // Required: The KYC action to perform
  "data": {},                   // Required: Action-specific data payload
  "metadata": {                 // Optional: Request metadata
    "requestId": "string",
    "clientId": "string",
    "sessionId": "string",
    "timestamp": "2024-01-01T00:00:00Z",
    "userAgent": "string",
    "ipAddress": "string"
  },
  "options": {                  // Optional: Processing options
    "async": false,             // Boolean: Process asynchronously
    "timeout": 30,              // Integer: Timeout in seconds (1-900)
    "retryOnFailure": true,     // Boolean: Retry on failure
    "includeDebugInfo": false   // Boolean: Include debug information
  }
}
```

#### Response Structure
```json
{
  "success": true,              // Boolean: Operation success status
  "action": "string",           // String: Action that was performed
  "result": {},                 // Object: Action-specific result data
  "error": "string",            // String/Object: Error info (if success=false)
  "timestamp": "2024-01-01T00:00:00Z",  // ISO timestamp
  "metadata": {                 // Response metadata
    "requestId": "string",
    "processingTime": 1.234,    // Number: Processing time in seconds
    "functionInvoked": "kyc_orchestrator",
    "version": "1.0.0"
  },
  "debug": {}                   // Object: Debug info (if requested)
}
```

---

## Supported Actions

### 1. Document Validation Actions

#### 1.1 National ID Validation
**Action**: `validate_nationalid`

**Request Example**:
```json
{
  "action": "validate_nationalid",
  "data": {
    "nationalIdUrl": "https://s3.amazonaws.com/docs/national_id_123.jpg",
    "personalData": {
      "name": "John Doe",
      "idNumber": "12345678",
      "dateOfBirth": "1990-01-15",
      "gender": "Male",
      "placeOfBirth": "Nairobi",
      "nationality": "Kenyan"
    },
    "validationOptions": {
      "extractText": true,
      "validatePhoto": true,
      "checkSecurity": true
    }
  },
  "metadata": {
    "requestId": "req_123456",
    "clientId": "client_abc"
  }
}
```

**Response Example**:
```json
{
  "success": true,
  "action": "validate_nationalid",
  "result": {
    "validation_status": "valid",
    "confidence_score": 0.95,
    "extracted_data": {
      "name": "John Doe",
      "id_number": "12345678",
      "date_of_birth": "1990-01-15",
      "gender": "Male",
      "place_of_birth": "Nairobi",
      "nationality": "Kenyan"
    },
    "validation_checks": {
      "format_valid": true,
      "data_match": true,
      "photo_quality": true,
      "security_features": true
    },
    "processing_details": {
      "document_type": "national_id",
      "image_quality": "high",
      "processing_time": 2.1
    }
  },
  "timestamp": "2024-01-01T10:30:00Z",
  "metadata": {
    "requestId": "req_123456",
    "processingTime": 2.1,
    "functionInvoked": "kyc_orchestrator",
    "version": "1.0.0"
  }
}
```

#### 1.2 Passport Validation
**Action**: `validate_passport`

**Request Example**:
```json
{
  "action": "validate_passport",
  "data": {
    "passportUrl": "https://s3.amazonaws.com/docs/passport_456.jpg",
    "personalData": {
      "name": "Jane Smith",
      "passportNumber": "AB1234567",
      "dateOfBirth": "1985-06-20",
      "nationality": "Kenyan",
      "issuingCountry": "Kenya",
      "expiryDate": "2030-06-20"
    }
  }
}
```

**Response Example**:
```json
{
  "success": true,
  "action": "validate_passport",
  "result": {
    "validation_status": "valid",
    "confidence_score": 0.92,
    "extracted_data": {
      "name": "Jane Smith",
      "passport_number": "AB1234567",
      "date_of_birth": "1985-06-20",
      "nationality": "Kenyan",
      "issuing_country": "Kenya",
      "expiry_date": "2030-06-20",
      "issue_date": "2020-06-20"
    },
    "validation_checks": {
      "format_valid": true,
      "data_match": true,
      "expiry_valid": true,
      "mrz_valid": true
    }
  },
  "timestamp": "2024-01-01T10:35:00Z",
  "metadata": {
    "requestId": "req_789012",
    "processingTime": 1.8,
    "functionInvoked": "kyc_orchestrator",
    "version": "1.0.0"
  }
}
```

#### 1.3 KRA PIN Certificate Validation
**Action**: `validate_krapincertificate`

**Request Example**:
```json
{
  "action": "validate_krapincertificate",
  "data": {
    "kraUrl": "https://s3.amazonaws.com/docs/kra_789.pdf",
    "personalData": {
      "name": "Michael Johnson",
      "pinNumber": "A012345678B",
      "dateOfBirth": "1988-03-10",
      "idNumber": "87654321"
    }
  }
}
```

#### 1.4 CR12 Company Registration Validation
**Action**: `validate_cr12`

**Request Example**:
```json
{
  "action": "validate_cr12",
  "data": {
    "cr12Url": "https://s3.amazonaws.com/docs/cr12_101112.pdf",
    "companyData": {
      "companyName": "Tech Innovations Ltd",
      "registrationNumber": "CPR/2020/123456",
      "incorporationDate": "2020-05-15",
      "directors": [
        {
          "name": "Alice Brown",
          "idNumber": "11223344"
        },
        {
          "name": "Bob Wilson",
          "idNumber": "55667788"
        }
      ]
    }
  }
}
```

### 2. Government Verification Actions

#### 2.1 Government National ID Verification
**Action**: `government_verify_nationalid`

**Request Example**:
```json
{
  "action": "government_verify_nationalid",
  "data": {
    "personalData": {
      "name": "John Doe",
      "idNumber": "12345678",
      "dateOfBirth": "1990-01-15"
    },
    "verificationLevel": "enhanced"
  }
}
```

**Response Example**:
```json
{
  "success": true,
  "action": "government_verify_nationalid",
  "result": {
    "verification_status": "verified",
    "verification_level": "enhanced",
    "match_score": 0.98,
    "verified_data": {
      "name_match": true,
      "id_number_match": true,
      "date_of_birth_match": true,
      "status": "active"
    },
    "government_response": {
      "provider": "eCitizen",
      "reference_id": "GV_789012345",
      "response_time": 3.2
    }
  },
  "timestamp": "2024-01-01T10:40:00Z",
  "metadata": {
    "requestId": "req_345678",
    "processingTime": 3.2,
    "functionInvoked": "kyc_orchestrator",
    "version": "1.0.0"
  }
}
```

### 3. Other KYC Operations

#### 3.1 Background Check
**Action**: `background_check`

**Request Example**:
```json
{
  "action": "background_check",
  "data": {
    "personalData": {
      "name": "Robert Davis",
      "dateOfBirth": "1975-12-03",
      "nationality": "Kenyan",
      "aliases": ["Rob Davis", "R. Davis"]
    },
    "checkTypes": ["criminal", "sanctions", "pep", "watchlist"]
  }
}
```

**Response Example**:
```json
{
  "success": true,
  "action": "background_check",
  "result": {
    "check_status": "clear",
    "risk_level": "low",
    "checks_performed": ["criminal", "sanctions", "pep", "watchlist"],
    "findings": {
      "criminal_records": [],
      "sanctions_matches": [],
      "pep_matches": [],
      "watchlist_matches": []
    },
    "sources": [
      {
        "name": "World-Check",
        "last_updated": "2024-01-01T00:00:00Z"
      },
      {
        "name": "OFAC",
        "last_updated": "2024-01-01T00:00:00Z"
      }
    ]
  },
  "timestamp": "2024-01-01T10:45:00Z",
  "metadata": {
    "requestId": "req_901234",
    "processingTime": 5.7,
    "functionInvoked": "kyc_orchestrator",
    "version": "1.0.0"
  }
}
```

#### 3.2 Face Liveness Detection
**Action**: `face_liveness`

**Request Example**:
```json
{
  "action": "face_liveness",
  "data": {
    "faceImageUrl": "https://s3.amazonaws.com/docs/face_567.jpg",
    "sessionId": "session_789",
    "livenessType": "active"
  }
}
```

**Response Example**:
```json
{
  "success": true,
  "action": "face_liveness",
  "result": {
    "liveness_status": "live",
    "confidence_score": 0.94,
    "liveness_type": "active",
    "analysis_results": {
      "face_detected": true,
      "quality_score": 0.89,
      "liveness_checks": {
        "blink_detection": true,
        "head_movement": true,
        "depth_analysis": true,
        "texture_analysis": true
      }
    }
  },
  "timestamp": "2024-01-01T10:50:00Z",
  "metadata": {
    "requestId": "req_567890",
    "processingTime": 1.4,
    "functionInvoked": "kyc_orchestrator",
    "version": "1.0.0"
  }
}
```

#### 3.3 Agent Registration
**Action**: `agent_registration`

**Request Example**:
```json
{
  "action": "agent_registration",
  "data": {
    "agentData": {
      "name": "Sarah Connor",
      "email": "sarah.connor@example.com",
      "agentType": "individual",
      "phoneNumber": "+254712345678",
      "licenseNumber": "LIC123456",
      "address": {
        "street": "123 Business Street",
        "city": "Nairobi",
        "country": "Kenya",
        "postalCode": "00100"
      }
    }
  }
}
```

#### 3.4 Customer Registration
**Action**: `customer_registration`

**Request Example**:
```json
{
  "action": "customer_registration",
  "data": {
    "customerData": {
      "name": "David Miller",
      "email": "david.miller@example.com",
      "phoneNumber": "+254723456789",
      "dateOfBirth": "1992-08-25",
      "nationality": "Kenyan",
      "address": {
        "street": "456 Residential Road",
        "city": "Mombasa",
        "country": "Kenya",
        "postalCode": "80100"
      }
    }
  }
}
```

### 4. Document Streaming

#### 4.1 Stream Document
**Action**: `stream_document`

**Request Example**:
```json
{
  "action": "stream_document",
  "data": {
    "bucketType": "kyc_documents",
    "documentKey": "documents/customer_123/national_id.jpg",
    "downloadOptions": {
      "presignedUrl": true,
      "expiryMinutes": 30
    }
  }
}
```

**Response Example**:
```json
{
  "success": true,
  "action": "stream_document",
  "result": {
    "stream_status": "ready",
    "document_info": {
      "document_key": "documents/customer_123/national_id.jpg",
      "document_type": "image/jpeg",
      "file_size": 2048576,
      "content_type": "image/jpeg"
    },
    "access_details": {
      "presigned_url": "https://s3.amazonaws.com/bucket/documents/customer_123/national_id.jpg?AWSAccessKeyId=...",
      "expiry_time": "2024-01-01T11:20:00Z",
      "download_method": "GET"
    }
  },
  "timestamp": "2024-01-01T10:50:00Z",
  "metadata": {
    "requestId": "req_234567",
    "processingTime": 0.3,
    "functionInvoked": "kyc_orchestrator",
    "version": "1.0.0"
  }
}
```

### 5. Legacy Workflow (Backward Compatibility)

#### 5.1 Process Workflow
**Action**: `process_workflow`

**Request Example**:
```json
{
  "action": "process_workflow",
  "data": {
    "processType": "customer",
    "personalData": {
      "name": "Legacy Customer",
      "idNumber": "98765432",
      "email": "legacy@example.com"
    },
    "documents": {
      "nationalId": "https://s3.amazonaws.com/docs/legacy_id.jpg",
      "faceImage": "https://s3.amazonaws.com/docs/legacy_face.jpg"
    },
    "options": {
      "skipBackgroundCheck": false,
      "enhancedVerification": true
    }
  }
}
```

---

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "action": "validate_nationalid",
  "error": {
    "message": "Validation failed: Invalid document format",
    "error_code": "VALIDATION_ERROR",
    "details": {
      "field": "nationalIdUrl",
      "reason": "Document format not supported"
    }
  },
  "timestamp": "2024-01-01T10:55:00Z",
  "metadata": {
    "requestId": "req_error_123",
    "processingTime": 0.5,
    "functionInvoked": "kyc_orchestrator",
    "version": "1.0.0"
  }
}
```

### HTTP Status Codes
- **200**: Success
- **207**: Multi-Status (Partial Success)
- **400**: Bad Request (Validation Error)
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **408**: Request Timeout
- **422**: Unprocessable Entity
- **429**: Too Many Requests
- **500**: Internal Server Error
- **503**: Service Unavailable

### Common Error Codes
- `INVALID_ACTION`: Unknown or unsupported action
- `VALIDATION_ERROR`: Request validation failed
- `AUTHENTICATION_ERROR`: Authentication failed
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `DOCUMENT_ERROR`: Document processing failed
- `GOVERNMENT_ERROR`: Government verification failed
- `TIMEOUT_ERROR`: Request timeout
- `RATE_LIMIT_ERROR`: Rate limit exceeded
- `INTERNAL_ERROR`: Internal system error

---

## Rate Limiting

- **Default Rate Limit**: 100 requests per minute per API key
- **Document Processing**: 20 requests per minute per API key
- **Government Verification**: 10 requests per minute per API key
- **Background Checks**: 5 requests per minute per API key

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

---

## Security Headers

All responses include SOW-required security headers:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'; script-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
X-XSS-Protection: 1; mode=block
```

---

## Migration from Legacy Endpoints

### Mapping Legacy Endpoints to Actions

| Legacy Endpoint | New Action | Notes |
|----------------|------------|-------|
| `/document/validate/nationalid` | `validate_nationalid` | Direct mapping |
| `/document/validate/passport` | `validate_passport` | Direct mapping |
| `/document/validate/kra` | `validate_krapincertificate` | Direct mapping |
| `/document/validate/cr12` | `validate_cr12` | Direct mapping |
| `/government/verify/nationalid` | `government_verify_nationalid` | Direct mapping |
| `/government/verify/passport` | `government_verify_passport` | Direct mapping |
| `/government/verify/kra` | `government_verify_kra` | Direct mapping |
| `/background/check` | `background_check` | Direct mapping |
| `/face/liveness` | `face_liveness` | Direct mapping |
| `/agent/register` | `agent_registration` | Direct mapping |
| `/customer/register` | `customer_registration` | Direct mapping |
| `/document/stream` | `stream_document` | Direct mapping |
| `/kyc/process` | `process_workflow` | Legacy compatibility |

### Migration Timeline
- **Phase 1**: Legacy endpoints remain functional
- **Phase 2**: New action-based endpoint live
- **Phase 3**: Legacy endpoints deprecated (6 months notice)
- **Phase 4**: Legacy endpoints removed (after 1 year)

---

## Testing

### Test Endpoint
```

```

### Sample Test Requests
Test requests and responses are available in the `/tests` directory of this repository.

---

## Support

For API support and questions:
- **Documentation**: Shinrai Technologies 

---

## Changelog

### Version 1.0.0 (2025-09-22)
- Initial release of unified action-based KYC API
- Support for 12+ KYC operations
- SOW-compliant security enhancements
- Backward compatibility with legacy workflows