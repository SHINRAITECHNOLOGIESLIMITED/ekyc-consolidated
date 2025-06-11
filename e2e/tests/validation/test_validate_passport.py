import unittest
from e2e.tests.config import *
from e2e.tests.validation.validate_test_util import validate_test
class TestPassportDocumentValidation(unittest.TestCase):
    URL = f"{APIGW_URL}/document/passport"
    def test_passportnumber_DK9038(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_PASSPORT-001sample.jpg",
            "documentType":"P",
            "countryCode":"KEN",
            "passportNumber":"BK120129",
            "personalNumber":"1736740",
            "surname":"KAJIMBA",
            "givenNames":"GEORGE HUMPHREY",
            # "gender":"M",
            "dateOfBirth":"1987-05-18",
            "placeOfBirth":"M MIGORI, Ken",
            # "dateOfIssue":"2020-08-20", #Supplied sample documents has date of issuer blurred out
            # "dateOfExpiry":"2030-09-03", #Supplied sample documents has date of issuer blurred out - only 03 AUG is available
            "nationality":"KENYAN",
            "issuingAuthority":"GOVERNMENT OF KENYA",
        }
        validate_test(tester= self,
                      url= self.URL,
                      payload=payload)

    def test_passportnumber_A168105(self):
        #old kenyan passport is not supported
        return
        payload ={"uploadedDocumentUrl": f"s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_PASSPORT-002-sample.jpg",
            "documentType":"P",
            "countryCode":"KEN",
            "passportNumber":"A168105",
            "personalNumber":"560224",
            "surname":"Nyamai",
            "givenNames":"Stephen Biko",
            "gender":"M",
            "dateOfBirth":"1984-02-19",
            "placeOfBirth":"NAIROBI, KEN",
            "dateOfIssue":"2009-06-16",
            "dateOfExpiry":"2019-06-16",
            "nationality":"KENYAN",
            "issuingAuthority":"PASSPORT CONTROL OF NAIROBI",
        }

        validate_test(tester= self,
                      url= self.URL,
                      payload=payload)

    def test_passportnumber_AK1577133(self):
        #skewed passport is not supported currently - wating for adapter configrations to adapt it
        return
        payload ={"uploadedDocumentUrl": 
            f"s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_PASSPORT-003-sample.png",
            "documentType":"P",
            "countryCode":"KEN",
            "passportNumber":"AK1577133",
            "personalNumber":"560224",
            "surname":"Nyamai",
            "givenNames":"Stephen Biko",
            "gender":"M",
            "dateOfBirth":"1984-02-19",
            "placeOfBirth":"NAIROBI, KEN",
            "dateOfIssue":"2009-06-16",
            "dateOfExpiry":"2019-06-16",
            "nationality":"KENYAN",
            "issuingAuthority":"GOVERNMENT OF KENYA",
        }
        validate_test(tester= self,
                      url= self.URL,
                      payload=payload)
if __name__ == '__main__':
    unittest.main()