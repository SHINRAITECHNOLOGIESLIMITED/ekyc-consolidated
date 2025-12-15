"""
Standardized Payload Format for Action-Based KYC API
SOW Day 2 Requirement: Unified request/response format for all 10+ operations

Defines the structure for the new single /kyc endpoint with action parameters.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import json


class KYCAction(Enum):
    """Enumeration of all supported KYC actions."""
    # Document validation actions
    VALIDATE_NATIONALID = "validate_nationalid"
    VALIDATE_PASSPORT = "validate_passport"
    VALIDATE_KRA = "validate_krapincertificate"
    VALIDATE_CR12 = "validate_cr12"

    # Government verification actions
    GOVERNMENT_VERIFY_NATIONALID = "government_verify_nationalid"
    GOVERNMENT_VERIFY_PASSPORT = "government_verify_passport"
    GOVERNMENT_VERIFY_KRA = "government_verify_kra"

    # Other KYC operations
    BACKGROUND_CHECK = "background_check"
    FACE_LIVENESS = "face_liveness"
    AGENT_REGISTRATION = "agent_registration"
    CUSTOMER_REGISTRATION = "customer_registration"

    # Supporting operations
    STREAM_DOCUMENT = "stream_document"
    GET_CERTIFICATE = "get_certificate"
    GENERATE_CERTIFICATE = "generate_certificate"
    GET_KYC_STATUS = "get_kyc_status"

    # Legacy workflow (backward compatibility)
    PROCESS_WORKFLOW = "process_workflow"

    @classmethod
    def get_all_actions(cls) -> List[str]:
        """Get list of all valid action strings."""
        return [action.value for action in cls]

    @classmethod
    def is_valid_action(cls, action: str) -> bool:
        """Check if an action string is valid."""
        return action in cls.get_all_actions()


class PayloadValidator:
    """
    Validates request payloads for the standardized KYC API format.
    """

    @staticmethod
    def get_base_request_schema() -> Dict[str, Any]:
        """
        Get the base schema for all KYC requests.
        SOW requirement: Single /kyc endpoint with action parameter.
        """
        return {
            "type": "object",
            "required": ["action", "data"],
            "properties": {
                "action": {
                    "type": "string",
                    "enum": KYCAction.get_all_actions(),
                    "description": "The KYC action to perform"
                },
                "data": {
                    "type": "object",
                    "description": "Action-specific data payload"
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional metadata for the request",
                    "properties": {
                        "requestId": {"type": "string"},
                        "clientId": {"type": "string"},
                        "sessionId": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "userAgent": {"type": "string"},
                        "ipAddress": {"type": "string"}
                    }
                },
                "options": {
                    "type": "object",
                    "description": "Optional processing options",
                    "properties": {
                        "async": {"type": "boolean", "default": False},
                        "timeout": {"type": "integer", "minimum": 1, "maximum": 900},
                        "retryOnFailure": {"type": "boolean", "default": True},
                        "includeDebugInfo": {"type": "boolean", "default": False}
                    }
                }
            },
            "additionalProperties": False
        }

    @staticmethod
    def get_base_response_schema() -> Dict[str, Any]:
        """
        Get the base schema for all KYC responses.
        SOW requirement: Consistent response structure.
        """
        return {
            "type": "object",
            "required": ["success", "action", "timestamp"],
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the action completed successfully"
                },
                "action": {
                    "type": "string",
                    "enum": KYCAction.get_all_actions(),
                    "description": "The action that was performed"
                },
                "result": {
                    "type": "object",
                    "description": "Action-specific result data"
                },
                "error": {
                    "type": ["string", "object"],
                    "description": "Error information if success is false"
                },
                "timestamp": {
                    "type": "string",
                    "format": "date-time",
                    "description": "ISO timestamp of the response"
                },
                "metadata": {
                    "type": "object",
                    "description": "Response metadata",
                    "properties": {
                        "requestId": {"type": "string"},
                        "processingTime": {"type": "number"},
                        "functionInvoked": {"type": "string"},
                        "version": {"type": "string"}
                    }
                },
                "debug": {
                    "type": "object",
                    "description": "Debug information (only included if requested)"
                }
            },
            "additionalProperties": False
        }

    @staticmethod
    def get_action_data_schemas() -> Dict[str, Dict[str, Any]]:
        """
        Get specific data schemas for each action type.
        These define what should be in the 'data' field for each action.
        """
        return {
            "validate_nationalid": {
                "type": "object",
                "required": ["nationalIdUrl", "personalData"],
                "properties": {
                    "nationalIdUrl": {
                        "type": "string",
                        "format": "uri",
                        "description": "S3 URL or public URL of the national ID document"
                    },
                    "personalData": {
                        "type": "object",
                        "required": ["name", "idNumber"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "idNumber": {"type": "string", "minLength": 1},
                            "dateOfBirth": {"type": "string", "format": "date"},
                            "gender": {"type": "string", "enum": ["Male", "Female"]},
                            "placeOfBirth": {"type": "string"},
                            "nationality": {"type": "string"}
                        }
                    },
                    "validationOptions": {
                        "type": "object",
                        "properties": {
                            "extractText": {"type": "boolean", "default": True},
                            "validatePhoto": {"type": "boolean", "default": True},
                            "checkSecurity": {"type": "boolean", "default": True}
                        }
                    }
                }
            },

            "validate_passport": {
                "type": "object",
                "required": ["passportUrl", "personalData"],
                "properties": {
                    "passportUrl": {
                        "type": "string",
                        "format": "uri",
                        "description": "S3 URL or public URL of the passport document"
                    },
                    "personalData": {
                        "type": "object",
                        "required": ["name", "passportNumber"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "passportNumber": {"type": "string", "minLength": 1},
                            "dateOfBirth": {"type": "string", "format": "date"},
                            "nationality": {"type": "string"},
                            "issuingCountry": {"type": "string"},
                            "expiryDate": {"type": "string", "format": "date"}
                        }
                    }
                }
            },

            "validate_krapincertificate": {
                "type": "object",
                "required": ["kraUrl", "personalData"],
                "properties": {
                    "kraUrl": {
                        "type": "string",
                        "format": "uri",
                        "description": "S3 URL or public URL of the KRA PIN certificate"
                    },
                    "personalData": {
                        "type": "object",
                        "required": ["name", "pinNumber"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "pinNumber": {"type": "string", "pattern": "^[A-Z][0-9]{9}[A-Z]$"},
                            "dateOfBirth": {"type": "string", "format": "date"},
                            "idNumber": {"type": "string"}
                        }
                    }
                }
            },

            "validate_cr12": {
                "type": "object",
                "required": ["cr12Url", "companyData"],
                "properties": {
                    "cr12Url": {
                        "type": "string",
                        "format": "uri",
                        "description": "S3 URL or public URL of the CR12 certificate"
                    },
                    "companyData": {
                        "type": "object",
                        "required": ["companyName", "registrationNumber"],
                        "properties": {
                            "companyName": {"type": "string", "minLength": 1},
                            "registrationNumber": {"type": "string", "minLength": 1},
                            "incorporationDate": {"type": "string", "format": "date"},
                            "directors": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "idNumber": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            },

            "government_verify_nationalid": {
                "type": "object",
                "required": ["personalData"],
                "properties": {
                    "personalData": {
                        "type": "object",
                        "required": ["name", "idNumber"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "idNumber": {"type": "string", "minLength": 1},
                            "dateOfBirth": {"type": "string", "format": "date"}
                        }
                    },
                    "verificationLevel": {
                        "type": "string",
                        "enum": ["basic", "standard", "enhanced"],
                        "default": "standard"
                    }
                }
            },

            "background_check": {
                "type": "object",
                "required": ["personalData"],
                "properties": {
                    "personalData": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "dateOfBirth": {"type": "string", "format": "date"},
                            "nationality": {"type": "string"},
                            "aliases": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    },
                    "checkTypes": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["criminal", "sanctions", "pep", "watchlist"]
                        },
                        "default": ["criminal", "sanctions", "pep"]
                    }
                }
            },

            "face_liveness": {
                "type": "object",
                "required": ["faceImageUrl"],
                "properties": {
                    "faceImageUrl": {
                        "type": "string",
                        "format": "uri",
                        "description": "S3 URL or public URL of the face image"
                    },
                    "sessionId": {"type": "string"},
                    "livenessType": {
                        "type": "string",
                        "enum": ["passive", "active"],
                        "default": "passive"
                    }
                }
            },

            "agent_registration": {
                "type": "object",
                "required": ["agentData"],
                "properties": {
                    "agentData": {
                        "type": "object",
                        "required": ["name", "email", "agentType"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "email": {"type": "string", "format": "email"},
                            "agentType": {"type": "string", "enum": ["individual", "business"]},
                            "phoneNumber": {"type": "string"},
                            "licenseNumber": {"type": "string"},
                            "companyName": {"type": "string"},
                            "address": {
                                "type": "object",
                                "properties": {
                                    "street": {"type": "string"},
                                    "city": {"type": "string"},
                                    "country": {"type": "string"},
                                    "postalCode": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },

            "customer_registration": {
                "type": "object",
                "required": ["customerData"],
                "properties": {
                    "customerData": {
                        "type": "object",
                        "required": ["name", "email"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "email": {"type": "string", "format": "email"},
                            "phoneNumber": {"type": "string"},
                            "dateOfBirth": {"type": "string", "format": "date"},
                            "nationality": {"type": "string"},
                            "address": {
                                "type": "object",
                                "properties": {
                                    "street": {"type": "string"},
                                    "city": {"type": "string"},
                                    "country": {"type": "string"},
                                    "postalCode": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },

            "stream_document": {
                "type": "object",
                "required": ["bucketType", "documentKey"],
                "properties": {
                    "bucketType": {
                        "type": "string",
                        "enum": ["kyc_documents", "liveness_captures"],
                        "description": "Type of S3 bucket to stream from"
                    },
                    "documentKey": {
                        "type": "string",
                        "minLength": 1,
                        "description": "S3 object key for the document"
                    },
                    "downloadOptions": {
                        "type": "object",
                        "properties": {
                            "presignedUrl": {"type": "boolean", "default": True},
                            "expiryMinutes": {"type": "integer", "minimum": 1, "maximum": 60, "default": 15}
                        }
                    }
                }
            },

            "get_certificate": {
                "type": "object",
                "description": "Retrieve existing KYC certificate by entity ID",
                "properties": {
                    "customerId": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Customer ID to retrieve certificate for"
                    },
                    "agentId": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Agent ID to retrieve certificate for"
                    }
                },
                "oneOf": [
                    {"required": ["customerId"]},
                    {"required": ["agentId"]}
                ]
            },

            "generate_certificate": {
                "type": "object",
                "description": "Generate KYC certificate from stored verification results (simplified approach)",
                "properties": {
                    "customerId": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Customer ID to generate certificate for"
                    },
                    "agentId": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Agent ID to generate certificate for"
                    },
                    "idNumber": {
                        "type": "string",
                        "minLength": 1,
                        "description": "National ID number (natural identifier)"
                    },
                    "passportNumber": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Passport number (natural identifier)"
                    },
                    "businessNumber": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Business registration number (natural identifier)"
                    },
                    "certificateType": {
                        "type": "string",
                        "enum": ["customer", "individual_agent", "business_agent"],
                        "description": "Type of certificate (required for agents)"
                    }
                },
                "oneOf": [
                    {"required": ["customerId"]},
                    {"required": ["agentId"]},
                    {"required": ["idNumber"]},
                    {"required": ["passportNumber"]},
                    {"required": ["businessNumber"]}
                ]
            },

            "get_kyc_status": {
                "type": "object",
                "description": "Retrieve KYC verification status and completed verifications",
                "properties": {
                    "customerId": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Customer ID to get status for"
                    },
                    "agentId": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Agent ID to get status for"
                    },
                    "idNumber": {
                        "type": "string",
                        "minLength": 1,
                        "description": "National ID number (natural identifier)"
                    },
                    "passportNumber": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Passport number (natural identifier)"
                    },
                    "businessNumber": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Business registration number (natural identifier)"
                    }
                },
                "oneOf": [
                    {"required": ["customerId"]},
                    {"required": ["agentId"]},
                    {"required": ["idNumber"]},
                    {"required": ["passportNumber"]},
                    {"required": ["businessNumber"]}
                ]
            },

            "process_workflow": {
                "type": "object",
                "description": "Legacy workflow format for backward compatibility",
                "required": ["processType", "personalData", "documents"],
                "properties": {
                    "processType": {
                        "type": "string",
                        "enum": ["customer", "individual_agent", "business_agent"]
                    },
                    "personalData": {"type": "object"},
                    "documents": {"type": "object"},
                    "options": {"type": "object"}
                }
            }
        }

    @staticmethod
    def validate_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a KYC request against the standardized format.

        Args:
            request_data: The request payload to validate

        Returns:
            Validation result with success/error information
        """
        try:
            # Check base structure
            if not isinstance(request_data, dict):
                return {
                    "valid": False,
                    "errors": ["Request must be a JSON object"]
                }

            # Check required fields
            if "action" not in request_data:
                return {
                    "valid": False,
                    "errors": ["Missing required field: action"]
                }

            if "data" not in request_data:
                return {
                    "valid": False,
                    "errors": ["Missing required field: data"]
                }

            # Validate action
            action = request_data["action"]
            if not KYCAction.is_valid_action(action):
                return {
                    "valid": False,
                    "errors": [f"Invalid action: {action}. Valid actions: {KYCAction.get_all_actions()}"]
                }

            # TODO: Add JSON schema validation for action-specific data
            # This would use jsonschema library to validate the data field
            # against the action-specific schema

            return {
                "valid": True,
                "action": action,
                "message": "Request validation successful"
            }

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }


class ResponseFormatter:
    """
    Formats responses according to the standardized KYC API format.
    """

    @staticmethod
    def format_success_response(action: str, result: Any,
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format a successful action response.

        Args:
            action: The action that was performed
            result: The action result data
            metadata: Optional metadata

        Returns:
            Standardized success response
        """
        from datetime import datetime

        response = {
            "success": True,
            "action": action,
            "result": result,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }

        if metadata:
            response["metadata"] = metadata

        return response

    @staticmethod
    def format_error_response(action: str, error: Any,
                            metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format an error response.

        Args:
            action: The action that failed
            error: The error information
            metadata: Optional metadata

        Returns:
            Standardized error response
        """
        from datetime import datetime

        response = {
            "success": False,
            "action": action,
            "error": error,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }

        if metadata:
            response["metadata"] = metadata

        return response