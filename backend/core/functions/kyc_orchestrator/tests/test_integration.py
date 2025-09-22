"""
Integration tests for the KYC orchestrator.
Tests the complete workflow integration.
"""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestKYCOrchestratorIntegration:
    """Integration test cases for the complete KYC workflow."""

    def test_end_to_end_customer_kyc_success(self, mock_dependencies, mock_environment_variables,
                                           sample_customer_request, mock_lambda_responses):
        """Test complete end-to-end customer KYC workflow."""
        from app import handler

        # Mock all Lambda function responses
        def mock_invoke(FunctionName, InvocationType, Payload):
            mock_response = MagicMock()

            payload_data = json.loads(Payload)
            path = payload_data.get('path', '')

            if '/document/' in path:
                response_data = mock_lambda_responses['document_validation']
            elif '/government/' in path:
                response_data = mock_lambda_responses['government_verification']
            elif '/backgroundcheck' in path:
                response_data = mock_lambda_responses['background_check']
            elif '/faceliveness' in path:
                response_data = mock_lambda_responses['face_liveness']
            elif '/certification/' in path:
                response_data = mock_lambda_responses['certification']
            else:
                response_data = {'statusCode': 404, 'body': '{"error": "Not found"}'}

            mock_response.read.return_value = json.dumps(response_data).encode()
            return {'Payload': mock_response}

        mock_dependencies['mock_lambda_client'].invoke.side_effect = mock_invoke

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

        assert 'kycId' in response_body
        assert response_body['overallStatus'] in ['success', 'partial']
        assert response_body['processType'] == 'customer'
        assert 'results' in response_body
        assert 'documentValidation' in response_body['results']
        assert 'governmentVerification' in response_body['results']
        assert 'backgroundCheck' in response_body['results']
        assert 'metadata' in response_body
        assert len(response_body['metadata']['functionsInvoked']) > 0

    def test_end_to_end_individual_agent_kyc_with_liveness(self, mock_dependencies, mock_environment_variables,
                                                         sample_individual_agent_request, mock_lambda_responses):
        """Test complete individual agent KYC workflow with face liveness."""
        from app import handler

        def mock_invoke(FunctionName, InvocationType, Payload):
            mock_response = MagicMock()

            payload_data = json.loads(Payload)
            path = payload_data.get('path', '')

            if '/document/' in path:
                response_data = mock_lambda_responses['document_validation']
            elif '/government/' in path:
                response_data = mock_lambda_responses['government_verification']
            elif '/backgroundcheck' in path:
                response_data = mock_lambda_responses['background_check']
            elif '/faceliveness' in path:
                response_data = mock_lambda_responses['face_liveness']
            elif '/certification/' in path:
                response_data = mock_lambda_responses['certification']
            else:
                response_data = {'statusCode': 404, 'body': '{"error": "Not found"}'}

            mock_response.read.return_value = json.dumps(response_data).encode()
            return {'Payload': mock_response}

        mock_dependencies['mock_lambda_client'].invoke.side_effect = mock_invoke

        event = {
            'httpMethod': 'POST',
            'path': '/kyc/process',
            'body': json.dumps(sample_individual_agent_request)
        }
        context = MagicMock()

        response = handler(event, context)

        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])

        assert response_body['processType'] == 'individual_agent'
        assert 'faceLiveness' in response_body['results']
        assert response_body['results']['faceLiveness']['status'] == 'success'

    def test_end_to_end_business_agent_kyc_minimal(self, mock_dependencies, mock_environment_variables,
                                                 sample_business_agent_request, mock_lambda_responses):
        """Test business agent KYC workflow with minimal options."""
        from app import handler

        def mock_invoke(FunctionName, InvocationType, Payload):
            mock_response = MagicMock()

            payload_data = json.loads(Payload)
            path = payload_data.get('path', '')

            if '/document/' in path:
                response_data = mock_lambda_responses['document_validation']
            elif '/certification/' in path:
                response_data = mock_lambda_responses['certification']
            else:
                response_data = {'statusCode': 404, 'body': '{"error": "Not found"}'}

            mock_response.read.return_value = json.dumps(response_data).encode()
            return {'Payload': mock_response}

        mock_dependencies['mock_lambda_client'].invoke.side_effect = mock_invoke

        event = {
            'httpMethod': 'POST',
            'path': '/kyc/process',
            'body': json.dumps(sample_business_agent_request)
        }
        context = MagicMock()

        response = handler(event, context)

        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])

        assert response_body['processType'] == 'business_agent'
        # Should not include background check or face liveness due to options
        assert 'backgroundCheck' not in response_body['results']
        assert 'faceLiveness' not in response_body['results']

    def test_partial_failure_scenario(self, mock_dependencies, mock_environment_variables,
                                    sample_customer_request):
        """Test scenario where some steps succeed and others fail."""
        from app import handler

        def mock_invoke(FunctionName, InvocationType, Payload):
            mock_response = MagicMock()

            payload_data = json.loads(Payload)
            path = payload_data.get('path', '')

            if '/document/' in path:
                # Document validation succeeds
                response_data = {
                    'statusCode': 200,
                    'body': '{"status": "Valid", "success": true}'
                }
            elif '/government/' in path:
                # Government verification fails
                response_data = {
                    'statusCode': 400,
                    'body': '{"message": "Government API unavailable", "error": "Service timeout"}'
                }
            elif '/backgroundcheck' in path:
                # Background check succeeds
                response_data = {
                    'statusCode': 200,
                    'body': '{"riskScore": 15, "status": "Low Risk", "success": true}'
                }
            elif '/certification/' in path:
                # Certification succeeds
                response_data = {
                    'statusCode': 200,
                    'body': '{"s3Path": "certificates/cert.pdf", "success": true}'
                }
            else:
                response_data = {'statusCode': 404, 'body': '{"error": "Not found"}'}

            mock_response.read.return_value = json.dumps(response_data).encode()
            return {'Payload': mock_response}

        mock_dependencies['mock_lambda_client'].invoke.side_effect = mock_invoke

        event = {
            'httpMethod': 'POST',
            'path': '/kyc/process',
            'body': json.dumps(sample_customer_request)
        }
        context = MagicMock()

        response = handler(event, context)

        # Should return 207 Multi-Status for partial success
        assert response['statusCode'] == 207
        response_body = json.loads(response['body'])

        assert response_body['overallStatus'] == 'partial'
        assert len(response_body['errors']) > 0
        assert response_body['results']['documentValidation']['status'] == 'success'
        assert response_body['results']['governmentVerification']['status'] == 'failed'

    def test_complete_failure_scenario(self, mock_dependencies, mock_environment_variables,
                                     sample_customer_request):
        """Test scenario where all steps fail."""
        from app import handler

        def mock_invoke(FunctionName, InvocationType, Payload):
            mock_response = MagicMock()

            # All functions return errors
            response_data = {
                'statusCode': 500,
                'body': '{"message": "Internal server error", "error": "Service unavailable"}'
            }

            mock_response.read.return_value = json.dumps(response_data).encode()
            return {'Payload': mock_response}

        mock_dependencies['mock_lambda_client'].invoke.side_effect = mock_invoke

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
        assert len(response_body['errors']) > 0

    def test_lambda_invoke_timeout_handling(self, mock_dependencies, mock_environment_variables,
                                          sample_customer_request):
        """Test handling of Lambda function timeouts."""
        from app import handler

        # Mock timeout exception
        mock_dependencies['mock_lambda_client'].invoke.side_effect = Exception("Task timed out after 300.00 seconds")

        event = {
            'httpMethod': 'POST',
            'path': '/kyc/process',
            'body': json.dumps(sample_customer_request)
        }
        context = MagicMock()

        response = handler(event, context)

        assert response['statusCode'] == 500
        response_body = json.loads(response['body'])

        assert response_body['overallStatus'] == 'failed'
        assert 'KYC processing failed' in response_body['message']

    def test_certificate_generation_integration(self, mock_dependencies, mock_environment_variables):
        """Test certificate generation integration with all workflow results."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Mock certification response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': '{"s3Path": "certificates/customer-cert-123.pdf", "certificateUrl": "https://example.com/cert.pdf"}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        request_data = {'processType': 'customer'}
        response = {'metadata': {'functionsInvoked': []}, 'results': {}}

        # Mock workflow results
        doc_results = {'nationalId': {'status': 'Valid', 'success': True}}
        gov_results = {'nationalIdVerification': {'status': 'Valid', 'success': True}}
        bg_results = {'riskScore': 10, 'status': 'Low Risk', 'success': True}
        liveness_results = {'sessionId': 'sess-123', 'confidence': 95, 'success': True}

        result = orchestrator._process_certification(
            request_data, response, doc_results, gov_results, bg_results, liveness_results
        )

        assert result is not None
        assert 'certificateUrl' in response
        assert response['results']['certification']['status'] == 'success'

        # Verify the certification request contains all workflow results
        call_args = mock_lambda_client.invoke.call_args
        payload = json.loads(call_args[1]['Payload'])
        cert_data = json.loads(payload['body'])

        assert 'registration' in cert_data
        assert 'documentValidation' in cert_data
        assert 'governmentVerification' in cert_data
        assert 'backgroundCheck' in cert_data
        assert 'faceLiveness' in cert_data

    def test_response_structure_consistency(self, mock_dependencies, mock_environment_variables,
                                          sample_customer_request, mock_lambda_responses):
        """Test that response structure is consistent across different scenarios."""
        from app import handler

        def mock_invoke(FunctionName, InvocationType, Payload):
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(mock_lambda_responses['document_validation']).encode()
            return {'Payload': mock_response}

        mock_dependencies['mock_lambda_client'].invoke.side_effect = mock_invoke

        event = {
            'httpMethod': 'POST',
            'path': '/kyc/process',
            'body': json.dumps(sample_customer_request)
        }
        context = MagicMock()

        response = handler(event, context)
        response_body = json.loads(response['body'])

        # Check required top-level fields
        required_fields = ['kycId', 'overallStatus', 'processType', 'timestamp',
                          'processingTime', 'results', 'errors', 'metadata']

        for field in required_fields:
            assert field in response_body, f"Missing required field: {field}"

        # Check metadata structure
        assert 'functionsInvoked' in response_body['metadata']
        assert 'totalSteps' in response_body['metadata']
        assert 'successfulSteps' in response_body['metadata']

        # Check that functionsInvoked is a list
        assert isinstance(response_body['metadata']['functionsInvoked'], list)

        # Check that errors is a list
        assert isinstance(response_body['errors'], list)

    def test_environment_variable_missing(self, mock_dependencies):
        """Test handling of missing environment variables."""
        from orchestrator import KYCOrchestrator

        # Initialize orchestrator without environment variables
        orchestrator = KYCOrchestrator()
        arns = orchestrator._get_function_arns()

        # All ARNs should be None when environment variables are missing
        for arn in arns.values():
            assert arn is None

    def test_concurrent_request_simulation(self, mock_dependencies, mock_environment_variables,
                                         sample_customer_request, mock_lambda_responses):
        """Test that multiple concurrent requests work independently."""
        from orchestrator import KYCOrchestrator

        def mock_invoke(FunctionName, InvocationType, Payload):
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(mock_lambda_responses['document_validation']).encode()
            return {'Payload': mock_response}

        mock_dependencies['mock_lambda_client'].invoke.side_effect = mock_invoke

        # Create two orchestrator instances (simulating concurrent requests)
        orchestrator1 = KYCOrchestrator()
        orchestrator2 = KYCOrchestrator()

        # Process requests
        result1 = orchestrator1.process_kyc(sample_customer_request)
        result2 = orchestrator2.process_kyc(sample_customer_request)

        # Each should have unique KYC IDs
        assert result1['kycId'] != result2['kycId']
        assert result1['overallStatus'] in ['success', 'partial', 'failed']
        assert result2['overallStatus'] in ['success', 'partial', 'failed']