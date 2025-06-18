import unittest
from e2e.tests.config import *
from e2e.tests.registration.register_test_util import register_200_test

class TestCustomerRegistration(unittest.TestCase):
    URL=f"{APIGW_URL}/customer-registration"
    def test_customer_joel(self):
        payload = {
            "name": "JOEL MUUO",
            "pinNumber":"A011797599Y",
            "idNumber": "36296352",
            "gender": "Male",
            "dateOfBirth": "1998-08-30",
            "passportPhotoUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
            "nationalIdCardUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
            "kraPinCardUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KRA_PIN_CERTIFICATE-002samplekra.jpg"
        }
        register_200_test(tester= self, 
                      url= self.URL,
                      payload=payload)

    def test_customer_roy(self):
        payload = {
            "agentType": "Individual",
            "name": "Roy Githara",
            "pinNumber": "A015539643F",
            "idNumber": "38750033",
            "gender": "Male",
            "dateOfBirth": "1985-05-05",
            "passportPhotoUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
            "nationalIdCardUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
            "kraPinCardUrl": ""
        }
        register_200_test(tester= self, 
                      url= self.URL,
                      payload=payload)

    def test_customer_pato(self):
        payload = {
            "agentType": "Individual",
            "name": "Patrick odhiambo",
            "pinNumber":"A005394549Z",
            "idNumber": "24106259",
            "gender": "Male",
            "passportPhotoUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
            "nationalIdCardUrl": "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
            "dateOfBirth": "1985-05-05",
            "kraPinCardUrl": ""
        }
        register_200_test(tester= self, 
                      url= self.URL,
                      payload=payload)

if __name__ == '__main__':
    unittest.main()

