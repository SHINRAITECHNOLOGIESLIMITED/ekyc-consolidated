import unittest
from pprint import pprint
import json

from e2e.tests.config import *
class TestPassportDocumentVerification(unittest.TestCase):
    def test_passportnumber_AK1515374(self):
        payload ={"documentType":"P",
            "countryCode":"KEN",
            "passportNumber":"AK1515374",
            "idNumber":"32140017",
            "personalNumber":"741116",
            "surname":"NYAMBURA",
            "gender": "F",
            "givenNames":"EFFIE NJOKI",
            "dateOfBirth":"1994-12-19",
            "placeOfBirth":"KIAMBU, KEN",
            "dateOfIssue":"2024-05-06",
            "dateOfExpiry":"2034-05-05",
            "nationality":"KENYAN",
            "issuingAuthority":"GOVERNMENT OF KENYA",
        }
        response = post_with_auth(f"{APIGW_URL}/government/passport", json= json.dumps(payload))
        # Check if the response status code is 200 (OK)
        if response.status_code != 200:
            print(response.text)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)


    def test_passportnumber_AK1370344(self):
        payload ={"documentType":"P",
            "countryCode":"KEN",
            "idNumber":"",
            "passportNumber":"AK1370344",
            "personalNumber":"1944445",
            "gender": "M",
            "surname":"Munyao",
            "givenNames":"Timothy",
            "dateOfBirth":"1988-01-13",
            "placeOfBirth":"NAIROBI, KEN",
            "dateOfIssue":"2023-07-20",
            "dateOfExpiry":"2033-07-19",
            "nationality":"KENYAN",
            "issuingAuthority":"GOVERNMENT OF KENYA",
        }
        response = post_with_auth(f"{APIGW_URL}/government/passport", json= json.dumps(payload))
        # Check if the response status code is 200 (OK)
        if response.status_code != 200:
            print(response.text)
        self.assertEqual(response.status_code, 200)

        #print the validation results
        results = response.json()
        pprint(results)


    ## --- Test with debug --- ##
    
    # def test_debug_passport_api_response(self):
    #     """
    #     Test to debug the passport API response by printing both the request payload
    #     and the raw API response to identify payload issues.
    #     """
    #     payload ={"documentType":"P",
    #         "countryCode":"KEN",
    #         "passportNumber":"AK1515374",
    #         "idNumber":"32140017",
    #         "personalNumber":"741116",
    #         "surname":"NYAMBURA",
    #         "gender": "F",
    #         "givenNames":"EFFIE NJOKI",
    #         "dateOfBirth":"1994-12-19",
    #         "placeOfBirth":"KIAMBU, KEN",
    #         "dateOfIssue":"2024-05-06",
    #         "dateOfExpiry":"2034-05-05",
    #         "nationality":"KENYAN",
    #         "issuingAuthority":"GOVERNMENT OF KENYA",
    #     }
    #     response = post_with_auth(f"{APIGW_URL}/government/passport", json=payload)

    #     print("\n=== RAW API RESPONSE ===")
    #     print(f"Status Code: {response.status_code}")
    #     print("Headers:")
    #     pprint(dict(response.headers))
    #     print("\nResponse Body:")

    #     try:
    #         response_json = response.json()
    #         pprint(response_json)
    #     except json.JSONDecodeError:
    #         print(response.text)

    #     self.assertTrue(True, "This test is for debugging purposes only")


if __name__ == '__main__':
    unittest.main()