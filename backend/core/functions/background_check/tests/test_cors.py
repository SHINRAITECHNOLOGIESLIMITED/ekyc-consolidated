import json
import unittest
import sys
import os

# Use the mock version of app.py for testing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mock_app import make_response

class TestCORSHeaders(unittest.TestCase):
    
    def test_cors_headers_in_response(self):
        """Test that CORS headers are correctly set in responses"""
        response = make_response(200, {"message": "Success"})
        
        expected_headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': 'https://main.d2896e60a8d7f8.amplifyapp.com',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key, X-Amz-Date, X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        }
        
        for header, value in expected_headers.items():
            self.assertEqual(response['headers'][header], value)

if __name__ == '__main__':
    unittest.main()