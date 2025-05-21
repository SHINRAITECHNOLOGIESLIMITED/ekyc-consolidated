import unittest
from pprint import pprint
import json

from e2e.tests.config import *
class TestPassportDocumentValidation(unittest.TestCase):
    def test_passportnumber_DK9038(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_PASSPORT-001sample.jpg",
            "documentType":"P", 
            "countryCode":"KEN", 
            "passportNumber":"DK9038", 
            "personalNumber":"1736740", 
            "surname":"KAJIMBA", 
            "givenNames":"GEORGE HUMPHREY", 
            "gender":"M", 
            "dateOfBirth":"1987-05-18", 
            "placeOfBirth":"MIGORI, Ken", 
            "dateOfIssue":"2020-08-20", 
            "dateOfExpiry":"2030-09-03", 
            "nationality":"KENYAN", 
            "issuingAuthority":"GOVERNMENT OF KENYA",  
        }
        
        # print(json.dumps(payload))
        response = post_with_auth(f"{APIGW_URL}/document/passport", json= json.dumps(payload))
        
        # Check if the response status code is 200 (OK)
        if response.status_code != 200:
            print(response.text)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)

if __name__ == '__main__':
    unittest.main()