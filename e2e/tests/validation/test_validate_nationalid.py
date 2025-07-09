from pprint import pprint
import unittest
import json

from e2e.tests.config import *
from e2e.tests.validation.validate_test_util import validate_test
class TestNationalIDDocumentValidation(unittest.TestCase):
    URL = f"{APIGW_URL}/document/nationalid"
    def test_36296352_JOEL(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/JoelID.jpg",
            "serialNumber":"244772451",
            "idNumber":"36296352",
            "fullNames":"JOEL MUUO",
            "dateOfBirth":"30-08-1998",
            "dateOfIssue":"28-03-2017",
            # "gender":"M",
            "districtOfBirth":"KIBWEZI",
            "placeOfIssue":"BIASHARA",
        }
        validate_test(tester= self,
                      url= self.URL,
                      payload=payload)

    def test_23224868_STEPHEN(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/BiksxID.pdf",
            "serialNumber":"217990310",
            "idNumber":"23224868",
            "fullNames":"STEPHEN BIKO NYAMAI",
            # "dateOfBirth":"19-02-1984",
            "dateOfIssue":"01-04-2003",
            "gender":"M",
            "districtOfBirth":"NAIROBI",
            "placeOfIssue":"MAKADARA",
        }
        validate_test(tester= self,
                      url= self.URL,
                      payload=payload)


if __name__ == '__main__':
    unittest.main()