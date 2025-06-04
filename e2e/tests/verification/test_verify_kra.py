import unittest

from e2e.tests.config import *
from e2e.tests.verification.verify_test_util import verifity_test
class TestKRAPinCertificateDocumentVerification(unittest.TestCase):
    URL = f"{APIGW_URL}/government/kra"
    def test_pin_A003388522V(self):
        payload ={
            "idNumber":"32140017",
            "pin":"A003388522V",
            "taxPayerName":"Jackson Gitonga Mwangi",
        }
        verifity_test(tester= self, 
                      url= self.URL,
                      payload=payload)

    def test_pin_A011797599Y(self):
        payload ={
            "idNumber":"36296352",
            "pin":"A011797599Y",
            "taxPayerName":"JOEL MUUO",
        }
        verifity_test(tester= self, 
                      url= self.URL,
                      payload=payload)
        
    def test_pin_A008279496S(self):
        payload ={
            "idNumber":"32140017",
            "pin":"A008279496S",
            "taxPayerName":"EFFIE NJOKI NYAMBURA",
        }
        verifity_test(tester= self, 
                      url= self.URL,
                      payload=payload)

    def test_pin_A005394549Z(self):
        payload ={
            "idNumber":"24106259",
            "pin":"A005394549Z",
            "taxPayerName":"PATRICK OMONDI ODHIAMBO ",
        }
        verifity_test(tester= self, 
                      url= self.URL,
                      payload=payload)


if __name__ == '__main__':
    unittest.main()