from pprint import pprint
import unittest
import json

from e2e.tests.config import *
from e2e.tests.validation.validate_test_util import validate_test
class TestNationalIDDocumentValidation(unittest.TestCase):
    URL = f"{APIGW_URL}/document/nationalid"
    def test_36296352_JOEL(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
            "serialNumber":"244772451",
            "idNumber":"36296352",
            "fullNames":"JOEL MUUO",
            "dateOfBirth":"30-08-1998",
            "dateOfIssue":"28-03-2017",
            "gender":"Male",
            "districtOfBirth":"KIBWEZI",
            "placeOfIssue":"BIASHARA",
        }
        validate_test(tester= self,
                      url= self.URL,
                      payload=payload)

    def test_23224868_STEPHEN(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/c2a5e464-30b1-70e8-eeb0-8c196da88147/23224868/KENYAN_NATIONAL_ID-fc1aa117beca19366fcc301c9aa87e50e7f4e5aa.pdf",
            "serialNumber":"217990310",
            "idNumber":"23224868",
            "fullNames":"STEPHEN BIKO NYAMAI",
            "dateOfBirth":"19-02-1984",
            "dateOfIssue":"01-04-2003",
            "gender":"MALE",
            "districtOfBirth":"NAIROBI",
            "placeOfIssue":"MAKADARA",
        }
        validate_test(tester= self,
                      url= self.URL,
                      payload=payload)


if __name__ == '__main__':
    unittest.main()