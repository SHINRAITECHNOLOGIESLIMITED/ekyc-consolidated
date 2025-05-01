import json
import time
from http import HTTPStatus
from typing import Dict, Any

import boto3
import requests
from aws_lambda_powertools import Logger, Tracer
from botocore.exceptions import ClientError
from requests import Response

logger = Logger()
tracer = Tracer()


class JubileeESBError(Exception):
    """Custom exception for ESB validation errors"""
    pass


class JubileeESBUtilities:

    def __init__(self):
        """Initialize Jubilee ESB API with AWS Secrets Manager configuration"""
        self.secrets_client = boto3.client('secretsmanager')
        self._load_jubilee_esb_credentials()
        self._load_portal_credentials()

    def _retrieve_jwt_token(self, username: str, password: str) -> str:
        try:
            login_data = {
                "username": username,
                "password": password
            }

            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{self.base_url}/auth/login",
                json=login_data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            token_data = response.json()
            if not token_data.get('token'):
                raise JubileeESBError("No token received in authentication response")

            logger.info("Successfully retrieved JWT token")
            return token_data['token']

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve JWT token: {str(e)}")
            raise JubileeESBError(f"Authentication failed: {str(e)}")

    def _load_jubilee_esb_credentials(self) -> None:
        """Load API credentials from AWS Secrets Manager"""
        try:
            SECRET_ID = "JubileeESBAPISecret"
            try:
                base_url_response = self.secrets_client.get_secret_value(
                    SecretId=SECRET_ID
                )
            except Exception as e:
                logger.error(f"Failed to load ESB credentials: {str(e)}")
                raise JubileeESBError("Failed to initialize ESB service")
            if 'SecretString' not in base_url_response:
                logger.error("Failed to load ESB credentials: SecretString not found")
                raise JubileeESBError("Failed to initialize ESB service")

            credentials = json.loads(base_url_response['SecretString'])
            self.base_url = credentials['BaseUrl']
            self.business = credentials['Business']

            username = credentials['Username']
            password = credentials['Pasword']

            if not username or not password:
                raise JubileeESBError("Missing username or password in credentials")

            # Retrieve JWT token through login
            self.authorization_jwt = self._retrieve_jwt_token(username, password)
        except ClientError as e:
            logger.error(f"Failed to load ESB credentials: {str(e)}")
            raise JubileeESBError("Failed to initialize ESB service")

    def _load_portal_credentials(self) -> None:
        """Load API credentials from AWS Secrets Manager"""
        try:
            SECRET_ID = "portaldatacredentials"
            try:
                base_url_response = self.secrets_client.get_secret_value(
                    SecretId=SECRET_ID
                )
            except Exception as e:
                logger.error(f"Failed to load ESB credentials: {str(e)}")
                raise JubileeESBError("Failed to initialize Portal connection")
            if 'SecretString' not in base_url_response:
                logger.error("Failed to load Protal Connection credentials: SecretString not found")
                raise JubileeESBError("Failed to initialize ESB service")

            portal_credentials = json.loads(base_url_response['SecretString'])
            self.portal_graphql_url = portal_credentials['url']
            self.portal_graphql_api_key = portal_credentials['api_key']
            self.portal_graphql_region = portal_credentials['aws_region']

        except ClientError as e:
            logger.error(f"Failed to load ESB credentials: {str(e)}")
            raise JubileeESBError("Failed to initialize ESB service")

    def _project_api_call_to_portal(self, response: Response, api_name: str, api_method: str):
        mutation = """
        mutation CreateAPICall($input: CreateAPICallInput!) {
            createAPICall(input: $input) {
                apiCallId
                userId
                apiName
                apiMethod
                requestIPAddress
                requestHttpMethod
                requestTimestamp
                responseStatusCode
                responseResult
            }
        }
        """

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
                "userId": "",
                "apiName": api_name,
                "apiMethod": api_method,
                "requestIPAddress": response.request.headers.get('X-Forwarded-For',
                                                                 response.request.headers.get('Remote-Addr', '')),
                "requestHttpMethod": response.request.method,
                "requestTimestamp": int(time.time()),
                "responseStatusCode": response.status_code,
                "responseResult": responseResult
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
    def _make_api_call(self,
                       service: str,
                       url: str,
                       data: Dict[str, Any], is_post: bool = True):
        """
        Make API call with error handling and logging

        Args:
            service: Service name for logging
            url: API endpoint URL
            data: Request payload
        """
        try:
            headers = {
                "Authorization": self.authorization_jwt,
                "Content-Type": "application/json"
            }
            if is_post:
                response = requests.post(
                    f"{self.base_url}{url}",
                    json=data,
                    headers=headers,
                    timeout=30
                )
            else:
                response = requests.get(
                    f"{self.base_url}{url}",
                    headers=headers,
                    timeout=30
                )

            self._project_api_call_to_portal(response)
            response.raise_for_status()

            logger.info(f"Jubilee ESB: {service} API call successful")
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Jubilee ESB: {service} API call failed: {str(e)}")
            raise JubileeESBError(f"{service} API call failed: {str(e)}")
