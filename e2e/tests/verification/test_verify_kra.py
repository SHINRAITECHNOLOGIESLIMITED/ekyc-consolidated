import json
import unittest
from pprint import pprint

from e2e.tests.config import *
class TestKRAPinCertificateDocumentVerification(unittest.TestCase):
    def test_pin_A003388522V(self):
        payload ={"certificateDate":"2014-10-14", 
            "idNumber":"32140017",
            "pin":"A003388522V", 
            "taxPayerName":"Jackson Gitonga Mwangi", 
            "emailAddress":"jackmwangi02@gmail.com",  
        }
        response = post_with_auth(f"{APIGW_URL}/government/kra", json= json.dumps(payload))
        
        # Check if the response status code is 200 (OK)
        if response.status_code != 200:
            print(response.text)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    
    def test_pin_A011797599Y(self):
        payload ={"pin":"A011797599Y", 
            "taxPayerName":"JOEL MUUO",   
        }
        response = post_with_auth(f"{APIGW_URL}/government/kra", json= json.dumps(payload))
        
        # Check if the response status code is 200 (OK)
        if response.status_code != 200:
            print(response.text)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    def test_pin_A008279496S(self):
        payload ={"pin":"A008279496S", 
            "taxPayerName":"EFFIE NJOKI NYAMBURA",   
        }
        response = post_with_auth(f"{APIGW_URL}/government/kra", json= json.dumps(payload))
        
        # Check if the response status code is 200 (OK)
        if response.status_code != 200:
            print(response.text)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    def test_pin_A005394549Z(self):
        payload ={"pin":"A005394549Z", 
            "taxPayerName":"PATRICK OMONDI ODHIAMBO ",   
        }
        response = post_with_auth(f"{APIGW_URL}/government/kra", json= json.dumps(payload))
        
        # Check if the response status code is 200 (OK)
        if response.status_code != 200:
            print(response.text)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    

if __name__ == '__main__':
    unittest.main()