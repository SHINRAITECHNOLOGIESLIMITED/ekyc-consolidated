import json
from pprint import pprint
import sys
from e2e.tests.config import *

def verifity_test(tester,payload,url):
    response = post_with_auth(url, json= json.dumps(payload))
    if response.status_code != 200:
        print("\nResponse Body:",file=sys.stderr)
        try:
            response_json = response.json()
            pprint(response_json,stream=sys.stderr)

        except json.JSONDecodeError:
            print(response.text,file=sys.stderr)
        tester.fail(f"Request failed with status code {response.status_code}")
    tester.assertEqual(response.status_code, 200)
    results = response.json()
    tester.assertTrue("results" in results)
    results = results["results"]
    for field_name, match_result in results.items():
        if match_result["status"] in ["Not Matched", "Not Found"]:
            print("\nFull Response (on failure):", file=sys.stderr)
            pprint(response.json(), stream=sys.stderr)
            if match_result["status"] == "Not Matched":
                tester.fail(f"Field {field_name} did not match {match_result['details']}")
            elif match_result["status"] == "Not Found":
                tester.fail(f"Field {field_name} was not found")

    # for field_name,match_result in results.items():
    #     if match_result["status"] == "Not Matched":
    #         tester.fail(f"Field {field_name} did not match {match_result['details']}")
    #     if match_result["status"] == "Not Found":
    #         tester.fail(f"Field {field_name} was not found")