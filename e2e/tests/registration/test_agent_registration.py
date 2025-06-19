
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
            "passportPhotoUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
            "nationalIdCardUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
            "dateOfBirth": "1994-12-19"
        }
        register_200_test(tester=self,
                          url=self.URL,
                          payload=payload)

    def test_INDIVIDUAL_ROY(self):
        payload = {
            "agentType": "Individual",
            "name": "Roy Githara",
            "pinNumber": "A015539643F",
            "idNumber": "38750033",
            "gender": "Male",
            "passportPhotoUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
            "nationalIdCardUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
            "dateOfBirth": "2001-09-04",
        }
        register_200_test(tester=self,
                          url=self.URL,
                          payload=payload)

    def test_INDIVIDUAL_24106259_PATRICK(self):
        payload = {
            "agentType": "Individual",
            "name": "Patrick odhiambo",
            "pinNumber": "A005394549Z",
            "idNumber": "24106259",
            "gender": "Male",
            "passportPhotoUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
            "nationalIdCardUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
            "dateOfBirth": "2001-09-04",
        }
        register_200_test(tester=self,
                          url=self.URL,
                          payload=payload)

    def test_COMPANY_BN987654321_ABC(self):
        payload = {
            "agentType": "Business",
            "name": "ABC Incoporated",
            "pinNumber": "B015539643F",
            "companyCertificateUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/CERTIFICATE_OF_INCORPORATION-003Sample.jpg",
            "businessNumber": "BN987654321"
        }
        register_200_test(tester=self,
                          url=self.URL,
                          payload=payload)

    def test_COMPANY_PVTRXUMYGVQ_DETALI(self):
        payload = {
            "agentType": "Business",
            "name": "DETALI INSURANCE AGENCY LIMITED",
            "pinNumber": "PVT-RXUMYGVQ",
            "companyCertificateUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/CERTIFICATE_OF_INCORPORATION-003Sample.jpg",
            "businessNumber": "PVT-RXUMYGVQ"
        }
        register_200_test(tester=self,
                          url=self.URL,
                          payload=payload)


if __name__ == '__main__':
    unittest.main()
