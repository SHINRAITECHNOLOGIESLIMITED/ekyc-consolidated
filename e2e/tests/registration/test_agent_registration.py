
import unittest
from e2e.tests.config import *
from e2e.tests.registration.register_test_util import register_200_test


class TestAgentRegistration(unittest.TestCase):
    URL = f"{APIGW_URL}/agent-registration"

    def test_INDIVIDUAL_EFFIE(self):
        payload = {
            "agentType": "Individual",
            "name": "Effie Njoki",
            "pinNumber": "A008279496S",
            "idNumber": "32140017",
            "gender": "Female",
            "passportPhotoUrl": "s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/effie1.jpg",
            "nationalIdCardUrl": "s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/effies-ID.jpg",
            "dateOfBirth": "1994-12-19"
        }
        register_200_test(tester=self,
                          url=self.URL,
                          payload=payload)

    def test_INDIVIDUAL_Peninah(self):
        payload = {
            "agentType": "Individual",
            "name": "Peninah Kabura Muchiri",
            "pinNumber": "A015539643F",
            "idNumber": "27681984",
            "gender": "Female",
            "passportPhotoUrl": "s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/pesh.jpg",
            "nationalIdCardUrl": "s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/PHOTO-2025-05-22-16-00-57.jpg",
            "dateOfBirth": "1990-05-26",
        }
        register_200_test(tester=self,
                          url=self.URL,
                          payload=payload)

    def test_INDIVIDUAL_24106259_Timothy(self):
        payload = {
            "agentType": "Individual",
            "name": "Timothy Munyao",
            "pinNumber": "A005394549Z",
            "idNumber": "26465570",
            "gender": "Male",
            "passportPhotoUrl": "s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/Tim.jpg",
            "nationalIdCardUrl": "s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/KENYAN_NATIONAL_ID.pdf",
            "dateOfBirth": "1988-01-13",
        }
        register_200_test(tester=self,
                          url=self.URL,
                          payload=payload)

    def test_COMPANY_PVTRXUMYGVQ_DETALI(self):
        payload = {
            "agentType": "Business",
            "name": "DETALI INSURANCE AGENCY LIMITED",
            "pinNumber": "PVT-RXUMYGVQ",
            "companyCertificateUrl": "s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/CR12-003Sample.jpg",
            "businessNumber": "PVT-RXUMYGVQ"
        }
        register_200_test(tester=self,
                          url=self.URL,
                          payload=payload)


if __name__ == '__main__':
    unittest.main()
