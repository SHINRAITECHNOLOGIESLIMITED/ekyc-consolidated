import json
import re

from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    logger.debug("Auth event", extra={"event": event})
    
    # Extract the Authorization header from the request
    auth_header = None
    if "headers" in event and event["headers"]:
        for header_name, header_value in event["headers"].items():
            if header_name.lower() == "authorization":
                auth_header = header_value
                break
    if not auth_header:
        logger.warning("Authorization header is missing")
        return generate_deny_response("Unauthorized", "Authorization header is missing")
    try:
        is_valid, user_id, claims = validate_token(token)
        
        if not is_valid:
            logger.warning("Invalid token")
            return generate_deny_response("Unauthorized", "Invalid token")
        
        # If token is valid, generate an allow response
        return generate_allow_response(user_id, claims)
        
    except Exception as e:
        logger.error(f"Error during token validation: {str(e)}")
        return generate_deny_response("Unauthorized", f"Error during token validation: {str(e)}")


def validate_token(token):
    """
    Validate the provided token and extract user information.
    
    Args:
        token (str): The token to validate
        
    Returns:
        tuple: (is_valid, user_id, claims)
    """
    logger.info(token)
    #TODO: Add complex validation logic here
    if token and len(token) > 10:
        user_id, claims = None,None
        return True, user_id, claims
    
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
    return {
        "isAuthorized": True,
        "context": context or {}
    }


def generate_deny_response(error_code, error_message):
    """
    Generate an IAM policy that denies access.
    
    Args:
        error_code (str): The error code
        error_message (str): The error message
        
    Returns:
        dict: The IAM policy
    """
    return {
        "isAuthorized": False,
        "context": {
            "error": error_code,
            "message": error_message
        }
    }