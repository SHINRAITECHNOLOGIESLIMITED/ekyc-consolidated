import json
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Use the mock version of app.py for testing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mock_app import lambda_handler

class TestBackgroundCheckIntegration(unittest.TestCase):
    
    def setUp(self):
        # Set up mocks for external dependencies
        self.mock_portal = MagicMock()
        self.mock_esb = MagicMock()
        self.mock_lexisnexis = MagicMock()
        self.mock_esb.lexisnexis = self.mock_lexisnexis
    
    @patch('mock_app.validator.lexisnexis.search_record')
    @patch('mock_app.portal.capture_background_check')
    def test_end_to_end_success(self, mock_capture, mock_search):
        """Test the entire Lambda function flow with mocked external dependencies"""
        # Mock the LexisNexis API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "result": "PASS",
                "score": 95,
                "details": {
                    "matches": []
                }
            }
        }
        mock_search.return_value = mock_response
        
        # Create test event
        test_event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                "firstName": "John",
                "middleName": "Doe",
                "lastName": "Smith",
                "gender": "Male",
                "dateOfBirth": "1990-01-01",
                "nationalIdentificationNumber": "12345678"
            })
        }
        
        # Execute
        response = lambda_handler(test_event, {})
        
        # Assert
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body["result"], "PASS")
        self.assertEqual(response_body["score"], 95)
        self.assertIn("message", response_body)
        
        # Verify external service calls
        mock_search.assert_called_once()
        mock_capture.assert_called_once()
        
        # Verify correct data was passed to LexisNexis
        lexis_call_args = mock_search.call_args[0][0]
        self.assertEqual(lexis_call_args["firstName"], "John")
        self.assertEqual(lexis_call_args["middleName"], "Doe")
        self.assertEqual(lexis_call_args["lastName"], "Smith")
        self.assertEqual(lexis_call_args["countryCode"], "KEN")
    
    @patch('mock_app.validator.lexisnexis.search_record')
    @patch('mock_app.portal.capture_background_check')
    def test_lexisnexis_error_handling(self, mock_capture, mock_search):
        """Test handling of LexisNexis API errors"""
        # Mock the LexisNexis API error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "success": False,
            "error": "Invalid data format"
        }
        mock_search.return_value = mock_response
        
        # Create test event
        test_event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                "firstName": "John",
                "lastName": "Smith",
                "gender": "Male",
                "dateOfBirth": "1990-01-01",
                "nationalIdentificationNumber": "12345678"
            })
        }
        
        # Execute
        response = lambda_handler(test_event, {})
        
        # Assert
        self.assertEqual(response['statusCode'], 400)
        
        # Verify external service calls
        mock_search.assert_called_once()
        mock_capture.assert_not_called()
    
    @patch('mock_app.validate')
    def test_missing_required_fields(self, mock_validate):
        """Test validation of required fields"""
        # Mock validation failure
        mock_validate.side_effect = Exception("Missing required fields")
        
        # Create test event with missing required fields
        test_event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                "firstName": "John",
                # Missing lastName, gender, dateOfBirth, nationalIdentificationNumber
            })
        }
        
        # Execute
        response = lambda_handler(test_event, {})
        
        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('validation failed', json.loads(response['body'])['message'])

if __name__ == '__main__':
    unittest.main()