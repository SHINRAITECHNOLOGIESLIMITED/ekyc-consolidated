import unittest
from e2e.tests.config import *
from e2e.tests.registration.register_test_util import register_200_test

class TestCustomerRegistration(unittest.TestCase):
    URL=f"{APIGW_URL}/customer-registration"
    def test_customer_effie(self):
        payload = {
            "name": "EFFIE NJOKI NYAMBURA",
            "pinNumber":"A008279496S",
            "idNumber": "32140017",
            "gender": "Female",
            "dateOfBirth": "1994-12-19",
            "passportPhotoUrl": "s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/effie1.jpg",
            "nationalIdCardUrl": "s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/effies-ID.jpg",
            "kraPinCardUrl": "s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/effies-KRA.jpg"
        }
        register_200_test(tester= self,
                      url= self.URL,
                      payload=payload)

if __name__ == '__main__':
    unittest.main()

