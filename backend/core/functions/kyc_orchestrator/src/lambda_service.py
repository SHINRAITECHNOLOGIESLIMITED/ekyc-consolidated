"""
Lambda Service for Action Handler Invocations
SOW Day 4-5 Requirement: Connect action handlers to existing Lambda functions

Provides service layer for invoking existing Lambda functions from action handlers.
Implements performance optimization and error handling for function invocations.
"""

import json
import os
import boto3
from typing import Dict, Any, Optional
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError
import asyncio
import concurrent.futures
from datetime import datetime

logger = Logger()


class LambdaService:
    """
    Service class for invoking existing Lambda functions from action handlers.
    Implements SOW requirements for <3 second response times and error handling.
    """

    def __init__(self):
        self.lambda_client = boto3.client('lambda')
        self.function_names = self._get_function_names()

    def _get_function_names(self) -> Dict[str, str]:
        """
        Get the actual deployed Lambda function names.
        Uses environment variables or AWS API to find current function names.
        """
        # Function name mapping based on current deployment
        return {
            'document_validation': os.environ.get('DOCUMENT_VALIDATION_FUNCTION',
                                                'jubilee-ekyc-backend-DocumentValidationFn-sX697rYQ8AYw'),
            'government_verification': os.environ.get('GOVERNMENT_VERIFICATION_FUNCTION',
                                                   'jubilee-ekyc-backend-GovernmentVerificationFn-i19xxoO1d3ia'),
            'background_checks': os.environ.get('BACKGROUND_CHECK_FUNCTION',
                                              'jubilee-ekyc-backend-BackgroundChecksFn-U37eW5O12VZk'),
            'face_liveness': os.environ.get('FACE_LIVENESS_FUNCTION',
                                          'jubilee-ekyc-backend-FaceLivenessFn-M7Sci6jlul3P'),
            'registration': os.environ.get('REGISTRATION_FUNCTION',
                                         'jubilee-ekyc-backend-RegistrationFn-Tt4n5IS2aGxw'),
            'document_streaming': os.environ.get('DOCUMENT_STREAMING_FUNCTION',
                                               'jubilee-ekyc-backend-DocumentStreamingFn-CIEfZ4k3epfo'),
            'certification': os.environ.get('CERTIFICATION_FUNCTION',
                                          'jubilee-ekyc-backend-CertificationFn-XTZ04Ew73YMw')
        }

    def invoke_function(self, function_key: str, payload: Dict[str, Any],
                       invocation_type: str = 'RequestResponse') -> Dict[str, Any]:
        """
        Invoke a Lambda function with the specified payload.

        Args:
            function_key: Key to identify the function (e.g., 'document_validation')
            payload: Payload to send to the function
            invocation_type: 'RequestResponse' for sync, 'Event' for async

        Returns:
            Function response or error information
        """
        function_name = self.function_names.get(function_key)
        if not function_name:
            logger.error(f"Function key '{function_key}' not found in function mapping")
            return {
                'success': False,
                'error': {
                    'message': f'Function {function_key} not configured',
                    'error_code': 'FUNCTION_NOT_FOUND'
                }
            }

        try:
            logger.info(f"Invoking function {function_name} with payload size: {len(json.dumps(payload))}")

            response = self.lambda_client.invoke(
                FunctionName=function_name,
                InvocationType=invocation_type,
                Payload=json.dumps(payload)
            )

            if invocation_type == 'RequestResponse':
                # Process synchronous response
                response_payload = json.loads(response['Payload'].read())

                # Check for function errors
                if response.get('FunctionError'):
                    logger.error(f"Function {function_name} returned error: {response['FunctionError']}")
                    return {
                        'success': False,
                        'error': {
                            'message': f'Function execution error: {response["FunctionError"]}',
                            'error_code': 'FUNCTION_EXECUTION_ERROR',
                            'details': response_payload
                        }
                    }

                logger.info(f"Function {function_name} executed successfully")
                return {
                    'success': True,
                    'response': response_payload,
                    'execution_time': self._extract_execution_time(response)
                }
            else:
                # Async invocation - just return success
                return {
                    'success': True,
                    'message': f'Function {function_name} invoked asynchronously',
                    'request_id': response.get('ResponseMetadata', {}).get('RequestId')
                }

        except ClientError as e:
            logger.error(f"AWS error invoking function {function_name}: {e}")
            return {
                'success': False,
                'error': {
                    'message': f'AWS error: {str(e)}',
                    'error_code': 'AWS_CLIENT_ERROR',
                    'aws_error_code': e.response['Error']['Code'] if e.response else None
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error invoking function {function_name}: {e}")
            return {
                'success': False,
                'error': {
                    'message': f'Unexpected error: {str(e)}',
                    'error_code': 'INVOCATION_ERROR'
                }
            }

    def _extract_execution_time(self, response: Dict[str, Any]) -> Optional[float]:
        """Extract execution time from Lambda response metadata."""
        try:
            # Look for execution time in response metadata
            log_result = response.get('LogResult', '')
            if log_result:
                # Parse execution time from logs if available
                # This is a best-effort extraction
                pass
            return None
        except Exception:
            return None

    # Document Validation Functions
    def invoke_document_validation(self, document_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke document validation function for specific document type.

        Args:
            document_type: Type of document (nationalid, passport, krapincertificate, cr12)
            data: Document validation data

        Returns:
            Validation result
        """
        # Create event payload matching the existing function's expected format
        event_payload = {
            'httpMethod': 'POST',
            'path': f'/document/{document_type}',
            'body': json.dumps(data),
            'headers': {'Content-Type': 'application/json'},
            'requestContext': {'requestId': f'action-{datetime.utcnow().isoformat()}'}
        }

        return self.invoke_function('document_validation', event_payload)

    # Government Verification Functions
    def invoke_government_verification(self, verification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke government verification function for specific verification type.

        Args:
            verification_type: Type of verification (nationalid, passport, kra)
            data: Verification data

        Returns:
            Verification result
        """
        # Create event payload matching the existing function's expected format
        event_payload = {
            'httpMethod': 'POST',
            'path': f'/government/{verification_type}',
            'body': json.dumps(data),
            'headers': {'Content-Type': 'application/json'},
            'requestContext': {'requestId': f'action-{datetime.utcnow().isoformat()}'}
        }

        return self.invoke_function('government_verification', event_payload)

    # Other Service Functions
    def invoke_background_check(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke background check function."""
        event_payload = {
            'httpMethod': 'POST',
            'path': '/background-check',
            'body': json.dumps(data),
            'headers': {'Content-Type': 'application/json'},
            'requestContext': {'requestId': f'action-{datetime.utcnow().isoformat()}'}
        }

        return self.invoke_function('background_checks', event_payload)

    def invoke_face_liveness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke face liveness function."""
        # FaceLivenessFn expects action: "create" or "get_results" in the body
        # If userId is provided, create a session; if sessionId, get results
        liveness_action = 'get_results' if 'sessionId' in data else 'create'

        # Merge the action with the data
        liveness_payload = {
            'action': liveness_action,
            **data
        }

        event_payload = {
            'body': json.dumps(liveness_payload),
            'headers': {'Content-Type': 'application/json'},
            'requestContext': {'requestId': f'action-{datetime.utcnow().isoformat()}'}
        }

        return self.invoke_function('face_liveness', event_payload)

    def invoke_registration(self, registration_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke registration function for agent or customer."""
        event_payload = {
            'httpMethod': 'POST',
            'path': f'/{registration_type}-registration',
            'body': json.dumps(data),
            'headers': {'Content-Type': 'application/json'},
            'requestContext': {'requestId': f'action-{datetime.utcnow().isoformat()}'}
        }

        return self.invoke_function('registration', event_payload)

    def invoke_document_streaming(self, bucket_type: str, document_key: str) -> Dict[str, Any]:
        """Invoke document streaming function."""
        event_payload = {
            'httpMethod': 'GET',
            'pathParameters': {
                'bucketType': bucket_type,
                'documentKey': document_key
            },
            'requestContext': {'requestId': f'action-{datetime.utcnow().isoformat()}'}
        }

        return self.invoke_function('document_streaming', event_payload)

    # Performance Optimization Methods
    def invoke_parallel(self, invocations: list) -> Dict[str, Any]:
        """
        Invoke multiple functions in parallel for performance optimization.
        SOW Requirement: <3 seconds response time.

        Args:
            invocations: List of (function_key, payload) tuples

        Returns:
            Combined results from all invocations
        """
        logger.info(f"Starting parallel invocation of {len(invocations)} functions")

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all invocations
            future_to_key = {
                executor.submit(
                    self.invoke_function,
                    inv['function_key'],
                    inv['payload']
                ): inv['action'] for inv in invocations
            }

            results = {}
            for future in concurrent.futures.as_completed(future_to_key, timeout=30):
                action = future_to_key[future]
                try:
                    result = future.result()
                    results[action] = result
                    logger.info(f"Parallel invocation completed for action: {action}")
                except Exception as e:
                    logger.error(f"Parallel invocation failed for action {action}: {e}")
                    results[action] = {
                        'success': False,
                        'error': {
                            'message': f'Parallel execution error: {str(e)}',
                            'error_code': 'PARALLEL_EXECUTION_ERROR'
                        }
                    }

            return results

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all configured Lambda functions.

        Returns:
            Health status of all functions
        """
        health_status = {}

        for function_key, function_name in self.function_names.items():
            try:
                # Use get-function to check if function exists and is accessible
                response = self.lambda_client.get_function(FunctionName=function_name)
                health_status[function_key] = {
                    'status': 'healthy',
                    'function_name': function_name,
                    'last_modified': response['Configuration']['LastModified'],
                    'state': response['Configuration']['State']
                }
            except ClientError as e:
                health_status[function_key] = {
                    'status': 'unhealthy',
                    'function_name': function_name,
                    'error': str(e)
                }
            except Exception as e:
                health_status[function_key] = {
                    'status': 'error',
                    'function_name': function_name,
                    'error': str(e)
                }

        return {
            'overall_health': 'healthy' if all(
                status['status'] == 'healthy'
                for status in health_status.values()
            ) else 'degraded',
            'functions': health_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }