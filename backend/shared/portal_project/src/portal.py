import json
import os
import time
import uuid
from http import HTTPStatus
from enum import Enum
import boto3
import requests
from aws_lambda_powertools import Logger, Tracer
from requests import Response

# init - load secrets
PORTAL_GRAPHQL_SECRET_ARN = os.getenv('PORTAL_GRAPHQL_SECRET_ARN', None)
assert PORTAL_GRAPHQL_SECRET_ARN, "PORTAL_GRAPHQL_SECRET_ARN environment variable is not set"

logger = Logger()
tracer = Tracer()

#enum document types

class DOCUMENT_TYPE(Enum):
    PASSPORT = "Passport"
    NATIONAL_ID = "NationalID"
    KRA_PIN_CERTIFICATE ="KRAPinCertificate"
    CERTIFICATE_OF_INCORPORATION = "CR12"

SUPPORTED_DOCUMENT_TYPES = [e.value for e in DOCUMENT_TYPE]    
    

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

    def capture_background_check(self, backgroud_check):
        """
        Create a new background check record in the portal using Amplify GraphQL API.
        
        Args:
            backgroud_check: Dictionary containing background check data
            
        Returns:
            The created background check record or None if there was an error
        """
        try:
            # Create a new background check
            create_mutation = """
                mutation CreateBackGroundCheck($input: CreateBackGroundCheckInput!) {
                    createBackGroundCheck(input: $input) {
                        backGroundCheckId
                        firstName
                        lastName
                    }
                }
            """
            
            # Prepare input with required fields from Amplify schema
            background_check_id = str(uuid.uuid4())
            
            # Map the input data to the schema fields
            document = {
                "backGroundCheckId": background_check_id,
                "firstName": backgroud_check.get("firstName"),
                "middleName": backgroud_check.get("middleName", ""),
                "lastName": backgroud_check.get("lastName"),
                "gender": backgroud_check.get("gender"),
                "dob": backgroud_check.get("dob"),
                "nationalIdentificationNumber": backgroud_check.get("nationalIdentificationNumber"),
                "countryCode": backgroud_check.get("countryCode"),
                "entityType": backgroud_check.get("entityType"),
                "sourceName": backgroud_check.get("sourceName"),
                "results": json.dumps(backgroud_check.get("result")) if backgroud_check.get("result") else None
            }
            
            create_variables = {
                "input": document
            }
            
            # Prepare the create request body
            create_payload = {
                'query': create_mutation,
                'variables': create_variables
            }
            
            # Make the create request to AppSync
            create_response = requests.post(
                self.PORTAL_GRAPHQL_URL,
                headers=self.headers,
                json=create_payload
            )
            
            # Check if create was successful
            if create_response.status_code == 200:
                create_result = create_response.json()
                if 'errors' in create_result:
                    logger.error(f"GraphQL Errors during create: {create_result['errors']}")
                    return None
                logger.info(f"Background check created successfully: {background_check_id}")
                return create_result['data']['createBackGroundCheck']
            else:
                logger.error(f"HTTP Error during create: {create_response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error creating background check: {str(e)}")
            return None

        
    def capture_doc_validation(self, documentType, s3Path, documentIdentifier, matchResults, keywords_checks,
                               validation_accuracy,processing_accuracy,overall_confidence):
        """
        Create a new document validation record in the portal using Amplify GraphQL API.
        
        Args:
            documentType: Type of document (ID, Passport, etc.)
            s3Path: Path to the document in S3
            documentIdentifier: Identifier for the document (ID number, passport number)
            matchResults: JSON object with match results
            keywords_checks: JSON object with keyword check results
            
        Returns:
            The created document validation record or None if there was an error
        """
        assert documentType.value in SUPPORTED_DOCUMENT_TYPES, f"Invalid document type: {documentType} expected one of {SUPPORTED_DOCUMENT_TYPES}"
        documentType = documentType.value
        try:
            # Create a new document validation
            create_mutation = """
                mutation CreateDocumentValidation($input: CreateDocumentValidationInput!) {
                    createDocumentValidation(input: $input) {
                        validationId
                        documentType
                        s3Path
                    }
                }
            """
            
            # Prepare input with required fields from Amplify schema
            validation_id = str(uuid.uuid4())
            document = {
                "validationId": validation_id,
                "documentType": documentType,
                "s3Path": s3Path,
                "documentIdentifier": documentIdentifier,
                "validation_accuracy": validation_accuracy,
                "processing_accuracy": processing_accuracy,
                "overall_confidence": overall_confidence,
                "matchResults": json.dumps(matchResults) if matchResults else None,
                "keywords_checks": json.dumps(keywords_checks) if keywords_checks else None
            }
            
            create_variables = {
                "input": document
            }
            
            # Prepare the create request body
            create_payload = {
                'query': create_mutation,
                'variables': create_variables
            }
            
            # Make the create request to AppSync
            create_response = requests.post(
                self.PORTAL_GRAPHQL_URL,
                headers=self.headers,
                json=create_payload
            )
            
            # Check if create was successful
            if create_response.status_code == 200:
                create_result = create_response.json()
                if 'errors' in create_result:
                    logger.error(f"GraphQL Errors during create: {create_result['errors']}")
                    return None
                logger.info(f"Document validation created successfully: {validation_id}")
                return create_result['data']['createDocumentValidation']
            else:
                logger.error(f"HTTP Error during create: {create_response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error creating document validation: {str(e)}")
            return None
    def capture_doc_verification(self, documentType,documentIdentifier, matchResults,validation_accuracy,processing_accuracy):
        """
        Create a new document verification record in the portal using Amplify GraphQL API.

        Args:
            documentType: Type of document (ID, Passport, etc.)
            documentIdentifier: Identifier for the document (ID number, passport number)
            matchResults: JSON object with match results

        Returns:
            The created document verification record or None if there was an error
        """
        assert documentType.value in SUPPORTED_DOCUMENT_TYPES, f"Invalid document type: {documentType} expected one of {SUPPORTED_DOCUMENT_TYPES}"
        documentType = documentType.value
        
        try:
            # Create a new document verification
            create_mutation = """
                mutation CreateDocumentVerification($input: CreateDocumentVerificationInput!) {
                    createDocumentVerification(input: $input) {
                        verificationId
                        documentType
                    }
                }
            """

            # Prepare input with required fields from Amplify schema
            verification_id = str(uuid.uuid4())
            document = {
                "verificationId": verification_id,
                "documentType": documentType,
                "documentIdentifier": documentIdentifier,
                "validation_accuracy": validation_accuracy,
                "processing_accuracy": processing_accuracy,
                "matchResults": json.dumps(matchResults) if matchResults else None
            }

            create_variables = {
                "input": document
            }

            # Prepare the create request body
            create_payload = {
                'query': create_mutation,
                'variables': create_variables
            }

            # Make the create request to AppSync
            create_response = requests.post(
                self.PORTAL_GRAPHQL_URL,
                headers=self.headers,
                json=create_payload
            )

            # Check if create was successful
            if create_response.status_code == 200:
                create_result = create_response.json()
                if 'errors' in create_result:
                    logger.error(f"GraphQL Errors during create: {create_result['errors']}")
                    return None
                logger.info(f"Document verification created successfully: {verification_id}")
                return create_result['data']['createDocumentVerification']
            else:
                logger.error(f"HTTP Error during create: {create_response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error creating document verification: {str(e)}")
            return None
        pass
        
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
        isResponse = False
        try:
            200 == response.status_code
            isResponse = False
        except:
            pass
        if isResponse:
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
