import json
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer
from orchestrator import KYCOrchestrator
from validators import validate_kyc_request
from portal import Portal

logger = Logger()
tracer = Tracer()
portal = Portal()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    """
    Lambda handler for consolidated KYC processing.
    Orchestrates the complete KYC workflow including document validation,
    government verification, background checks, face liveness, and certification.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    http_method = event.get('httpMethod')
    path = event.get('path', '')

    if http_method == 'POST' and path.endswith('/kyc/process'):
        try:
            # Parse request body
            data = event.get('body', {})
            # Handle string bodies from API Gateway
            while isinstance(data, str):
                data = json.loads(data)

            logger.info(f"Request Data (body): {data}")

            return handle_kyc_processing(data)

        except json.JSONDecodeError:
            logger.error("Error decoding JSON body")
            return make_response(400, {'message': 'Invalid JSON body', 'error': 'Request body is not valid JSON'})
        except Exception as e:
            logger.error(f"An unexpected error occurred in handler: {e}")
            return make_response(500, {'message': 'Internal Server Error', 'error': str(e)})
    else:
        logger.error(f'Method Not Allowed - received {http_method} for path {path}')
        return make_response(405, {'message': 'Method Not Allowed'})


def handle_kyc_processing(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main KYC processing handler.
    Validates input and orchestrates the complete KYC workflow.
    """
    try:
        # Validate request schema
        validation_result = validate_kyc_request(data)
        if not validation_result['valid']:
            logger.error(f"Schema validation failed: {validation_result['errors']}")
            return make_response(400, {
                'message': 'Request validation failed',
                'error': validation_result['errors']
            })

        # Initialize orchestrator
        orchestrator = KYCOrchestrator()

        # Process KYC workflow
        result = orchestrator.process_kyc(data)

        logger.info(f"KYC processing completed with status: {result.get('overallStatus')}")

        # Return response based on overall status
        if result.get('overallStatus') == 'success':
            return make_response(200, result)
        elif result.get('overallStatus') == 'partial':
            return make_response(207, result)  # Multi-Status for partial success
        else:
            return make_response(400, result)

    except Exception as e:
        logger.error(f"Error occurred during KYC processing: {e}")
        return make_response(500, {
            'message': 'KYC processing failed',
            'error': str(e),
            'overallStatus': 'failed'
        })


def make_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to format responses for API Gateway.
    Maintains consistency with existing function response patterns.
    """
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key, X-Amz-Date, X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(body, default=str)  # Handle datetime serialization
    }
    logger.info(f"Response: {response}")
    return response