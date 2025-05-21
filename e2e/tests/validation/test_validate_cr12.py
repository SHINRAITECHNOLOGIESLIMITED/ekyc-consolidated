import unittest
from pprint import pprint

import requests

from e2e.tests.config import *


class TestCertificateOfIncorporationDocumentValidation(unittest.TestCase):
    def test_businessnumber_PVTRXUMYGVQ(self):
        payload ={"uploadedDocumentUrl": f"{DOCUMENTS_URL}/CertificateOfIncorporation/businessnumber_PVTRXUMYGVQ.pdf",
            "businessNumber":"PVT-RXUMYGVQ", 
            "businessName":"DETALI INSURANCE AGENCY LIMITED", 
            "dateOfIncorporation":"9 Apr 2024", 
            "businessType":"Private Limited Company",  
        }
        response = requests.post(f"{APIGW_URL}/documents/cr12", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    def test_businessnumber_PVTV7UAY893(self):
        payload ={"uploadedDocumentUrl": f"{DOCUMENTS_URL}/CertificateOfIncorporation/businessnumber_PVTV7UAY893.pdf",
            "businessNumber":"PVT-V7UAY893", 
            "businessName":"Cloudtech Crafters Limited", 
            "dateOfIncorporation":"20 Feb 2024", 
            "businessType":"Private Limited Company",  
        }
        response = requests.post(f"{APIGW_URL}/documents/cr12", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    

if __name__ == '__main__':
    unittest.main()