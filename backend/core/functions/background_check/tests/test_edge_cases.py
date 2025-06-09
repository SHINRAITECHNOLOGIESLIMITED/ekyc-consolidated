import json
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Use the mock version of app.py for testing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mock_app import lambda_handler

class TestEdgeCases(unittest.TestCase):
    
    @patch('mock_app.validate')
    @patch('mock_app.validator.lexisnexis.search_record')
    def test_empty_required_fields(self, mock_search, mock_validate):
        """Test handling of empty strings for required fields"""
        # Create test event with empty required fields
        test_event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                "firstName": "",
                "lastName": "",
                "gender": "",
                "dateOfBirth": "1990-01-01",
                "nationalIdentificationNumber": ""
            })
        }
        
        # Mock successful validation
        mock_validate.return_value = True
        
        # Mock successful API response
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
        
        # Execute
        response = lambda_handler(test_event, {})
        
        # The function should accept empty strings as valid values
        self.assertEqual(response['statusCode'], 200)
    
    @patch('mock_app.validate')
    def test_malformed_date_format(self, mock_validate):
        """Test handling of malformed date format"""
        # Create test event with malformed date
        test_event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                "firstName": "John",
                "lastName": "Smith",
                "gender": "Male",
                "dateOfBirth": "01/01/1990",  # Wrong format, should be YYYY-MM-DD
                "nationalIdentificationNumber": "12345678"
            })
        }
        
        # Mock validation failure
        mock_validate.side_effect = Exception("Invalid date format")
        
        # Execute
        response = lambda_handler(test_event, {})
        
        # Should fail validation due to date format
        self.assertEqual(response['statusCode'], 400)
    
    @patch('mock_app.validate')
    def test_additional_properties(self, mock_validate):
        """Test handling of additional properties in request"""
        # Create test event with additional properties
        test_event = {
            'httpMethod': 'POST',
            'body': json.dumps({
                "firstName": "John",
                "lastName": "Smith",
                "gender": "Male",
                "dateOfBirth": "1990-01-01",
                "nationalIdentificationNumber": "12345678",
                "extraField": "This should be rejected"
            })
        }
        
        # Mock validation failure
        mock_validate.side_effect = Exception("Additional properties not allowed")
        
        # Execute
        response = lambda_handler(test_event, {})
        
        # Should fail validation due to additional properties
        self.assertEqual(response['statusCode'], 400)

if __name__ == '__main__':
    unittest.main()