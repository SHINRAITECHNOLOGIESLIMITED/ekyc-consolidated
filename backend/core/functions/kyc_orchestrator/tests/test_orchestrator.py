"""
Unit tests for the KYC orchestrator core logic.
"""

import json
import pytest
from unittest.mock import patch, MagicMock, call


class TestKYCOrchestrator:
    """Test cases for the KYC orchestrator class."""

    def test_orchestrator_initialization(self, mock_dependencies, mock_environment_variables):
        """Test orchestrator initialization."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()

        assert orchestrator.lambda_client is not None
        assert orchestrator.function_arns is not None
        assert orchestrator.start_time is None

    def test_get_function_arns(self, mock_dependencies, mock_environment_variables):
        """Test function ARN retrieval from environment variables."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        arns = orchestrator._get_function_arns()

        expected_functions = [
            'document_validation',
            'government_verification',
            'background_check',
            'face_liveness',
            'certification'
        ]

        for func in expected_functions:
            assert func in arns
            assert arns[func] is not None

    def test_process_kyc_customer_success(self, mock_dependencies, mock_environment_variables,
                                        sample_customer_request, mock_lambda_responses):
        """Test successful customer KYC processing."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()

        # Mock Lambda client responses
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Create mock responses for each function call
        def mock_invoke(FunctionName, InvocationType, Payload):
            mock_response = MagicMock()
            if 'DocumentValidation' in FunctionName:
                mock_response.read.return_value = json.dumps(mock_lambda_responses['document_validation']).encode()
            elif 'GovernmentVerification' in FunctionName:
                mock_response.read.return_value = json.dumps(mock_lambda_responses['government_verification']).encode()
            elif 'BackgroundChecks' in FunctionName:
                mock_response.read.return_value = json.dumps(mock_lambda_responses['background_check']).encode()
            elif 'Certification' in FunctionName:
                mock_response.read.return_value = json.dumps(mock_lambda_responses['certification']).encode()

            return {'Payload': mock_response}

        mock_lambda_client.invoke.side_effect = mock_invoke

        # Execute test
        result = orchestrator.process_kyc(sample_customer_request)

        # Assertions
        assert result['overallStatus'] in ['success', 'partial']
        assert result['processType'] == 'customer'
        assert 'kycId' in result
        assert 'timestamp' in result
        assert 'processingTime' in result
        assert 'results' in result
        assert 'documentValidation' in result['results']
        assert 'governmentVerification' in result['results']
        assert 'backgroundCheck' in result['results']  # Should be included due to options
        assert result['metadata']['totalSteps'] > 0

    def test_process_kyc_individual_agent_success(self, mock_dependencies, mock_environment_variables,
                                                sample_individual_agent_request, mock_lambda_responses):
        """Test successful individual agent KYC processing."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        def mock_invoke(FunctionName, InvocationType, Payload):
            mock_response = MagicMock()
            if 'DocumentValidation' in FunctionName:
                mock_response.read.return_value = json.dumps(mock_lambda_responses['document_validation']).encode()
            elif 'GovernmentVerification' in FunctionName:
                mock_response.read.return_value = json.dumps(mock_lambda_responses['government_verification']).encode()
            elif 'BackgroundChecks' in FunctionName:
                mock_response.read.return_value = json.dumps(mock_lambda_responses['background_check']).encode()
            elif 'FaceLiveness' in FunctionName:
                mock_response.read.return_value = json.dumps(mock_lambda_responses['face_liveness']).encode()
            elif 'Certification' in FunctionName:
                mock_response.read.return_value = json.dumps(mock_lambda_responses['certification']).encode()

            return {'Payload': mock_response}

        mock_lambda_client.invoke.side_effect = mock_invoke

        result = orchestrator.process_kyc(sample_individual_agent_request)

        assert result['overallStatus'] in ['success', 'partial']
        assert result['processType'] == 'individual_agent'
        assert 'faceLiveness' in result['results']  # Should be included due to options

    def test_process_kyc_business_agent_success(self, mock_dependencies, mock_environment_variables,
                                              sample_business_agent_request, mock_lambda_responses):
        """Test successful business agent KYC processing."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        def mock_invoke(FunctionName, InvocationType, Payload):
            mock_response = MagicMock()
            if 'DocumentValidation' in FunctionName:
                mock_response.read.return_value = json.dumps(mock_lambda_responses['document_validation']).encode()
            elif 'Certification' in FunctionName:
                mock_response.read.return_value = json.dumps(mock_lambda_responses['certification']).encode()

            return {'Payload': mock_response}

        mock_lambda_client.invoke.side_effect = mock_invoke

        result = orchestrator.process_kyc(sample_business_agent_request)

        assert result['overallStatus'] in ['success', 'partial']
        assert result['processType'] == 'business_agent'
        assert 'backgroundCheck' not in result['results']  # Should not be included due to options
        assert 'faceLiveness' not in result['results']  # Should not be included due to options

    def test_process_document_validation_national_id(self, mock_dependencies, mock_environment_variables):
        """Test document validation for national ID."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': '{"status": "Valid", "extractedData": {"name": "John Doe"}, "success": true}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        request_data = {
            'processType': 'customer',
            'personalData': {
                'name': 'John Doe',
                'idNumber': '12345678',
                'dateOfBirth': '1990-01-15'
            },
            'documents': {
                'nationalIdUrl': 'https://example.com/nationalid.pdf'
            }
        }

        response = {'metadata': {'functionsInvoked': []}, 'results': {}}
        result = orchestrator._process_document_validation(request_data, response)

        assert result is not None
        assert response['results']['documentValidation']['status'] == 'success'
        assert 'DocumentValidation-NationalID' in response['metadata']['functionsInvoked']

    def test_process_government_verification_national_id(self, mock_dependencies, mock_environment_variables):
        """Test government verification for national ID."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': '{"status": "Valid", "matchDetails": {"names": {"valid": true}}, "success": true}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        request_data = {
            'processType': 'customer',
            'personalData': {
                'name': 'John Doe',
                'idNumber': '12345678',
                'dateOfBirth': '1990-01-15',
                'gender': 'Male'
            }
        }

        response = {'metadata': {'functionsInvoked': []}, 'results': {}}
        result = orchestrator._process_government_verification(request_data, response)

        assert result is not None
        assert response['results']['governmentVerification']['status'] == 'success'
        assert 'GovernmentVerification-NationalID' in response['metadata']['functionsInvoked']

    def test_process_background_check(self, mock_dependencies, mock_environment_variables):
        """Test background check processing."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': '{"riskScore": 10, "status": "Low Risk", "success": true}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        request_data = {
            'personalData': {
                'name': 'John Michael Doe',
                'idNumber': '12345678',
                'dateOfBirth': '1990-01-15',
                'gender': 'Male'
            }
        }

        response = {'metadata': {'functionsInvoked': []}, 'results': {}}
        result = orchestrator._process_background_check(request_data, response)

        assert result is not None
        assert response['results']['backgroundCheck']['status'] == 'success'
        assert 'BackgroundCheck' in response['metadata']['functionsInvoked']

    def test_process_face_liveness(self, mock_dependencies, mock_environment_variables):
        """Test face liveness processing."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': '{"sessionId": "sess-12345", "status": "Created", "success": true}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        request_data = {}
        response = {'kycId': 'test-kyc-123', 'metadata': {'functionsInvoked': []}, 'results': {}}
        result = orchestrator._process_face_liveness(request_data, response)

        assert result is not None
        assert response['results']['faceLiveness']['status'] == 'success'
        assert 'FaceLiveness' in response['metadata']['functionsInvoked']

    def test_process_certification_customer(self, mock_dependencies, mock_environment_variables):
        """Test certification processing for customer."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': '{"s3Path": "certificates/cert-12345.pdf", "certificateUrl": "https://example.com/cert.pdf", "success": true}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        request_data = {'processType': 'customer'}
        response = {'metadata': {'functionsInvoked': []}, 'results': {}}

        result = orchestrator._process_certification(request_data, response, {}, {}, {}, {})

        assert result is not None
        assert response['results']['certification']['status'] == 'success'
        assert 'certificateUrl' in response
        assert 'Certification' in response['metadata']['functionsInvoked']

    def test_invoke_lambda_function_success(self, mock_dependencies, mock_environment_variables):
        """Test successful Lambda function invocation."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Mock successful response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': '{"status": "success", "data": "test"}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        function_arn = 'arn:aws:lambda:us-east-1:123456789:function:TestFunction'
        payload = {'test': 'data'}

        result = orchestrator._invoke_lambda_function(function_arn, payload)

        assert result['success'] is True
        assert 'status' in result
        mock_lambda_client.invoke.assert_called_once()

    def test_invoke_lambda_function_error_response(self, mock_dependencies, mock_environment_variables):
        """Test Lambda function invocation with error response."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Mock error response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 400,
            'body': '{"message": "Validation error", "error": "Invalid input"}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        function_arn = 'arn:aws:lambda:us-east-1:123456789:function:TestFunction'
        payload = {'test': 'data'}

        result = orchestrator._invoke_lambda_function(function_arn, payload)

        assert result['success'] is False
        assert 'error' in result
        assert result['statusCode'] == 400

    def test_invoke_lambda_function_exception(self, mock_dependencies, mock_environment_variables):
        """Test Lambda function invocation with exception."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Mock exception
        mock_lambda_client.invoke.side_effect = Exception("Connection error")

        function_arn = 'arn:aws:lambda:us-east-1:123456789:function:TestFunction'
        payload = {'test': 'data'}

        result = orchestrator._invoke_lambda_function(function_arn, payload)

        assert result['success'] is False
        assert 'Connection error' in result['error']

    def test_determine_step_status_all_success(self, mock_dependencies):
        """Test step status determination with all successful results."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()

        results = {
            'nationalId': {'success': True, 'status': 'Valid'},
            'passport': {'success': True, 'status': 'Valid'},
            'kra': {'success': True, 'status': 'Valid'}
        }

        status = orchestrator._determine_step_status(results)
        assert status == 'success'

    def test_determine_step_status_partial_success(self, mock_dependencies):
        """Test step status determination with partial success."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()

        results = {
            'nationalId': {'success': True, 'status': 'Valid'},
            'passport': {'success': False, 'status': 'Invalid'},
            'kra': {'success': True, 'status': 'Valid'}
        }

        status = orchestrator._determine_step_status(results)
        assert status == 'partial'

    def test_determine_step_status_all_failed(self, mock_dependencies):
        """Test step status determination with all failed results."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()

        results = {
            'nationalId': {'success': False, 'status': 'Invalid'},
            'passport': {'success': False, 'status': 'Invalid'}
        }

        status = orchestrator._determine_step_status(results)
        assert status == 'failed'

    def test_determine_step_status_empty_results(self, mock_dependencies):
        """Test step status determination with empty results."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()

        results = {}

        status = orchestrator._determine_step_status(results)
        assert status == 'failed'

    def test_finalize_response(self, mock_dependencies):
        """Test response finalization."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        orchestrator.start_time = 1000000.0  # Mock start time

        response = {
            'overallStatus': 'processing',
            'results': {
                'documentValidation': {'status': 'success'},
                'governmentVerification': {'status': 'success'}
            },
            'errors': [],
            'metadata': {
                'functionsInvoked': ['DocumentValidation', 'GovernmentVerification'],
                'totalSteps': 0,
                'successfulSteps': 2
            }
        }

        with patch('time.time', return_value=1000001.5):  # Mock current time
            finalized = orchestrator._finalize_response(response)

        assert finalized['overallStatus'] == 'success'
        assert finalized['processingTime'] == 1500  # 1.5 seconds in milliseconds
        assert finalized['metadata']['totalSteps'] == 2

    def test_fatal_error_handling(self, mock_dependencies, mock_environment_variables, sample_customer_request):
        """Test handling of fatal errors during processing."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()

        # Mock a fatal error during document validation
        with patch.object(orchestrator, '_process_document_validation', side_effect=Exception("Fatal error")):
            result = orchestrator.process_kyc(sample_customer_request)

        assert result['overallStatus'] == 'failed'
        assert len(result['errors']) > 0
        assert any('Fatal error occurred' in error.get('message', '') for error in result['errors'])