import json
import unittest
from pprint import pprint

from e2e.tests.config import *

class TestCustomerRegistration(unittest.TestCase):

    def test_valid_customer_registration_effie(self):
        payload = {
            "name": "Effie Njoki",
            "pinNumber":"A008279496S",
            "idNumber": "32140017",
            "gender": "Female",
            "dateOfBirth": "1994-12-19",
            "passportPhotoUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
            "nationalIdOrPassportUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID.pdf",
            "kraPinCardUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KRA_PIN_CERTIFICATE-002samplekra.jpg"
        }

        response = post_with_auth(f"{APIGW_URL}/customer-registration", json=payload)

        print("\n=== RAW API RESPONSE ===")
        print(f"Status Code: {response.status_code}")
        print("Headers:")
        pprint(dict(response.headers))
        print("\nResponse Body:")

        try:
            response_json = response.json()
            pprint(response_json)
        except json.JSONDecodeError:
            print(response.text)

        # self.assertTrue(True)
        self.assertEqual(response.status_code, 200)

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

        response = post_with_auth(f"{APIGW_URL}/agent-registration", json=payload)

        print("\n=== RAW API RESPONSE ===")
        print(f"Status Code: {response.status_code}")
        print("Headers:")
        pprint(dict(response.headers))
        print("\nResponse Body:")

        try:
            response_json = response.json()
            pprint(response_json)
        except json.JSONDecodeError:
            print(response.text)

        # self.assertTrue(True)
        self.assertEqual(response.status_code, 200)

    def test_valid_agent_registration_pato(self):
        payload = {
            "agentType": "Individual",
            "name": "Patrick odhiambo",
            "pin":"A005394549Z",
            "idNumber": "24106259",
            "passportPhotoUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/PHOTO-2025-05-22-16-00-57.jpg",
            "nationalIdCardUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/KENYAN_NATIONAL_ID-9f0ea801f683f6c8314c9d7ad0e7a93ed01b9693.jpg",
            "companyCertificateUrl": "https://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq.s3.eu-west-1.amazonaws.com/uploaded_kyc_docs/8205e4c4-80a1-7006-b6ef-6aa6c57e84ec/effie-upload-test/CERTIFICATE_OF_INCORPORATION-003Sample.jpg",
            "dateOfBirth": "1985-05-05",
            "businessNumber": "BN987654321"
        }

        response = post_with_auth(f"{APIGW_URL}/agent-registration", json=payload)

        print("\n=== RAW API RESPONSE ===")
        print(f"Status Code: {response.status_code}")
        print("Headers:")
        pprint(dict(response.headers))
        print("\nResponse Body:")

        try:
            response_json = response.json()
            pprint(response_json)
        except json.JSONDecodeError:
            print(response.text)

        # self.assertTrue(True)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()

