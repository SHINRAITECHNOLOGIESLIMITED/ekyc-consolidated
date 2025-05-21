from pprint import pprint
import unittest
import json

from e2e.tests.config import *
class TestNationalIDDocumentValidation(unittest.TestCase):
    def test_idnumber_36296352(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
            "serialNumber":"242772451", 
            "idNumber":"36296352", 
            "fullNames":"JOEL MUUO", 
            "dateOfBirth":"1998-08-30", 
            "dateOfIssue":"2017-03-31", 
            "gender":"Male", 
            "districtOfBirth":"KIBWEZI", 
            "placeOfIssue":"KIBWEZI",  
        }
        # print(json.dumps(payload))
        response = post_with_auth(f"{APIGW_URL}/document/nationalid", json= json.dumps(payload))
        
        # Check if the response status code is 200 (OK)
        if response.status_code != 200:
            print(response.text)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    def test_idnumber_23224868(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/c2a5e464-30b1-70e8-eeb0-8c196da88147/23224868/KENYAN_NATIONAL_ID-fc1aa117beca19366fcc301c9aa87e50e7f4e5aa.pdf",
            "serialNumber":"217990310", 
            "idNumber":"23224868", 
            "fullNames":"STEPHEN BIKO NYAMAI", 
            "dateOfBirth":"19-02-1984", 
            "dateOfIssue":"01-04-2003", 
            "gender":"MALE", 
            "districtOfBirth":"KIBWEZI", 
            "placeOfIssue":"MAKADARA",  
        }
        # print(json.dumps(payload))
        response = post_with_auth(f"{APIGW_URL}/document/nationalid", json= json.dumps(payload))
        
        # Check if the response status code is 200 (OK)
        if response.status_code != 200:
            print(response.text)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    

if __name__ == '__main__':
    unittest.main()