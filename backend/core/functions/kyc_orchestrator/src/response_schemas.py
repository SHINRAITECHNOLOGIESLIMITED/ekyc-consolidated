"""
Standardized Response Structure for Action-Based KYC API
SOW Day 2 Requirement: Consistent response format for all operations

Defines comprehensive response formatting for all KYC actions with:
- Standardized success/error structures
- Action-specific result schemas
- Metadata and debug information
- HTTP status code mapping
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
import json


class ResponseStatus(Enum):
    """Standard response status values."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"
    ERROR = "error"


class StandardResponseBuilder:
    """
    Builds standardized responses for all KYC actions.
    Ensures SOW compliance for consistent API responses.
    """

    @staticmethod
    def build_success_response(
        action: str,
        result: Dict[str, Any],
        request_id: Optional[str] = None,
        processing_time: Optional[float] = None,
        debug_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build a standardized success response.

        Args:
            action: The KYC action that was performed
            result: Action-specific result data
            request_id: Optional request identifier
            processing_time: Processing time in seconds
            debug_info: Debug information (only included if requested)

        Returns:
            Standardized success response
        """
        response = {
            "success": True,
            "action": action,
            "result": result,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "metadata": {
                "processingTime": processing_time,
                "functionInvoked": "kyc_orchestrator",
                "version": "1.0.0"
            }
        }

        if request_id:
            response["metadata"]["requestId"] = request_id

        if debug_info:
            response["debug"] = debug_info

        return response

    @staticmethod
    def build_error_response(
        action: str,
        error: Union[str, Dict[str, Any]],
        error_code: Optional[str] = None,
        request_id: Optional[str] = None,
        debug_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build a standardized error response.

        Args:
            action: The KYC action that failed
            error: Error message or detailed error object
            error_code: Optional error code for categorization
            request_id: Optional request identifier
            debug_info: Debug information for troubleshooting

        Returns:
            Standardized error response
        """
        response = {
            "success": False,
            "action": action,
            "error": error,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "metadata": {
                "functionInvoked": "kyc_orchestrator",
                "version": "1.0.0"
            }
        }

        if error_code:
            response["errorCode"] = error_code

        if request_id:
            response["metadata"]["requestId"] = request_id

        if debug_info:
            response["debug"] = debug_info

        return response

    @staticmethod
    def build_partial_response(
        action: str,
        successful_operations: List[str],
        failed_operations: List[str],
        results: Dict[str, Any],
        errors: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a partial success response for multi-step operations.

        Args:
            action: The KYC action attempted
            successful_operations: List of operations that succeeded
            failed_operations: List of operations that failed
            results: Results from successful operations
            errors: Errors from failed operations
            request_id: Optional request identifier

        Returns:
            Standardized partial response
        """
        response = {
            "success": True,
            "partial": True,
            "action": action,
            "result": {
                "status": "partial_success",
                "successful_operations": successful_operations,
                "failed_operations": failed_operations,
                "results": results,
                "errors": errors,
                "completion_rate": len(successful_operations) / (len(successful_operations) + len(failed_operations))
            },
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "metadata": {
                "functionInvoked": "kyc_orchestrator",
                "version": "1.0.0"
            }
        }

        if request_id:
            response["metadata"]["requestId"] = request_id

        return response


class ActionResultSchemas:
    """
    Defines expected result schemas for each KYC action.
    Ensures consistent structure within action-specific results.
    """

    @staticmethod
    def get_action_result_schemas() -> Dict[str, Dict[str, Any]]:
        """Get result schemas for all supported actions."""
        return {
            "validate_nationalid": {
                "type": "object",
                "properties": {
                    "validation_status": {"type": "string", "enum": ["valid", "invalid", "partial"]},
                    "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "extracted_data": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "id_number": {"type": "string"},
                            "date_of_birth": {"type": "string", "format": "date"},
                            "gender": {"type": "string"},
                            "place_of_birth": {"type": "string"},
                            "nationality": {"type": "string"}
                        }
                    },
                    "validation_checks": {
                        "type": "object",
                        "properties": {
                            "format_valid": {"type": "boolean"},
                            "data_match": {"type": "boolean"},
                            "photo_quality": {"type": "boolean"},
                            "security_features": {"type": "boolean"}
                        }
                    },
                    "processing_details": {
                        "type": "object",
                        "properties": {
                            "document_type": {"type": "string"},
                            "image_quality": {"type": "string"},
                            "processing_time": {"type": "number"}
                        }
                    }
                }
            },

            "validate_passport": {
                "type": "object",
                "properties": {
                    "validation_status": {"type": "string", "enum": ["valid", "invalid", "partial"]},
                    "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "extracted_data": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "passport_number": {"type": "string"},
                            "date_of_birth": {"type": "string", "format": "date"},
                            "nationality": {"type": "string"},
                            "issuing_country": {"type": "string"},
                            "expiry_date": {"type": "string", "format": "date"},
                            "issue_date": {"type": "string", "format": "date"}
                        }
                    },
                    "validation_checks": {
                        "type": "object",
                        "properties": {
                            "format_valid": {"type": "boolean"},
                            "data_match": {"type": "boolean"},
                            "expiry_valid": {"type": "boolean"},
                            "mrz_valid": {"type": "boolean"}
                        }
                    }
                }
            },

            "validate_krapincertificate": {
                "type": "object",
                "properties": {
                    "validation_status": {"type": "string", "enum": ["valid", "invalid", "partial"]},
                    "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "extracted_data": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "pin_number": {"type": "string"},
                            "date_of_birth": {"type": "string", "format": "date"},
                            "id_number": {"type": "string"},
                            "issue_date": {"type": "string", "format": "date"}
                        }
                    },
                    "validation_checks": {
                        "type": "object",
                        "properties": {
                            "format_valid": {"type": "boolean"},
                            "pin_format_valid": {"type": "boolean"},
                            "data_match": {"type": "boolean"}
                        }
                    }
                }
            },

            "validate_cr12": {
                "type": "object",
                "properties": {
                    "validation_status": {"type": "string", "enum": ["valid", "invalid", "partial"]},
                    "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "extracted_data": {
                        "type": "object",
                        "properties": {
                            "company_name": {"type": "string"},
                            "registration_number": {"type": "string"},
                            "incorporation_date": {"type": "string", "format": "date"},
                            "directors": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "id_number": {"type": "string"},
                                        "appointment_date": {"type": "string", "format": "date"}
                                    }
                                }
                            }
                        }
                    },
                    "validation_checks": {
                        "type": "object",
                        "properties": {
                            "format_valid": {"type": "boolean"},
                            "registration_valid": {"type": "boolean"},
                            "data_match": {"type": "boolean"}
                        }
                    }
                }
            },

            "government_verify_nationalid": {
                "type": "object",
                "properties": {
                    "verification_status": {"type": "string", "enum": ["verified", "not_verified", "pending"]},
                    "verification_level": {"type": "string", "enum": ["basic", "standard", "enhanced"]},
                    "match_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "verified_data": {
                        "type": "object",
                        "properties": {
                            "name_match": {"type": "boolean"},
                            "id_number_match": {"type": "boolean"},
                            "date_of_birth_match": {"type": "boolean"},
                            "status": {"type": "string"}
                        }
                    },
                    "government_response": {
                        "type": "object",
                        "properties": {
                            "provider": {"type": "string"},
                            "reference_id": {"type": "string"},
                            "response_time": {"type": "number"}
                        }
                    }
                }
            },

            "background_check": {
                "type": "object",
                "properties": {
                    "check_status": {"type": "string", "enum": ["clear", "flagged", "inconclusive"]},
                    "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                    "checks_performed": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["criminal", "sanctions", "pep", "watchlist"]}
                    },
                    "findings": {
                        "type": "object",
                        "properties": {
                            "criminal_records": {"type": "array", "items": {"type": "object"}},
                            "sanctions_matches": {"type": "array", "items": {"type": "object"}},
                            "pep_matches": {"type": "array", "items": {"type": "object"}},
                            "watchlist_matches": {"type": "array", "items": {"type": "object"}}
                        }
                    },
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "last_updated": {"type": "string", "format": "date-time"}
                            }
                        }
                    }
                }
            },

            "face_liveness": {
                "type": "object",
                "properties": {
                    "liveness_status": {"type": "string", "enum": ["live", "spoof", "inconclusive"]},
                    "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
                    "liveness_type": {"type": "string", "enum": ["passive", "active"]},
                    "analysis_results": {
                        "type": "object",
                        "properties": {
                            "face_detected": {"type": "boolean"},
                            "quality_score": {"type": "number"},
                            "liveness_checks": {
                                "type": "object",
                                "properties": {
                                    "blink_detection": {"type": "boolean"},
                                    "head_movement": {"type": "boolean"},
                                    "depth_analysis": {"type": "boolean"},
                                    "texture_analysis": {"type": "boolean"}
                                }
                            }
                        }
                    }
                }
            },

            "agent_registration": {
                "type": "object",
                "properties": {
                    "registration_status": {"type": "string", "enum": ["approved", "pending", "rejected"]},
                    "agent_id": {"type": "string"},
                    "registration_details": {
                        "type": "object",
                        "properties": {
                            "approval_date": {"type": "string", "format": "date-time"},
                            "license_status": {"type": "string"},
                            "verification_level": {"type": "string"},
                            "permissions": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "required_actions": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },

            "customer_registration": {
                "type": "object",
                "properties": {
                    "registration_status": {"type": "string", "enum": ["approved", "pending", "rejected"]},
                    "customer_id": {"type": "string"},
                    "kyc_level": {"type": "string", "enum": ["basic", "standard", "enhanced"]},
                    "registration_details": {
                        "type": "object",
                        "properties": {
                            "approval_date": {"type": "string", "format": "date-time"},
                            "verification_status": {"type": "string"},
                            "risk_assessment": {"type": "string"},
                            "account_status": {"type": "string"}
                        }
                    },
                    "required_documents": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            },

            "stream_document": {
                "type": "object",
                "properties": {
                    "stream_status": {"type": "string", "enum": ["ready", "streaming", "error"]},
                    "document_info": {
                        "type": "object",
                        "properties": {
                            "document_key": {"type": "string"},
                            "document_type": {"type": "string"},
                            "file_size": {"type": "integer"},
                            "content_type": {"type": "string"}
                        }
                    },
                    "access_details": {
                        "type": "object",
                        "properties": {
                            "presigned_url": {"type": "string", "format": "uri"},
                            "expiry_time": {"type": "string", "format": "date-time"},
                            "download_method": {"type": "string"}
                        }
                    }
                }
            },

            "process_workflow": {
                "type": "object",
                "properties": {
                    "workflow_status": {"type": "string", "enum": ["completed", "partial", "failed"]},
                    "overall_result": {"type": "string"},
                    "step_results": {
                        "type": "object",
                        "description": "Results from each workflow step"
                    },
                    "processing_summary": {
                        "type": "object",
                        "properties": {
                            "total_steps": {"type": "integer"},
                            "completed_steps": {"type": "integer"},
                            "failed_steps": {"type": "integer"},
                            "total_processing_time": {"type": "number"}
                        }
                    }
                }
            }
        }


class HTTPStatusMapper:
    """
    Maps KYC operation results to appropriate HTTP status codes.
    Ensures consistent status code usage across all actions.
    """

    @staticmethod
    def map_result_to_status_code(action: str, result: Dict[str, Any]) -> int:
        """
        Map an action result to appropriate HTTP status code.

        Args:
            action: The KYC action performed
            result: The action result data

        Returns:
            Appropriate HTTP status code
        """
        # Default mapping based on success/failure
        if result.get("success", False):
            if result.get("partial", False):
                return 207  # Multi-Status for partial success
            return 200  # Success

        # Error case mappings
        error = result.get("error", "")
        if isinstance(error, str):
            error_lower = error.lower()
            if "validation" in error_lower or "invalid" in error_lower:
                return 400  # Bad Request
            elif "unauthorized" in error_lower or "authentication" in error_lower:
                return 401  # Unauthorized
            elif "forbidden" in error_lower or "permission" in error_lower:
                return 403  # Forbidden
            elif "not found" in error_lower:
                return 404  # Not Found
            elif "timeout" in error_lower:
                return 408  # Request Timeout
            elif "rate limit" in error_lower:
                return 429  # Too Many Requests

        # Action-specific status codes
        action_specific_codes = {
            "government_verify_nationalid": {
                "verification_pending": 202,  # Accepted (processing)
                "verification_failed": 422   # Unprocessable Entity
            },
            "background_check": {
                "check_pending": 202,
                "sources_unavailable": 503   # Service Unavailable
            },
            "face_liveness": {
                "analysis_pending": 202,
                "poor_image_quality": 422
            }
        }

        if action in action_specific_codes:
            status_key = result.get("status", "")
            if status_key in action_specific_codes[action]:
                return action_specific_codes[action][status_key]

        # Default to 500 for unhandled errors
        return 500


def create_standardized_response(
    action: str,
    success: bool,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[Union[str, Dict[str, Any]]] = None,
    partial: bool = False,
    request_id: Optional[str] = None,
    processing_time: Optional[float] = None,
    debug_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Factory function to create standardized responses for any KYC action.

    Args:
        action: The KYC action being responded to
        success: Whether the operation was successful
        result: Result data (if successful)
        error: Error information (if failed)
        partial: Whether this is a partial success
        request_id: Optional request identifier
        processing_time: Processing time in seconds
        debug_info: Optional debug information

    Returns:
        Standardized response dictionary
    """
    builder = StandardResponseBuilder()

    if success and not partial:
        return builder.build_success_response(
            action, result or {}, request_id, processing_time, debug_info
        )
    elif success and partial:
        # For partial responses, extract the required fields from result
        successful_ops = result.get("successful_operations", [])
        failed_ops = result.get("failed_operations", [])
        results = result.get("results", {})
        errors = result.get("errors", {})

        return builder.build_partial_response(
            action, successful_ops, failed_ops, results, errors, request_id
        )
    else:
        return builder.build_error_response(
            action, error or "Unknown error", None, request_id, debug_info
        )