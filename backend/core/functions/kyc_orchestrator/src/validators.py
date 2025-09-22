"""
Input validation schemas and functions for KYC orchestrator.
Follows existing validation patterns from other functions.
"""

import json
from typing import Dict, Any, List
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.validation import validate

logger = Logger()


def validate_kyc_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the consolidated KYC request schema.

    Args:
        data: Request body data

    Returns:
        Dict containing validation result and any errors
    """

    # Base schema for consolidated KYC request
    base_schema = {
        "type": "object",
        "properties": {
            "processType": {
                "type": "string",
                "enum": ["customer", "individual_agent", "business_agent"]
            },
            "personalData": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "idNumber": {"type": "string"},
                    "pinNumber": {"type": "string"},
                    "dateOfBirth": {"type": "string", "format": "date"},
                    "gender": {"type": "string", "enum": ["Male", "Female"]}
                },
                "required": ["name", "idNumber", "pinNumber", "dateOfBirth"],
                "additionalProperties": False
            },
            "documents": {
                "type": "object",
                "properties": {
                    "nationalIdUrl": {"type": "string", "format": "uri"},
                    "passportUrl": {"type": "string", "format": "uri"},
                    "kraUrl": {"type": "string", "format": "uri"},
                    "passportPhotoUrl": {"type": "string", "format": "uri"},
                    "companyCertificateUrl": {"type": "string", "format": "uri"}
                },
                "additionalProperties": False
            },
            "options": {
                "type": "object",
                "properties": {
                    "includeFaceLiveness": {"type": "boolean"},
                    "includeBackgroundCheck": {"type": "boolean"},
                    "generateCertificate": {"type": "boolean"},
                    "skipValidationErrors": {"type": "boolean"}
                },
                "additionalProperties": False
            },
            "beneficiaries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "idNumber": {"type": "string"},
                        "relationship": {"type": "string"},
                        "gender": {"type": "string", "enum": ["Male", "Female"]},
                        "dateOfBirth": {"type": "string", "format": "date"}
                    },
                    "required": ["idNumber", "relationship", "gender", "dateOfBirth"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["processType", "personalData", "documents"],
        "additionalProperties": False
    }

    try:
        # Validate base schema
        validate(schema=base_schema, event=data)

        # Process-type specific validation
        process_type = data.get("processType")
        validation_errors = []

        # Validate process type manually (in case schema validation is mocked)
        valid_process_types = ["customer", "individual_agent", "business_agent"]
        if process_type not in valid_process_types:
            validation_errors.append(f"Invalid processType: {process_type}. Must be one of: {', '.join(valid_process_types)}")

        if process_type == "customer":
            validation_errors.extend(validate_customer_specific(data))
        elif process_type == "individual_agent":
            validation_errors.extend(validate_individual_agent_specific(data))
        elif process_type == "business_agent":
            validation_errors.extend(validate_business_agent_specific(data))

        if validation_errors:
            return {
                "valid": False,
                "errors": validation_errors
            }

        return {
            "valid": True,
            "errors": []
        }

    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return {
            "valid": False,
            "errors": [f"Schema validation failed: {str(e)}"]
        }


def validate_customer_specific(data: Dict[str, Any]) -> List[str]:
    """
    Customer-specific validation rules.
    """
    errors = []
    documents = data.get("documents", {})
    personal_data = data.get("personalData", {})

    # Customer requires national ID or passport
    if not documents.get("nationalIdUrl") and not documents.get("passportUrl"):
        errors.append("Customer registration requires either nationalIdUrl or passportUrl")

    # Customer requires passport photo
    if not documents.get("passportPhotoUrl"):
        errors.append("Customer registration requires passportPhotoUrl")

    # Customer requires KRA document
    if not documents.get("kraUrl"):
        errors.append("Customer registration requires kraUrl")

    # Customer requires gender
    if not personal_data.get("gender"):
        errors.append("Customer registration requires gender in personalData")

    return errors


def validate_individual_agent_specific(data: Dict[str, Any]) -> List[str]:
    """
    Individual agent-specific validation rules.
    """
    errors = []
    documents = data.get("documents", {})
    personal_data = data.get("personalData", {})

    # Individual agent requires national ID
    if not documents.get("nationalIdUrl"):
        errors.append("Individual agent registration requires nationalIdUrl")

    # Individual agent requires passport photo
    if not documents.get("passportPhotoUrl"):
        errors.append("Individual agent registration requires passportPhotoUrl")

    # Individual agent requires gender
    if not personal_data.get("gender"):
        errors.append("Individual agent registration requires gender in personalData")

    return errors


def validate_business_agent_specific(data: Dict[str, Any]) -> List[str]:
    """
    Business agent-specific validation rules.
    """
    errors = []
    documents = data.get("documents", {})
    personal_data = data.get("personalData", {})

    # Business agent requires company certificate
    if not documents.get("companyCertificateUrl"):
        errors.append("Business agent registration requires companyCertificateUrl")

    # Business agent requires passport photo
    if not documents.get("passportPhotoUrl"):
        errors.append("Business agent registration requires passportPhotoUrl")

    # Business agent requires business number in personalData
    if not personal_data.get("businessNumber"):
        errors.append("Business agent registration requires businessNumber in personalData")

    return errors


def validate_document_urls(documents: Dict[str, str]) -> List[str]:
    """
    Validates document URLs format and accessibility.
    """
    errors = []

    for doc_type, url in documents.items():
        if url and not url.startswith(('http://', 'https://')):
            errors.append(f"Invalid URL format for {doc_type}: {url}")

    return errors


def validate_date_format(date_string: str, field_name: str) -> List[str]:
    """
    Validates date format (YYYY-MM-DD).
    """
    errors = []

    try:
        from datetime import datetime
        datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        errors.append(f"Invalid date format for {field_name}. Expected YYYY-MM-DD format.")

    return errors