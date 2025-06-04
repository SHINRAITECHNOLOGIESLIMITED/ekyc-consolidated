import unittest
from e2e.tests.config import *
from e2e.tests.verification.verify_test_util import verifity_test

class TestPassportDocumentVerification(unittest.TestCase):
    URL=f"{APIGW_URL}/government/passport"
    def test_passportnumber_AK1515374(self):
        payload ={"documentType":"P",
            "countryCode":"KEN",
            "passportNumber":"AK1515374",
            "idNumber":"32140017",
            "personalNumber":"741116",
            "surname":"NYAMBURA",
            "gender": "F",
            "givenNames":"EFFIE NJOKI",
            "dateOfBirth":"1994-12-19",
            "placeOfBirth":"KIAMBU, KEN",
            "dateOfIssue":"2024-05-06",
            "dateOfExpiry":"2034-05-05",
            "nationality":"KENYAN",
            "issuingAuthority":"GOVERNMENT OF KENYA",
        }
        verifity_test(tester= self, 
                      url= self.URL,
                      payload=payload)


    def test_passportnumber_AK1370344(self):
        payload ={"documentType":"P",
            "countryCode":"KEN",
            "idNumber":"",
            "passportNumber":"AK1370344",
            "personalNumber":"1944445",
            "gender": "M",
            "surname":"Munyao",
            "givenNames":"Timothy",
            "dateOfBirth":"1988-01-13",
            "placeOfBirth":"NAIROBI, KEN",
            "dateOfIssue":"2023-07-20",
            "dateOfExpiry":"2033-07-19",
            "nationality":"KENYAN",
            "issuingAuthority":"GOVERNMENT OF KENYA",
        }
        verifity_test(tester= self, 
                      url= self.URL,
                      payload=payload)

if __name__ == '__main__':
    unittest.main()