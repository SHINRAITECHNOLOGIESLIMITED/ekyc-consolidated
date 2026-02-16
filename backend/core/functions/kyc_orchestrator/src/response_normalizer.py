"""
Response Normalization Module for KYC Verifications

Handles inconsistent response structures from different verification types:
- Document Validation (OCR): nested matchResults with confidence scores
- Government Verification: flat results without confidence scores
- Background Check: flat structure with entity scores
- Face Liveness: flat structure with liveness score

Normalizes all responses into a consistent format for DynamoDB storage.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime


def normalize_verification_response(
    action: str,
    raw_response: Dict[str, Any],
    entity_type: str,
    entity_id: str
) -> Dict[str, Any]:
    """
    Normalize verification responses into consistent structure.

    Args:
        action: The verification action performed
        raw_response: The raw API response
        entity_type: 'customer', 'agent', or 'business'
        entity_id: The entity ID (customerId, agentId, businessId)

    Returns:
        Normalized verification data structure
    """
    # Parse nested response if needed (result.body is JSON string)
    parsed_response = _parse_nested_response(raw_response)

    # Route to appropriate normalizer based on action
    if action.startswith('validate_'):
        return _normalize_document_validation(action, parsed_response, entity_type, entity_id)
    elif action.startswith('government_verify_'):
        return _normalize_government_verification(action, parsed_response, entity_type, entity_id)
    elif action == 'background_check':
        return _normalize_background_check(parsed_response, entity_type, entity_id)
    elif action == 'face_liveness':
        return _normalize_face_liveness(parsed_response, entity_type, entity_id)
    elif action == 'face_match':
        return _normalize_face_match(parsed_response, entity_type, entity_id)
    else:
        raise ValueError(f"Unknown action type: {action}")


def _parse_nested_response(raw_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse double-nested responses where result.body is a JSON string.

    Example input:
    {
        "success": true,
        "action": "validate_nationalid",
        "result": {
            "statusCode": 200,
            "body": "{\"message\": \"...\", \"results\": {...}}"
        }
    }

    Returns the parsed body content.
    """
    if 'result' in raw_response and 'body' in raw_response['result']:
        body = raw_response['result']['body']
        if isinstance(body, str):
            return json.loads(body)
        return body

    # Already parsed or different structure
    return raw_response


def _normalize_document_validation(
    action: str,
    response: Dict[str, Any],
    entity_type: str,
    entity_id: str
) -> Dict[str, Any]:
    """
    Normalize document validation responses (OCR-based).

    Structure:
    {
        "message": "Validation successfull",
        "s3Path": "NationalID/23667272.pdf",
        "results": {
            "keywords_checks": [...],
            "matchResults": {
                "idNumber": {
                    "status": "Matched",
                    "details": {
                        "editdistance": 0,
                        "expected": "23667272",
                        "actual": "23667272",
                        "confidence": 93.71786499023438
                    }
                }
            }
        }
    }
    """
    match_results = response.get('results', {}).get('matchResults', {})
    keywords_checks = response.get('results', {}).get('keywords_checks', [])
    s3_path = response.get('s3Path', '')

    # Extract all confidence scores
    confidence_scores = []
    fields_verified = {}

    for field_name, field_data in match_results.items():
        status = field_data.get('status', 'Unknown')
        details = field_data.get('details', {})
        confidence = details.get('confidence')

        fields_verified[field_name] = {
            'status': status,
            'expected': details.get('expected'),
            'actual': details.get('actual'),
            'edit_distance': details.get('editdistance'),
            'confidence': confidence
        }

        if confidence is not None:
            confidence_scores.append(confidence)

    # Calculate average confidence
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else None

    # Determine overall match status
    all_matched = all(
        field.get('status') == 'Matched'
        for field in fields_verified.values()
    )

    # Check if all keyword checks passed
    all_keywords_passed = all(
        check.get('result', False)
        for check in keywords_checks
    )

    return {
        'verificationType': _action_to_verification_type(action),
        'action': action,
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'VERIFIED' if (all_matched and all_keywords_passed) else 'FAILED',
        'documentPath': s3_path,
        'fieldsVerified': fields_verified,
        'keywordChecks': keywords_checks,
        'averageConfidence': avg_confidence,
        'rawResponse': response,
        'entityType': entity_type,
        'entityId': entity_id
    }


