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

from portal import Portal,DOCUMENT_TYPE

KYCDOCUMENTSBUCKET_NAME = os.environ.get('KYCDOCUMENTSBUCKET_NAME', None)
assert KYCDOCUMENTSBUCKET_NAME is not None, "KYCDOCUMENTSBUCKET_NAME is not set"

SETTING_NATIONAL_ID_USE_ADAPTER = False

logger = Logger()
tracer = Tracer()
portal = Portal()
s3_client = boto3.client('s3')


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    """
    Lambda handler for KYC Certification creation
    """
    logger.info(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')

    if http_method == 'POST':
        try:
            data = event.get('body', {})
            
            while isinstance(data, str):
                data = json.loads(data)
            logger.info(f"Request Data (body): {data}")
            return create_customer_certificate(data)
        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON body")
            return make_response(400, {'message': 'Invalid JSON body','error': str(e)})
        except Exception as e:
            logger.error(f"An unexpected error occurred in lambda_handler: {e}")
            return make_response(500, {'message': 'Internal Server Error', 'error': str(e)})
    else:
        logger.error('Method Not Allowed - received {http_method}')
        return make_response(405, {'message': 'Method Not Allowed','error': 'Method Not Allowed'})

def create_customer_certificate(data):
    # Define schema for validation
    schema = {
        "type": "object",
        "properties": {
            "registration": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "idNumber": {"type": "string"},
                    "pinNumber": {"type": "string"},
                    "gender": {"type": "string"},
                    "dateOfBirth": {"type": "string"}
                },
                "required": ["name", "idNumber"]
            },
            "idVerification": {
                "type": "object",
                "properties": {
                    "results": {"type": "object"}
                },
                "required": ["results"]
            },
            "taxPayerVerification": {
                "type": "object",
                "properties": {
                    "results": {"type": "object"}
                },
                "required": ["results"]
            },
            "backgroundCheck": {
                "type": "object",
                "properties": {
                    "BestCountryScore": {"type": ["number", "integer"]},
                    "BestNameScore": {"type": ["number", "integer"]},
                    "EntityScore": {"type": ["number", "integer"]},
                    "ReasonListed": {"type": "string"},
                    "entityDetails": {"type": "array"},
                    "message": {"type": "string"}
                },
                "required": ["EntityScore", "message"]
            }
        },
        "required": ["registration", "idVerification", "taxPayerVerification", "backgroundCheck"]
    }
    
    try:
        # Validate input data against schema
        validate(event=data, schema=schema)
        
        # Extract required data from the input
        registration = data['registration']
        id_verification = data['idVerification']
        tax_verification = data['taxPayerVerification']
        background_check = data['backgroundCheck']
        
        # Create PDF certificate
        pdf_buffer = generate_kyc_certificate(registration, id_verification, tax_verification, background_check)
        
        # Generate S3 path for the certificate
        id_number = registration['idNumber']
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        s3_key = f"kyc_certificates/{id_number}/{timestamp}_certificate.pdf"
        
        # Upload to S3
        s3_client.put_object(
            Bucket=KYCDOCUMENTSBUCKET_NAME,
            Key=s3_key,
            Body=pdf_buffer.getvalue(),
            ContentType='application/pdf'
        )
        
        # Update portal with certificate information
        portal.update_document(
            id_number=id_number,
            document_type=DOCUMENT_TYPE.KYC_CERTIFICATE,
            s3_path=s3_key
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

def generate_kyc_certificate(registration, id_verification, tax_verification, background_check):
    """
    Generate a PDF KYC certificate based on verification results
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    
    # Set up the document
    pdf.setTitle("KYC Verification Certificate")
    
    # Add header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(300, 770, "KYC VERIFICATION CERTIFICATE")
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(300, 750, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Add customer information
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, 700, "Customer Information")
    pdf.setFont("Helvetica", 12)
    
    y_position = 680
    pdf.drawString(70, y_position, f"Name: {registration.get('name', 'N/A')}")
    y_position -= 20
    pdf.drawString(70, y_position, f"ID Number: {registration.get('idNumber', 'N/A')}")
    y_position -= 20
    pdf.drawString(70, y_position, f"PIN Number: {registration.get('pinNumber', 'N/A')}")
    y_position -= 20
    pdf.drawString(70, y_position, f"Gender: {registration.get('gender', 'N/A')}")
    y_position -= 20
    pdf.drawString(70, y_position, f"Date of Birth: {registration.get('dateOfBirth', 'N/A')}")
    
    # Add verification results
    y_position -= 40
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y_position, "Verification Results")
    pdf.setFont("Helvetica", 12)
    
    # ID verification
    y_position -= 30
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(70, y_position, "ID Verification:")
    pdf.setFont("Helvetica", 12)
    
    id_results = id_verification.get('results', {})
    y_position -= 20
    pdf.drawString(90, y_position, f"ID Number: {get_verification_status(id_results.get('idNumber', {}))}") 
    y_position -= 20
    pdf.drawString(90, y_position, f"Full Names: {get_verification_status(id_results.get('fullNames', {}))}")
    y_position -= 20
    pdf.drawString(90, y_position, f"Date of Birth: {get_verification_status(id_results.get('dateOfBirth', {}))}")
    y_position -= 20
    pdf.drawString(90, y_position, f"Gender: {get_verification_status(id_results.get('gender', {}))}")
    
    # Tax verification
    y_position -= 30
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(70, y_position, "Tax Verification:")
    pdf.setFont("Helvetica", 12)
    
    tax_results = tax_verification.get('results', {})
    y_position -= 20
    pdf.drawString(90, y_position, f"PIN: {get_verification_status(tax_results.get('pin', {}))}")
    y_position -= 20
    pdf.drawString(90, y_position, f"Taxpayer Name: {get_verification_status(tax_results.get('taxPayerName', {}))}")
    
    # Background check
    y_position -= 30
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(70, y_position, "Background Check:")
    pdf.setFont("Helvetica", 12)
    y_position -= 20
    pdf.drawString(90, y_position, f"Status: {background_check.get('message', 'N/A')}")
    y_position -= 20
    pdf.drawString(90, y_position, f"Entity Score: {background_check.get('EntityScore', 'N/A')}")
    y_position -= 20
    pdf.drawString(90, y_position, f"Name Score: {background_check.get('BestNameScore', 'N/A')}")
    y_position -= 20
    pdf.drawString(90, y_position, f"Country Score: {background_check.get('BestCountryScore', 'N/A')}")
    
    # Add entity details if present
    entity_details = background_check.get('entityDetails', [])
    if entity_details:
        y_position -= 20
        pdf.drawString(90, y_position, "Entity Details:")
        for i, entity in enumerate(entity_details[:3]):  # Limit to first 3 entities to avoid overflow
            y_position -= 15
            pdf.drawString(100, y_position, f"Entity {i+1}: {str(entity)}")
    
    # Add certification statement
    y_position -= 40
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(50, y_position, "This certificate confirms that the customer's identity has been verified according to KYC requirements.")
    
    # Add footer
    pdf.setFont("Helvetica", 8)
    pdf.drawString(50, 50, f"Certificate ID: {registration.get('idNumber')}-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    pdf.drawString(50, 40, "This is a system-generated document.")
    
    pdf.save()
    buffer.seek(0)
    return buffer

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
