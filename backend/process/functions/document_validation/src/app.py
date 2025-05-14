import json

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate
from aws_lambda_powertools.utilities.validation.exceptions import SchemaValidationError
from textract_utils import extract
import requests
from urllib.parse import urlparse
import os
from portal import Portal

KYCDOCUMENTSBUCKET_NAME = os.environ.get('KYCDOCUMENTSBUCKET_NAME', None)
assert KYCDOCUMENTSBUCKET_NAME is not None, "KYCDOCUMENTSBUCKET_NAME is not set"

logger = Logger()
tracer = Tracer()
portal = Portal()

def download_document_to_s3(s3_client, url, object_key):
    """
    Downloads a document from a URL and uploads it to an S3 bucket.
    
    Parameters:
    - s3_client: boto3 S3 client instance
    - url: URL of the document to download
    - bucket_name: Name of the S3 bucket to upload to
    - object_key: Key to use for the S3 object (if None, will be derived from URL)
    
    Returns:
    - S3 URI of the uploaded document
    """
    
    
    try:
        # Download the document from the URL
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Upload the document to S3
        s3_client.upload_fileobj(
            response.raw,
            KYCDOCUMENTSBUCKET_NAME,
            object_key,
            ExtraArgs={'ContentType': response.headers.get('Content-Type')}
        )
        
        # Return the S3 URI
        s3_uri = f"s3://{bucket_name}/{object_key}"
        return s3_uri,object_key
    
    except requests.exceptions.RequestException as e:
        # Handle request errors (connection, timeout, etc.)
        raise Exception(f"Error downloading document from URL: {e}")
    except Exception as e:
        # Handle other errors (S3 upload failures, etc.)
        raise Exception(f"Error uploading document to S3: {e}")


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    """
    Lambda handler for document validation endpoints.
    Handles POST requests to various /document/* paths.
    Routes requests to specific handlers which perform schema validation.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')
    path = event.get('path')

    if http_method == 'POST':
        try:
            data = json.loads(event.get('body', '{}'))
            logger.error(f"Request body: {data}")
            match path:
                case  '/document/nationalid-validation':
                    return handle_nationalid_document_validation(data)
                case   '/document/passport-validation':
                    return handle_passport_document_validation(data)
                case   '/document/kra-validation':
                    return handle_kra_document_validation(data)
                case   '/document/company-validation':
                    return handle_company_document_validation(data)
                case _:
                    return make_response(404, {'message': 'Path Not Found'})

        except json.JSONDecodeError:
            logger.error("Error decoding JSON body")
            return make_response(400, {'message': 'Invalid JSON body'})
        

        except Exception as e:
            logger.error(f"An unexpected error occurred in lambda_handler: {e}")
            return make_response(500, {'message': 'Internal Server Error'})

    else:
        logger.error('Method Not Allowed - received {http_method}')
        return make_response(405, {'message': 'Method Not Allowed'})

def handle_nationalid_document_validation(data):
    """
    Validates schema (defined inline and locally) and indicates not implemented for National ID document validation.
    """
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "url"},
            "idNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "dateOfBirth": {"type": "string", "format": "date"}
        },
        "required": ["uploadedDocumentUrl", "idNumber", "fullNames", "dateOfBirth"],
        "additionalProperties": False
    }
    validate(schema=schema,event=data)
    
    
    
    try:
        #download document to local s3
        url,s3Path = download_document_to_s3(url=data['uploadedDocumentUrl'], object_key=None)
        logger.info(f"Downloaded {data['uploadedDocumentUrl']} to {url}")    
        extractedData =  extract(s3Path)
        logger.info(f"Textracted {data['uploadedDocumentUrl']}")
        logger.info(extractedData)    
        
        idnumberValid = False,"Not processed"
        namesValid = False,"Not processed"
        dobValid = False,"Not processed"
        
        #verify 
        if 'ID_NUMBER' in extractedData:
            if extractedData['ID_NUMBER'] == data['idNumber']:
                idnumberValid = True,"Matched"
            else:
                idnumberValid = False,f"Mismatch - found {extractedData['ID_NUMBER']} expected {data['idNumber']}"
        else:
            idnumberValid = False,"ID Number field not found in the document"
        
        
        if 'DATE_OF_BIRTH' in extractedData:
            if extractedData['DATE_OF_BIRTH'] == data['dateOfBirth'] :
                dobValid = True,"Matched"
            else:
                dobValid = False,f"Mismatch - found {extractedData['DATE_OF_BIRTH']} expected {data['dateOfBirth'] }"
        else:
            dobValid = False,"Date of Birth field not found in the document"
        
        if 'FULL_NAME' in extractedData:
            if extractedData['FULL_NAME'] == data['fullNames'] :
                dobValid = True,"Matched"
            else:
                dobValid = False,f"Mismatch - found {extractedData['FULL_NAME']} expected {data['fullNames'] }"
        else:
            dobValid = False,"FullName field not found in the document"
        
        if dobValid[0] and idnumberValid[0] and namesValid[0]:
            status="Valid"
        else:
            status="Invalid"
        matchDetails = dict(idNumber = dict(valid=idnumberValid[0],reason=idnumberValid[1]),
                          names = dict(valid=namesValid[0],reason=namesValid[1]),
                          dob = dict(valid=dobValid[0],reason=dobValid[1]),)
        validation = dict(matchDetails=matchDetails,extractedData=extractedData,status=status)
        return make_response(200, validation)

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for National ID document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_nationalid_document_validation: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def handle_passport_document_validation(data):
    """
    Validates schema (defined inline and locally) and indicates not implemented for Passport document validation.
    """
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "url"},
            "passportNumber": {"type": "string"},
            "fullNames": {"type": "string"},
            "dateOfBirth": {"type": "string", "format": "date"}
        },
        "required": ["uploadedDocumentUrl", "passportNumber", "fullNames", "dateOfBirth"],
        "additionalProperties": False
    }
    
    try:
        validate(schema=schema,event=data)    
        

        return make_response(501, {'message': 'Passport document validation endpoint not implemented'})

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for Passport document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_passport_document_validation: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def handle_kra_document_validation(data):
    """
    Validates schema (defined inline and locally) and indicates not implemented for KRA document validation.
    """
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "url"},
            "kraPin": {"type": "string"},
            "fullNames": {"type": "string"},
            "idNumber": {"type": "string"} 
        },
        "required": ["uploadedDocumentUrl", "kraPin", "fullNames", "idNumber"],
        "additionalProperties": False
    }
    
    try:
        validate(schema=schema,event=data)
        

        
        return make_response(501, {'message': 'KRA document validation endpoint not implemented'})

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for KRA document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_kra_document_validation: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def handle_company_document_validation(data):
    """
    Validates schema (defined inline and locally) and indicates not implemented for Company document validation.
    """
    schema = {
        "type": "object",
        "properties": {
            "uploadedDocumentUrl": {"type": "string", "format": "url"},
            "businessNumber": {"type": "string"},
            "fullNames": {"type": "string"} # Maps to Registered Company Name
        },
        "required": ["uploadedDocumentUrl", "businessNumber", "fullNames"],
        "additionalProperties": False
    }
    
    try:
        validate(schema=schema,event=data)
        
        return make_response(501, {'message': 'Company document validation endpoint not implemented'})

    except SchemaValidationError as e:
        logger.error(f"Schema validation failed for Company document validation: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'details': str(e)})
    except Exception as e:
        logger.error(f"An unexpected error occurred in handle_company_document_validation: {e}")
        return make_response(500, {'message': 'Internal Server Error'})


def make_response(status_code, body):
    """
    Helper function to format responses for API Gateway.
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }
