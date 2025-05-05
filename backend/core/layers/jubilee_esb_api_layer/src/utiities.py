import json
import os
import time
import uuid
from http import HTTPStatus
from typing import Dict, Any
from aws_xray_sdk.core import xray_recorder
import boto3
import requests
from aws_lambda_powertools import Logger, Tracer
from botocore.exceptions import ClientError
from requests import Response

logger = Logger()
tracer = Tracer()

JUBILEE_ESB_API_SECRET_ARN = os.getenv('JUBILEE_ESB_API_SECRET_ARN', None)
assert JUBILEE_ESB_API_SECRET_ARN, "JUBILEE_ESB_API_SECRET_ARN environment variable is not set"
PORTAL_GRAPHQL_SECRET_ARN = os.getenv('PORTAL_GRAPHQL_SECRET_ARN', None)
assert PORTAL_GRAPHQL_SECRET_ARN, "PORTAL_GRAPHQL_SECRET_ARN environment variable is not set"
JUBILEE_ESB_TOKEN_VALIDITY_MINS = 4.5


class JubileeESBError(Exception):
    """Custom exception for ESB validation errors"""
    pass


class JubileeESBUtilities:

    def __init__(self):
        """Initialize Jubilee ESB API with AWS Secrets Manager configuration"""
        self.secrets_client = boto3.client('secretsmanager')
        self._load_portal_credentials()  # portal credentials are loded first and esb depends on them
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
            self._project_api_call_to_portal(response, api_name="EBS", api_method="auth/signin",
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

    def _load_portal_credentials(self) -> None:
        """Load API credentials from AWS Secrets Manager"""
        try:
            portal_credentials_response = self.secrets_client.get_secret_value(
                SecretId=PORTAL_GRAPHQL_SECRET_ARN
            )
            if 'SecretString' not in portal_credentials_response:
                logger.error("Failed to load Protal Connection credentials: SecretString not found")
                raise JubileeESBError("Failed to initialize ESB service")
            portal_credentials = json.loads(portal_credentials_response['SecretString'])
            self.portal_graphql_url = portal_credentials['url']
            self.portal_graphql_api_key = portal_credentials['api_key']
            logger.info("Successfully loaded Portal Connection credentials")
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(f"Access denied to secret {PORTAL_GRAPHQL_SECRET_ARN}: {str(e)}")
                raise JubileeESBError(f"Failed to initialize Portal GraphQl credentials: Access denied to secret")
            elif e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.error(f"Secret {PORTAL_GRAPHQL_SECRET_ARN} not found: {str(e)}")
                raise JubileeESBError(f"Failed to load Portal GraphQl credentials: Secret not found")
            else:
                logger.error(f"Failed to load Portal GraphQl credentials: {str(e)}")
                raise JubileeESBError(f"Failed to load Portal GraphQl credentials: {str(e)}")

    def _project_api_call_to_portal(self, response: Response, api_name: str, api_method: str, duration_ms: int,
                                    trace_id: str, capture_data=False):
        mutation = """
        mutation CreateAPICall($input: CreateAPICallInput!) {
            createAPICall(input: $input) {
                apiCallId
            }
        }
        """
        if capture_data:
            # Handle request data
            try:
                request_data = response.request.body
                if isinstance(request_data, (str, bytes)):
                    try:
                        request_data = json.loads(request_data)
                    except (json.JSONDecodeError, TypeError):
                        request_data = {}
            except AttributeError:
                request_data = {}

            # Handle response data
            try:
                response_data = response.json() if response.text else {}
            except (json.JSONDecodeError, AttributeError):
                response_data = {}
        else:
            request_data = {}
            response_data = {}
        # Request headers
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.portal_graphql_api_key
        }
        try:
            responseResult = HTTPStatus(response.status_code).phrase
        except ValueError:
            responseResult = f"Unknown Status Code: {response.status_code}"
        # Variables for the mutation
        variables = {
            "input": {
                "apiCallId": str(uuid.uuid4()),
                "durationMs": duration_ms,
                "traceId": trace_id,
                "apiName": api_name,
                "apiMethod": api_method,
                "requestIPAddress": response.request.headers.get('X-Forwarded-For',
                                                                 response.request.headers.get('Remote-Addr', '')),
                "requestHttpMethod": response.request.method,
                "requestTimestamp": int(time.time()),
                "responseStatusCode": response.status_code,
                "responseResult": responseResult,
                "requestData": json.dumps(request_data,indent=4),
                "responseData": json.dumps(response_data,indent=4)
            }
        }

        # Prepare the request body
        payload = {
            'query': mutation,
            'variables': variables
        }
        try:
            # Make the request to AppSync
            response = requests.post(
                self.portal_graphql_url,
                headers=headers,
                json=payload
            )

            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                if 'errors' in result:
                    print(f"GraphQL Errors: {result['errors']}")
                    return None
                return result['data']['createAPICall']
            else:
                print(f"HTTP Error: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error making API call: {str(e)}")
            return None

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
            self._project_api_call_to_portal(response, api_name=service, api_method=api_method, duration_ms=duration_ms,
                                             trace_id=trace_id, capture_data=True)
            response.raise_for_status()

            logger.info(f"Jubilee ESB: {service} API call successful")
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Jubilee ESB: {service} API call failed: {str(e)}")
            raise JubileeESBError(f"{service} API call failed: {str(e)}")
