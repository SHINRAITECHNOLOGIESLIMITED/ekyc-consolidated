import io
import json
import os
from io import BytesIO

import boto3
import requests
from PIL import Image
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate
from botocore.exceptions import ClientError
from reportlab.pdfgen import canvas
from datetime import datetime

from portal import Portal, DOCUMENT_TYPE

CERTIFICATION_BUCKET_NAME = os.environ.get('CERTIFICATION_BUCKET_NAME', None)
assert CERTIFICATION_BUCKET_NAME is not None, "CERTIFICATION_BUCKET_NAME is not set"

logger = Logger()
tracer = Tracer()
portal = Portal()
s3_client = boto3.client('s3')


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    """
    Lambda handler for KYC Certification creation

    MANUAL REVIEW WORKFLOW (for CRM Team):
    ========================================
    When a KYC operation fails after retries, the state machine flags the record in DynamoDB with:
    - kycStatus: "Manual Review Required"
    - manualReviewRequired: true
    - failedStep: <step that failed>
    - failureReason: <error details>
    - failedAt: <timestamp>

    After manual review and approval, CRM team should call the appropriate endpoint:

    1. Customer Registration:
       POST /certification/customer_registration
       Body: { registration, nationalIdValidation, idVerification, taxPayerVerification, backgroundCheck }

    2. Individual Agent Registration:
       POST /certification/individual_agent_registration
       Body: { registration, nationalIdValidation, idVerification, taxPayerVerification, backgroundCheck }

    3. Business Agent Registration:
       POST /certification/business_agent_registration
       Body: { registration, cr12Validation }

    Note: All verification data must be provided. Retrieve from DynamoDB or re-run failed steps manually.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')
    path = event.get('path')

    if http_method == 'POST':
        try:
            data = event.get('body', {})
            # check if data is dict - if its a string convert to dict
            while isinstance(data, str):
                data = json.loads(data)
            logger.info(f"Request Data (body): {data}")
            match path:
                case '/certification/customer_registration':
                    return create_customer_certificate(data)
                case '/certification/individual_agent_registration':
                    return create_individual_agent_certificate(data)
                case '/certification/business_agent_registration':
                    return create_business_agent_certificate(data)
                case _:
                    return make_response(404, {'message': 'Path Not Found'})
        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON body")
            return make_response(400, {'message': 'Invalid JSON body', 'error': str(e)})
        except Exception as e:
            logger.error(
                f"An unexpected error occurred in lambda_handler: {e}")
            return make_response(500, {'message': 'Internal Server Error', 'error': str(e)})
    else:
        logger.error('Method Not Allowed - received {http_method}')
        return make_response(405, {'message': 'Method Not Allowed', 'error': 'Method Not Allowed'})


def create_customer_certificate(data):
    # Define schema for validation
    schema = {"type": "object",
              "properties": {
                  "registration": {
                      "type": "object",
                      "properties": {
                          "agentType": {"type": "string"},
                          "name": {"type": "string"},
                          "pinNumber": {"type": "string"},
                          "idNumber": {"type": "string"},
                          "gender": {"type": "string"},
                          "passportPhotoUrl": {"type": "string"},
                          "nationalIdCardUrl": {"type": "string"},
                          "dateOfBirth": {"type": "string"},
                          "kycStatus": {"type": "string"},
                          "customerId": {"type": "string"}
                      },
                      "required": ["name", "idNumber"]
                  },
                  "nationalIdValidation": {
                      "type": "object",
                      "properties": {
                          "message": {"type": "string"},
                          "error": {"type": "string"},
                          "results": {"type": "object"}
                      },
                      "required": ["message"]
                  },
                  "idVerification": {
                      "type": "object",
                      "properties": {
                          "message": {"type": "string"},
                          "error": {"type": "string"},
                          "results": {"type": "object"}
                      },
                      "required": ["message"]
                  },
                  "taxPayerVerification": {
                      "type": "object",
                      "properties": {
                          "message": {"type": "string"},
                          "error": {"type": "string"},
                          "results": {"type": "object"}
                      },
                      "required": ["message"]
                  },
                  "backgroundCheck": {
                      "type": "object",
                      "properties": {
                          "message": {"type": "string"},
                          "error": {"type": "string"},
                          "BestCountryScore": {"type": ["number", "integer"]},
                          "BestNameScore": {"type": ["number", "integer"]},
                          "EntityScore": {"type": ["number", "integer"]},
                          "ReasonListed": {"type": "string"},
                          "entityDetails": {"type": "array"}
                      },
                      "required": ["message"]
                  }
              },
              "required": ["registration", "nationalIdValidation", "idVerification", "taxPayerVerification", "backgroundCheck"]
              }

    try:
        # Validate input data against schema
        validate(event=data, schema=schema)

        # Extract required data from the input
        registration = data['registration']
        id_validation = data['nationalIdValidation']
        id_verification = data['idVerification']
        tax_verification = data['taxPayerVerification']
        background_check = data['backgroundCheck']
        identifier = registration["customerId"]
        # Create PDF certificate
        pdf_buffer = generate_kyc_certificate("Customer", identifier,
                                              registration, id_validation, id_verification, tax_verification, background_check)

        # Generate S3 path for the certificate
        id_number = registration['idNumber']
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        s3_key = f"customer_ekyc_certificates/{id_number}/{identifier}_{timestamp}_certificate.pdf"

        # Upload to S3
        s3_client.put_object(
            Bucket=CERTIFICATION_BUCKET_NAME,
            Key=s3_key,
            Body=pdf_buffer.getvalue(),
            ContentType='application/pdf'
        )

        return make_response(200, {
            'message': 'KYC Certificate created successfully',
            's3Path': s3_key
        })
    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error: {e}")
        return make_response(400, {'message': 'Invalid input data', 'error': str(e)})
    except Exception as e:
        logger.error(f"Error creating KYC certificate: {e}")
        return make_response(500, {'message': 'Failed to create KYC certificate', 'error': str(e)})


def create_individual_agent_certificate(data):
    # Define schema for validation
    schema = {
        "type": "object",
        "properties": {
            "registration": {
                "type": "object",
                "properties": {
                    "agentType": {"type": "string"},
                    "name": {"type": "string"},
                    "pinNumber": {"type": "string"},
                    "idNumber": {"type": "string"},
                    "gender": {"type": "string"},
                    "passportPhotoUrl": {"type": "string"},
                    "nationalIdCardUrl": {"type": "string"},
                    "dateOfBirth": {"type": "string"},
                    "kycStatus": {"type": "string"},
                    "agentId": {"type": "string"}
                },
                "required": ["name", "idNumber"]
            },
            "nationalIdValidation": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                    "results": {"type": "object"}
                },
                "required": ["message"]
            },
            "idVerification": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                    "results": {"type": "object"}
                },
                "required": ["message"]
            },
            "taxPayerVerification": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                    "results": {"type": "object"}
                },
                "required": ["message"]
            },
            "backgroundCheck": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                    "BestCountryScore": {"type": ["number", "integer"]},
                    "BestNameScore": {"type": ["number", "integer"]},
                    "EntityScore": {"type": ["number", "integer"]},
                    "ReasonListed": {"type": "string"},
                    "entityDetails": {"type": "array"}
                },
                "required": ["message"]
            }
        },
        "required": ["registration", "nationalIdValidation", "idVerification", "taxPayerVerification", "backgroundCheck"]
    }

    try:
        # Validate input data against schema
        validate(event=data, schema=schema)

        # Extract required data from the input
        registration = data['registration']
        id_validation = data['nationalIdValidation']
        id_verification = data['idVerification']
        tax_verification = data['taxPayerVerification']
        background_check = data['backgroundCheck']
        identifier = registration["agentId"]
        # Create PDF certificate
        pdf_buffer = generate_kyc_certificate("Individual Agent", identifier,
                                              registration, id_validation, id_verification, tax_verification, background_check)

        # Generate S3 path for the certificate
        id_number = registration['idNumber']
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        s3_key = f"individual_agents_ekyc_certificates/{id_number}/{identifier}_{timestamp}_certificate.pdf"

        # Upload to S3
        s3_client.put_object(
            Bucket=CERTIFICATION_BUCKET_NAME,
            Key=s3_key,
            Body=pdf_buffer.getvalue(),
            ContentType='application/pdf'
        )

        return make_response(200, {
            'message': 'KYC Certificate created successfully',
            's3Path': s3_key
        })
    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error: {e}")
        return make_response(400, {'message': 'Invalid input data', 'error': str(e)})
    except Exception as e:
        logger.error(f"Error creating KYC certificate: {e}")
        return make_response(500, {'message': 'Failed to create KYC certificate', 'error': str(e)})


def create_business_agent_certificate(data):
    # Define schema for validation
    schema = {
        "type": "object",
        "properties": {
            "registration": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "businessNumber": {"type": "string"},
                    "pinNumber": {"type": "string"}
                },
                "required": ["name", "businessNumber"]
            },
            "cr12Validation": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "error": {"type": "string"},
                    "results": {"type": "object"}
                },
                "required": ["message"]
            },

        },
        "required": ["registration", "cr12Validation"]
    }

    try:
        # Validate input data against schema
        validate(event=data, schema=schema)

        # Extract required data from the input
        registration = data['registration']
        cr12Validation = data['cr12Validation']
        identifier = registration["agentId"]
        # Create PDF certificate
        pdf_buffer = generate_business_kyc_certificate("Business Agent", identifier,
                                                       registration, cr12Validation)

        # Generate S3 path for the certificate
        businessNumber = registration['businessNumber']
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        s3_key = f"business_agents_ekyc_certificates/{businessNumber}/{identifier}_{timestamp}_certificate.pdf"

        # Upload to S3
        s3_client.put_object(
            Bucket=CERTIFICATION_BUCKET_NAME,
            Key=s3_key,
            Body=pdf_buffer.getvalue(),
            ContentType='application/pdf'
        )

        return make_response(200, {
            'message': 'KYC Certificate created successfully',
            's3Path': s3_key
        })
    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error: {e}")
        return make_response(400, {'message': 'Invalid input data', 'error': str(e)})
    except Exception as e:
        logger.error(f"Error creating KYC certificate: {e}")
        return make_response(500, {'message': 'Failed to create KYC certificate', 'error': str(e)})


def generate_kyc_certificate(certificateType, identifier, registration, id_validation, id_verification, tax_verification, background_check):
    """
    Generate a PDF KYC certificate based on verification results
    """
    try:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        try:
            # Set up the document
            pdf.setTitle(f"{certificateType} eKYC Certificate")

            # Add header
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawCentredString(300, 770, "KYC VERIFICATION CERTIFICATE")
            pdf.setFont("Helvetica", 12)
            pdf.drawCentredString(
                300, 750, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"Error setting up PDF document- Creating Title: {e}")
            #raise Exception("Failed to set up PDF document")
        try:
            # Add customer information
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(50, 700, f"{certificateType} Information")
            pdf.setFont("Helvetica", 12)

            y_position = 680
            pdf.drawString(
                70, y_position, f"{certificateType} Identifier: {identifier}")
            y_position -= 20
            pdf.drawString(
                70, y_position, f"Name: {registration.get('name', 'N/A')}")
            y_position -= 20
            pdf.drawString(
                70, y_position, f"ID Number: {registration.get('idNumber', 'N/A')}")
            y_position -= 20
            pdf.drawString(
                70, y_position, f"PIN Number: {registration.get('pinNumber', 'N/A')}")
            y_position -= 20
            if 'gender' in registration:
                pdf.drawString(
                    70, y_position, f"Gender: {registration.get('gender', 'N/A')}")
                y_position -= 20
            pdf.drawString(
                70, y_position, f"Date of Birth: {registration.get('dateOfBirth', 'N/A')}")
        except Exception as e:
            logger.error(f"Error adding customer information: {e}")
            #raise Exception("Failed to add customer information to PDF")
        # Add verification results
        y_position -= 40
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "Verification Results")
        pdf.setFont("Helvetica", 12)
        try:
        
            # National ID validation
            y_position -= 30
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(70, y_position, "National ID Validation:")
            pdf.setFont("Helvetica", 12)
            y_position -= 20
            pdf.drawString(
                90, y_position, f"Status: {id_validation.get('message', 'N/A')}")
            if 'error' in id_validation:
                y_position -= 20
                error_text = f"Error: {id_validation.get('error', 'N/A')}"
                y_position = wrap_text(pdf, error_text, 90, y_position, 450)
            if 'results' in id_validation:
                id_results = id_validation.get('results', {})
                checks = id_results.get('checks', {})
                for check in checks:
                    y_position -= 20
                    pdf.drawString(
                        90, y_position, f"{check}: {'Ok' if checks['result'] else 'Nok'}")
                id_val_results = id_results.get('matchResults', {})
                for key, value in id_val_results.items():
                    y_position -= 20
                    pdf.drawString(
                        90, y_position, f"{key}: {get_verification_status(value) if isinstance(value, dict) else str(value)}")
        except Exception as e:
            logger.error(f"Error adding National ID validation: {e}")
            #raise Exception("Failed to add National ID validation to PDF")
        try:
            # ID verification
            y_position -= 30
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(70, y_position, "ID Verification:")
            pdf.setFont("Helvetica", 12)
            if 'error' in id_verification:
                y_position -= 20
                error_text = f"Error: {id_verification.get('error', 'N/A')}"
                y_position = wrap_text(pdf, error_text, 90, y_position, 450)
            if 'results' in id_verification:
                id_results = id_verification.get('results', {})
                y_position -= 20
                pdf.drawString(
                    90, y_position, f"ID Number: {get_verification_status(id_results.get('idNumber', {}))}")
                y_position -= 20
                pdf.drawString(
                    90, y_position, f"Full Names: {get_verification_status(id_results.get('fullNames', {}))}")
                y_position -= 20
                pdf.drawString(
                    90, y_position, f"Date of Birth: {get_verification_status(id_results.get('dateOfBirth', {}))}")
                y_position -= 20
                pdf.drawString(
                    90, y_position, f"Gender: {get_verification_status(id_results.get('gender', {}))}")
        except Exception as e:
            logger.error(f"Error adding ID verification: {e}")
            #raise Exception("Failed to add ID verification to PDF")
        try:
            # Tax verification
            y_position -= 30
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(70, y_position, "Tax Verification:")
            pdf.setFont("Helvetica", 12)
            if 'error' in tax_verification:
                y_position -= 20
                error_text = f"Error: {tax_verification.get('error', 'N/A')}"
                y_position = wrap_text(pdf, error_text, 90, y_position, 450)
            if 'results' in tax_verification:
                tax_results = tax_verification.get('results', {})
                y_position -= 20
                pdf.drawString(
                    90, y_position, f"PIN: {get_verification_status(tax_results.get('pin', {}))}")
                y_position -= 20
                pdf.drawString(
                    90, y_position, f"Taxpayer Name: {get_verification_status(tax_results.get('taxPayerName', {}))}")
        except Exception as e:
            logger.error(f"Error adding Tax verification: {e}")
            #raise Exception("Failed to add Tax verification to PDF")
        try:    
            # Background check
            y_position -= 30
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(70, y_position, "Background Check:")
            pdf.setFont("Helvetica", 12)
            if 'error' in background_check:
                y_position -= 20
                error_text = f"Error: {background_check.get('error', 'N/A')}"
                y_position = wrap_text(pdf, error_text, 90, y_position, 450)
            else:
                y_position -= 20
                pdf.drawString(
                    90, y_position, f"Status: {background_check.get('message', 'N/A')}")
                y_position -= 20
                pdf.drawString(
                    90, y_position, f"Entity Score: {background_check.get('EntityScore', 'N/A')}")
                y_position -= 20
                pdf.drawString(
                    90, y_position, f"Name Score: {background_check.get('BestNameScore', 'N/A')}")
                y_position -= 20
                pdf.drawString(
                    90, y_position, f"Country Score: {background_check.get('BestCountryScore', 'N/A')}")

                # Add entity details if present
                entity_details = background_check.get('entityDetails', [])
                if entity_details:
                    y_position -= 20
                    pdf.drawString(90, y_position, "Entity Details:")
                    # Limit to first 3 entities to avoid overflow
                    for i, entity in enumerate(entity_details[:3]):
                        y_position -= 15
                        entity_text = f"Entity {i+1}: {str(entity)}"
                        y_position = wrap_text(
                            pdf, entity_text, 100, y_position, 440)
        except Exception as e:
            logger.error(f"Error adding Background check: {e}")
            #raise Exception("Failed to add Background check to PDF")
        try:
            # Add certification statement
            y_position -= 40
            pdf.setFont("Helvetica-Oblique", 10)
            cert_statement = f"This certificate confirms that the {certificateType.lower()}'s identity has been verified according to KYC requirements as above."
            y_position = wrap_text(pdf, cert_statement, 50, y_position, 500)
        except Exception as e:
            logger.error(f"Error adding certification statement: {e}")
            #raise Exception("Failed to add certification statement to PDF")
        try:
            # Add footer
            pdf.setFont("Helvetica", 8)
            pdf.drawString(
                50, 50, f"Certificate ID: {registration.get('idNumber')}-{datetime.now().strftime('%Y%m%d%H%M%S')}")
            pdf.drawString(50, 40, "This is a system-generated document.")
        except Exception as e:
            logger.error(f"Error adding footer: {e}")
            #raise Exception("Failed to add footer to PDF")
        pdf.save()
        buffer.seek(0)
        return buffer

    except Exception as e:
        logger.error(f"Error generating PDF certificate: {e}")
        # Create a minimal error PDF
        try:
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer)
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawCentredString(300, 400, "CERTIFICATE GENERATION ERROR")
            pdf.setFont("Helvetica", 12)
            pdf.drawCentredString(300, 370, f"Error: {str(e)}")
            pdf.drawCentredString(
                300, 350, "Please contact support for assistance")
            pdf.save()
            buffer.seek(0)
            return buffer
        except Exception as fallback_error:
            logger.error(f"Failed to create error PDF: {fallback_error}")
            raise Exception(f"PDF generation failed: {e}")


def generate_business_kyc_certificate(certificateType, identifier, registration, cr12_validation):
    """
    Generate a PDF KYC certificate based on verification results
    """
    try:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)

        # Set up the document
        pdf.setTitle(f"{certificateType} eKYC Certificate")

        # Add header
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawCentredString(300, 770, "KYC VERIFICATION CERTIFICATE")
        pdf.setFont("Helvetica", 12)
        pdf.drawCentredString(
            300, 750, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Add customer information
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, 700, f"{certificateType} Information")
        pdf.setFont("Helvetica", 12)

        y_position = 680
        pdf.drawString(
            70, y_position, f"{certificateType} Identifier: {identifier}")
        y_position -= 20
        pdf.drawString(
            70, y_position, f"Name: {registration.get('name', 'N/A')}")
        y_position -= 20
        pdf.drawString(
            70, y_position, f"Business Number: {registration.get('businessNumber', 'N/A')}")
        y_position -= 20
        pdf.drawString(
            70, y_position, f"PIN Number: {registration.get('pinNumber', 'N/A')}")

        # Add verification results
        y_position -= 40
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "Verification Results")
        pdf.setFont("Helvetica", 12)

        # CR12 ID validation
        y_position -= 30
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(70, y_position, "CR12 ID Validation:")
        pdf.setFont("Helvetica", 12)
        y_position -= 20
        pdf.drawString(
            90, y_position, f"Status: {cr12_validation.get('message', 'N/A')}")
        if 'error' in cr12_validation:
            y_position -= 20
            error_text = f"Error: {cr12_validation.get('error', 'N/A')}"
            y_position = wrap_text(pdf, error_text, 90, y_position, 450)
        if 'results' in cr12_validation:
            id_results = cr12_validation.get('results', {})
            checks = id_results.get('matchResults', {})
            for check in checks:
                y_position -= 20
                pdf.drawString(
                    90, y_position, f"{check}: {'Ok' if checks['result'] else 'Nok'}")
            id_val_results = id_results.get('matchResults', {})
            for key, value in id_val_results.items():
                y_position -= 20
                pdf.drawString(
                    90, y_position, f"{key}: {get_verification_status(value) if isinstance(value, dict) else str(value)}")

        # Add certification statement
        y_position -= 40
        pdf.setFont("Helvetica-Oblique", 10)
        cert_statement = f"This certificate confirms that the {certificateType.lower()}'s entity identity has been verified according to KYC requirements as above."
        y_position = wrap_text(pdf, cert_statement, 50, y_position, 500)

        # Add footer
        pdf.setFont("Helvetica", 8)
        pdf.drawString(
            50, 50, f"Certificate ID: {registration.get('businessNumber')}-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        pdf.drawString(50, 40, "This is a system-generated document.")

        pdf.save()
        buffer.seek(0)
        return buffer

    except Exception as e:
        logger.error(f"Error generating PDF certificate: {e}")
        # Create a minimal error PDF
        try:
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer)
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawCentredString(300, 400, "CERTIFICATE GENERATION ERROR")
            pdf.setFont("Helvetica", 12)
            pdf.drawCentredString(300, 370, f"Error: {str(e)}")
            pdf.drawCentredString(
                300, 350, "Please contact support for assistance")
            pdf.save()
            buffer.seek(0)
            return buffer
        except Exception as fallback_error:
            logger.error(f"Failed to create error PDF: {fallback_error}")
            raise Exception(f"PDF generation failed: {e}")


def wrap_text(pdf, text, x, y, max_width, line_height=15):
    """
    Helper function to wrap text that exceeds page width
    """
    words = str(text).split(' ')
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if pdf.stringWidth(test_line) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    for i, line in enumerate(lines):
        pdf.drawString(x, y - (i * line_height), line)

    return y - (len(lines) * line_height)


def get_verification_status(result):
    """
    Helper function to format verification status
    """
    if not result:
        return "Not Verified"

    status = result.get('status')
    if status == "Matched":
        return "✓ Verified"
    elif status == "Not Matched":
        expected = result.get('details', {}).get('expected', 'N/A')
        actual = result.get('details', {}).get('actual', 'N/A')
        return f"✗ Not Verified (Expected: {expected}, Actual: {actual})"
    else:
        return f"{status}"


def make_response(status_code, body):
    """
    Helper function to format responses for API Gateway.
    """
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key, X-Amz-Date, X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(body)
    }
    logger.info(f"Response: {response}")
    return response