def _normalize_government_verification(
    action: str,
    response: Dict[str, Any],
    entity_type: str,
    entity_id: str
) -> Dict[str, Any]:
    """
    Normalize government verification responses (API-based).

    Structure:
    {
        "message": "Verification Sucessful",
        "results": {
            "idNumber": {
                "status": "Matched",
                "details": {
                    "editdistance": 0,
                    "expected": "32140017",
                    "actual": "32140017"
                }
            },
            "fullNames": {
                "status": "Matched",
                "details": {...}
            }
        }
    }
    """
    results = response.get('results', {})
    message = response.get('message', '')

    # Extract verification results
    fields_verified = {}

    for field_name, field_data in results.items():
        status = field_data.get('status', 'Unknown')
        details = field_data.get('details', {})

        fields_verified[field_name] = {
            'status': status,
            'expected': details.get('expected'),
            'actual': details.get('actual'),
            'edit_distance': details.get('editdistance'),
            'confidence': None  # Government verifications don't provide confidence scores
        }

    # Determine overall match status
    all_matched = all(
        field.get('status') == 'Matched'
        for field in fields_verified.values()
    )

    return {
        'verificationType': _action_to_verification_type(action),
        'action': action,
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'VERIFIED' if all_matched else 'FAILED',
        'message': message,
        'fieldsVerified': fields_verified,
        'averageConfidence': None,  # Not available for government verifications
        'rawResponse': response,
        'entityType': entity_type,
        'entityId': entity_id
    }


def _normalize_background_check(
    response: Dict[str, Any],
    entity_type: str,
    entity_id: str
) -> Dict[str, Any]:
    """
    Normalize background check responses.

    Structure:
    {
        "BestCountryScore": 0.0,
        "BestNameScore": 0.0,
        "EntityScore": 0.0,
        "ReasonListed": "0",
        "entityDetails": [],
        "message": "Background check completed successfully"
    }
    """
    entity_score = response.get('EntityScore', 0.0)
    best_name_score = response.get('BestNameScore', 0.0)
    best_country_score = response.get('BestCountryScore', 0.0)
    reason_listed = response.get('ReasonListed', '0')
    entity_details = response.get('entityDetails', [])
    message = response.get('message', '')

    # Background check passes if no entities found (all scores are 0)
    is_clear = (
        entity_score == 0.0 and
        best_name_score == 0.0 and
        best_country_score == 0.0 and
        reason_listed == '0' and
        len(entity_details) == 0
    )

    return {
        'verificationType': 'background_check',
        'action': 'background_check',
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'CLEAR' if is_clear else 'FLAGGED',
        'message': message,
        'scores': {
            'entityScore': entity_score,
            'bestNameScore': best_name_score,
            'bestCountryScore': best_country_score
        },
        'reasonListed': reason_listed,
        'entityDetails': entity_details,
        'rawResponse': response,
        'entityType': entity_type,
        'entityId': entity_id
    }


def _normalize_face_liveness(
    response: Dict[str, Any],
    entity_type: str,
    entity_id: str
) -> Dict[str, Any]:
    """
    Normalize face liveness responses.

    Structure varies based on implementation.
    """
    # Extract liveness data (structure may vary)
    liveness_score = response.get('livenessScore')
    confidence = response.get('confidence')
    is_live = response.get('isLive', False)
    message = response.get('message', '')

    return {
        'verificationType': 'liveness',
        'action': 'face_liveness',
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'VERIFIED' if is_live else 'FAILED',
        'message': message,
        'livenessScore': liveness_score,
        'confidence': confidence,
        'rawResponse': response,
        'entityType': entity_type,
        'entityId': entity_id
    }

