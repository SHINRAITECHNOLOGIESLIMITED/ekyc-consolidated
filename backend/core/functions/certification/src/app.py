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
from textract_utils import extract,query
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
            return create_certificate(data)
        except json.JSONDecodeError as e:
            logger.error("Error decoding JSON body")
            return make_response(400, {'message': 'Invalid JSON body','error': str(e)})
        except Exception as e:
            logger.error(f"An unexpected error occurred in lambda_handler: {e}")
            return make_response(500, {'message': 'Internal Server Error', 'error': str(e)})
    else:
        logger.error('Method Not Allowed - received {http_method}')
        return make_response(405, {'message': 'Method Not Allowed','error': 'Method Not Allowed'})

def create_certificate(data):
    schema = {
        "type": "object",
        "properties": {
            "idNumber": {"type": "string"},
            "fullNames": {"type": "string"},
        },
        "required": ["idNumber", "fullNames"],
        "additionalProperties": False
    }
    try:
        validate(event=data, schema=schema)
        return make_response(400, {'message': 'Create KYC Certifcates is not Implemented', 'error': 'Not Implemented'})
    except Exception as e:
        logger.error(f"Schema validation failed for Create KYC Certificate document: {e}")
        return make_response(400, {'message': 'Request body validation failed', 'error': str(e)})

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
