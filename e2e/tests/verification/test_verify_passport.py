import unittest
import json
from e2e.tests.config import *
from e2e.tests.verification.verify_test_util import verifity_test

class TestPassportDocumentVerification(unittest.TestCase):
    URL=f"{APIGW_URL}/government/passport"
    def test_passportnumber_AK1515374(self):
        payload ={
            "idNumber": "32140017",
            "passportNumber":"AK1515374",
            "surname":"NYAMBURA",
            "gender": "F",
            "firstName": "EFFIE",
            "otherName": "NJOKI",
            "dateOfBirth":"1994-12-19",
            "dateOfIssue":"2024-05-06",
            "dateOfExpiry":"2034-05-05",
        }
        verifity_test(tester= self,
                      url= self.URL,
                      payload=payload)
        # self.assertEqual(post_with_auth(self.URL, json=payload).status_code, 417)

    def test_passportnumber_A2312084_old(self):
            payload ={
                "idNumber": "32140017",
                "passportNumber":"A2312084",
                "surname":"NYAMBURA",
                "gender": "F",
                "firstName": "EFFIE",
                "otherName": "NJOKI",
                "dateOfBirth":"1994-12-19",
                "dateOfIssue":"2014-12-29",
                "dateOfExpiry":"2024-12-27",
            }
            verifity_test(tester= self,
                          url= self.URL,
                          payload=payload)
            # self.assertEqual(post_with_auth(self.URL, json=payload).status_code, 417)


    def test_passportnumber_AK1370344(self):
        payload ={
            "idNumber": "26465570",
            "passportNumber":"AK1370344",
            "gender": "M",
            "firstName":"Timothy",
            "otherName": "",
            "surname":"Munyao",
            "dateOfBirth":"1988-01-13",
            "dateOfIssue":"2023-07-20",
            "dateOfExpiry":"2033-07-19",
        }
        verifity_test(tester= self,
                      url= self.URL,
                      payload=payload)

    def test_passportnumber_A168105_old(self):
        payload ={
            "idNumber": "23224868",
            "passportNumber":"A168105",
            "gender": "M",
            "surname":"Nyamai",
            "firstName":"Stephen",
            "otherName": "Biko",
            "dateOfBirth":"1984-02-19",
            "dateOfIssue":"2009-06-16",
            "dateOfExpiry":"2019-06-16",
        }
        verifity_test(tester= self,
                      url= self.URL,
                      payload=payload)

    def test_passportnumber_AK1577133_new(self):
        payload ={
            "idNumber":"23224868",
            "passportNumber":"AK1577133",
            "gender": "M",
            "surname":"Nyamai",
            "firstName":"Stephen",
            "otherName": "Biko",
            "dateOfBirth":"1984-02-19",
            "dateOfIssue":"2024-08-06",
            "dateOfExpiry":"2034-07-06",
        }
        verifity_test(tester= self,
                      url= self.URL,
                      payload=payload)

if __name__ == '__main__':
    unittest.main()