import unittest
import requests

APIGW_URL = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
DOCUMENTS_URL = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
headers = {
    "Content-Type": "application/json",
    "Authorization": "XXXXXXXXXXXXXXXXXXXXXX"
}
class TestCertificateOfIncorporation DocumentValidation(unittest.TestCase):
    def test_businessnumber_PVT-RXUMYGVQ(self):
        payload ={"uploadedDocumentUrl": f"{DOCUMENTS_URL}/CertificateOfIncorporation /businessnumber_PVT-RXUMYGVQ.pdf",
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
    
    def test_businessnumber_PVT-V7UAY893(self):
        payload ={"uploadedDocumentUrl": f"{DOCUMENTS_URL}/CertificateOfIncorporation /businessnumber_PVT-V7UAY893.pdf",
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