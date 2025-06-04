
import unittest

from e2e.tests.background_checks.background_checks_test_util import background_check_test
from e2e.tests.config import *

class TestBackgroundCheck(unittest.TestCase):
    URL=f"{APIGW_URL}/backgroundcheck"
    def test_valid_background_check_effie(self):
        payload = {
            "firstName": "Effie",
            "middleName": "Njoki",
            "lastName": "Nyambura",
            "gender": "Female",
            "dateOfBirth": "1994-12-19",
            "nationalIdentificationNumber": "32140017"
        }

        background_check_test(tester= self, 
                      url= self.URL,
                      payload=payload)

        

    def test_valid_background_check_joseph(self):
        payload = {
            "firstName": "Joseph",
            "middleName": "",
            "lastName": "karanja",
            "gender": "Male",
            "dateOfBirth": "1992-01-01",
            "nationalIdentificationNumber": ""
        }

        background_check_test(tester= self, 
                      url= self.URL,
                      payload=payload)
        

    def test_valid_background_check_timothy(self):
        payload = {
            "firstName": "Timothy",
            "middleName": "",
            "lastName": "Munyao",
            "gender": "Male",
            "dateOfBirth": "1988-01-13",
            "nationalIdentificationNumber": "26465570"
        }
        background_check_test(tester= self, 
                      url= self.URL,
                      payload=payload)

if __name__ == '__main__':
    unittest.main()
