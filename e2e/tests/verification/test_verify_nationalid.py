import unittest

from e2e.tests.config import *
from e2e.tests.verification.verify_test_util import verifity_200_test
class TestNationalIDDocumentVerification(unittest.TestCase):
    URL =f"{APIGW_URL}/government/nationalid"
    def test_23667272_JANE_SAMPLE(self):
        payload ={"serialNumber":"217934147",
            "idNumber":"23667272",
            "fullNames":"JANE WAIRIMU MAINA",
            # "dateOfBirth":"1985-01-01", #IPRS and Supplied sample have a mismatch
            # "dateOfIssue":"2016-10-28",  #IPRS and Supplied sample have a mismatch
            "gender":"F",
            # "districtOfBirth":"THIKA WEST"  #IPRS and Supplied sample have a mismatch
        }
        verifity_200_test(tester= self,
                      url= self.URL,
                      payload=payload)
    def test_32140017_EFFIE(self):
        payload ={"serialNumber":"702945559",
            "idNumber":"32140017",
            "fullNames":"EFFIE NJOKI NYAMBURA",
            "dateOfBirth":"12-19-1994",
            "dateOfIssue":"2021-09-06",
            "gender":"F",
            "districtOfBirth":"KIAMBU\nDISTRICT - KIAMBU\n"
        }
        verifity_200_test(tester= self,
                      url= self.URL,
                      payload=payload)

    def test_36296352_JOEL(self):
        payload ={"serialNumber":"244772451",
            "idNumber":"36296352",
            "fullNames":"JOEL MUUO",
            "dateOfBirth":"1998-08-30",
            "dateOfIssue":"2017-03-31",
            "gender":"M",
            "districtOfBirth":"KIBWEZI\nDISTRICT - KIBWEZI\n"
        }
        verifity_200_test(tester= self,
                      url= self.URL,
                      payload=payload)

    def test_23224868_STEPEHN(self):
        payload ={"serialNumber":"229769449",
            "idNumber":"23224868",
            "fullNames":"STEPHEN BIKO NYAMAI",
            "dateOfBirth":"1984-02-19",
            "dateOfIssue":"2011-10-24",
            "gender":"M",
            "districtOfBirth":"NAIROBI\nDISTRICT - STAREHE\n\n"
        }
        verifity_200_test(tester= self,
                      url= self.URL,
                      payload=payload)

if __name__ == '__main__':
    unittest.main()