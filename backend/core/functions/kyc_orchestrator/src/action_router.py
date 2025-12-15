"""
Action-Based Router for KYC Operations
SOW Day 2 Requirement: Single /kyc endpoint with action parameter routing

Maps all existing endpoints to action-based operations:
- Document Operations: /document/* -> validate_*
- Government Operations: /government/* -> government_verify_*
- Other Operations: Direct mapping to action names
"""

import json
import os
import boto3
import hashlib
from typing import Dict, Any, Optional, Callable, Tuple
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
from response_normalizer import (
    normalize_verification_response,
    calculate_overall_verification_status
)

logger = Logger()


class ActionRouter:
    """
    Routes action-based requests to appropriate handlers.
    Implements SOW requirement for single /kyc endpoint with action parameters.
    """

    def __init__(self):
        self.action_handlers = self._initialize_action_handlers()
        self.lambda_service = LambdaService()
        self.dynamodb = boto3.client('dynamodb')
        self.customer_table = os.environ.get('AMPLIFY_DYNAMODB_CUSTOMER_TABLE', 'Customer-7s7oergeyvc23jelhjmhef4uki-NONE')
        self.agent_table = os.environ.get('AMPLIFY_DYNAMODB_AGENT_TABLE', 'Agent-7s7oergeyvc23jelhjmhef4uki-NONE')

    def _extract_natural_identifier(self, action: str, data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract natural identifier from verification data and return entity_id and entity_type.

        Uses natural identifiers from the data (idNumber, passportNumber, etc.)
        and hashes them for privacy.

        Args:
            action: The verification action being performed
            data: The verification data

        Returns:
            Tuple of (entity_id, entity_type) where entity_id is hashed natural identifier
        """
        identifier = None
        identifier_type = None

        # Priority 1: Check for explicit customerId/agentId (from registration or client)
        if data.get('customerId'):
            return data['customerId'], 'customer'
        if data.get('agentId'):
            return data['agentId'], 'agent'

        # Priority 2: Extract natural identifiers from verification data
        if action in ['validate_nationalid', 'government_verify_nationalid']:
            identifier = data.get('idNumber')
            identifier_type = 'id'
        elif action in ['validate_passport', 'government_verify_passport']:
            identifier = data.get('passportNumber')
            identifier_type = 'passport'
        elif action in ['validate_krapincertificate', 'government_verify_kra']:
            # Try idNumber first (if client provides for linking), else use pin
            identifier = data.get('idNumber') or data.get('pin')
            identifier_type = 'id' if data.get('idNumber') else 'kra'
        elif action == 'validate_cr12':
            identifier = data.get('businessNumber')
            identifier_type = 'business'
        elif action == 'background_check':
            identifier = data.get('nationalIdentificationNumber') or data.get('idNumber')
            identifier_type = 'id'
        elif action == 'face_liveness':
            # Try idNumber or userId
            identifier = data.get('idNumber') or data.get('userId')
            identifier_type = 'id' if data.get('idNumber') else 'user'

        if not identifier:
            logger.warning(f"No identifier found for action {action}")
            return None, None

        # Hash the identifier for privacy
        hashed_id = hashlib.sha256(f"{identifier_type}:{identifier}".encode()).hexdigest()

        # Determine entity type for DynamoDB table selection
        entity_type = 'business' if identifier_type == 'business' else 'customer'

        logger.info(f"Extracted identifier type={identifier_type}, hashed_id={hashed_id[:8]}...")
        return hashed_id, entity_type

    def _store_verification_result(
        self,
        entity_type: str,
        entity_id: str,
        normalized_verification: Dict[str, Any],
        registration_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Store normalized verification result in DynamoDB.

        Args:
            entity_type: 'customer', 'agent', or 'business'
            entity_id: The entity's ID (customerId, agentId, businessId)
            normalized_verification: Normalized verification data
            registration_data: Optional registration data (name, ID, etc.) to store for new records
        """
        try:
            # Determine table and key based on entity type
            if entity_type == 'customer':
                table_name = self.customer_table
                key = {'customerId': {'S': entity_id}}
                id_attr = 'customerId'
            elif entity_type in ['agent', 'business']:
                table_name = self.agent_table
                key = {'agentId': {'S': entity_id}}
                id_attr = 'agentId'
            else:
                logger.error(f"Unknown entity type: {entity_type}")
                return

            verification_type = normalized_verification['verificationType']

            # Prepare verification data for DynamoDB (convert to DynamoDB format)
            verification_data = {
                'M': {
                    'status': {'S': normalized_verification['status']},
                    'timestamp': {'S': normalized_verification['timestamp']},
                    'action': {'S': normalized_verification['action']}
                }
            }

            # Add optional fields
            if normalized_verification.get('documentPath'):
                verification_data['M']['documentPath'] = {'S': normalized_verification['documentPath']}
            if normalized_verification.get('message'):
                verification_data['M']['message'] = {'S': normalized_verification['message']}
            if normalized_verification.get('averageConfidence') is not None:
                verification_data['M']['averageConfidence'] = {'N': str(normalized_verification['averageConfidence'])}

            # Store fields verified as JSON
            if normalized_verification.get('fieldsVerified'):
                verification_data['M']['fieldsVerified'] = {'S': json.dumps(normalized_verification['fieldsVerified'])}

            # Store scores for background check
            if normalized_verification.get('scores'):
                verification_data['M']['scores'] = {'S': json.dumps(normalized_verification['scores'])}

            # Store entity details for background check
            if normalized_verification.get('entityDetails'):
                verification_data['M']['entityDetails'] = {'S': json.dumps(normalized_verification['entityDetails'])}

            # Check if item exists and has verifications map
            try:
                response = self.dynamodb.get_item(TableName=table_name, Key=key)
                item = response.get('Item', {})
                has_verifications = 'verifications' in item
                item_exists = 'Item' in response
            except Exception:
                has_verifications = False
                item_exists = False

            # Check if item has basic registration data (name and idNumber)
            has_registration_data = item_exists and 'name' in item and 'idNumber' in item

            # Build update expression based on whether verifications map exists
            if has_verifications:
                # Verifications map exists, just update the specific verification type
                update_expr_parts = ["SET verifications.#vtype = :vdata"]
                expr_attr_names = {'#vtype': verification_type}
                expr_attr_values = {':vdata': verification_data}

                # If registration data is missing and we have it now, add it
                if not has_registration_data and registration_data:
                    # Extract name from multiple possible field names
                    name = (registration_data.get('name') or
                           registration_data.get('fullNames') or
                           registration_data.get('fullName') or
                           registration_data.get('taxPayerName'))
                    if name:
                        update_expr_parts.append("#n = :name")
                        expr_attr_names['#n'] = 'name'
                        expr_attr_values[':name'] = {'S': name}

                    # Extract ID number
                    if registration_data.get('idNumber'):
                        update_expr_parts.append("idNumber = :idNum")
                        expr_attr_values[':idNum'] = {'S': registration_data['idNumber']}

                    # Extract PIN from multiple possible field names
                    pin = (registration_data.get('pinNumber') or
                          registration_data.get('pin') or
                          registration_data.get('taxPayerPin'))
                    if pin:
                        update_expr_parts.append("pinNumber = :pin")
                        expr_attr_values[':pin'] = {'S': pin}

                    # Extract gender
                    gender = registration_data.get('gender')
                    if gender:
                        # Normalize gender to full word
                        gender_map = {'M': 'Male', 'F': 'Female', 'm': 'Male', 'f': 'Female'}
                        normalized_gender = gender_map.get(gender, gender)
                        update_expr_parts.append("gender = :gender")
                        expr_attr_values[':gender'] = {'S': normalized_gender}

                    # Extract date of birth
                    if registration_data.get('dateOfBirth'):
                        update_expr_parts.append("dateOfBirth = :dob")
                        expr_attr_values[':dob'] = {'S': registration_data['dateOfBirth']}

                    # Set initial KYC status if missing
                    if 'kycStatus' not in item:
                        update_expr_parts.append("kycStatus = :status")
                        expr_attr_values[':status'] = {'S': 'Pending'}

                update_params = {
                    'TableName': table_name,
                    'Key': key,
                    'UpdateExpression': ", ".join(update_expr_parts),
                    'ExpressionAttributeNames': expr_attr_names,
                    'ExpressionAttributeValues': expr_attr_values
                }
            else:
                # Creating new record or adding first verification
                update_expr_parts = ["SET verifications = :verifications_map"]
                expr_attr_names = {}
                expr_attr_values = {
                    ':verifications_map': {
                        'M': {verification_type: verification_data}
                    }
                }

                # If this is a new record and we have registration data, store it
                if not item_exists and registration_data:
                    # Extract name from multiple possible field names
                    name = (registration_data.get('name') or
                           registration_data.get('fullNames') or
                           registration_data.get('fullName') or
                           registration_data.get('taxPayerName'))
                    if name:
                        update_expr_parts.append("#n = :name")
                        expr_attr_names['#n'] = 'name'
                        expr_attr_values[':name'] = {'S': name}

                    # Extract ID number
                    if registration_data.get('idNumber'):
                        update_expr_parts.append("idNumber = :idNum")
                        expr_attr_values[':idNum'] = {'S': registration_data['idNumber']}

                    # Extract PIN from multiple possible field names
                    pin = (registration_data.get('pinNumber') or
                          registration_data.get('pin') or
                          registration_data.get('taxPayerPin'))
                    if pin:
                        update_expr_parts.append("pinNumber = :pin")
                        expr_attr_values[':pin'] = {'S': pin}

                    # Extract gender
                    gender = registration_data.get('gender')
                    if gender:
                        # Normalize gender to full word
                        gender_map = {'M': 'Male', 'F': 'Female', 'm': 'Male', 'f': 'Female'}
                        normalized_gender = gender_map.get(gender, gender)
                        update_expr_parts.append("gender = :gender")
                        expr_attr_values[':gender'] = {'S': normalized_gender}

                    # Extract date of birth
                    if registration_data.get('dateOfBirth'):
                        update_expr_parts.append("dateOfBirth = :dob")
                        expr_attr_values[':dob'] = {'S': registration_data['dateOfBirth']}

                    # Extract business number (for agents)
                    if registration_data.get('businessNumber'):
                        update_expr_parts.append("businessNumber = :bizNum")
                        expr_attr_values[':bizNum'] = {'S': registration_data['businessNumber']}

                    # Set initial KYC status
                    update_expr_parts.append("kycStatus = :status")
                    expr_attr_values[':status'] = {'S': 'Pending'}

                update_params = {
                    'TableName': table_name,
                    'Key': key,
                    'UpdateExpression': ", ".join(update_expr_parts),
                    'ExpressionAttributeValues': expr_attr_values
                }

                # Add expression attribute names if we have any (for reserved keywords like 'name')
                if expr_attr_names:
                    update_params['ExpressionAttributeNames'] = expr_attr_names

            self.dynamodb.update_item(**update_params)

            logger.info(f"Stored {verification_type} for {entity_type} {entity_id}")

        except Exception as e:
            logger.error(f"Error storing verification result: {e}")
            # Don't fail the request if storage fails
            pass

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

            # Certificate Operations (3 operations)
            'get_certificate': self._handle_get_certificate,
            'generate_certificate': self._handle_generate_certificate,
            'get_kyc_status': self._handle_get_kyc_status,

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
                request_id=request_context.get('request_id') if request_context else None
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
                request_id=request_context.get('request_id') if request_context else None
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
                    processing_time=execution_time / 1000  # Convert ms to seconds
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
            # Extract natural identifier for storage
            entity_id, entity_type = self._extract_natural_identifier('validate_nationalid', data)

            # Invoke existing DocumentValidationFn for national ID
            result = self.lambda_service.invoke_document_validation('nationalid', data)

            if not result['success']:
                logger.error(f"National ID validation failed: {result['error']}")
                error_response = create_standardized_response(
                    action='validate_nationalid',
                    success=False,
                    error=result['error'],
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('validate_nationalid', error_response)
                return secure_response_factory(status_code, error_response)

            # Process successful response
            validation_response = result['response']

            # Store verification result in DynamoDB if entity ID provided
            if entity_id and entity_type:
                try:
                    normalized = normalize_verification_response(
                        action='validate_nationalid',
                        raw_response=validation_response,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                    self._store_verification_result(entity_type, entity_id, normalized, registration_data=data)
                except Exception as storage_error:
                    logger.warning(f"Failed to store verification result: {storage_error}")

            standardized_result = create_standardized_response(
                action='validate_nationalid',
                success=True,
                result=validation_response,
                request_id=context.get('request_id') if context else None
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
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('validate_nationalid', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_passport_validation(self, data: Dict[str, Any],
                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle passport document validation."""
        logger.info("Processing passport validation")

        try:
            # Extract natural identifier for storage
            entity_id, entity_type = self._extract_natural_identifier('validate_passport', data)

            result = self.lambda_service.invoke_document_validation('passport', data)

            if not result['success']:
                logger.error(f"Passport validation failed: {result['error']}")
                error_response = create_standardized_response(
                    action='validate_passport',
                    success=False,
                    error=result['error'],
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('validate_passport', error_response)
                return secure_response_factory(status_code, error_response)

            validation_response = result['response']

            # Store verification result in DynamoDB if entity ID provided
            if entity_id and entity_type:
                try:
                    normalized = normalize_verification_response(
                        action='validate_passport',
                        raw_response=validation_response,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                    self._store_verification_result(entity_type, entity_id, normalized, registration_data=data)
                except Exception as storage_error:
                    logger.warning(f"Failed to store verification result: {storage_error}")

            standardized_result = create_standardized_response(
                action='validate_passport',
                success=True,
                result=validation_response,
                request_id=context.get('request_id') if context else None
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
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('validate_passport', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_kra_validation(self, data: Dict[str, Any],
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle KRA PIN certificate validation."""
        logger.info("Processing KRA PIN validation")

        try:
            # Extract natural identifier for storage
            entity_id, entity_type = self._extract_natural_identifier('validate_krapincertificate', data)

            result = self.lambda_service.invoke_document_validation('krapincertificate', data)

            if not result['success']:
                logger.error(f"KRA validation failed: {result['error']}")
                error_response = create_standardized_response(
                    action='validate_krapincertificate',
                    success=False,
                    error=result['error'],
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('validate_krapincertificate', error_response)
                return secure_response_factory(status_code, error_response)

            validation_response = result['response']

            # Store verification result in DynamoDB if entity ID provided
            if entity_id and entity_type:
                try:
                    normalized = normalize_verification_response(
                        action='validate_krapincertificate',
                        raw_response=validation_response,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                    self._store_verification_result(entity_type, entity_id, normalized, registration_data=data)
                except Exception as storage_error:
                    logger.warning(f"Failed to store verification result: {storage_error}")

            standardized_result = create_standardized_response(
                action='validate_krapincertificate',
                success=True,
                result=validation_response,
                request_id=context.get('request_id') if context else None
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
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('validate_krapincertificate', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_cr12_validation(self, data: Dict[str, Any],
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle CR12 company registration validation."""
        logger.info("Processing CR12 validation")

        try:
            # Extract natural identifier for storage
            entity_id, entity_type = self._extract_natural_identifier('validate_cr12', data)

            result = self.lambda_service.invoke_document_validation('cr12', data)

            if not result['success']:
                logger.error(f"CR12 validation failed: {result['error']}")
                error_response = create_standardized_response(
                    action='validate_cr12',
                    success=False,
                    error=result['error'],
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('validate_cr12', error_response)
                return secure_response_factory(status_code, error_response)

            validation_response = result['response']

            # Store verification result in DynamoDB if entity ID provided
            if entity_id and entity_type:
                try:
                    normalized = normalize_verification_response(
                        action='validate_cr12',
                        raw_response=validation_response,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                    self._store_verification_result(entity_type, entity_id, normalized, registration_data=data)
                except Exception as storage_error:
                    logger.warning(f"Failed to store verification result: {storage_error}")

            standardized_result = create_standardized_response(
                action='validate_cr12',
                success=True,
                result=validation_response,
                request_id=context.get('request_id') if context else None
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
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('validate_cr12', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_nationalid_verification(self, data: Dict[str, Any],
                                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle government national ID verification."""
        logger.info("Processing government national ID verification")

        try:
            # Extract natural identifier for storage
            entity_id, entity_type = self._extract_natural_identifier('government_verify_nationalid', data)

            result = self.lambda_service.invoke_government_verification('nationalid', data)

            if not result['success']:
                logger.error(f"Government ID verification failed: {result['error']}")
                error_response = create_standardized_response(
                    action='government_verify_nationalid',
                    success=False,
                    error=result['error'],
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_nationalid', error_response)
                return secure_response_factory(status_code, error_response)

            verification_response = result['response']

            # Store verification result in DynamoDB if entity ID provided
            if entity_id and entity_type:
                try:
                    normalized = normalize_verification_response(
                        action='government_verify_nationalid',
                        raw_response=verification_response,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                    self._store_verification_result(entity_type, entity_id, normalized, registration_data=data)
                except Exception as storage_error:
                    logger.warning(f"Failed to store verification result: {storage_error}")

            standardized_result = create_standardized_response(
                action='government_verify_nationalid',
                success=True,
                result=verification_response,
                request_id=context.get('request_id') if context else None
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
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_nationalid', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_passport_verification(self, data: Dict[str, Any],
                                    context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle government passport verification."""
        logger.info("Processing government passport verification")

        try:
            # Extract natural identifier for storage
            entity_id, entity_type = self._extract_natural_identifier('government_verify_passport', data)

            result = self.lambda_service.invoke_government_verification('passport', data)

            if not result['success']:
                logger.error(f"Government passport verification failed: {result['error']}")
                error_response = create_standardized_response(
                    action='government_verify_passport',
                    success=False,
                    error=result['error'],
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_passport', error_response)
                return secure_response_factory(status_code, error_response)

            verification_response = result['response']

            # Store verification result in DynamoDB if entity ID provided
            if entity_id and entity_type:
                try:
                    normalized = normalize_verification_response(
                        action='government_verify_passport',
                        raw_response=verification_response,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                    self._store_verification_result(entity_type, entity_id, normalized, registration_data=data)
                except Exception as storage_error:
                    logger.warning(f"Failed to store verification result: {storage_error}")

            standardized_result = create_standardized_response(
                action='government_verify_passport',
                success=True,
                result=verification_response,
                request_id=context.get('request_id') if context else None
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
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_passport', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_kra_verification(self, data: Dict[str, Any],
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle government KRA verification."""
        logger.info("Processing government KRA verification")

        try:
            # Extract natural identifier for storage
            entity_id, entity_type = self._extract_natural_identifier('government_verify_kra', data)

            result = self.lambda_service.invoke_government_verification('kra', data)

            if not result['success']:
                logger.error(f"Government KRA verification failed: {result['error']}")
                error_response = create_standardized_response(
                    action='government_verify_kra',
                    success=False,
                    error=result['error'],
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_kra', error_response)
                return secure_response_factory(status_code, error_response)

            verification_response = result['response']

            # Store verification result in DynamoDB if entity ID provided
            if entity_id and entity_type:
                try:
                    normalized = normalize_verification_response(
                        action='government_verify_kra',
                        raw_response=verification_response,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                    self._store_verification_result(entity_type, entity_id, normalized, registration_data=data)
                except Exception as storage_error:
                    logger.warning(f"Failed to store verification result: {storage_error}")

            standardized_result = create_standardized_response(
                action='government_verify_kra',
                success=True,
                result=verification_response,
                request_id=context.get('request_id') if context else None
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
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('government_verify_kra', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_background_check(self, data: Dict[str, Any],
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle background check operation."""
        logger.info("Processing background check")

        try:
            # Extract natural identifier for storage
            entity_id, entity_type = self._extract_natural_identifier('background_check', data)

            result = self.lambda_service.invoke_background_check(data)

            if not result['success']:
                logger.error(f"Background check failed: {result['error']}")
                error_response = create_standardized_response(
                    action='background_check',
                    success=False,
                    error=result['error'],
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('background_check', error_response)
                return secure_response_factory(status_code, error_response)

            check_response = result['response']

            # Store verification result in DynamoDB if entity ID provided
            if entity_id and entity_type:
                try:
                    normalized = normalize_verification_response(
                        action='background_check',
                        raw_response=check_response,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                    self._store_verification_result(entity_type, entity_id, normalized, registration_data=data)
                except Exception as storage_error:
                    logger.warning(f"Failed to store verification result: {storage_error}")

            standardized_result = create_standardized_response(
                action='background_check',
                success=True,
                result=check_response,
                request_id=context.get('request_id') if context else None
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
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('background_check', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_face_liveness(self, data: Dict[str, Any],
                            context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle face liveness verification."""
        logger.info("Processing face liveness")

        try:
            # Extract natural identifier for storage
            entity_id, entity_type = self._extract_natural_identifier('face_liveness', data)

            result = self.lambda_service.invoke_face_liveness(data)

            if not result['success']:
                logger.error(f"Face liveness failed: {result['error']}")
                error_response = create_standardized_response(
                    action='face_liveness',
                    success=False,
                    error=result['error'],
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('face_liveness', error_response)
                return secure_response_factory(status_code, error_response)

            liveness_response = result['response']

            # Store verification result in DynamoDB if entity ID provided
            if entity_id and entity_type:
                try:
                    normalized = normalize_verification_response(
                        action='face_liveness',
                        raw_response=liveness_response,
                        entity_type=entity_type,
                        entity_id=entity_id
                    )
                    self._store_verification_result(entity_type, entity_id, normalized, registration_data=data)
                except Exception as storage_error:
                    logger.warning(f"Failed to store verification result: {storage_error}")

            standardized_result = create_standardized_response(
                action='face_liveness',
                success=True,
                result=liveness_response,
                request_id=context.get('request_id') if context else None
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
                request_id=context.get('request_id') if context else None
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
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('agent_registration', error_response)
                return secure_response_factory(status_code, error_response)

            registration_response = result['response']
            standardized_result = create_standardized_response(
                action='agent_registration',
                success=True,
                result=registration_response,
                request_id=context.get('request_id') if context else None
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
                request_id=context.get('request_id') if context else None
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
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('customer_registration', error_response)
                return secure_response_factory(status_code, error_response)

            registration_response = result['response']
            standardized_result = create_standardized_response(
                action='customer_registration',
                success=True,
                result=registration_response,
                request_id=context.get('request_id') if context else None
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
                request_id=context.get('request_id') if context else None
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
                    request_id=context.get('request_id') if context else None
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
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('stream_document', error_response)
                return secure_response_factory(status_code, error_response)

            streaming_response = result['response']
            standardized_result = create_standardized_response(
                action='stream_document',
                success=True,
                result=streaming_response,
                request_id=context.get('request_id') if context else None
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
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('stream_document', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_get_certificate(self, data: Dict[str, Any],
                                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle certificate retrieval by customerId or agentId."""
        logger.info("Processing certificate retrieval")

        try:
            import boto3
            import os
            from botocore.config import Config

            # Determine if this is a customer or agent certificate
            customer_id = data.get('customerId')
            agent_id = data.get('agentId')

            if not customer_id and not agent_id:
                error_response = create_standardized_response(
                    action='get_certificate',
                    success=False,
                    error={
                        'message': 'Missing required parameter: customerId or agentId',
                        'error_code': 'MISSING_PARAMETERS'
                    },
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('get_certificate', error_response)
                return secure_response_factory(status_code, error_response)

            # Get table names from environment
            customer_table = os.environ.get('AMPLIFY_DYNAMODB_CUSTOMER_TABLE', 'Customer-7s7oergeyvc23jelhjmhef4uki-NONE')
            agent_table = os.environ.get('AMPLIFY_DYNAMODB_AGENT_TABLE', 'Agent-7s7oergeyvc23jelhjmhef4uki-NONE')
            certification_bucket = os.environ.get('CERTIFICATION_BUCKET_NAME')

            dynamodb = boto3.client('dynamodb')
            # S3 client with Signature Version 4 (required for KMS-encrypted buckets)
            s3_client = boto3.client('s3', config=Config(signature_version='s3v4'))

            # Query DynamoDB based on type
            if customer_id:
                table_name = customer_table
                key = {'customerId': {'S': customer_id}}
                id_type = 'customer'
            else:
                table_name = agent_table
                key = {'agentId': {'S': agent_id}}
                id_type = 'agent'

            try:
                response = dynamodb.get_item(
                    TableName=table_name,
                    Key=key,
                    ProjectionExpression='kycCertificateS3Path, kycStatus, #n',
                    ExpressionAttributeNames={'#n': 'name'}
                )

                if 'Item' not in response:
                    error_response = create_standardized_response(
                        action='get_certificate',
                        success=False,
                        error={
                            'message': f'{id_type.capitalize()} not found',
                            'error_code': 'NOT_FOUND'
                        },
                        request_id=context.get('request_id') if context else None
                    )
                    status_code = HTTPStatusMapper.map_result_to_status_code('get_certificate', error_response)
                    return secure_response_factory(status_code, error_response)

                item = response['Item']
                certificate_path = item.get('kycCertificateS3Path', {}).get('S')
                kyc_status = item.get('kycStatus', {}).get('S')
                name = item.get('name', {}).get('S', 'Unknown')

                if not certificate_path:
                    error_response = create_standardized_response(
                        action='get_certificate',
                        success=False,
                        error={
                            'message': 'Certificate not yet generated',
                            'error_code': 'CERTIFICATE_NOT_READY',
                            'details': {
                                'kycStatus': kyc_status,
                                'name': name
                            }
                        },
                        request_id=context.get('request_id') if context else None
                    )
                    status_code = HTTPStatusMapper.map_result_to_status_code('get_certificate', error_response)
                    return secure_response_factory(status_code, error_response)

                # Generate presigned URL for the certificate
                try:
                    presigned_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': certification_bucket,
                            'Key': certificate_path
                        },
                        ExpiresIn=3600  # 1 hour
                    )

                    standardized_result = create_standardized_response(
                        action='get_certificate',
                        success=True,
                        result={
                            'certificatePath': certificate_path,
                            'presignedUrl': presigned_url,
                            'expiresIn': 3600,
                            'kycStatus': kyc_status,
                            'name': name,
                            f'{id_type}Id': customer_id or agent_id
                        },
                        request_id=context.get('request_id') if context else None
                    )
                    status_code = HTTPStatusMapper.map_result_to_status_code('get_certificate', standardized_result)
                    return secure_response_factory(status_code, standardized_result)

                except Exception as s3_error:
                    logger.error(f"Error generating presigned URL: {s3_error}")
                    error_response = create_standardized_response(
                        action='get_certificate',
                        success=False,
                        error={
                            'message': f'Certificate exists but could not generate download URL: {str(s3_error)}',
                            'error_code': 'S3_ACCESS_ERROR',
                            'certificatePath': certificate_path
                        },
                        request_id=context.get('request_id') if context else None
                    )
                    status_code = HTTPStatusMapper.map_result_to_status_code('get_certificate', error_response)
                    return secure_response_factory(status_code, error_response)

            except Exception as db_error:
                logger.error(f"Error querying DynamoDB: {db_error}")
                error_response = create_standardized_response(
                    action='get_certificate',
                    success=False,
                    error={
                        'message': f'Database query error: {str(db_error)}',
                        'error_code': 'DATABASE_ERROR'
                    },
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('get_certificate', error_response)
                return secure_response_factory(status_code, error_response)

        except Exception as e:
            logger.error(f"Error in certificate retrieval: {e}")
            error_response = create_standardized_response(
                action='get_certificate',
                success=False,
                error={
                    'message': f'Certificate retrieval error: {str(e)}',
                    'error_code': 'CERTIFICATE_RETRIEVAL_ERROR'
                },
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('get_certificate', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_generate_certificate(self, data: Dict[str, Any],
                                     context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle certificate generation using stored verification results from DynamoDB.

        New simplified approach:
        - Client only needs to provide customerId or agentId
        - Backend fetches all verification results from DynamoDB
        - Generates certificate based on actual verifications performed
        """
        logger.info("Processing certificate generation from DynamoDB stored verifications")

        try:
            # Extract entity ID - support both registered IDs and natural identifiers
            customer_id = data.get('customerId')
            agent_id = data.get('agentId')
            id_number = data.get('idNumber')
            passport_number = data.get('passportNumber')
            business_number = data.get('businessNumber')

            # Determine entity_id and entity_type
            if customer_id:
                entity_id = customer_id
                entity_type = 'customer'
                certificate_type = 'customer'
            elif agent_id:
                entity_id = agent_id
                entity_type = 'agent'
                certificate_type = data.get('certificateType', 'individual_agent')
            elif id_number:
                # Use hashed natural identifier
                entity_id = hashlib.sha256(f"id:{id_number}".encode()).hexdigest()
                entity_type = 'customer'
                certificate_type = 'customer'
            elif passport_number:
                entity_id = hashlib.sha256(f"passport:{passport_number}".encode()).hexdigest()
                entity_type = 'customer'
                certificate_type = 'customer'
            elif business_number:
                entity_id = hashlib.sha256(f"business:{business_number}".encode()).hexdigest()
                entity_type = 'business'
                certificate_type = 'business_agent'
            else:
                error_response = create_standardized_response(
                    action='generate_certificate',
                    success=False,
                    error={
                        'message': 'Missing required parameter: customerId, agentId, idNumber, passportNumber, or businessNumber',
                        'error_code': 'MISSING_ENTITY_ID'
                    },
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('generate_certificate', error_response)
                return secure_response_factory(status_code, error_response)

            # Determine table name
            if entity_type == 'business':
                table_name = self.agent_table
                key = {'agentId': {'S': entity_id}}
            else:
                table_name = self.customer_table
                key = {'customerId': {'S': entity_id}}

            # Fetch stored verification results from DynamoDB
            try:
                response = self.dynamodb.get_item(TableName=table_name, Key=key)

                if 'Item' not in response:
                    error_response = create_standardized_response(
                        action='generate_certificate',
                        success=False,
                        error={
                            'message': f'{entity_type.capitalize()} not found or no verifications performed',
                            'error_code': 'ENTITY_NOT_FOUND'
                        },
                        request_id=context.get('request_id') if context else None
                    )
                    status_code = HTTPStatusMapper.map_result_to_status_code('generate_certificate', error_response)
                    return secure_response_factory(status_code, error_response)

                item = response['Item']
                verifications = item.get('verifications', {}).get('M', {})

                if not verifications:
                    error_response = create_standardized_response(
                        action='generate_certificate',
                        success=False,
                        error={
                            'message': 'No verifications found for this entity. Please complete verifications first.',
                            'error_code': 'NO_VERIFICATIONS'
                        },
                        request_id=context.get('request_id') if context else None
                    )
                    status_code = HTTPStatusMapper.map_result_to_status_code('generate_certificate', error_response)
                    return secure_response_factory(status_code, error_response)

                # Parse verifications from DynamoDB format
                verification_results = {}
                for verification_type, verification_data in verifications.items():
                    vdata = verification_data.get('M', {})
                    verification_results[verification_type] = {
                        'status': vdata.get('status', {}).get('S'),
                        'timestamp': vdata.get('timestamp', {}).get('S'),
                        'action': vdata.get('action', {}).get('S')
                    }
                    # Add optional fields if present
                    if 'documentPath' in vdata:
                        verification_results[verification_type]['documentPath'] = vdata['documentPath'].get('S')
                    if 'message' in vdata:
                        verification_results[verification_type]['message'] = vdata['message'].get('S')
                    if 'averageConfidence' in vdata:
                        verification_results[verification_type]['averageConfidence'] = float(vdata['averageConfidence'].get('N'))
                    if 'fieldsVerified' in vdata:
                        verification_results[verification_type]['fieldsVerified'] = json.loads(vdata['fieldsVerified'].get('S'))
                    if 'scores' in vdata:
                        verification_results[verification_type]['scores'] = json.loads(vdata['scores'].get('S'))

                logger.info(f"Found {len(verification_results)} verifications for {entity_type} {entity_id}")

                # Extract registration data from DynamoDB item for certificate
                registration = {}
                if 'name' in item:
                    registration['name'] = item['name'].get('S', 'N/A')
                if 'idNumber' in item:
                    registration['idNumber'] = item['idNumber'].get('S', 'N/A')
                if 'pinNumber' in item:
                    registration['pinNumber'] = item['pinNumber'].get('S', 'N/A')
                if 'gender' in item:
                    registration['gender'] = item['gender'].get('S', 'N/A')
                if 'dateOfBirth' in item:
                    registration['dateOfBirth'] = item['dateOfBirth'].get('S', 'N/A')
                if 'kycStatus' in item:
                    registration['kycStatus'] = item['kycStatus'].get('S', 'Pending')
                if 'businessNumber' in item:
                    registration['businessNumber'] = item['businessNumber'].get('S', 'N/A')

                # Add entity ID to registration
                if entity_type == 'customer':
                    registration['customerId'] = entity_id
                else:
                    registration['agentId'] = entity_id

                # If PIN is missing from registration, try to extract from KRA verification
                if not registration.get('pinNumber') or registration.get('pinNumber') == 'N/A':
                    if 'kra_verification' in verification_results:
                        # Try to get PIN from the verification data passed in the request
                        # The PIN would be in the original request data, not the response
                        # For now, just set to empty string to avoid "N/A" in certificate
                        pass  # We'll handle this by storing PIN during verification

            except Exception as db_error:
                logger.error(f"Error fetching verification data from DynamoDB: {db_error}")
                error_response = create_standardized_response(
                    action='generate_certificate',
                    success=False,
                    error={
                        'message': f'Database error: {str(db_error)}',
                        'error_code': 'DATABASE_ERROR'
                    },
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('generate_certificate', error_response)
                return secure_response_factory(status_code, error_response)

            # Invoke CertificationFn with verification results
            certification_function = os.environ.get('CERTIFICATION_FUNCTION')
            if not certification_function:
                error_response = create_standardized_response(
                    action='generate_certificate',
                    success=False,
                    error={
                        'message': 'Certification function not configured',
                        'error_code': 'CONFIGURATION_ERROR'
                    },
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('generate_certificate', error_response)
                return secure_response_factory(status_code, error_response)

            # Transform verification results into CertificationFn expected format
            # CertificationFn expects: nationalIdValidation, idVerification, taxPayerVerification, backgroundCheck
            cert_payload_data = {
                'registration': registration
            }

            # Map stored verification types to CertificationFn expected field names
            verification_mapping = {
                'national_id_validation': 'nationalIdValidation',
                'national_id_verification': 'idVerification',
                'passport_validation': 'passportValidation',
                'passport_verification': 'passportVerification',
                'kra_validation': 'kraValidation',
                'kra_verification': 'taxPayerVerification',
                'cr12_validation': 'cr12Validation',
                'background_check': 'backgroundCheck',
                'liveness': 'livenessCheck'
            }

            # Transform each verification into the old API response format
            for verification_type, cert_field_name in verification_mapping.items():
                if verification_type in verification_results:
                    v = verification_results[verification_type]

                    # Build old-style verification response
                    old_format = {
                        'message': v.get('message', f'{verification_type} completed')
                    }

                    # Add results if fieldsVerified exists (for validation/verification actions)
                    if 'fieldsVerified' in v:
                        old_format['results'] = v['fieldsVerified']

                    # Add scores if present (for background check)
                    if 'scores' in v:
                        old_format.update(v['scores'])

                    # Add entity details if present (for background check)
                    if verification_type == 'background_check':
                        # Background check specific fields from raw_response if available
                        old_format['BestCountryScore'] = v.get('scores', {}).get('bestCountryScore', 0)
                        old_format['BestNameScore'] = v.get('scores', {}).get('bestNameScore', 0)
                        old_format['EntityScore'] = v.get('scores', {}).get('entityScore', 0)
                        old_format['ReasonListed'] = '0'
                        old_format['entityDetails'] = []

                    cert_payload_data[cert_field_name] = old_format

            # Check if we have minimum required verifications for certificate
            # Required: (nationalIdValidation OR passportValidation) AND idVerification AND taxPayerVerification AND backgroundCheck
            # Liveness is OPTIONAL
            has_id_validation = 'nationalIdValidation' in cert_payload_data or 'passportValidation' in cert_payload_data
            has_id_verification = 'idVerification' in cert_payload_data or 'passportVerification' in cert_payload_data
            has_tax_verification = 'taxPayerVerification' in cert_payload_data
            has_background_check = 'backgroundCheck' in cert_payload_data

            if not (has_id_verification and has_tax_verification and has_background_check):
                missing = []
                if not has_id_verification:
                    missing.append('ID verification')
                if not has_tax_verification:
                    missing.append('Tax verification')
                if not has_background_check:
                    missing.append('Background check')

                error_response = create_standardized_response(
                    action='generate_certificate',
                    success=False,
                    error={
                        'message': f'Incomplete verifications. Missing: {", ".join(missing)}',
                        'error_code': 'INCOMPLETE_VERIFICATIONS',
                        'missingVerifications': missing
                    },
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('generate_certificate', error_response)
                return secure_response_factory(status_code, error_response)

            # Prepare certification payload
            path_mapping = {
                'customer': '/certification/customer_registration',
                'individual_agent': '/certification/individual_agent_registration',
                'business_agent': '/certification/business_agent_registration'
            }

            certification_path = path_mapping.get(certificate_type)
            certification_payload = {
                'httpMethod': 'POST',
                'path': certification_path,
                'body': cert_payload_data
            }

            lambda_client = boto3.client('lambda')
            logger.info(f"Invoking certification function for {certificate_type}: {entity_id}")

            lambda_response = lambda_client.invoke(
                FunctionName=certification_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(certification_payload)
            )

            # Parse response
            response_payload = json.loads(lambda_response['Payload'].read())

            if lambda_response['StatusCode'] != 200:
                logger.error(f"Certification function failed: {response_payload}")
                error_response = create_standardized_response(
                    action='generate_certificate',
                    success=False,
                    error={
                        'message': 'Certificate generation failed',
                        'error_code': 'CERTIFICATION_FUNCTION_ERROR',
                        'details': response_payload
                    },
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('generate_certificate', error_response)
                return secure_response_factory(status_code, error_response)

            # Parse certification response body
            cert_body = response_payload.get('body')
            if isinstance(cert_body, str):
                cert_body = json.loads(cert_body)

            # Update DynamoDB with certificate path
            try:
                s3_path = cert_body.get('s3Path')
                if s3_path:
                    self.dynamodb.update_item(
                        TableName=table_name,
                        Key=key,
                        UpdateExpression='SET kycCertificateS3Path = :path, kycStatus = :status',
                        ExpressionAttributeValues={
                            ':path': {'S': s3_path},
                            ':status': {'S': 'Approved'}
                        }
                    )
                    logger.info(f"Updated {entity_type} {entity_id} with certificate path")
            except Exception as update_error:
                logger.warning(f"Failed to update DynamoDB with certificate path: {update_error}")

            # Return success
            standardized_result = create_standardized_response(
                action='generate_certificate',
                success=True,
                result={
                    'certificateGenerated': True,
                    'certificateType': certificate_type,
                    's3Path': cert_body.get('s3Path'),
                    'message': cert_body.get('message', 'Certificate generated successfully'),
                    f'{entity_type}Id': entity_id,
                    'verificationsUsed': list(verification_results.keys())
                },
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('generate_certificate', standardized_result)
            return secure_response_factory(status_code, standardized_result)

        except Exception as e:
            logger.error(f"Error in certificate generation: {e}")
            import traceback
            logger.error(traceback.format_exc())
            error_response = create_standardized_response(
                action='generate_certificate',
                success=False,
                error={
                    'message': f'Certificate generation error: {str(e)}',
                    'error_code': 'CERTIFICATE_GENERATION_ERROR'
                },
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('generate_certificate', error_response)
            return secure_response_factory(status_code, error_response)

    def _handle_get_kyc_status(self, data: Dict[str, Any],
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle KYC status retrieval for an entity.

        Returns all verifications completed for the entity and overall KYC status.
        """
        logger.info("Processing KYC status retrieval")

        try:
            # Extract entity ID - support both registered IDs and natural identifiers
            customer_id = data.get('customerId')
            agent_id = data.get('agentId')
            id_number = data.get('idNumber')
            passport_number = data.get('passportNumber')
            business_number = data.get('businessNumber')

            # Determine entity_id and entity_type
            if customer_id:
                entity_id = customer_id
                entity_type = 'customer'
            elif agent_id:
                entity_id = agent_id
                entity_type = 'agent'
            elif id_number:
                entity_id = hashlib.sha256(f"id:{id_number}".encode()).hexdigest()
                entity_type = 'customer'
            elif passport_number:
                entity_id = hashlib.sha256(f"passport:{passport_number}".encode()).hexdigest()
                entity_type = 'customer'
            elif business_number:
                entity_id = hashlib.sha256(f"business:{business_number}".encode()).hexdigest()
                entity_type = 'business'
            else:
                error_response = create_standardized_response(
                    action='get_kyc_status',
                    success=False,
                    error={
                        'message': 'Missing required parameter: customerId, agentId, idNumber, passportNumber, or businessNumber',
                        'error_code': 'MISSING_ENTITY_ID'
                    },
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('get_kyc_status', error_response)
                return secure_response_factory(status_code, error_response)

            # Determine table name
            if entity_type == 'business':
                table_name = self.agent_table
                key = {'agentId': {'S': entity_id}}
            else:
                table_name = self.customer_table
                key = {'customerId': {'S': entity_id}}

            # Fetch entity data from DynamoDB
            try:
                response = self.dynamodb.get_item(TableName=table_name, Key=key)

                if 'Item' not in response:
                    error_response = create_standardized_response(
                        action='get_kyc_status',
                        success=False,
                        error={
                            'message': f'{entity_type.capitalize()} not found',
                            'error_code': 'ENTITY_NOT_FOUND'
                        },
                        request_id=context.get('request_id') if context else None
                    )
                    status_code = HTTPStatusMapper.map_result_to_status_code('get_kyc_status', error_response)
                    return secure_response_factory(status_code, error_response)

                item = response['Item']
                verifications = item.get('verifications', {}).get('M', {})

                # Parse verifications
                verification_results = {}
                for verification_type, verification_data in verifications.items():
                    vdata = verification_data.get('M', {})
                    verification_results[verification_type] = {
                        'status': vdata.get('status', {}).get('S'),
                        'timestamp': vdata.get('timestamp', {}).get('S'),
                        'action': vdata.get('action', {}).get('S')
                    }
                    if 'averageConfidence' in vdata:
                        verification_results[verification_type]['averageConfidence'] = float(vdata['averageConfidence'].get('N'))

                # Calculate overall status using the normalizer's logic
                overall_status = calculate_overall_verification_status(verification_results) if verification_results else 'INCOMPLETE'

                # Get KYC status and certificate path if available
                kyc_status = item.get('kycStatus', {}).get('S', 'Pending')
                certificate_path = item.get('kycCertificateS3Path', {}).get('S')

                # Return status
                standardized_result = create_standardized_response(
                    action='get_kyc_status',
                    success=True,
                    result={
                        f'{entity_type}Id': entity_id,
                        'kycStatus': kyc_status,
                        'overallVerificationStatus': overall_status,
                        'verifications': verification_results,
                        'verificationsCompleted': len(verification_results),
                        'certificateGenerated': certificate_path is not None,
                        'certificatePath': certificate_path
                    },
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('get_kyc_status', standardized_result)
                return secure_response_factory(status_code, standardized_result)

            except Exception as db_error:
                logger.error(f"Error fetching KYC status from DynamoDB: {db_error}")
                error_response = create_standardized_response(
                    action='get_kyc_status',
                    success=False,
                    error={
                        'message': f'Database error: {str(db_error)}',
                        'error_code': 'DATABASE_ERROR'
                    },
                    request_id=context.get('request_id') if context else None
                )
                status_code = HTTPStatusMapper.map_result_to_status_code('get_kyc_status', error_response)
                return secure_response_factory(status_code, error_response)

        except Exception as e:
            logger.error(f"Error in KYC status retrieval: {e}")
            error_response = create_standardized_response(
                action='get_kyc_status',
                success=False,
                error={
                    'message': f'KYC status retrieval error: {str(e)}',
                    'error_code': 'KYC_STATUS_RETRIEVAL_ERROR'
                },
                request_id=context.get('request_id') if context else None
            )
            status_code = HTTPStatusMapper.map_result_to_status_code('get_kyc_status', error_response)
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