import json
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the src directory to the path so we can import the app module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.mock_app import lambda_handler, handle_background_check, make_response

class TestBackgroundCheckLambda(unittest.TestCase):
    
    def test_make_response(self):
        """Test the make_response helper function"""
        status_code = 200
        body = {"message": "Success"}
        response = make_response(status_code, body)
        
        self.assertEqual(response['statusCode'], status_code)
        self.assertEqual(json.loads(response['body']), body)
        self.assertEqual(response['headers']['Content-Type'], 'application/json')
        self.assertEqual(response['headers']['Access-Control-Allow-Origin'], 'https://main.d2896e60a8d7f8.amplifyapp.com')
    
    @patch('src.app.handle_background_check')
    def test_lambda_handler_post_success(self, mock_handle):
        """Test successful POST request handling"""
        # Setup
        mock_handle.return_value = make_response(200, {"message": "Success"})
        test_event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                "firstName": "Test",
                "lastName": "User",
                "gender": "Male",
                "dateOfBirth": "1990-01-01",
                "nationalIdentificationNumber": "12345678"
            })
        }
        
        # Execute
        response = lambda_handler(test_event, {})
        
        # Assert
        mock_handle.assert_called_once()
        self.assertEqual(response['statusCode'], 200)
    
    def test_lambda_handler_invalid_method(self):
        """Test handling of non-POST methods"""
        test_event = {'httpMethod': 'GET'}
        response = lambda_handler(test_event, {})
        self.assertEqual(response['statusCode'], 405)
    
    def test_lambda_handler_invalid_json(self):
        """Test handling of invalid JSON in request body"""
        test_event = {
            'httpMethod': 'POST',
            'body': "invalid json"
        }
        response = lambda_handler(test_event, {})
        self.assertEqual(response['statusCode'], 400)
    
    @patch('src.app.validate')
    def test_handle_background_check_schema_validation_failure(self, mock_validate):
        """Test schema validation failure handling"""
        # Setup
        mock_validate.side_effect = Exception("Validation error")
        test_data = {
            "firstName": "Test",
            # Missing required fields
        }
        
        # Execute
        response = handle_background_check(test_data)
        
        # Assert
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('validation failed', json.loads(response['body'])['message'])
    
    @patch('src.app.validator.lexisnexis.search_record')
    def test_handle_background_check_lexisnexis_error(self, mock_search):
        """Test handling of LexisNexis API errors"""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "API error"}
        mock_search.return_value = mock_response
        
        test_data = {
            "firstName": "Test",
            "lastName": "User",
            "gender": "Male",
            "dateOfBirth": "1990-01-01",
            "nationalIdentificationNumber": "12345678"
        }
        
        # Execute
        response = handle_background_check(test_data)
        
        # Assert
        self.assertEqual(response['statusCode'], 500)
    
    @patch('src.app.validator.lexisnexis.search_record')
    @patch('src.app.portal.capture_background_check')
    def test_handle_background_check_success(self, mock_capture, mock_search):
        """Test successful background check processing"""
        # Setup
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "result": "PASS",
                "score": 95
            }
        }
        mock_search.return_value = mock_response
        
        test_data = {
            "firstName": "Test",
            "lastName": "User",
            "gender": "Male",
            "dateOfBirth": "1990-01-01",
            "nationalIdentificationNumber": "12345678"
        }
        
        # Execute
        response = handle_background_check(test_data)
        
        # Assert
        mock_capture.assert_called_once()
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body["result"], "PASS")
        self.assertIn("message", response_body)

if __name__ == '__main__':
    unittest.main()