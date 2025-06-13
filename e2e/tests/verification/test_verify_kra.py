import unittest

from e2e.tests.config import *
from e2e.tests.verification.verify_test_util import verifity_200_test
class TestKRAPinCertificateDocumentVerification(unittest.TestCase):
    URL = f"{APIGW_URL}/government/kra"
    def test_A011797599Y_JOEL(self):
        payload ={
            "idNumber":"36296352",
            "pin":"A011797599Y",
            "taxPayerName":"UUO19 TEST OEL01",
        }
        verifity_200_test(tester= self,
                      url= self.URL,
                      payload=payload)

    def test_A008279496S_EFFIE(self):
        payload ={
            "idNumber":"32140017",
            "pin":"A008279496S",
            "taxPayerName":"YAMBU09 TEST FFIE05",
        }
        verifity_200_test(tester= self,
                      url= self.URL,
                      payload=payload)

    def test_A005394549Z_PATRICK(self):
        payload ={
            "idNumber":"24106259",
            "pin":"A005394549Z",
            "taxPayerName":"DHIAM20 TEST ATRIC10",
        }
        verifity_200_test(tester= self,
                      url= self.URL,
                      payload=payload)


if __name__ == '__main__':
    unittest.main()