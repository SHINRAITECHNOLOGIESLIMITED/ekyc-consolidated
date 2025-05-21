import unittest
import requests

from e2e.tests.config import *
class TestNationalIDDocumentValidation(unittest.TestCase):
    def test_idnumber_23667272(self):
        payload ={"uploadedDocumentUrl": f"{DOCUMENTS_URL}/NationalID/idnumber_23667272.pdf",
            "serialNumber":"242865407", 
            "idNumber":"23667272", 
            "fullNames":"JANE WAIRIMU MAINA", 
            "dateOfBirth":"01-01-1985", 
            "dateOfIssue":"28-10-2016", 
            "gender":"FEMALE", 
            "districtOfBirth":"THIKA WEST", 
            "placeOfIssue":"NGENDA",  
        }
        response = requests.post(f"{APIGW_URL}/documents/nationalid", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    def test_idnumber_32140017(self):
        payload ={"uploadedDocumentUrl": f"{DOCUMENTS_URL}/NationalID/idnumber_32140017.pdf",
            "serialNumber":"702945559", 
            "idNumber":"32140017", 
            "fullNames":"EFFIE NJOKI NYAMBURA", 
            "dateOfBirth":"12-19-1994", 
            "dateOfIssue":"2021-09-06 00:00:00", 
            "gender":"FEMALE", 
            "districtOfBirth":"KIAMBU", 
            "placeOfIssue":"KIAMBU",  
        }
        response = requests.post(f"{APIGW_URL}/documents/nationalid", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    def test_idnumber_36296352(self):
        payload ={"uploadedDocumentUrl": f"{DOCUMENTS_URL}/NationalID/idnumber_36296352.pdf",
            "serialNumber":"242772451", 
            "idNumber":"36296352", 
            "fullNames":"JOEL MUUO", 
            "dateOfBirth":"8 -30-1998", 
            "dateOfIssue":"3-31-2017", 
            "gender":"MALE", 
            "districtOfBirth":"KIBWEZI", 
            "placeOfIssue":"KIBWEZI",  
        }
        response = requests.post(f"{APIGW_URL}/documents/nationalid", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    
    def test_idnumber_23224868(self):
        payload ={"uploadedDocumentUrl": f"{DOCUMENTS_URL}/NationalID/idnumber_23224868.pdf",
            "serialNumber":"217990310", 
            "idNumber":"23224868", 
            "fullNames":"STEPHEN BIKO NYAMAI", 
            "dateOfBirth":"19-02-1984", 
            "dateOfIssue":"01-04-2003", 
            "gender":"MALE", 
            "districtOfBirth":"KIBWEZI", 
            "placeOfIssue":"MAKADARA",  
        }
        response = requests.post(f"{APIGW_URL}/documents/nationalid", json=payload, headers=headers)
        # Check if the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)
    

if __name__ == '__main__':
    unittest.main()