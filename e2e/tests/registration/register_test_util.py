import json
from pprint import pprint
import sys
from e2e.tests.config import *

def register_test(tester,payload,url):
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
    tester.assertTrue("executionArn" in results)
    tester.assertTrue("message" in results)
    tester.assertTrue("registration accepted" in results["message"])
    