import json
import os
import time
from http import HTTPStatus
from typing import Dict, Any

import boto3
import requests
from aws_lambda_powertools import Logger, Tracer
from aws_xray_sdk.core import xray_recorder
from botocore.exceptions import ClientError

logger = Logger()
tracer = Tracer()

JUBILEE_ESB_API_SECRET_ARN = os.getenv('JUBILEE_ESB_API_SECRET_ARN', None)
assert JUBILEE_ESB_API_SECRET_ARN, "JUBILEE_ESB_API_SECRET_ARN environment variable is not set"
JUBILEE_ESB_TOKEN_VALIDITY_MINS = 4.5


class JubileeESBError(Exception):
    """Custom exception for ESB validation errors"""
    pass


class JubileeESBUtilities:

    def __init__(self,portal):
        """Initialize Jubilee ESB API with AWS Secrets Manager configuration"""
        self.secrets_client = boto3.client('secretsmanager')
        self.portal = portal
        self._load_jubilee_esb_credentials()

    def _retrieve_jwt_token(self, username: str, password: str) -> str:
        try:
            login_data = {
                "username": username,
                "password": password
            }

            headers = {
                "Content-Type": "application/json"
            }
            # logger.info(f"Attempting to retrieve JWT token for {login_data}")
            start_time = time.time() * 1000
            response = requests.post(
                f"{self.base_url}/api/auth/signin",
                json=login_data,
                headers=headers,
                timeout=15
            )
            if response.status_code == HTTPStatus.OK:
                logger.info(f"Authentication response: {response.status_code}")
            else:
                logger.info(f"Authentication response: {response.text}")
            duration_ms = round(time.time() * 1000 - start_time)
            current_segment = xray_recorder.current_segment()
            trace_id = current_segment.trace_id if current_segment else ""
            self.portal.log_api_call(response, api_name="EBS", api_method="auth/signin",
                                     duration_ms=duration_ms,
                                     trace_id=trace_id, capture_data=False)
            response.raise_for_status()

            token_data = response.json()
            if not token_data.get('tokenType'):
                raise JubileeESBError("No tokenType received in authentication response")
            if not token_data.get('accessToken'):
                raise JubileeESBError("No accessToken received in authentication response")
            logger.info("Successfully retrieved ESB JWT token")
            return f"{token_data['tokenType']} {token_data['accessToken']}"

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve JWT token: {str(e)}")
            raise JubileeESBError(f"Authentication failed: {str(e)}")

    def _load_jubilee_esb_credentials(self) -> None:
        """Load API credentials from AWS Secrets Manager"""
        try:
            jubilee_esb_response = self.secrets_client.get_secret_value(
                SecretId=JUBILEE_ESB_API_SECRET_ARN
            )

            if 'SecretString' not in jubilee_esb_response:
                logger.error("Failed to load ESB credentials: SecretString not found")
                raise JubileeESBError("Failed to initialize ESB service: Secret value not found")
            secretString = jubilee_esb_response['SecretString']
            # logger.info(f"Successfully retrieved ESB credentials: {secretString}")
            credentials = json.loads(secretString)
            self.base_url = credentials['baseurl']
            self.business = credentials['business']
            username = credentials['username']
            password = credentials['password']

            if not username or not password:
                raise JubileeESBError("Missing username or password in credentials")

            # Retrieve JWT token through login
            self.authorization_jwt = self._retrieve_jwt_token(username, password)
            self.authorization_jwt_time = int(time.time())
            logger.info("Successfully loaded Jubilee ESB credentials")
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(f"Access denied to secret {JUBILEE_ESB_API_SECRET_ARN}: {str(e)}")
                raise JubileeESBError(f"Failed to initialize ESB service: Access denied to secret")
            elif e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.error(f"Secret {JUBILEE_ESB_API_SECRET_ARN} not found: {str(e)}")
                raise JubileeESBError(f"Failed to initialize ESB service: Secret not found")
            else:
                logger.error(f"Failed to load ESB credentials: {str(e)}")
                raise JubileeESBError(f"Failed to initialize ESB service: {str(e)}")

    @tracer.capture_method
    def make_api_call(self,
                      service: str,
                      api_method: str,
                      url: str,
                      data: Dict[str, Any], is_post: bool = True):
        """
        Make API call with error handling and logging

        Args:
            service: Service name for logging eg IPRS,KRA,NexisLexis,
            api_method: Method of API being called for logging eg SearchById,validate_id
            url: API endpoint URL
            data: Request payload
            is_post: true if http method is POST other it will call GET
            :param :
        """
        try:
            current_segment = xray_recorder.current_segment()
            trace_id = current_segment.trace_id if current_segment else None

            headers = {
                "Authorization": self.authorization_jwt,
                "Content-Type": "application/json"
            }
            # re-authetincating every four and hald a minute.
            # JWT access tokens are valid for 5 mins only
            if int(time.time()) - self.authorization_jwt_time > 60 * JUBILEE_ESB_TOKEN_VALIDITY_MINS:
                self._load_jubilee_esb_credentials()
            start_time = time.time() * 1000
            if is_post:
                response = requests.post(
                    f"{self.base_url}{url}",
                    json=data,
                    headers=headers,
                    timeout=240
                )
            else:
                response = requests.get(
                    f"{self.base_url}{url}",
                    headers=headers,
                    timeout=240
                )
            duration_ms = round(time.time() * 1000 - start_time)
            if response.status_code == 500:
                logger.error(response.json())
            self.portal.log_api_call(response, api_name=service, api_method=api_method, duration_ms=duration_ms,
                                     trace_id=trace_id, capture_data=True)
            response.raise_for_status()

            logger.info(f"Jubilee ESB: {service} API call successful")
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Jubilee ESB: {service} API call failed: {str(e)}")
            raise JubileeESBError(f"{service} API call failed: {str(e)}")
