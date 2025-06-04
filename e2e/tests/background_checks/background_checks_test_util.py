import json
from pprint import pprint
from e2e.tests.config import *
import sys

def background_check_test(tester,payload,url):
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
    pprint(response.json(), stream=sys.stderr)
    