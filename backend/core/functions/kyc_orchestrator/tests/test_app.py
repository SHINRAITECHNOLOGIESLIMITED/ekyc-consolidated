"""
Unit tests for the main KYC orchestrator Lambda handler.
"""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestKYCOrchestratorHandler:
    """Test cases for the main Lambda handler function."""

    def test_handler_post_kyc_process_success(self, mock_dependencies, sample_customer_request):
        """Test successful KYC processing via handler."""
        # Import after mocking
        from app import handler

        # Mock successful orchestrator response
        mock_orchestrator_response = {
            'kycId': 'test-kyc-id-123',
            'overallStatus': 'success',
            'processType': 'customer',
            'results': {
                'documentValidation': {'status': 'success'},
                'governmentVerification': {'status': 'success'}
            },
            'errors': []
        }

        with patch('app.KYCOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = MagicMock()
            mock_orchestrator.process_kyc.return_value = mock_orchestrator_response
            mock_orchestrator_class.return_value = mock_orchestrator

            # Prepare API Gateway event
            event = {
                'httpMethod': 'POST',
                'path': '/kyc/process',
                'body': json.dumps(sample_customer_request)
            }
            context = MagicMock()

            # Execute handler
            response = handler(event, context)

            # Assertions
            assert response['statusCode'] == 200
            response_body = json.loads(response['body'])
            assert response_body['kycId'] == 'test-kyc-id-123'
            assert response_body['overallStatus'] == 'success'
            assert mock_orchestrator.process_kyc.called

    def test_handler_post_kyc_process_partial_success(self, mock_dependencies, sample_customer_request):
        """Test partial success KYC processing."""
        from app import handler

        mock_orchestrator_response = {
            'kycId': 'test-kyc-id-123',
            'overallStatus': 'partial',
            'processType': 'customer',
            'results': {
                'documentValidation': {'status': 'success'},
                'governmentVerification': {'status': 'failed'}
            },
            'errors': [{'step': 'government_verification', 'message': 'API unavailable'}]
        }

        with patch('app.KYCOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = MagicMock()
            mock_orchestrator.process_kyc.return_value = mock_orchestrator_response
            mock_orchestrator_class.return_value = mock_orchestrator

            event = {
                'httpMethod': 'POST',
                'path': '/kyc/process',
                'body': json.dumps(sample_customer_request)
            }
            context = MagicMock()

            response = handler(event, context)

            # Partial success should return 207 Multi-Status
            assert response['statusCode'] == 207
            response_body = json.loads(response['body'])
            assert response_body['overallStatus'] == 'partial'
            assert len(response_body['errors']) > 0

    def test_handler_post_kyc_process_failure(self, mock_dependencies, sample_customer_request):
        """Test failed KYC processing."""
        from app import handler

        mock_orchestrator_response = {
            'kycId': 'test-kyc-id-123',
            'overallStatus': 'failed',
            'processType': 'customer',
            'results': {},
            'errors': [{'step': 'validation', 'message': 'Invalid input'}]
        }

        with patch('app.KYCOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = MagicMock()
            mock_orchestrator.process_kyc.return_value = mock_orchestrator_response
            mock_orchestrator_class.return_value = mock_orchestrator

            event = {
                'httpMethod': 'POST',
                'path': '/kyc/process',
                'body': json.dumps(sample_customer_request)
            }
            context = MagicMock()

            response = handler(event, context)

            assert response['statusCode'] == 400
            response_body = json.loads(response['body'])
            assert response_body['overallStatus'] == 'failed'

    def test_handler_invalid_json_body(self, mock_dependencies):
        """Test handling of invalid JSON in request body."""
        from app import handler

        event = {
            'httpMethod': 'POST',
            'path': '/kyc/process',
            'body': '{"invalid": json}'  # Invalid JSON
        }
        context = MagicMock()

        response = handler(event, context)

        assert response['statusCode'] == 400
        response_body = json.loads(response['body'])
        assert 'Invalid JSON body' in response_body['message']

    def test_handler_invalid_method(self, mock_dependencies):
        """Test handling of invalid HTTP method."""
        from app import handler

        event = {
            'httpMethod': 'GET',
            'path': '/kyc/process',
            'body': '{}'
        }
        context = MagicMock()

        response = handler(event, context)

        assert response['statusCode'] == 405
        response_body = json.loads(response['body'])
        assert 'Method Not Allowed' in response_body['message']

    def test_handler_invalid_path(self, mock_dependencies, sample_customer_request):
        """Test handling of invalid path."""
        from app import handler

        event = {
            'httpMethod': 'POST',
            'path': '/invalid/path',
            'body': json.dumps(sample_customer_request)
        }
        context = MagicMock()

        response = handler(event, context)

        assert response['statusCode'] == 405

    def test_handler_validation_error(self, mock_dependencies):
        """Test handling of validation errors."""
        from app import handler

        # Invalid request missing required fields
        invalid_request = {
            "processType": "customer"
            # Missing personalData and documents
        }

        with patch('app.validate_kyc_request') as mock_validate:
            mock_validate.return_value = {
                'valid': False,
                'errors': ['Missing required field: personalData']
            }

            event = {
                'httpMethod': 'POST',
                'path': '/kyc/process',
                'body': json.dumps(invalid_request)
            }
            context = MagicMock()

            response = handler(event, context)

            assert response['statusCode'] == 400
            response_body = json.loads(response['body'])
            assert 'Request validation failed' in response_body['message']

    def test_handler_orchestrator_exception(self, mock_dependencies, sample_customer_request):
        """Test handling of exceptions from orchestrator."""
        from app import handler

        with patch('app.KYCOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = MagicMock()
            mock_orchestrator.process_kyc.side_effect = Exception("Orchestrator error")
            mock_orchestrator_class.return_value = mock_orchestrator

            with patch('app.validate_kyc_request') as mock_validate:
                mock_validate.return_value = {'valid': True, 'errors': []}

                event = {
                    'httpMethod': 'POST',
                    'path': '/kyc/process',
                    'body': json.dumps(sample_customer_request)
                }
                context = MagicMock()

                response = handler(event, context)

                assert response['statusCode'] == 500
                response_body = json.loads(response['body'])
                assert 'KYC processing failed' in response_body['message']

    def test_make_response_function(self, mock_dependencies):
        """Test the make_response helper function."""
        from app import make_response

        test_body = {'message': 'Test response', 'data': {'key': 'value'}}
        response = make_response(200, test_body)

        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert 'Access-Control-Allow-Headers' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']

        response_body = json.loads(response['body'])
        assert response_body == test_body

    def test_cors_headers(self, mock_dependencies, sample_customer_request):
        """Test that CORS headers are properly set."""
        from app import handler

        mock_orchestrator_response = {
            'kycId': 'test-kyc-id-123',
            'overallStatus': 'success'
        }

        with patch('app.KYCOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = MagicMock()
            mock_orchestrator.process_kyc.return_value = mock_orchestrator_response
            mock_orchestrator_class.return_value = mock_orchestrator

            event = {
                'httpMethod': 'POST',
                'path': '/kyc/process',
                'body': json.dumps(sample_customer_request)
            }
            context = MagicMock()

            response = handler(event, context)

            headers = response['headers']
            assert headers['Access-Control-Allow-Origin'] == '*'
            assert 'Content-Type, Authorization, X-Api-Key' in headers['Access-Control-Allow-Headers']
            assert 'POST, OPTIONS' in headers['Access-Control-Allow-Methods']