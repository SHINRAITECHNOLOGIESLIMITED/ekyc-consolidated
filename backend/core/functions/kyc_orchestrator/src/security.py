"""
Security utilities for KYC Orchestrator
Implements SOW Day 1 required security features:
- HttpOnly cookie configuration
- 2FA integration with Cognito
- Security token handling
"""

import json
import boto3
from typing import Dict, Any, Optional, Tuple
from aws_lambda_powertools import Logger

logger = Logger()


class SecurityManager:
    """
    Manages security features for the KYC system.
    Implements SOW-required security enhancements.
    """

    def __init__(self):
        self.cognito_client = boto3.client('cognito-idp')

    def configure_secure_cookies(self, response: Dict[str, Any], tokens: Dict[str, str]) -> Dict[str, Any]:
        """
        Configure HttpOnly cookies for refresh tokens as required by SOW.

        Args:
            response: The response object to modify
            tokens: Dictionary containing access_token, refresh_token, etc.

        Returns:
            Modified response with secure cookie headers
        """
        if 'headers' not in response:
            response['headers'] = {}

        cookies = []

        # Configure refresh token as HttpOnly cookie (SOW requirement)
        if 'refresh_token' in tokens:
            refresh_cookie = self._create_secure_cookie(
                'jubilee_refresh_token',
                tokens['refresh_token'],
                max_age=30 * 24 * 60 * 60,  # 30 days
                http_only=True,
                secure=True,
                same_site='Strict'
            )
            cookies.append(refresh_cookie)

        # Configure access token as HttpOnly cookie for additional security
        if 'access_token' in tokens:
            access_cookie = self._create_secure_cookie(
                'jubilee_access_token',
                tokens['access_token'],
                max_age=60 * 60,  # 1 hour
                http_only=True,
                secure=True,
                same_site='Strict'
            )
            cookies.append(access_cookie)

        if cookies:
            response['headers']['Set-Cookie'] = '; '.join(cookies)
            logger.info("Configured secure HttpOnly cookies for tokens")

        return response

    def _create_secure_cookie(self, name: str, value: str, max_age: int,
                            http_only: bool = True, secure: bool = True,
                            same_site: str = 'Strict') -> str:
        """
        Create a secure cookie string with all security flags.

        Args:
            name: Cookie name
            value: Cookie value
            max_age: Cookie max age in seconds
            http_only: Whether to set HttpOnly flag
            secure: Whether to set Secure flag
            same_site: SameSite policy

        Returns:
            Formatted cookie string
        """
        cookie_parts = [f"{name}={value}"]
        cookie_parts.append(f"Max-Age={max_age}")
        cookie_parts.append("Path=/")

        if http_only:
            cookie_parts.append("HttpOnly")
        if secure:
            cookie_parts.append("Secure")
        if same_site:
            cookie_parts.append(f"SameSite={same_site}")

        return '; '.join(cookie_parts)

    def enable_2fa_for_user(self, user_pool_id: str, username: str) -> Dict[str, Any]:
        """
        Enable 2FA (TOTP) for a user in Cognito as required by SOW.

        Args:
            user_pool_id: Cognito User Pool ID
            username: Username to enable 2FA for

        Returns:
            Result of 2FA enablement operation
        """
        try:
            # Enable TOTP MFA for the user
            response = self.cognito_client.admin_set_user_mfa_preference(
                UserPoolId=user_pool_id,
                Username=username,
                TOTPMFASettings={
                    'Enabled': True,
                    'PreferredMfa': True
                }
            )

            logger.info(f"Successfully enabled 2FA for user: {username}")
            return {
                'success': True,
                'message': '2FA enabled successfully',
                'username': username
            }

        except Exception as e:
            logger.error(f"Failed to enable 2FA for user {username}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'username': username
            }

    def setup_2fa_for_user_pool(self, user_pool_id: str) -> Dict[str, Any]:
        """
        Configure 2FA settings for the entire user pool.

        Args:
            user_pool_id: Cognito User Pool ID

        Returns:
            Result of user pool 2FA configuration
        """
        try:
            # Update user pool to support TOTP MFA
            response = self.cognito_client.update_user_pool(
                UserPoolId=user_pool_id,
                MfaConfiguration='OPTIONAL'  # Allow optional MFA
            )

            logger.info(f"Successfully configured 2FA for user pool: {user_pool_id}")
            return {
                'success': True,
                'message': 'User pool 2FA configuration updated',
                'user_pool_id': user_pool_id
            }

        except Exception as e:
            logger.error(f"Failed to configure 2FA for user pool {user_pool_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_pool_id': user_pool_id
            }

    def verify_2fa_token(self, username: str, access_token: str, mfa_code: str) -> Dict[str, Any]:
        """
        Verify a 2FA TOTP code for a user.

        Args:
            username: Username
            access_token: User's access token
            mfa_code: 6-digit TOTP code

        Returns:
            Verification result
        """
        try:
            response = self.cognito_client.verify_software_token(
                AccessToken=access_token,
                UserCode=mfa_code
            )

            logger.info(f"2FA verification successful for user: {username}")
            return {
                'success': True,
                'verified': True,
                'username': username
            }

        except Exception as e:
            logger.error(f"2FA verification failed for user {username}: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'error': str(e),
                'username': username
            }

    def get_2fa_setup_qr_code(self, access_token: str) -> Dict[str, Any]:
        """
        Get QR code for setting up 2FA TOTP.

        Args:
            access_token: User's access token

        Returns:
            QR code setup information
        """
        try:
            response = self.cognito_client.associate_software_token(
                AccessToken=access_token
            )

            secret_code = response.get('SecretCode')

            return {
                'success': True,
                'secret_code': secret_code,
                'qr_code_url': f"otpauth://totp/JubileeKYC?secret={secret_code}&issuer=JubileeInsurance"
            }

        except Exception as e:
            logger.error(f"Failed to generate 2FA setup QR code: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


def add_security_headers(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standalone function to add security headers to any response.
    Used for backwards compatibility with existing functions.

    Args:
        response: Response object to enhance

    Returns:
        Response with security headers added
    """
    if 'headers' not in response:
        response['headers'] = {}

    # SOW Day 1 Required Security Headers
    security_headers = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https:; font-src 'self'; object-src 'none'; frame-ancestors 'none';",
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'X-XSS-Protection': '1; mode=block'
    }

    response['headers'].update(security_headers)
    return response


def secure_response_factory(status_code: int, body: Dict[str, Any],
                          tokens: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Factory function to create secure responses with all SOW security features.

    Args:
        status_code: HTTP status code
        body: Response body
        tokens: Optional tokens to set as secure cookies

    Returns:
        Secure response with headers and cookies
    """
    response = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            # CORS headers
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key, X-Amz-Date, X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(body, default=str)
    }

    # Add security headers
    response = add_security_headers(response)

    # Add secure cookies if tokens provided
    if tokens:
        security_manager = SecurityManager()
        response = security_manager.configure_secure_cookies(response, tokens)

    return response