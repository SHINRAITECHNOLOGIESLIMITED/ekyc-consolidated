
import unittest
from e2e.tests.config import *
from e2e.tests.validation.validate_test_util import validate_test

expected_headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key, X-Amz-Date, X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        }

class TestCORSRegistration(unittest.TestCase):
    
    def check_endpoint(self,endpoint):
        URL = f"{APIGW_URL}/{endpoint}"
        response =  requests.options(url=URL, headers={'Content-Type': 'application/json'})
        self.assertEqual(200, response.status_code)
        response_headers = response.headers
        for name,value in response_headers.items():
            if name in expected_headers:
                self.assertEqual(expected_headers[name], value)
        for name,value in expected_headers.items():
            self.assertTrue(name in response_headers)
        
    def test_cors_agent_registration(self):    
        self.check_endpoint("agent-registration")
    def test_cors_customer_registration(self):    
        self.check_endpoint("customer-registration")


if __name__ == '__main__':
    unittest.main()