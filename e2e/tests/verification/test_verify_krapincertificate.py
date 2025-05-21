import unittest
from pprint import pprint

import requests

from e2e.tests.config import *
class TestKRAPinCertificateDocumentValidation(unittest.TestCase):
    def test_pin_A003388522V(self):
        payload ={"uploadedDocumentUrl": f"{DOCUMENTS_URL}/KRAPinCertificate/pin_A003388522V.pdf",
            "certificateDate":"14/10/2014", 
            "pin":"A003388522V", 
            "taxpayerName":"Jackson Gitonga Mwangi", 
            "emailAddress":"jackmwangi02@gmail.com",  
        }
        response = requests.post(f"{APIGW_URL}/documents/krapincertificate", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    def test_pin_A011797599Y(self):
        payload ={"uploadedDocumentUrl": f"{DOCUMENTS_URL}/KRAPinCertificate/pin_A011797599Y.pdf", 
            "pin":"A011797599Y", 
            "taxpayerName":"JOEL MUUO",   
        }
        response = requests.post(f"{APIGW_URL}/documents/krapincertificate", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    def test_pin_A008279496S(self):
        payload ={"uploadedDocumentUrl": f"{DOCUMENTS_URL}/KRAPinCertificate/pin_A008279496S.pdf", 
            "pin":"A008279496S", 
            "taxpayerName":"EFFIE NJOKI NYAMBURA",   
        }
        response = requests.post(f"{APIGW_URL}/documents/krapincertificate", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    def test_pin_A005394549Z(self):
        payload ={"uploadedDocumentUrl": f"{DOCUMENTS_URL}/KRAPinCertificate/pin_A005394549Z.pdf", 
            "pin":"A005394549Z", 
            "taxpayerName":"PATRICK OMONDI ODHIAMBO ",   
        }
        response = requests.post(f"{APIGW_URL}/documents/krapincertificate", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    

if __name__ == '__main__':
    unittest.main()