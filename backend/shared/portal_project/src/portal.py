import json
import os
import time
import uuid
from http import HTTPStatus

import boto3
import requests
from aws_lambda_powertools import Logger, Tracer
from requests import Response

# init - load secrets
PORTAL_GRAPHQL_SECRET_ARN = os.getenv('PORTAL_GRAPHQL_SECRET_ARN', None)
assert PORTAL_GRAPHQL_SECRET_ARN, "PORTAL_GRAPHQL_SECRET_ARN environment variable is not set"

logger = Logger()
tracer = Tracer()


class Portal:
    def __init__(self):
        self._load_secrets()

    def _load_secrets(self):
        secrets_client = boto3.client('secretsmanager')
        logger.info(f"Loading portal graphql credentials from {PORTAL_GRAPHQL_SECRET_ARN}")
        portal_credentials_response = secrets_client.get_secret_value(
            SecretId=PORTAL_GRAPHQL_SECRET_ARN
        )
        if 'SecretString' not in portal_credentials_response:
            logger.error("Failed to load Portal Connection credentials: SecretString not found")
            raise Exception("Failed to load Portal service")
        _portal_credentials = json.loads(portal_credentials_response['SecretString'])
        self.PORTAL_GRAPHQL_URL = _portal_credentials['url']
        assert self.PORTAL_GRAPHQL_URL != "https://example.com", "Portal URL and API Key has not been configured in Secrets Manager"

        self.PORTAL_GRAPHQL_API_KEY = _portal_credentials['api_key']
        self.headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.PORTAL_GRAPHQL_API_KEY
        }
        logger.info(f"Loaded portal graphql credentials. GraphQL URL: {self.PORTAL_GRAPHQL_URL}")

    def update_kyc_document(self, document):
        try:
            mutation = """
                mutation CreateKYCDocument($input: CreateKYCDocumentInput!) {
                    createKYCDocument(input: $input) {
                        documentId
                    }
                }
            """

            variables = {
                "input": document
            }

            # Prepare the request body
            payload = {
                'query': mutation,
                'variables': variables
            }
            # Make the request to AppSync
            response = requests.post(
                self.PORTAL_GRAPHQL_URL,
                headers=self.headers,
                json=payload
            )
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                if 'errors' in result:
                    logger.error(f"GraphQL Errors: {result['errors']}")
                    return None
                return result['data']['createAPICall']
            else:
                print(f"HTTP Error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error projecting to portal: {str(e)}")
            return None

    def log_api_call(self, response: Response, api_name: str, api_method: str, duration_ms: int,
                     trace_id: str, capture_data=False):
        mutation = """
            mutation CreateAPICall($input: CreateAPICallInput!) {
                createAPICall(input: $input) {
                    apiCallId
                }
            }
            """
        request_data = {}
        response_data = {}
        if isinstance(request_data, Response):
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
            try:
                responseResult = HTTPStatus(response.status_code).phrase
            except ValueError:
                responseResult = f"Unknown Status Code: {response.status_code}"
            requestHttpMethod = response.request.method
            responseStatusCode = response.status_code
        else:
            logger.info(response)
            responseResult = ""
            requestHttpMethod = ""
            responseStatusCode = 0
        # Variables for the mutation
        variables = {
            "input": {
                "apiCallId": str(uuid.uuid4()),
                "durationMs": duration_ms,
                "traceId": trace_id,
                "apiName": api_name,
                "apiMethod": api_method,
                "requestIPAddress": "",
                "requestHttpMethod": requestHttpMethod,
                "requestTimestamp": int(time.time()),
                "responseStatusCode": responseStatusCode,
                "responseResult": responseResult,
                "requestData": json.dumps(request_data, indent=4),
                "responseData": json.dumps(response_data, indent=4)
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
                self.PORTAL_GRAPHQL_URL,
                headers=self.headers,
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
