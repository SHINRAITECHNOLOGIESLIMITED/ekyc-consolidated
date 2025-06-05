import unittest
from e2e.tests.config import *
from e2e.tests.verification.verify_test_util import verifity_test

class TestPassportDocumentVerification(unittest.TestCase):
    URL=f"{APIGW_URL}/government/passport"
    def test_passportnumber_AK1515374(self):
        payload ={
            "citizenship":"KEN",
            "passportNumber":"AK1515374",
            "idNumber":"32140017",
            "surname":"NYAMBURA",
            "gender": "F",
            "firstName": "EFFIE",
            "otherName": "NJOKI",
            "dateOfBirthFromPassport":"1994-12-19",
            "placeOfBirth":"KIAMBU, KEN",
            "dateOfIssue":"2024-05-06",
            "dateOfExpiry":"2034-05-05",
        }
        verifity_test(tester= self,
                      url= self.URL,
                      payload=payload)


    def test_passportnumber_AK1370344(self):
        payload ={
            "citizenship":"KENYAN",
            "idNumber":"",
            "passportNumber":"AK1370344",
            "gender": "M",
            "firstName":"Timothy",
            "otherName": "",
            "surname":"Munyao",
            "dateOfBirthFromPassport":"1988-01-13",
            "placeOfBirth":"NAIROBI, KEN",
            "dateOfIssue":"2023-07-20",
            "dateOfExpiry":"2033-07-19",
        }
        verifity_test(tester= self,
                      url= self.URL,
                      payload=payload)

    def test_passportnumber_A168105_old(self):
        payload ={
            "citizenship":"KEN",
            "idNumber":"23224868",
            "passportNumber":"A168105",
            "gender": "M",
            "surname":"Nyamai",
            "firstName":"Stephen",
            "otherName": "Biko",
            "dateOfBirthFromPassport":"1984-02-19",
            "placeOfBirth":"NAIROBI, KEN",
            "dateOfIssue":"2009-06-16",
            "dateOfExpiry":"2019-06-16",
        }
        verifity_test(tester= self,
                      url= self.URL,
                      payload=payload)

    def test_passportnumber_AK1577133_new(self):
        payload ={
            "citizenship":"KEN",
            "idNumber":"23224868",
            "passportNumber":"AK1577133",
            "gender": "M",
            "surname":"Nyamai",
            "firstName":"Stephen",
            "otherName": "Biko",
            "dateOfBirthFromPassport":"1984-02-19",
            "placeOfBirth":"NAIROBI, KEN",
            "dateOfIssue":"2024-06-08",
            "dateOfExpiry":"2034-06-07",
        }
        verifity_test(tester= self,
                      url= self.URL,
                      payload=payload)

if __name__ == '__main__':
    unittest.main()