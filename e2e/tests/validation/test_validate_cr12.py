
import unittest
from e2e.tests.config import *
from e2e.tests.validation.validate_test_util import validate_test


class TestCertificateOfIncorporationDocumentValidation(unittest.TestCase):
    URL = f"{APIGW_URL}/document/cr12"
    def test_businessnumber_PVTRXUMYGVQ(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/CERTIFICATE_OF_INCORPORATION-003Sample.jpg",
            "businessNumber":"PVT-RXUMYGVQ", 
            "businessName":"DETALI INSURANCE AGENCY LIMITED", 
            "dateOfIncorporation":"2024-04-09", 
            "businessType":"Private Limited Company",  
        }
        validate_test(tester= self, 
                      url= self.URL,
                      payload=payload)
if __name__ == '__main__':
    unittest.main()