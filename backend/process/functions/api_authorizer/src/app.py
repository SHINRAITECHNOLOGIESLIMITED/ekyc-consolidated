import json
import re
import base64
from urllib.parse import unquote

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    logger.info(event)
    schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "API Gateway Lambda Authorizer Event",
                "description": "Schema for the event object passed to an API Gateway Lambda authorizer",
                "type": "object",
                "required": ["type", "methodArn", "authorizationToken"],
                "properties": {
                    "type": {
                    "type": "string",
                    "description": "The type of authorizer, typically 'TOKEN' for token-based authorizers",
                    "enum": ["TOKEN"]
                    },
                    "methodArn": {
                    "type": "string",
                    "description": "The ARN of the API Gateway method being authorized",
                    "pattern": "^arn:aws:execute-api:[a-z0-9-]+:[0-9]+:[a-z0-9]+/[^/]+/[A-Z]+/.*$"
                    },
                    "authorizationToken": {
                    "type": "string",
                    "description": "The token string submitted by the client, typically a JWT token from Cognito or another identity provider"
                    }
                }
            }
    validate(event=event, schema=schema)

    authorizationToken = event['authorizationToken']
    if not authorizationToken:
        logger.warning("Authorization token is missing")
        return generate_deny_response("Unauthorized", "Authorization token is missing")
    try:
        is_valid, user_id, claims = validate_token(authorizationToken)
        if not is_valid:
            logger.warning("Invalid token")
            return generate_deny_response("Unauthorized", "Invalid token")
        
        # If token is valid, generate an allow response
        return generate_allow_response(user_id, claims)
        
    except Exception as e:
        logger.error(f"Error during token validation: {str(e)}")
        return generate_deny_response("Unauthorized", f"Error during token validation: {str(e)}")


def base64url_decode(input):
    """
    Decode base64url encoded string (JWT specific encoding).
    
    Args:
        input (str): The base64url encoded string
        
    Returns:
        bytes: The decoded bytes
    """
    # Add padding if needed
    remainder = len(input) % 4
    if remainder > 0:
        input += '=' * (4 - remainder)
    
    # Replace URL-safe characters
    input = input.replace('-', '+').replace('_', '/')
    
    # Decode
    return base64.b64decode(input)

def validate_token(token):
    """
    Validate the provided token and extract user information.
    
    Args:
        token (str): The token to validate
        
    Returns:
        tuple: (is_valid, user_id, claims)
    """
    # Remove 'Bearer ' prefix if present
    if token.startswith('Bearer '):
        token = token[7:]
    
    token_parts = token.split('.')
    if len(token_parts) != 3:
        logger.warning("Token does not have three parts")
        return False, None, None
    
    try:
        # Decode header
        # token_header = json.loads(base64url_decode(token_parts[0]).decode('utf-8'))
        # logger.info(f"Token header: {token_header}")
        
        # Decode payload (claims)
        token_payload = json.loads(base64url_decode(token_parts[1]).decode('utf-8'))
        # logger.info(f"Token payload: {token_payload}")
        
        # Extract user ID from claims (adjust based on your JWT structure)
        user_id = token_payload.get('sub') or token_payload.get('user_id')
        logger.info(f"User ID: {user_id}")
        # In a real implementation, you would verify the signature here
        # using the third part of the token (token_parts[2])
        
        return True, user_id, token_payload
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        return False, None, None
    

def generate_allow_response(principal_id, context=None):
    """
    Generate an IAM policy that allows access.
    
    Args:
        principal_id (str): The principal ID (typically user ID)
        context (dict, optional): Additional context to include in the response
        
    Returns:
        dict: The IAM policy
    """
    
    response = {
        "isAuthorized": True,
        "context": context or {}
    }
    logger.info(f"Allow response: {response}")
    return response

def generate_deny_response(error_code, error_message):
    """
    Generate an IAM policy that denies access.
    
    Args:
        error_code (str): The error code
        error_message (str): The error message
        
    Returns:
        dict: The IAM policy
    """
    response = {
        "isAuthorized": False,
        "context": {
            "error": error_code,
            "message": error_message
        }
    }
    logger.info(f"Deny response: {response}")
    return response