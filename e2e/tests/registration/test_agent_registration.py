
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
            "passportPhotoUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/customer-registration/passportPhotoUrl/9d0556685ab002c09376c8b5832d8717123dd686.jpg",
            "nationalIdCardUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/document/nationalid/uploadedDocumentUrl/e677499a43d2644ea635393c504b6e0027cc6fb7.png",
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
            "passportPhotoUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
            "nationalIdCardUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
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
            "passportPhotoUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/b2d5f444-7081-70b4-d0ad-0fcbb5320bd3/customer-registration/passportPhotoUrl/fecfeb7833b8284b9e3979fa36dc1f8759d64127.jpg",
            "nationalIdCardUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID.pdf",
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
            "companyCertificateUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/c2a5e464-30b1-70e8-eeb0-8c196da88147/agent-registration/companyCertificateUrl/9bcb0e79dcd42f130f9b5d67d6ab2b0749a9aefb.pdf",
            "businessNumber": "PVT-RXUMYGVQ"
        }
        register_200_test(tester=self,
                          url=self.URL,
                          payload=payload)


if __name__ == '__main__':
    unittest.main()
