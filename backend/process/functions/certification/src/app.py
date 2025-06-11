import json
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate

from portal import Portal

logger = Logger()
tracer = Tracer()
portal = Portal()

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")


    logger.error(f"Certification not implemented")
    return make_response(500, {'message': 'Certification not implemented'})
    
                
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
