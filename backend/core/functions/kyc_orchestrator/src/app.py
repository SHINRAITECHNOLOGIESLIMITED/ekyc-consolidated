import json
from typing import Dict, Any
from datetime import datetime
from aws_lambda_powertools import Logger, Tracer
# Legacy imports removed - using SOW-compliant action-based approach only
from security import secure_response_factory, SecurityManager
from mfa_setup import handle_2fa_management
from action_router import ActionRouter
from payload_schemas import PayloadValidator
from feature_flags import should_use_unified_endpoint, FeatureFlag

logger = Logger()
tracer = Tracer()


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

    if http_method == 'POST' and (path.endswith('/kyc/process') or path.endswith('/kyc')):
        try:
            # Parse request body
            data = event.get('body', {})
            # Handle string bodies from API Gateway
            while isinstance(data, str):
                data = json.loads(data)

            logger.info(f"Request Data (body): {data}")

            # Create request context for feature flag evaluation
            request_context = {
                'request_id': event.get('requestContext', {}).get('requestId'),
                'client_id': event.get('headers', {}).get('X-Client-Id'),
                'user_id': event.get('requestContext', {}).get('authorizer', {}).get('principalId'),
                'source_ip': event.get('requestContext', {}).get('identity', {}).get('sourceIp'),
                'user_agent': event.get('headers', {}).get('User-Agent'),
                'api_gateway_context': event.get('requestContext', {})
            }

            # Check if this is a new action-based request or legacy workflow
            if 'action' in data and should_use_unified_endpoint(request_context):
                logger.info("Processing action-based request via unified endpoint")
                return handle_action_based_request(data, request_context)
            else:
                logger.info("Processing legacy workflow request")
                return handle_kyc_processing(data)

    elif http_method == 'POST' and path.endswith('/kyc/2fa'):
        # SOW Day 1 requirement: 2FA management endpoint
        try:
            logger.info("Processing 2FA management request")
            return handle_2fa_management(event)

        except json.JSONDecodeError:
            logger.error("Error decoding JSON body")
            return secure_response_factory(400, {'message': 'Invalid JSON body', 'error': 'Request body is not valid JSON'})
        except Exception as e:
            logger.error(f"An unexpected error occurred in handler: {e}")
            return secure_response_factory(500, {'message': 'Internal Server Error', 'error': str(e)})
    else:
        logger.error(f'Method Not Allowed - received {http_method} for path {path}')
        return secure_response_factory(405, {'message': 'Method Not Allowed'})


def handle_action_based_request(data: Dict[str, Any], request_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle action-based KYC requests via the new unified endpoint.
    SOW Day 2 Requirement: Single /kyc endpoint with action parameters.
    """
    try:
        # Validate using new action-based schema
        validation_result = PayloadValidator.validate_request(data)
        if not validation_result['valid']:
            logger.error(f"Action-based validation failed: {validation_result['errors']}")
            return secure_response_factory(400, {
                'success': False,
                'action': data.get('action', 'unknown'),
                'error': {
                    'message': 'Request validation failed',
                    'details': validation_result['errors'],
                    'error_code': 'VALIDATION_ERROR'
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        # Route to appropriate action handler
        action_router = ActionRouter()
        result = action_router.route_action(
            action=data['action'],
            data=data['data'],
            request_context=request_context
        )

        logger.info(f"Action-based processing completed for action: {data['action']}")
        return result

    except Exception as e:
        logger.error(f"Error in action-based request handling: {e}")
        return secure_response_factory(500, {
            'success': False,
            'action': data.get('action', 'unknown'),
            'error': {
                'message': 'Action-based processing failed',
                'details': str(e),
                'error_code': 'PROCESSING_ERROR'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })


def handle_kyc_processing(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy KYC processing handler - redirects to action-based processing.
    SOW Compliance: All requests now use action-based routing.
    """
    try:
        logger.info("Legacy endpoint accessed - redirecting to action-based processing")

        # Convert legacy request to action-based format
        if 'processType' in data:
            # This is a legacy workflow request, convert to process_workflow action
            action_data = {
                'action': 'process_workflow',
                'data': data,
                'metadata': {
                    'legacy_conversion': True,
                    'original_endpoint': '/kyc/process'
                }
            }

            # Use action-based processing
            action_router = ActionRouter()
            result = action_router.route_action(
                action='process_workflow',
                data=data,
                request_context={'legacy_request': True}
            )

            return result
        else:
            # Unknown legacy format
            return secure_response_factory(400, {
                'success': False,
                'error': {
                    'message': 'Legacy request format not supported',
                    'error_code': 'LEGACY_FORMAT_UNSUPPORTED',
                    'suggestion': 'Use action-based format with /kyc endpoint'
                },
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

    except Exception as e:
        logger.error(f"Error in legacy processing handler: {e}")
        return secure_response_factory(500, {
            'success': False,
            'error': {
                'message': 'Legacy processing failed',
                'details': str(e),
                'error_code': 'LEGACY_PROCESSING_ERROR'
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })


def make_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to format responses for API Gateway.
    Maintains consistency with existing function response patterns.
    Includes SOW-required security headers for vulnerability mitigation.
    """
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            # CORS headers
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key, X-Amz-Date, X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            # SOW Day 1 Required Security Headers
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https:; font-src 'self'; object-src 'none'; frame-ancestors 'none';",
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'X-XSS-Protection': '1; mode=block'
        },
        'body': json.dumps(body, default=str)  # Handle datetime serialization
    }
    logger.info(f"Response: {response}")
    return response