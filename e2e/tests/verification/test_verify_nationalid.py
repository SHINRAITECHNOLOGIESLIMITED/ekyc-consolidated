import json
import unittest
from pprint import pprint

import requests

from e2e.tests.config import *
from e2e.tests.verification.verify_test_util import verifity_test
class TestNationalIDDocumentVerification(unittest.TestCase):
    URL =f"{APIGW_URL}/government/nationalid"
    def test_idnumber_23667272(self):
        payload ={"serialNumber":"242865407", 
            "idNumber":"23667272", 
            "fullNames":"JANE WAIRIMU MAINA", 
            "dateOfBirth":"1985-01-01", 
            "dateOfIssue":"2016-10-28", 
            "gender":"Female", 
            "districtOfBirth":"THIKA WEST"            
        }
        verifity_test(tester= self, 
                      url= self.URL,
                      payload=payload)
    def test_idnumber_32140017(self):
        payload ={"serialNumber":"702945559", 
            "idNumber":"32140017", 
            "fullNames":"EFFIE NJOKI NYAMBURA", 
            "dateOfBirth":"1994-19-12", 
            "dateOfIssue":"2021-09-06", 
            "gender":"Female", 
            "districtOfBirth":"KIAMBU"            
        }
        verifity_test(tester= self, 
                      url= self.URL,
                      payload=payload)
    
    def test_idnumber_36296352(self):
        payload ={"serialNumber":"242772451", 
            "idNumber":"36296352", 
            "fullNames":"JOEL MUUO", 
            "dateOfBirth":"1998-08-30", 
            "dateOfIssue":"2017-03-31", 
            "gender":"Male", 
            "districtOfBirth":"KIBWEZI"            
        }
        verifity_test(tester= self, 
                      url= self.URL,
                      payload=payload)
    
    def test_idnumber_23224868(self):
        payload ={"serialNumber":"217990310", 
            "idNumber":"23224868", 
            "fullNames":"STEPHEN BIKO NYAMAI", 
            "dateOfBirth":"1984-02-19", 
            "dateOfIssue":"2003-04-01", 
            "gender":"Male", 
            "districtOfBirth":"KIBWEZI"            
        }
        verifity_test(tester= self, 
                      url= self.URL,
                      payload=payload)

if __name__ == '__main__':
    unittest.main()