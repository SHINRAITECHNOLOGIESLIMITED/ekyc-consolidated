import json
import unittest
from pprint import pprint

import requests

from e2e.tests.config import *


class TestCertificateOfIncorporationDocumentValidation(unittest.TestCase):
    def test_businessnumber_PVTRXUMYGVQ(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/CERTIFICATE_OF_INCORPORATION-003Sample.jpg",
            "businessNumber":"PVT-RXUMYGVQ", 
            "businessName":"DETALI INSURANCE AGENCY LIMITED", 
            "dateOfIncorporation":"2024-04-09", 
            "businessType":"Private Limited Company",  
        }
        response = post_with_auth(f"{APIGW_URL}/document/cr12", json= json.dumps(payload))
        # Check if the response status code is 200 (OK)
        if response.status_code != 200:
            print(response.text)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)

if __name__ == '__main__':
    unittest.main()