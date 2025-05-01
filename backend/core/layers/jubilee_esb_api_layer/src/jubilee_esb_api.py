#
"""
Suggest a python lambda code sample for a library. (used by other lambdas)
This library should validate given data (dict) against APIs,
including IPRS (Integrated Population Registration System), KRA (Kenya Revenue Authority), and LexisNexis, ensuring the authenticity and accuracy of the submitted information.
The library should be called Jubilee ESB API

Below are the api calls that it should supprt
..........
IPRS: Search IPRS
IPRS: Ping IPRS
IPRS: Search by Alien ID
IPRS: Search by Passport Number
IPRS: Search by Birth Certificate Number
IPRS: Search by Death Certificate Number
IPRS: Bulk IPRS Search
LEXISNEXIS: Search Record
KRA: Validate ID Number
......
"""

import json
import os
from typing import Dict, Any, List

import boto3
import requests
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate
from botocore.exceptions import ClientError

logger = Logger()
tracer = Tracer()


class JubileeESBError(Exception):
    """Custom exception for ESB validation errors"""
    pass


class JubileeESBAPI:
    def __init__(self):
        """Initialize Jubilee ESB API with AWS Secrets Manager configuration"""
        self.secrets_client = boto3.client('secretsmanager')
        self._load_credentials()

    def _retrieve_jwt_token(self, username: str, password: str) -> str:
        try:
            login_data = {
                "username": username,
                "password": password
            }

            headers = {
                "Content-Type": "application/json",
                "X-Jubilee-Client-ID": os.environ.get('JUBILEE_CLIENT_ID', '')
            }

            response = requests.post(
                f"{self.base_url}/login",
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

    def _load_credentials(self) -> None:
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

    # IPRS Methods
    @tracer.capture_method
    def iprs_search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        This interface searches for an individual in the system.
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "identifier": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["identifier", "value"]
            }
            validate(event=data, schema=schema)

            return self._make_api_call(
                "IPRS",
                f"/iprs/searchV2/{self.business}",
                data
            )
        except Exception as e:
            logger.error(f"IPRS search failed: {str(e)}")
            raise JubileeESBError(f"IPRS search failed: {str(e)}")

    @tracer.capture_method
    def iprs_ping(self) -> Dict[str, Any]:
        """Check IPRS service availability"""
        try:
            return self._make_api_call(
                "IPRS",
                f"{self.iprs_base_url}/ping",
                {},
                self.iprs_credentials
            )
        except Exception as e:
            logger.error(f"IPRS ping failed: {str(e)}")
            raise JubileeESBError(f"IPRS ping failed: {str(e)}")

    @tracer.capture_method
    def iprs_search_alien_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search IPRS using Alien ID

        Args:
            data: Dictionary containing alien ID number
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "alien_id": {"type": "string"}
                },
                "required": ["alien_id"]
            }
            validate(event=data, schema=schema)

            return self._make_api_call(
                "IPRS",
                f"{self.iprs_base_url}/search/alien",
                data,
                self.iprs_credentials
            )
        except Exception as e:
            logger.error(f"IPRS alien ID search failed: {str(e)}")
            raise JubileeESBError(f"IPRS alien ID search failed: {str(e)}")

    @tracer.capture_method
    def iprs_search_passport(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search IPRS using Passport Number

        Args:
            data: Dictionary containing passport number
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "passport_number": {"type": "string"}
                },
                "required": ["passport_number"]
            }
            validate(event=data, schema=schema)

            return self._make_api_call(
                "IPRS",
                f"{self.iprs_base_url}/search/passport",
                data,
                self.iprs_credentials
            )
        except Exception as e:
            logger.error(f"IPRS passport search failed: {str(e)}")
            raise JubileeESBError(f"IPRS passport search failed: {str(e)}")

    @tracer.capture_method
    def iprs_search_birth_certificate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search IPRS using Birth Certificate Number

        Args:
            data: Dictionary containing birth certificate number
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "birth_certificate_number": {"type": "string"}
                },
                "required": ["birth_certificate_number"]
            }
            validate(event=data, schema=schema)

            return self._make_api_call(
                "IPRS",
                f"{self.iprs_base_url}/search/birth",
                data,
                self.iprs_credentials
            )
        except Exception as e:
            logger.error(f"IPRS birth certificate search failed: {str(e)}")
            raise JubileeESBError(f"IPRS birth certificate search failed: {str(e)}")

    @tracer.capture_method
    def iprs_search_death_certificate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search IPRS using Death Certificate Number

        Args:
            data: Dictionary containing death certificate number
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "death_certificate_number": {"type": "string"}
                },
                "required": ["death_certificate_number"]
            }
            validate(event=data, schema=schema)

            return self._make_api_call(
                "IPRS",
                f"{self.iprs_base_url}/search/death",
                data,
                self.iprs_credentials
            )
        except Exception as e:
            logger.error(f"IPRS death certificate search failed: {str(e)}")
            raise JubileeESBError(f"IPRS death certificate search failed: {str(e)}")

    @tracer.capture_method
    def iprs_bulk_search(self, data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Perform bulk IPRS search

        Args:
            data: Dictionary containing list of search requests
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "searches": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id_number": {"type": "string"},
                                "search_type": {"type": "string"}
                            },
                            "required": ["id_number"]
                        }
                    }
                },
                "required": ["searches"]
            }
            validate(event=data, schema=schema)

            return self._make_api_call(
                "IPRS",
                f"{self.iprs_base_url}/search/bulk",
                data,
                self.iprs_credentials
            )
        except Exception as e:
            logger.error(f"IPRS bulk search failed: {str(e)}")
            raise JubileeESBError(f"IPRS bulk search failed: {str(e)}")

    # LexisNexis Methods
    @tracer.capture_method
    def lexisnexis_search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search LexisNexis records

        Args:
            data: Dictionary containing search parameters
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "reference_id": {"type": "string"},
                    "search_parameters": {"type": "object"}
                },
                "required": ["reference_id", "search_parameters"]
            }
            validate(event=data, schema=schema)

            return self._make_api_call(
                "LexisNexis",
                f"{self.lexisnexis_base_url}/search",
                data,
                self.lexisnexis_credentials
            )
        except Exception as e:
            logger.error(f"LexisNexis search failed: {str(e)}")
            raise JubileeESBError(f"LexisNexis search failed: {str(e)}")

    # KRA Methods
    @tracer.capture_method
    def kra_validate_id(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        This interface validates an id number.

        Args:
            data: Dictionary containing ID number
        """
        try:
            schema = {
                "type": "object",
                "properties": {
                    "country": {"type": "string"},
                    "idNo": {"type": "string"}
                },
                "required": ["idNo", "country"]
            }
            validate(event=data, schema=schema)
            idNo = data['idNo']
            country = data['country']
            return self._make_api_call(
                "KRA",
                f"/api/v1/kra/validate-id?typeOfTaxpayer={country}&taxpayerID={idNo}",
                None,
                is_post=False
            )
        except Exception as e:
            logger.error(f"KRA ID validation failed: {str(e)}")
            raise JubileeESBError(f"KRA ID validation failed: {str(e)}")

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
            """
            200 OK Success #The request was sent successfully. Returns a success message.
            400 Bad RequestInvalid #RequestThe request contained invalid parameters.
            401 UnauthorizedAuthentication #FailedThe JWT token is missing, invalid, or expired.
            404 Not Found #Not FoundNo matching records were found.
            417 Invalid #IdNot FoundNo matching records were found.
            500 Internal #Server ErrorServer ErrorAn unexpected error occurred on the server.
            """
            response.raise_for_status()

            logger.info(f"Jubilee ESB: {service} API call successful")
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Jubilee ESB: {service} API call failed: {str(e)}")
            raise JubileeESBError(f"{service} API call failed: {str(e)}")
