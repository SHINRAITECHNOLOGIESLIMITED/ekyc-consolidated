import unittest
from e2e.tests.config import *
from e2e.tests.validation.validate_test_util import validate_test
class TestKRAPinCertificateDocumentValidation(unittest.TestCase):
    URL= f"{APIGW_URL}/document/krapincertificate"
    def test_A003388522V_JACKSON(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KRA_PIN_CERTIFICATE-002samplekra.jpg",
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