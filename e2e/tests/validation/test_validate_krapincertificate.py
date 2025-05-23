import unittest
from pprint import pprint
import json

from e2e.tests.config import *
class TestKRAPinCertificateDocumentValidation(unittest.TestCase):
    def test_pin_A003388522V(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KRA_PIN_CERTIFICATE-002samplekra.jpg",
            "certificateDate":"2014-10-14", 
            "pin":"A003388522V", 
            "taxPayerName":"Jackson Gitonga Mwangi", 
            "emailAddress":"jackmwangi02@gmail.com",  
        }
        # print(json.dumps(payload))
        response = post_with_auth(f"{APIGW_URL}/document/krapincertificate", json= json.dumps(payload))
        
        # Check if the response status code is 200 (OK)
        if response.status_code != 200:
            print(response.text)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)

if __name__ == '__main__':
    unittest.main()