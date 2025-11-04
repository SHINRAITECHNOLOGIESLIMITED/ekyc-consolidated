import json
import time
from typing import Tuple, Optional, Dict, Any

import jwt
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    """
    Lambda Authorizer for API Gateway REST API.
    Validates JWT tokens from Jubilee ESB.

    Architecture:
    User Request → Jubilee ESB (JWT Auth) → API Gateway → Lambda Authorizer → eKYC Backend

    Validation Strategy:
    - ESB is the primary authentication point (already validated user)
    - This authorizer provides defense-in-depth:
      1. Verifies JWT structure (3 parts: header.payload.signature)
      2. Validates token hasn't expired
      3. Checks required claims exist (sub, SubscriptionType, exp)
      4. Does NOT verify signature (ESB uses HS512 with shared secret we don't have)
    """
    logger.info(event)

    # Validate event structure
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
                "description": "The token string submitted by the client (JWT from ESB)"
            }
        }
    }
    validate(event=event, schema=schema)

    authorization_token = event['authorizationToken']
    method_arn = event['methodArn']

    if not authorization_token:
        logger.warning("Authorization token is missing")
        return generate_policy("Unauthorized", "Deny", method_arn,
                              error="Missing token")

    try:
        is_valid, user_id, claims, error_msg = validate_token(authorization_token)

        if not is_valid:
            logger.warning(f"Token validation failed: {error_msg}")
            return generate_policy("Unauthorized", "Deny", method_arn,
                                  error=error_msg)

        # Token is valid - generate allow policy
        logger.info(f"Token validated successfully for user: {user_id}")
        return generate_policy(user_id, "Allow", method_arn, context=claims)

    except Exception as e:
        logger.error(f"Error during token validation: {str(e)}")
        return generate_policy("Unauthorized", "Deny", method_arn,
                              error=f"Token validation error: {str(e)}")


def validate_token(token: str) -> Tuple[bool, Optional[str], Optional[Dict], Optional[str]]:
    """
    Validate the JWT token from Jubilee ESB.

    Performs basic validation without signature verification:
    1. Verifies JWT structure (3 parts)
    2. Decodes and parses payload
    3. Checks expiration
    4. Validates required claims

    Args:
        token (str): The JWT token (may include 'Bearer ' prefix)

    Returns:
        tuple: (is_valid, user_id, claims, error_message)
    """
    # Remove 'Bearer ' prefix if present
    if token.startswith('Bearer '):
        token = token[7:]

    # Verify token structure
    token_parts = token.split('.')
    if len(token_parts) != 3:
        return False, None, None, "Invalid token structure (expected 3 parts)"

    try:
        # Decode JWT WITHOUT signature verification
        # We skip verification because ESB uses HS512 with a shared secret we don't have
        # ESB is the primary auth point - this is defense-in-depth
        claims = jwt.decode(
            token,
            options={
                "verify_signature": False,  # Skip signature verification
                "verify_exp": True,         # Check expiration
                "require": ["sub", "exp"]   # Require these claims
            }
        )

        logger.info(f"Decoded JWT claims: {json.dumps(claims)}")

        # Validate required claims for ESB tokens
        if 'sub' not in claims:
            return False, None, None, "Missing 'sub' claim"

        if 'SubscriptionType' not in claims:
            return False, None, None, "Missing 'SubscriptionType' claim"

        if 'exp' not in claims:
            return False, None, None, "Missing 'exp' claim"

        # Check expiration manually as additional verification
        current_time = int(time.time())
        exp_time = claims['exp']

        if current_time >= exp_time:
            return False, None, None, f"Token expired (exp: {exp_time}, now: {current_time})"

        # Extract user ID from 'sub' claim
        user_id = claims['sub']

        logger.info(f"Token validated for user: {user_id}, subscription: {claims.get('SubscriptionType')}")

        return True, user_id, claims, None

    except jwt.ExpiredSignatureError:
        return False, None, None, "Token has expired"
    except jwt.InvalidTokenError as e:
        return False, None, None, f"Invalid token: {str(e)}"
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        return False, None, None, f"Token decode error: {str(e)}"


def generate_policy(
    principal_id: str,
    effect: str,
    resource: str,
    context: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate an IAM policy for API Gateway REST API (NOT HTTP API v2).

    REST API requires the format:
    {
      "principalId": "user_id",
      "policyDocument": {
        "Version": "2012-10-17",
        "Statement": [{
          "Action": "execute-api:Invoke",
          "Effect": "Allow|Deny",
          "Resource": "arn:aws:execute-api:..."
        }]
      },
      "context": {...}
    }

    Args:
        principal_id (str): The principal ID (user ID or "Unauthorized")
        effect (str): "Allow" or "Deny"
        resource (str): The method ARN from the event
        context (dict, optional): Additional context to pass to backend
        error (str, optional): Error message for deny responses

    Returns:
        dict: The IAM policy document
    """
    # Extract API Gateway ARN components to create wildcard resource
    # Format: arn:aws:execute-api:region:account:api-id/stage/method/path
    # We allow/deny all methods in the API
    arn_parts = resource.split(':')
    api_gateway_arn = ':'.join(arn_parts[:5]) + '/*'

    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "execute-api:Invoke",
                "Effect": effect,
                "Resource": api_gateway_arn
            }
        ]
    }

    response = {
        "principalId": principal_id,
        "policyDocument": policy_document
    }

    # Add context if provided (available to backend as event.requestContext.authorizer)
    if context:
        # API Gateway requires context values to be strings, numbers, or booleans
        # Convert complex objects to JSON strings
        sanitized_context = {}
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                sanitized_context[key] = str(value)
            else:
                sanitized_context[key] = json.dumps(value)
        response["context"] = sanitized_context

    # Add error message for deny responses
    if error:
        if "context" not in response:
            response["context"] = {}
        response["context"]["error"] = error

    logger.info(f"Generated {effect} policy for principal: {principal_id}")
    logger.debug(f"Policy: {json.dumps(response)}")

    return response
