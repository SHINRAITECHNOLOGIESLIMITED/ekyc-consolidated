import unittest
from pprint import pprint

import requests

from e2e.tests.config import *
class TestPassportDocumentVerification(unittest.TestCase):
    def test_passportnumber_DK9038(self):
        payload ={"documentType":"P", 
            "countryCode":"KEN", 
            "passportNumber":"DK9038", 
            "personalNumber":"1736740", 
            "surname":"KAJIMBA", 
            "givenNames":"GEORGE HUMPHREY", 
            "gender":"M", 
            "dateOfBirth":"18 May 1987", 
            "placeOfBirth":"MIGORI, Ken", 
            "dateOfIssue":"04 Aug 2020", 
            "dateOfExpiry":"03 aug 2030", 
            "nationality":"KENYAN", 
            "issuingAuthority":"GOVERNMENT OF KENYA",  
        }
        response = requests.post(f"{APIGW_URL}/documents/passport", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    def test_passportnumber_AK1515374(self):
        payload ={"documentType":"P", 
            "countryCode":"KEN", 
            "passportNumber":"AK1515374", 
            "personalNumber":"741116", 
            "surname":"NYAMBURA", 
            "givenNames":"EFFIE NJOKI", 
            "gender":"F", 
            "dateOfBirth":"1994-12-19 00:00:00", 
            "placeOfBirth":"KIAMBU, KEN", 
            "dateOfIssue":"2024-05-06 00:00:00", 
            "dateOfExpiry":"2034-05-05 00:00:00", 
            "nationality":"KENYAN", 
            "issuingAuthority":"GOVERNMENT OF KENYA",  
        }
        response = requests.post(f"{APIGW_URL}/documents/passport", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    def test_passportnumber_AK1370344(self):
        payload ={"documentType":"P", 
            "countryCode":"KEN", 
            "passportNumber":"AK1370344", 
            "personalNumber":"1944445", 
            "surname":"Munyao", 
            "givenNames":"Timothy", 
            "gender":"M", 
            "dateOfBirth":"13 JAN 1988", 
            "placeOfBirth":"NAIROBI, KEN", 
            "dateOfIssue":"20 Jul 2023", 
            "dateOfExpiry":"19 Jul 2033", 
            "nationality":"KENYAN", 
            "issuingAuthority":"GOVERNMENT OF KENYA",  
        }
        response = requests.post(f"{APIGW_URL}/documents/passport", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    

if __name__ == '__main__':
    unittest.main()