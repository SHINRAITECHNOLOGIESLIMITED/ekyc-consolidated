import unittest
from e2e.tests.config import *
from e2e.tests.validation.validate_test_util import validate_test
class TestKRAPinCertificateDocumentValidation(unittest.TestCase):
    URL= f"{APIGW_URL}/document/krapincertificate"
    def test_A003388522V_JACKSON(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/SampleKRAPIN.pdf",
            "certificateDate":"2014-10-14",
            "pin":"A003388522V",
            "taxPayerName":"Jackson Gitonga Mwangi",
            "emailAddress":"jackmwangi02@gmail.com",
        }
        validate_test(tester= self,
                      url= self.URL,
                      payload=payload)

if __name__ == '__main__':
    unittest.main()