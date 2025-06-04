import json
import unittest
from pprint import pprint

from e2e.tests.config import *

class TestBackgroundCheck(unittest.TestCase):
    def test_valid_background_check_effie(self):
        payload = {
            "firstName": "Effie",
            "middleName": "Njoki",
            "lastName": "Nyambura",
            "gender": "Female",
            "dateOfBirth": "1994-12-19",
            "nationalIdentificationNumber": "32140017"
        }

        response = post_with_auth(f"{APIGW_URL}/backgroundcheck", json=payload)


        if response.status_code != 200:
            print("ERROR:", response.text)

        self.assertEqual(response.status_code, 200)

        results = response.json()
        pprint(results)

    def test_valid_background_check_joseph(self):
        payload = {
            "firstName": "Joseph",
            "middleName": "",
            "lastName": "karanja",
            "gender": "Male",
            "dateOfBirth": "1992-01-01",
            "nationalIdentificationNumber": ""
        }

        response = post_with_auth(f"{APIGW_URL}/backgroundcheck", json=payload)


        if response.status_code != 200:
            print("ERROR:", response.text)

        self.assertEqual(response.status_code, 200)

        results = response.json()
        pprint(results)

    def test_valid_background_check_timothy(self):
        payload = {
            "firstName": "Tomothy",
            "middleName": "",
            "lastName": "Munyao",
            "gender": "Male",
            "dateOfBirth": "1988-01-13",
            "nationalIdentificationNumber": "26465570"
        }

        response = post_with_auth(f"{APIGW_URL}/backgroundcheck", json=payload)


        if response.status_code != 200:
            print("ERROR:", response.text)

        self.assertEqual(response.status_code, 200)

        results = response.json()
        pprint(results)

if __name__ == '__main__':
    unittest.main()


# print("\n=== RAW API RESPONSE ===")
        # print(f"Status Code: {response.status_code}")
        # print("Headers:")
        # pprint(dict(response.headers))
        # print("\nResponse Body:")

        # try:
        #     response_json = response.json()
        #     pprint(response_json)
        # except json.JSONDecodeError:
        #     print(response.text)

        # self.assertEqual(response.status_code, 200)