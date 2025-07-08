
import unittest
from e2e.tests.config import *
from e2e.tests.validation.validate_test_util import validate_test


class TestCertificateOfIncorporationDocumentValidation(unittest.TestCase):
    URL = f"{APIGW_URL}/document/cr12"
    def test_PVTRXUMYGVQ_DETALI(self):
        payload ={"uploadedDocumentUrl": f"s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/CR12-003Sample.jpg",
            "businessNumber":"PVT-RXUMYGVQ",
            "businessName":"DETALI INSURANCE AGENCY LIMITED",
        }
        validate_test(tester= self,
                      url= self.URL,
                      payload=payload)
if __name__ == '__main__':
    unittest.main()