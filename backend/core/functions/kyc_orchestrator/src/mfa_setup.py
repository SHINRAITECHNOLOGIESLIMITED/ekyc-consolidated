"""
2FA Setup and Management for KYC System
Implements SOW Day 1 requirement for 2FA integration with Cognito
"""

import json
import os
from typing import Dict, Any
from aws_lambda_powertools import Logger
from security import SecurityManager, secure_response_factory

logger = Logger()


def setup_user_pool_2fa() -> Dict[str, Any]:
    """
    Configure 2FA for the Cognito User Pool.
    This function should be called once to enable 2FA for the entire pool.

    Returns:
        Configuration result
    """
    user_pool_id = os.environ.get('COGNITO_USER_POOL_ID', 'eu-west-1_zn9jaZ2zR')

    security_manager = SecurityManager()
    result = security_manager.setup_2fa_for_user_pool(user_pool_id)

    if result['success']:
        logger.info(f"2FA configured for user pool: {user_pool_id}")
    else:
        logger.error(f"Failed to configure 2FA for user pool: {user_pool_id}")

    return result


def enable_user_2fa(username: str) -> Dict[str, Any]:
    """
    Enable 2FA for a specific user.

    Args:
        username: The username to enable 2FA for

    Returns:
        2FA enablement result
    """
    user_pool_id = os.environ.get('COGNITO_USER_POOL_ID', 'eu-west-1_zn9jaZ2zR')

    security_manager = SecurityManager()
    result = security_manager.enable_2fa_for_user(user_pool_id, username)

    if result['success']:
        logger.info(f"2FA enabled for user: {username}")
    else:
        logger.error(f"Failed to enable 2FA for user: {username}")

    return result


def handle_2fa_management(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle 2FA management requests.
    This is a utility function for administrative 2FA operations.

    Args:
        event: Lambda event containing 2FA management request

    Returns:
        2FA management response
    """
    try:
        # Parse request
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)

        action = body.get('action')

        if action == 'setup_user_pool':
            # Configure 2FA for the entire user pool
            result = setup_user_pool_2fa()
            return secure_response_factory(
                200 if result['success'] else 500,
                {
                    'message': 'User pool 2FA configuration',
                    'result': result
                }
            )

        elif action == 'enable_user_2fa':
            # Enable 2FA for a specific user
            username = body.get('username')
            if not username:
                return secure_response_factory(400, {
                    'message': 'Username required for user 2FA enablement',
                    'error': 'Missing username parameter'
                })

            result = enable_user_2fa(username)
            return secure_response_factory(
                200 if result['success'] else 500,
                {
                    'message': f'2FA enablement for user {username}',
                    'result': result
                }
            )

        elif action == 'get_2fa_setup':
            # Get 2FA setup QR code for a user
            access_token = body.get('access_token')
            if not access_token:
                return secure_response_factory(400, {
                    'message': 'Access token required for 2FA setup',
                    'error': 'Missing access_token parameter'
                })

            security_manager = SecurityManager()
            result = security_manager.get_2fa_setup_qr_code(access_token)
            return secure_response_factory(
                200 if result['success'] else 500,
                {
                    'message': '2FA setup information',
                    'result': result
                }
            )

        elif action == 'verify_2fa':
            # Verify a 2FA code
            username = body.get('username')
            access_token = body.get('access_token')
            mfa_code = body.get('mfa_code')

            if not all([username, access_token, mfa_code]):
                return secure_response_factory(400, {
                    'message': 'Username, access_token, and mfa_code required for verification',
                    'error': 'Missing required parameters'
                })

            security_manager = SecurityManager()
            result = security_manager.verify_2fa_token(username, access_token, mfa_code)
            return secure_response_factory(
                200 if result['success'] else 400,
                {
                    'message': '2FA verification result',
                    'result': result
                }
            )

        else:
            return secure_response_factory(400, {
                'message': 'Invalid 2FA management action',
                'error': f'Unknown action: {action}',
                'valid_actions': ['setup_user_pool', 'enable_user_2fa', 'get_2fa_setup', 'verify_2fa']
            })

    except Exception as e:
        logger.error(f"Error in 2FA management: {str(e)}")
        return secure_response_factory(500, {
            'message': '2FA management error',
            'error': str(e)
        })


def initialize_2fa_on_deployment():
    """
    Initialize 2FA settings when the function is deployed.
    This should be called automatically to ensure 2FA is configured.
    """
    try:
        result = setup_user_pool_2fa()
        if result['success']:
            logger.info("2FA initialization successful on deployment")
        else:
            logger.warning(f"2FA initialization failed: {result.get('error', 'Unknown error')}")
        return result
    except Exception as e:
        logger.error(f"Error during 2FA initialization: {str(e)}")
        return {'success': False, 'error': str(e)}


# Initialize 2FA when module is imported (deployment time)
logger.info("Initializing 2FA configuration...")
initialization_result = initialize_2fa_on_deployment()
if initialization_result['success']:
    logger.info("2FA initialization completed successfully")
else:
    logger.warning(f"2FA initialization failed: {initialization_result.get('error', 'Unknown error')}")