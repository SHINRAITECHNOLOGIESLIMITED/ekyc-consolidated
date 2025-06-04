
import unittest
from e2e.tests.config import *
from e2e.tests.registration.register_test_util import register_test

class TestAgentRegistration(unittest.TestCase):
    URL = f"{APIGW_URL}/agent-registration"
    def test_valid_agent_registration_njoki(self):
        payload = {
            "agentType": "Individual",
            "name": "Effie Njoki",
            "pinNumber":"A008279496S",
            "idNumber": "32140017",
            "passportPhotoUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
            "nationalIdCardUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
            "companyCertificateUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/CERTIFICATE_OF_INCORPORATION-003Sample.jpg",
            "dateOfBirth": "1994-12-19",
            "businessNumber": "BN987654321"
        }
        register_test(tester= self, 
                      url= self.URL,
                      payload=payload)

    def test_valid_agent_registration_roy(self):
        payload = {
            "agentType": "Individual",
            "name": "Roy Githara",
            "pinNumber": "A015539643F",
            "idNumber": "38750033",
            "passportPhotoUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
            "nationalIdCardUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
            "companyCertificateUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/CERTIFICATE_OF_INCORPORATION-003Sample.jpg",
            "dateOfBirth": "2001-09-04",
            "businessNumber": "BN987654321"
        }
        register_test(tester= self, 
                      url= self.URL,
                      payload=payload)

    def test_valid_agent_registration_pato(self):
        payload = {
            "agentType": "Individual",
            "name": "Patrick odhiambo",
            "pin":"A005394549Z",
            "idNumber": "24106259",
            "passportPhotoUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
            "nationalIdCardUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
            "companyCertificateUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/CERTIFICATE_OF_INCORPORATION-003Sample.jpg",
            "dateOfBirth": "2001-09-04",
            "businessNumber": "BN987654321"
        }
        register_test(tester= self, 
                      url= self.URL,
                      payload=payload)

if __name__ == '__main__':
    unittest.main()