def _normalize_face_match(
    response: Dict[str, Any],
    entity_type: str,
    entity_id: str
) -> Dict[str, Any]:
    """
    Normalize face match responses.

    Extracts comparison scores, overall decision, and manual review flag.
    """
    overall_decision = response.get('overall_decision', 'ERROR')
    comparisons = response.get('comparisons', {})
    lowest_score = response.get('lowest_score')
    iprs_photo_available = response.get('iprs_photo_available', False)
    requires_manual_review = response.get('requires_manual_review', False)

    # Determine status based on decision
    status_map = {
        'AUTO_APPROVED': 'VERIFIED',
        'MANUAL_REVIEW': 'PENDING_REVIEW',
        'AUTO_REJECTED': 'FAILED',
        'PARTIAL_MATCH': 'PENDING_REVIEW',
        'ERROR': 'FAILED',
    }
    status = status_map.get(overall_decision, 'FAILED')

    return {
        'verificationType': 'face_match',
        'action': 'face_match',
        'timestamp': datetime.utcnow().isoformat(),
        'status': status,
        'overallDecision': overall_decision,
        'comparisons': comparisons,
        'lowestScore': lowest_score,
        'iprsPhotoAvailable': iprs_photo_available,
        'requiresManualReview': requires_manual_review,
        'thresholds': response.get('thresholds', {}),
        'rawResponse': response,
        'entityType': entity_type,
        'entityId': entity_id
    }



def _action_to_verification_type(action: str) -> str:
    """
    Map action names to verification type categories.

    Examples:
        validate_nationalid -> national_id_validation
        government_verify_nationalid -> national_id_verification
        validate_passport -> passport_validation
        government_verify_kra -> kra_verification
    """
    mapping = {
        'validate_nationalid': 'national_id_validation',
        'government_verify_nationalid': 'national_id_verification',
        'validate_passport': 'passport_validation',
        'government_verify_passport': 'passport_verification',
        'validate_krapincertificate': 'kra_validation',
        'government_verify_kra': 'kra_verification',
        'validate_cr12': 'cr12_validation',
        'validate_alienid': 'alien_id_validation',
        'government_verify_alienid': 'alien_id_verification',
        'validate_militaryid': 'military_id_validation',
        'background_check': 'background_check',
        'face_liveness': 'liveness',
        'face_match': 'face_match'
    }

    return mapping.get(action, action)


def calculate_overall_verification_status(verifications: Dict[str, Any]) -> str:
    """
    Calculate overall verification status based on all verifications performed.

    Rules:
    - Must have identity verification (national ID OR passport - government verification required)
    - Must have KRA verification (government verification required)
    - Must pass background check
    - Liveness check is OPTIONAL (not required for COMPLETE status)

    Args:
        verifications: Dictionary of verification results

    Returns:
        Overall status: 'COMPLETE', 'PARTIAL', 'FAILED'
    """
    # Check identity verification (national ID OR passport - government verification is key)
    # Note: Document validation is optional, government verification is required
    has_identity_govt_verify = (
        _has_verified('national_id_verification', verifications) or
        _has_verified('passport_verification', verifications)
    )

    # Check KRA verification (government verification is key)
    # Note: Document validation is optional, government verification is required
    has_kra_govt_verify = _has_verified('kra_verification', verifications)

    # Check compliance - background check is required
    has_background_clear = _has_clear('background_check', verifications)

    # Liveness is OPTIONAL - check if present and passed (not required for COMPLETE)
    has_liveness = _has_verified('liveness', verifications)

    # Complete if all REQUIRED checks pass (identity govt verify + KRA govt verify + background clear)
    # Liveness is not required but is checked if present
    if has_identity_govt_verify and has_kra_govt_verify and has_background_clear:
        return 'COMPLETE'

    # Failed if any check explicitly failed
    if _has_failed_checks(verifications):
        return 'FAILED'

    # Otherwise partial (some checks done, not all)
    return 'PARTIAL'


def _has_verified(verification_type: str, verifications: Dict[str, Any]) -> bool:
    """Check if a verification type passed."""
    data = verifications.get(verification_type)
    return data is not None and data.get('status') == 'VERIFIED'


def _has_clear(verification_type: str, verifications: Dict[str, Any]) -> bool:
    """Check if background check is clear."""
    data = verifications.get(verification_type)
    return data is not None and data.get('status') == 'CLEAR'


def _has_failed_checks(verifications: Dict[str, Any]) -> bool:
    """Check if any verification explicitly failed."""
    for verification in verifications.values():
        status = verification.get('status')
        if status in ['FAILED', 'FLAGGED']:
            return True
    return False
