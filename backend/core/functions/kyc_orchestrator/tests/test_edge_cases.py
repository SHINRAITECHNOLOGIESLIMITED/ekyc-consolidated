"""
Edge case tests for the KYC orchestrator.
"""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestKYCOrchestratorEdgeCases:
    """Test edge cases and error scenarios."""

    def test_malformed_lambda_response(self, mock_dependencies, mock_environment_variables, sample_customer_request):
        """Test handling of malformed responses from Lambda functions."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Mock malformed response
        mock_response = MagicMock()
        mock_response.read.return_value = b'not-valid-json'
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        result = orchestrator.process_kyc(sample_customer_request)

        assert result['overallStatus'] == 'failed'
        assert len(result['errors']) > 0

    def test_empty_response_from_lambda(self, mock_dependencies, mock_environment_variables, sample_customer_request):
        """Test handling of empty responses from Lambda functions."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Mock empty response
        mock_response = MagicMock()
        mock_response.read.return_value = b''
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        result = orchestrator.process_kyc(sample_customer_request)

        assert result['overallStatus'] == 'failed'

    def test_lambda_function_not_found(self, mock_dependencies, mock_environment_variables, sample_customer_request):
        """Test handling when Lambda function doesn't exist."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Mock function not found error
        mock_lambda_client.invoke.side_effect = Exception("Function not found: arn:aws:lambda:...")

        result = orchestrator.process_kyc(sample_customer_request)

        assert result['overallStatus'] == 'failed'

    def test_very_long_processing_time(self, mock_dependencies, mock_environment_variables, sample_customer_request):
        """Test handling of very long processing times."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        orchestrator.start_time = 0  # Very old start time

        mock_lambda_client = mock_dependencies['mock_lambda_client']
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': '{"success": true}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        with patch('time.time', return_value=1000000000):  # Very large time
            result = orchestrator.process_kyc(sample_customer_request)

        assert result['processingTime'] > 0
        assert isinstance(result['processingTime'], (int, float))

    def test_complex_name_parsing(self, mock_dependencies, mock_environment_variables):
        """Test name parsing for background checks with complex names."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': '{"success": true, "riskScore": 5}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        # Test various complex name formats
        complex_names = [
            "Jean-Pierre Marie François",  # Hyphenated and multiple middle names
            "Mary Elizabeth O'Connor",     # Apostrophe
            "José María García-López",     # Accents and hyphen
            "SingleName",                  # Just one name
            "A B C D E F",                # Many names
            "",                           # Empty name (edge case)
        ]

        for name in complex_names:
            request_data = {
                'personalData': {
                    'name': name,
                    'idNumber': '12345678',
                    'dateOfBirth': '1990-01-15',
                    'gender': 'Male'
                }
            }

            response = {'metadata': {'functionsInvoked': []}, 'results': {}}

            if name:  # Skip empty names
                result = orchestrator._process_background_check(request_data, response)
                assert result is not None

    def test_unicode_and_special_characters(self, mock_dependencies, mock_environment_variables):
        """Test handling of Unicode and special characters in names."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': '{"status": "Valid", "success": true}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        unicode_request = {
            'processType': 'customer',
            'personalData': {
                'name': 'Αλέξανδρος Παπαδόπουλος',  # Greek characters
                'idNumber': '12345678',
                'dateOfBirth': '1990-01-15',
                'gender': 'Male'
            },
            'documents': {
                'nationalIdUrl': 'https://example.com/doc.pdf'
            }
        }

        response = {'metadata': {'functionsInvoked': []}, 'results': {}}
        result = orchestrator._process_document_validation(unicode_request, response)

        assert result is not None

    def test_boundary_date_values(self, mock_dependencies, mock_environment_variables):
        """Test boundary date values."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': '{"status": "Valid", "success": true}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        boundary_dates = [
            '1900-01-01',  # Very old date
            '2023-12-31',  # Recent date
            '2000-02-29',  # Leap year date
            '1999-02-28',  # Non-leap year boundary
        ]

        for date in boundary_dates:
            request_data = {
                'processType': 'customer',
                'personalData': {
                    'name': 'Test Person',
                    'idNumber': '12345678',
                    'dateOfBirth': date,
                    'gender': 'Male'
                },
                'documents': {
                    'nationalIdUrl': 'https://example.com/doc.pdf'
                }
            }

            response = {'metadata': {'functionsInvoked': []}, 'results': {}}
            result = orchestrator._process_document_validation(request_data, response)

            assert result is not None

    def test_missing_optional_fields(self, mock_dependencies, mock_environment_variables):
        """Test handling of missing optional fields."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': '{"success": true}'
        }).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        minimal_request = {
            'processType': 'customer',
            'personalData': {
                'name': 'Test Person',
                'idNumber': '12345678',
                'pinNumber': 'A000000000B',
                'dateOfBirth': '1990-01-15'
                # Missing gender (optional for some operations)
            },
            'documents': {
                'nationalIdUrl': 'https://example.com/doc.pdf',
                'passportPhotoUrl': 'https://example.com/photo.jpg',
                'kraUrl': 'https://example.com/kra.pdf'
            }
            # Missing options (should use defaults)
        }

        result = orchestrator.process_kyc(minimal_request)

        assert result is not None
        assert 'kycId' in result

    def test_lambda_response_status_edge_cases(self, mock_dependencies, mock_environment_variables):
        """Test various HTTP status codes from Lambda responses."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        status_codes = [200, 201, 400, 401, 403, 404, 500, 502, 503, 504]

        for status_code in status_codes:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({
                'statusCode': status_code,
                'body': '{"message": f"Status {status_code}", "error": "Test error"}'
            }).encode()
            mock_lambda_client.invoke.return_value = {'Payload': mock_response}

            function_arn = 'arn:aws:lambda:us-east-1:123456789:function:TestFunction'
            payload = {'test': 'data'}

            result = orchestrator._invoke_lambda_function(function_arn, payload)

            if status_code < 400:
                # Should parse as successful (might not have success=True, but that's ok)
                assert 'message' in result or 'success' in result
            else:
                # Should be marked as failed
                assert result['success'] is False
                assert 'error' in result

    def test_nested_json_parsing(self, mock_dependencies, mock_environment_variables):
        """Test handling of deeply nested JSON responses."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Create deeply nested response
        nested_response = {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'data': {
                    'level1': {
                        'level2': {
                            'level3': {
                                'deepValue': 'test',
                                'arrayData': [1, 2, 3],
                                'nullValue': None,
                                'booleanValue': True
                            }
                        }
                    }
                }
            })
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(nested_response).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        function_arn = 'arn:aws:lambda:us-east-1:123456789:function:TestFunction'
        payload = {'test': 'data'}

        result = orchestrator._invoke_lambda_function(function_arn, payload)

        assert result['success'] is True
        assert 'data' in result
        assert result['data']['level1']['level2']['level3']['deepValue'] == 'test'

    def test_memory_and_performance_edge_cases(self, mock_dependencies, mock_environment_variables):
        """Test handling of large responses and memory constraints."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Create large response (simulating a large document analysis result)
        large_data = {
            'extractedText': 'A' * 10000,  # Large text field
            'metadata': {f'field_{i}': f'value_{i}' for i in range(1000)},  # Many fields
            'arrayData': [{'item': i, 'data': 'x' * 100} for i in range(100)]  # Large array
        }

        large_response = {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'result': large_data
            })
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(large_response).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        function_arn = 'arn:aws:lambda:us-east-1:123456789:function:TestFunction'
        payload = {'test': 'data'}

        result = orchestrator._invoke_lambda_function(function_arn, payload)

        assert result['success'] is True
        assert 'result' in result
        assert len(result['result']['extractedText']) == 10000

    def test_concurrent_lambda_invocations_simulation(self, mock_dependencies, mock_environment_variables,
                                                    sample_customer_request):
        """Test simulation of concurrent Lambda invocations."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        invocation_count = 0

        def mock_invoke(FunctionName, InvocationType, Payload):
            nonlocal invocation_count
            invocation_count += 1

            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'invocationId': invocation_count
                })
            }).encode()
            return {'Payload': mock_response}

        mock_lambda_client.invoke.side_effect = mock_invoke

        result = orchestrator.process_kyc(sample_customer_request)

        # Should have made multiple Lambda invocations
        assert invocation_count > 0
        assert result is not None

    def test_null_and_undefined_values(self, mock_dependencies, mock_environment_variables):
        """Test handling of null and undefined values in responses."""
        from orchestrator import KYCOrchestrator

        orchestrator = KYCOrchestrator()
        mock_lambda_client = mock_dependencies['mock_lambda_client']

        # Response with various null/undefined values
        null_response = {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'nullField': None,
                'emptyString': '',
                'emptyArray': [],
                'emptyObject': {},
                'zeroValue': 0,
                'falseValue': False
            })
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(null_response).encode()
        mock_lambda_client.invoke.return_value = {'Payload': mock_response}

        function_arn = 'arn:aws:lambda:us-east-1:123456789:function:TestFunction'
        payload = {'test': 'data'}

        result = orchestrator._invoke_lambda_function(function_arn, payload)

        assert result['success'] is True
        assert result['nullField'] is None
        assert result['emptyString'] == ''
        assert result['emptyArray'] == []
        assert result['emptyObject'] == {}
        assert result['zeroValue'] == 0
        assert result['falseValue'] is False