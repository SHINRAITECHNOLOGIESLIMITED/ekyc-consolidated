import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests
import os

# API Gateway URLs for jubilee-ekyc-dev stack (pasha-eu account)
# Stage endpoint auto-approves requests for testing (no auth required)
APIGW_URL = "https://6corkstod4.execute-api.eu-west-1.amazonaws.com/Stage"
DOCUMENTS_URL = "s3://maisha-verification-dev-686255958278/uploaded_kyc_docs/"

PROFILE = "pasha-eu"
REGION = "eu-west-1"
SERVICE = "execute-api"


# Create a session using your AWS credentials
session = boto3.Session(profile_name=PROFILE)
credentials = session.get_credentials()

# Verify credentials are available
if not credentials:
    raise ValueError(f"No credentials found for profile: {PROFILE}")

def get_auth_headers(method, url, body=None):
    """Generate authentication headers for API Gateway Stage endpoint"""
    # Stage endpoint auto-approves requests with any Bearer token
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-token-for-stage"
    }

# Override the standard requests.post method to include authentication
def post_with_auth(url, json=None):
    import json as json_module
    body = json_module.dumps(json) if json else None
    auth_headers = get_auth_headers('POST', url, body=body)
    return requests.post(url, json=json, headers=auth_headers, verify=False)