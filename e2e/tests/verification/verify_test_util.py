import json
from pprint import pprint
import sys
from e2e.tests.config import *

def verifity_test(tester,payload,url):
    response = post_with_auth(url, json= json.dumps(payload))
    if response.status_code not in [200, 201]:
        print("\nResponse Body:",file=sys.stderr)
        try:
            response_json = response.json()
            pprint(response_json,stream=sys.stderr)

        except json.JSONDecodeError:
            print(response.text,file=sys.stderr)
        tester.fail(f"Request failed with status code {response.status_code}")
    
    
    results = response.json()
    tester.assertTrue("results" in results)
    results = results["results"]
    
    unmatched = []
    not_found = []
    for field_name, match_result in results.items():
        if match_result["status"] == "Not Matched":
            unmatched.append(field_name)
        if match_result["status"] == "Not Found":
            not_found.append(field_name)
    if unmatched or not_found:
        if unmatched:
            print("Not Matched ",  ",".join(unmatched), ")",file=sys.stderr)
        if not_found:
            print("Not Found ",  ",".join(not_found), ")",file=sys.stderr)
        tester.fail(f"Issues with Fields")