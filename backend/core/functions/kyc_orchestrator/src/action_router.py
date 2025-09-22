"""
Action-Based Router for KYC Operations
SOW Day 2 Requirement: Single /kyc endpoint with action parameter routing

Maps all existing endpoints to action-based operations:
- Document Operations: /document/* -> validate_*
- Government Operations: /government/* -> government_verify_*
- Other Operations: Direct mapping to action names
"""

import json
from typing import Dict, Any, Optional, Callable
from aws_lambda_powertools import Logger
from security import secure_response_factory
from response_schemas import create_standardized_response, HTTPStatusMapper
from feature_flags import (
    should_use_action_routing,
    is_action_enabled,
    FeatureFlag,
    FeatureFlagDecorator
)
from lambda_service import LambdaService

logger = Logger()


class ActionRouter:
    """
    Routes action-based requests to appropriate handlers.
    Implements SOW requirement for single /kyc endpoint with action parameters.
    """

    def __init__(self):
        self.action_handlers = self._initialize_action_handlers()
        self.lambda_service = LambdaService()

    def _initialize_action_handlers(self) -> Dict[str, Callable]:
        """
        Initialize mapping of actions to handler functions.
        SOW requires 10+ operations consolidated into actions.
        """
        return {
            # Document Validation Actions (4 operations)
            'validate_nationalid': self._handle_nationalid_validation,
            'validate_passport': self._handle_passport_validation,
            'validate_krapincertificate': self._handle_kra_validation,
            'validate_cr12': self._handle_cr12_validation,

            # Government Verification Actions (3 operations)
            'government_verify_nationalid': self._handle_nationalid_verification,
            'government_verify_passport': self._handle_passport_verification,
            'government_verify_kra': self._handle_kra_verification,

            # Other KYC Operations (4 operations)
            'background_check': self._handle_background_check,
            'face_liveness': self._handle_face_liveness,
            'agent_registration': self._handle_agent_registration,
            'customer_registration': self._handle_customer_registration,

            # Document Streaming (1 operation)
            'stream_document': self._handle_document_streaming,

            # Legacy workflow operation (maintains backward compatibility)
            'process_workflow': self._handle_workflow_orchestration
        }

    def route_action(self, action: str, data: Dict[str, Any],
                    request_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Route an action to its appropriate handler.
        SOW Performance Requirement: <3 seconds response time.

        Args:
            action: The action to perform (e.g., 'validate_nationalid')
            data: The request data for the action
            request_context: Optional request context from API Gateway

        Returns:
            Standardized action response
        """
        start_time = self._get_timestamp()
        logger.info(f"Routing action: {action} at {start_time}")

        # Check if action-based routing is enabled via feature flag
        if not should_use_action_routing(request_context):
            logger.info("Action-based routing disabled via feature flag, falling back to legacy workflow")
            return self._handle_workflow_orchestration(data, request_context)

        # Check if specific action is enabled
        if not is_action_enabled(action, request_context):
            logger.info(f"Action {action} disabled via feature flag")
            error_response = create_standardized_response(
                action=action,
                success=False,
                error={
                    'message': f'Action {action} is currently disabled',
                    'error_code': 'ACTION_DISABLED',
                    'fallback_available': True
                },
                request_context=request_context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code(action, error_response)
            return secure_response_factory(status_code, error_response)

        # Validate action exists
        if action not in self.action_handlers:
            error_response = create_standardized_response(
                action=action,
                success=False,
                error={
                    'message': f'Unknown action: {action}',
                    'valid_actions': list(self.action_handlers.keys()),
                    'error_code': 'INVALID_ACTION'
                },
                request_context=request_context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code(action, error_response)
            return secure_response_factory(status_code, error_response)

        try:
            # Execute action handler with performance monitoring
            handler = self.action_handlers[action]
            result = handler(data, request_context)

            # Calculate execution time for performance monitoring
            end_time = self._get_timestamp()
            execution_time = self._calculate_execution_time(start_time, end_time)
            logger.info(f"Action {action} completed in {execution_time}ms")

            # SOW Requirement: Log slow responses (>2.5 seconds)
            if execution_time > 2500:
                logger.warning(f"Slow action execution: {action} took {execution_time}ms (>2.5s threshold)")

            # Ensure result is in standardized format
            if not isinstance(result, dict) or 'statusCode' not in result:
                # Convert to standardized response format
                standardized_result = create_standardized_response(
                    action=action,
                    success=True,
                    result=result,
                    request_id=request_context.get('requestId') if request_context else None,
                    execution_time=execution_time
                )
                status_code = HTTPStatusMapper.map_result_to_status_code(action, standardized_result)
                return secure_response_factory(status_code, standardized_result)

            # Add execution time to existing response
            if isinstance(result, dict) and 'body' in result:
                try:
                    body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
                    body['execution_time_ms'] = execution_time
                    result['body'] = json.dumps(body) if isinstance(result['body'], str) else body
                except Exception:
                    # If we can't modify the response, that's okay
                    pass

            return result

        except Exception as e:
            logger.error(f"Error executing action {action}: {str(e)}")
            error_response = create_standardized_response(
                action=action,
                success=False,
                error={
                    'message': str(e),
                    'error_code': 'EXECUTION_ERROR'
                },
                request_id=request_context.get('requestId') if request_context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code(action, error_response)
            return secure_response_factory(status_code, error_response)

    def get_action_schema(self, action: str) -> Dict[str, Any]:
        """
        Get the expected data schema for a specific action.

        Args:
            action: The action to get schema for

        Returns:
            JSON schema for the action's data requirements
        """
        schemas = {
            'validate_nationalid': {
                'type': 'object',
                'required': ['nationalIdUrl', 'personalData'],
                'properties': {
                    'nationalIdUrl': {'type': 'string', 'format': 'uri'},
                    'personalData': {
                        'type': 'object',
                        'required': ['name', 'idNumber'],
                        'properties': {
                            'name': {'type': 'string'},
                            'idNumber': {'type': 'string'},
                            'dateOfBirth': {'type': 'string', 'format': 'date'},
                            'gender': {'type': 'string', 'enum': ['Male', 'Female']}
                        }
                    }
                }
            },
            'validate_passport': {
                'type': 'object',
                'required': ['passportUrl', 'personalData'],
                'properties': {
                    'passportUrl': {'type': 'string', 'format': 'uri'},
                    'personalData': {
                        'type': 'object',
                        'required': ['name', 'passportNumber'],
                        'properties': {
                            'name': {'type': 'string'},
                            'passportNumber': {'type': 'string'},
                            'dateOfBirth': {'type': 'string', 'format': 'date'},
                            'nationality': {'type': 'string'}
                        }
                    }
                }
            },
            'validate_krapincertificate': {
                'type': 'object',
                'required': ['kraUrl', 'personalData'],
                'properties': {
                    'kraUrl': {'type': 'string', 'format': 'uri'},
                    'personalData': {
                        'type': 'object',
                        'required': ['name', 'pinNumber'],
                        'properties': {
                            'name': {'type': 'string'},
                            'pinNumber': {'type': 'string'},
                            'dateOfBirth': {'type': 'string', 'format': 'date'}
                        }
                    }
                }
            },
            'validate_cr12': {
                'type': 'object',
                'required': ['cr12Url', 'companyData'],
                'properties': {
                    'cr12Url': {'type': 'string', 'format': 'uri'},
                    'companyData': {
                        'type': 'object',
                        'required': ['companyName', 'registrationNumber'],
                        'properties': {
                            'companyName': {'type': 'string'},
                            'registrationNumber': {'type': 'string'},
                            'incorporationDate': {'type': 'string', 'format': 'date'}
                        }
                    }
                }
            },
            'government_verify_nationalid': {
                'type': 'object',
                'required': ['personalData'],
                'properties': {
                    'personalData': {
                        'type': 'object',
                        'required': ['name', 'idNumber'],
                        'properties': {
                            'name': {'type': 'string'},
                            'idNumber': {'type': 'string'},
                            'dateOfBirth': {'type': 'string', 'format': 'date'}
                        }
                    }
                }
            },
            'background_check': {
                'type': 'object',
                'required': ['personalData'],
                'properties': {
                    'personalData': {
                        'type': 'object',
                        'required': ['name'],
                        'properties': {
                            'name': {'type': 'string'},
                            'dateOfBirth': {'type': 'string', 'format': 'date'},
                            'nationality': {'type': 'string'}
                        }
                    }
                }
            },
            'face_liveness': {
                'type': 'object',
                'required': ['faceImageUrl'],
                'properties': {
                    'faceImageUrl': {'type': 'string', 'format': 'uri'},
                    'sessionId': {'type': 'string'}
                }
            },
            'agent_registration': {
                'type': 'object',
                'required': ['agentData'],
                'properties': {
                    'agentData': {
                        'type': 'object',
                        'required': ['name', 'email', 'agentType'],
                        'properties': {
                            'name': {'type': 'string'},
                            'email': {'type': 'string', 'format': 'email'},
                            'agentType': {'type': 'string', 'enum': ['individual', 'business']},
                            'phoneNumber': {'type': 'string'},
                            'licenseNumber': {'type': 'string'}
                        }
                    }
                }
            },
            'customer_registration': {
                'type': 'object',
                'required': ['customerData'],
                'properties': {
                    'customerData': {
                        'type': 'object',
                        'required': ['name', 'email'],
                        'properties': {
                            'name': {'type': 'string'},
                            'email': {'type': 'string', 'format': 'email'},
                            'phoneNumber': {'type': 'string'},
                            'dateOfBirth': {'type': 'string', 'format': 'date'}
                        }
                    }
                }
            },
            'stream_document': {
                'type': 'object',
                'required': ['bucketType', 'documentKey'],
                'properties': {
                    'bucketType': {'type': 'string'},
                    'documentKey': {'type': 'string'}
                }
            }
        }

        return schemas.get(action, {'type': 'object'})

    def _get_timestamp(self) -> str:
        """Get ISO timestamp for responses."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'

    def _calculate_execution_time(self, start_time: str, end_time: str) -> float:
        """Calculate execution time in milliseconds."""
        from datetime import datetime
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            return (end - start).total_seconds() * 1000
        except Exception:
            return 0.0

    def route_parallel_actions(self, actions: list) -> Dict[str, Any]:
        """
        Route multiple actions in parallel for performance optimization.
        SOW Requirement: <3 seconds response time via parallel processing.

        Args:
            actions: List of action dictionaries with 'action', 'data', and optional 'context'

        Returns:
            Combined results from all actions
        """
        logger.info(f"Processing {len(actions)} actions in parallel")
        start_time = self._get_timestamp()

        # Prepare invocations for the Lambda service
        invocations = []
        for action_request in actions:
            action = action_request.get('action')
            data = action_request.get('data', {})

            # Map action to Lambda function for parallel processing
            if action.startswith('validate_'):
                doc_type = action.replace('validate_', '')
                invocations.append({
                    'action': action,
                    'function_key': 'document_validation',
                    'payload': {
                        'httpMethod': 'POST',
                        'path': f'/document/{doc_type}',
                        'body': json.dumps(data),
                        'headers': {'Content-Type': 'application/json'},
                        'requestContext': {'requestId': f'parallel-{action}'}
                    }
                })
            elif action.startswith('government_verify_'):
                verify_type = action.replace('government_verify_', '')
                invocations.append({
                    'action': action,
                    'function_key': 'government_verification',
                    'payload': {
                        'httpMethod': 'POST',
                        'path': f'/government/{verify_type}',
                        'body': json.dumps(data),
                        'headers': {'Content-Type': 'application/json'},
                        'requestContext': {'requestId': f'parallel-{action}'}
                    }
                })
            # Add other action types as needed

        # Execute parallel invocations if we have any
        if invocations:
            parallel_results = self.lambda_service.invoke_parallel(invocations)
        else:
            # Fall back to sequential processing for unsupported parallel actions
            parallel_results = {}
            for action_request in actions:
                action = action_request.get('action')
                data = action_request.get('data', {})
                context = action_request.get('context')
                parallel_results[action] = self.route_action(action, data, context)

        # Calculate total execution time
        end_time = self._get_timestamp()
        total_execution_time = self._calculate_execution_time(start_time, end_time)
        logger.info(f"Parallel processing completed in {total_execution_time}ms")

        return {
            'success': True,
            'results': parallel_results,
            'total_execution_time_ms': total_execution_time,
            'actions_processed': len(actions),
            'timestamp': end_time
        }

    # Action Handler Methods
    # These will invoke the existing Lambda functions via boto3

    def _handle_nationalid_validation(self, data: Dict[str, Any],
                                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle national ID document validation."""
        logger.info("Processing national ID validation")

        try:
            # Invoke existing DocumentValidationFn for national ID
            result = self.lambda_service.invoke_document_validation('nationalid', data)

            if not result['success']:
                logger.error(f"National ID validation failed: {result['error']}")
                error_response = create_standardized_response(
                    action='validate_nationalid',
                    success=False,
                    error=result['error'],
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('validate_nationalid', error_response)
                return secure_response_factory(status_code, error_response)

            # Process successful response
            validation_response = result['response']
            standardized_result = create_standardized_response(
                action='validate_nationalid',
                success=True,
                result=validation_response,
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('validate_nationalid', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in national ID validation: {e}")
            error_response = create_standardized_response(
                action='validate_nationalid',
                success=False,
                error={
                    'message': f'Validation processing error: {str(e)}',
                    'error_code': 'VALIDATION_PROCESSING_ERROR'
                },
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('validate_nationalid', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_passport_validation(self, data: Dict[str, Any],
                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle passport document validation."""
        logger.info("Processing passport validation")

        try:
            result = self.lambda_service.invoke_document_validation('passport', data)

            if not result['success']:
                logger.error(f"Passport validation failed: {result['error']}")
                error_response = create_standardized_response(
                    action='validate_passport',
                    success=False,
                    error=result['error'],
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('validate_passport', error_response)
                return secure_response_factory(status_code, error_response)

            validation_response = result['response']
            standardized_result = create_standardized_response(
                action='validate_passport',
                success=True,
                result=validation_response,
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('validate_passport', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in passport validation: {e}")
            error_response = create_standardized_response(
                action='validate_passport',
                success=False,
                error={
                    'message': f'Validation processing error: {str(e)}',
                    'error_code': 'VALIDATION_PROCESSING_ERROR'
                },
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('validate_passport', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_kra_validation(self, data: Dict[str, Any],
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle KRA PIN certificate validation."""
        logger.info("Processing KRA PIN validation")

        try:
            result = self.lambda_service.invoke_document_validation('krapincertificate', data)

            if not result['success']:
                logger.error(f"KRA validation failed: {result['error']}")
                error_response = create_standardized_response(
                    action='validate_krapincertificate',
                    success=False,
                    error=result['error'],
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('validate_krapincertificate', error_response)
                return secure_response_factory(status_code, error_response)

            validation_response = result['response']
            standardized_result = create_standardized_response(
                action='validate_krapincertificate',
                success=True,
                result=validation_response,
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('validate_krapincertificate', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in KRA validation: {e}")
            error_response = create_standardized_response(
                action='validate_krapincertificate',
                success=False,
                error={
                    'message': f'Validation processing error: {str(e)}',
                    'error_code': 'VALIDATION_PROCESSING_ERROR'
                },
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('validate_krapincertificate', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_cr12_validation(self, data: Dict[str, Any],
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle CR12 company registration validation."""
        logger.info("Processing CR12 validation")

        try:
            result = self.lambda_service.invoke_document_validation('cr12', data)

            if not result['success']:
                logger.error(f"CR12 validation failed: {result['error']}")
                error_response = create_standardized_response(
                    action='validate_cr12',
                    success=False,
                    error=result['error'],
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('validate_cr12', error_response)
                return secure_response_factory(status_code, error_response)

            validation_response = result['response']
            standardized_result = create_standardized_response(
                action='validate_cr12',
                success=True,
                result=validation_response,
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('validate_cr12', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in CR12 validation: {e}")
            error_response = create_standardized_response(
                action='validate_cr12',
                success=False,
                error={
                    'message': f'Validation processing error: {str(e)}',
                    'error_code': 'VALIDATION_PROCESSING_ERROR'
                },
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('validate_cr12', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_nationalid_verification(self, data: Dict[str, Any],
                                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle government national ID verification."""
        logger.info("Processing government national ID verification")

        try:
            result = self.lambda_service.invoke_government_verification('nationalid', data)

            if not result['success']:
                logger.error(f"Government ID verification failed: {result['error']}")
                error_response = create_standardized_response(
                    action='government_verify_nationalid',
                    success=False,
                    error=result['error'],
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_nationalid', error_response)
                return secure_response_factory(status_code, error_response)

            verification_response = result['response']
            standardized_result = create_standardized_response(
                action='government_verify_nationalid',
                success=True,
                result=verification_response,
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_nationalid', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in government ID verification: {e}")
            error_response = create_standardized_response(
                action='government_verify_nationalid',
                success=False,
                error={
                    'message': f'Verification processing error: {str(e)}',
                    'error_code': 'VERIFICATION_PROCESSING_ERROR'
                },
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_nationalid', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_passport_verification(self, data: Dict[str, Any],
                                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle government passport verification."""
        logger.info("Processing government passport verification")

        try:
            result = self.lambda_service.invoke_government_verification('passport', data)

            if not result['success']:
                logger.error(f"Government passport verification failed: {result['error']}")
                error_response = create_standardized_response(
                    action='government_verify_passport',
                    success=False,
                    error=result['error'],
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_passport', error_response)
                return secure_response_factory(status_code, error_response)

            verification_response = result['response']
            standardized_result = create_standardized_response(
                action='government_verify_passport',
                success=True,
                result=verification_response,
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_passport', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in government passport verification: {e}")
            error_response = create_standardized_response(
                action='government_verify_passport',
                success=False,
                error={
                    'message': f'Verification processing error: {str(e)}',
                    'error_code': 'VERIFICATION_PROCESSING_ERROR'
                },
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_passport', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_kra_verification(self, data: Dict[str, Any],
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle government KRA verification."""
        logger.info("Processing government KRA verification")

        try:
            result = self.lambda_service.invoke_government_verification('kra', data)

            if not result['success']:
                logger.error(f"Government KRA verification failed: {result['error']}")
                error_response = create_standardized_response(
                    action='government_verify_kra',
                    success=False,
                    error=result['error'],
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_kra', error_response)
                return secure_response_factory(status_code, error_response)

            verification_response = result['response']
            standardized_result = create_standardized_response(
                action='government_verify_kra',
                success=True,
                result=verification_response,
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_kra', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in government KRA verification: {e}")
            error_response = create_standardized_response(
                action='government_verify_kra',
                success=False,
                error={
                    'message': f'Verification processing error: {str(e)}',
                    'error_code': 'VERIFICATION_PROCESSING_ERROR'
                },
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_kra', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_background_check(self, data: Dict[str, Any],
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle background check operation."""
        logger.info("Processing background check")

        try:
            result = self.lambda_service.invoke_background_check(data)

            if not result['success']:
                logger.error(f"Background check failed: {result['error']}")
                error_response = create_standardized_response(
                    action='background_check',
                    success=False,
                    error=result['error'],
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('background_check', error_response)
                return secure_response_factory(status_code, error_response)

            check_response = result['response']
            standardized_result = create_standardized_response(
                action='background_check',
                success=True,
                result=check_response,
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('background_check', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in background check: {e}")
            error_response = create_standardized_response(
                action='background_check',
                success=False,
                error={
                    'message': f'Background check processing error: {str(e)}',
                    'error_code': 'BACKGROUND_CHECK_PROCESSING_ERROR'
                },
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('background_check', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_face_liveness(self, data: Dict[str, Any],
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle face liveness verification."""
        logger.info("Processing face liveness")

        try:
            result = self.lambda_service.invoke_face_liveness(data)

            if not result['success']:
                logger.error(f"Face liveness failed: {result['error']}")
                error_response = create_standardized_response(
                    action='face_liveness',
                    success=False,
                    error=result['error'],
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('face_liveness', error_response)
                return secure_response_factory(status_code, error_response)

            liveness_response = result['response']
            standardized_result = create_standardized_response(
                action='face_liveness',
                success=True,
                result=liveness_response,
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('face_liveness', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in face liveness: {e}")
            error_response = create_standardized_response(
                action='face_liveness',
                success=False,
                error={
                    'message': f'Face liveness processing error: {str(e)}',
                    'error_code': 'FACE_LIVENESS_PROCESSING_ERROR'
                },
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('face_liveness', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_agent_registration(self, data: Dict[str, Any],
                                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle agent registration workflow."""
        logger.info("Processing agent registration")

        try:
            result = self.lambda_service.invoke_registration('agent', data)

            if not result['success']:
                logger.error(f"Agent registration failed: {result['error']}")
                error_response = create_standardized_response(
                    action='agent_registration',
                    success=False,
                    error=result['error'],
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('agent_registration', error_response)
                return secure_response_factory(status_code, error_response)

            registration_response = result['response']
            standardized_result = create_standardized_response(
                action='agent_registration',
                success=True,
                result=registration_response,
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('agent_registration', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in agent registration: {e}")
            error_response = create_standardized_response(
                action='agent_registration',
                success=False,
                error={
                    'message': f'Agent registration processing error: {str(e)}',
                    'error_code': 'AGENT_REGISTRATION_PROCESSING_ERROR'
                },
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('agent_registration', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_customer_registration(self, data: Dict[str, Any],
                                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle customer registration workflow."""
        logger.info("Processing customer registration")

        try:
            result = self.lambda_service.invoke_registration('customer', data)

            if not result['success']:
                logger.error(f"Customer registration failed: {result['error']}")
                error_response = create_standardized_response(
                    action='customer_registration',
                    success=False,
                    error=result['error'],
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('customer_registration', error_response)
                return secure_response_factory(status_code, error_response)

            registration_response = result['response']
            standardized_result = create_standardized_response(
                action='customer_registration',
                success=True,
                result=registration_response,
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('customer_registration', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in customer registration: {e}")
            error_response = create_standardized_response(
                action='customer_registration',
                success=False,
                error={
                    'message': f'Customer registration processing error: {str(e)}',
                    'error_code': 'CUSTOMER_REGISTRATION_PROCESSING_ERROR'
                },
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('customer_registration', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_document_streaming(self, data: Dict[str, Any],
                                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle document streaming from S3."""
        logger.info("Processing document streaming")

        try:
            # Extract bucket type and document key from data
            bucket_type = data.get('bucketType')
            document_key = data.get('documentKey')

            if not bucket_type or not document_key:
                error_response = create_standardized_response(
                    action='stream_document',
                    success=False,
                    error={
                        'message': 'Missing required parameters: bucketType and documentKey',
                        'error_code': 'MISSING_PARAMETERS'
                    },
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('stream_document', error_response)
                return secure_response_factory(status_code, error_response)

            result = self.lambda_service.invoke_document_streaming(bucket_type, document_key)

            if not result['success']:
                logger.error(f"Document streaming failed: {result['error']}")
                error_response = create_standardized_response(
                    action='stream_document',
                    success=False,
                    error=result['error'],
                    request_context=context
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('stream_document', error_response)
                return secure_response_factory(status_code, error_response)

            streaming_response = result['response']
            standardized_result = create_standardized_response(
                action='stream_document',
                success=True,
                result=streaming_response,
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('stream_document', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in document streaming: {e}")
            error_response = create_standardized_response(
                action='stream_document',
                success=False,
                error={
                    'message': f'Document streaming processing error: {str(e)}',
                    'error_code': 'DOCUMENT_STREAMING_PROCESSING_ERROR'
                },
                request_context=context
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('stream_document', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_workflow_orchestration(self, data: Dict[str, Any],
                                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle legacy workflow orchestration (backward compatibility)."""
        logger.info("Processing legacy workflow orchestration")

        # SOW Compliance: Legacy workflows are deprecated in favor of action-based processing
        logger.warning("Legacy workflow orchestration accessed - this will be deprecated")

        # For now, return a deprecation notice with guidance to migrate
        return create_standardized_response(
            action='process_workflow',
            success=False,
            error={
                'message': 'Legacy workflow orchestration is deprecated',
                'error_code': 'DEPRECATED_WORKFLOW',
                'migration_guidance': {
                    'new_approach': 'Use individual action-based operations',
                    'example_actions': [
                        'validate_nationalid',
                        'government_verify_nationalid',
                        'background_check',
                        'face_liveness'
                    ],
                    'documentation': '/kyc API specification'
                },
                'support_until': '2024-06-01',
                'recommended_actions': [
                    'Migrate to action-based API calls',
                    'Update client applications',
                    'Test with new endpoint format'
                ]
            },
            request_id=context.get('requestId') if context else None
        )