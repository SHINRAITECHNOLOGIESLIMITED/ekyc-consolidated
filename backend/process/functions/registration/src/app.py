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


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    """
    Lambda handler for document validation endpoints.
    Handles POST requests to various /document/* paths.
    Routes requests to specific handlers which perform schema validation.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    return make_response(501, {'message': 'Regisration endpoint not implemented'})


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
