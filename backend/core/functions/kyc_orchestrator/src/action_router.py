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

logger = Logger()


class ActionRouter:
    """
    Routes action-based requests to appropriate handlers.
    Implements SOW requirement for single /kyc endpoint with action parameters.
    """

    def __init__(self):
        self.action_handlers = self._initialize_action_handlers()

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

        Args:
            action: The action to perform (e.g., 'validate_nationalid')
            data: The request data for the action
            request_context: Optional request context from API Gateway

        Returns:
            Standardized action response
        """
        logger.info(f"Routing action: {action}")

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
            # Execute action handler
            handler = self.action_handlers[action]
            result = handler(data, request_context)

            # Ensure result is in standardized format
            if not isinstance(result, dict) or 'statusCode' not in result:
                # Convert to standardized response format
                standardized_result = create_standardized_response(
                    action=action,
                    success=True,
                    result=result,
                    request_id=request_context.get('requestId') if request_context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code(action, standardized_result)
                return secure_response_factory(status_code, standardized_result)

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

    # Action Handler Methods
    # These will invoke the existing Lambda functions via boto3

    def _handle_nationalid_validation(self, data: Dict[str, Any],
                                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle national ID document validation."""
        logger.info("Processing national ID validation")

        # TODO: Invoke existing DocumentValidationFn for national ID
        # This will be implemented in Day 4-5 backend implementation
        return {
            'success': True,
            'action': 'validate_nationalid',
            'status': 'pending_implementation',
            'message': 'National ID validation will be implemented in Phase 2'
        }

    def _handle_passport_validation(self, data: Dict[str, Any],
                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle passport document validation."""
        logger.info("Processing passport validation")

        # TODO: Invoke existing DocumentValidationFn for passport
        return {
            'success': True,
            'action': 'validate_passport',
            'status': 'pending_implementation',
            'message': 'Passport validation will be implemented in Phase 2'
        }

    def _handle_kra_validation(self, data: Dict[str, Any],
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle KRA PIN certificate validation."""
        logger.info("Processing KRA PIN validation")

        # TODO: Invoke existing DocumentValidationFn for KRA
        return {
            'success': True,
            'action': 'validate_krapincertificate',
            'status': 'pending_implementation',
            'message': 'KRA validation will be implemented in Phase 2'
        }

    def _handle_cr12_validation(self, data: Dict[str, Any],
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle CR12 company registration validation."""
        logger.info("Processing CR12 validation")

        # TODO: Invoke existing DocumentValidationFn for CR12
        return {
            'success': True,
            'action': 'validate_cr12',
            'status': 'pending_implementation',
            'message': 'CR12 validation will be implemented in Phase 2'
        }

    def _handle_nationalid_verification(self, data: Dict[str, Any],
                                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle government national ID verification."""
        logger.info("Processing government national ID verification")

        # TODO: Invoke existing GovernmentVerificationFn for national ID
        return {
            'success': True,
            'action': 'government_verify_nationalid',
            'status': 'pending_implementation',
            'message': 'Government ID verification will be implemented in Phase 2'
        }

    def _handle_passport_verification(self, data: Dict[str, Any],
                                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle government passport verification."""
        logger.info("Processing government passport verification")

        # TODO: Invoke existing GovernmentVerificationFn for passport
        return {
            'success': True,
            'action': 'government_verify_passport',
            'status': 'pending_implementation',
            'message': 'Government passport verification will be implemented in Phase 2'
        }

    def _handle_kra_verification(self, data: Dict[str, Any],
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle government KRA verification."""
        logger.info("Processing government KRA verification")

        # TODO: Invoke existing GovernmentVerificationFn for KRA
        return {
            'success': True,
            'action': 'government_verify_kra',
            'status': 'pending_implementation',
            'message': 'Government KRA verification will be implemented in Phase 2'
        }

    def _handle_background_check(self, data: Dict[str, Any],
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle background check operation."""
        logger.info("Processing background check")

        # TODO: Invoke existing BackgroundChecksFn
        return {
            'success': True,
            'action': 'background_check',
            'status': 'pending_implementation',
            'message': 'Background check will be implemented in Phase 2'
        }

    def _handle_face_liveness(self, data: Dict[str, Any],
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle face liveness verification."""
        logger.info("Processing face liveness")

        # TODO: Invoke existing FaceLivenessFn
        return {
            'success': True,
            'action': 'face_liveness',
            'status': 'pending_implementation',
            'message': 'Face liveness will be implemented in Phase 2'
        }

    def _handle_agent_registration(self, data: Dict[str, Any],
                                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle agent registration workflow."""
        logger.info("Processing agent registration")

        # TODO: Invoke existing RegistrationFn for agent
        return {
            'success': True,
            'action': 'agent_registration',
            'status': 'pending_implementation',
            'message': 'Agent registration will be implemented in Phase 2'
        }

    def _handle_customer_registration(self, data: Dict[str, Any],
                                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle customer registration workflow."""
        logger.info("Processing customer registration")

        # TODO: Invoke existing RegistrationFn for customer
        return {
            'success': True,
            'action': 'customer_registration',
            'status': 'pending_implementation',
            'message': 'Customer registration will be implemented in Phase 2'
        }

    def _handle_document_streaming(self, data: Dict[str, Any],
                                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle document streaming from S3."""
        logger.info("Processing document streaming")

        # TODO: Invoke existing DocumentStreamingFn
        return {
            'success': True,
            'action': 'stream_document',
            'status': 'pending_implementation',
            'message': 'Document streaming will be implemented in Phase 2'
        }

    def _handle_workflow_orchestration(self, data: Dict[str, Any],
                                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle legacy workflow orchestration (backward compatibility)."""
        logger.info("Processing workflow orchestration")

        # Import here to avoid circular imports
        from orchestrator import KYCOrchestrator
        from validators import validate_kyc_request

        # Validate using existing validator
        validation_result = validate_kyc_request(data)
        if not validation_result['valid']:
            return secure_response_factory(400, {
                'success': False,
                'action': 'process_workflow',
                'error': validation_result['errors'],
                'message': 'Workflow validation failed'
            })

        # Process using existing orchestrator
        orchestrator = KYCOrchestrator()
        result = orchestrator.process_kyc(data)

        # Convert to action-based response format
        return secure_response_factory(
            200 if result.get('overallStatus') == 'success' else
            207 if result.get('overallStatus') == 'partial' else 400,
            {
                'success': result.get('overallStatus') in ['success', 'partial'],
                'action': 'process_workflow',
                'workflowResult': result,
                'timestamp': self._get_timestamp()
            }
        )