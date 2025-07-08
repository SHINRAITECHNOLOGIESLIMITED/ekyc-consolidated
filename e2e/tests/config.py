import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests
import os

# Set certificate bundle for SSL verification
os.environ['AWS_CA_BUNDLE'] = '/usr/local/etc/ca-certificates/cert.pem'
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

APIGW_URL = "https://k4m88497ad.execute-api.eu-west-1.amazonaws.com/Prod"
# APIGW_URL = "https://uppjkm7ere.execute-api.eu-west-1.amazonaws.com/Prod"
DOCUMENTS_URL = "s3://amplify-d3fnn95gtf6qnl-ma-kycdocumentsbucketa4bf11-sh8x1somscou/uploaded_kyc_docs/"

PROFILE = "shinrai.devpost"
REGION = "eu-west-1"
SERVICE = "execute-api"


# Create a session using your AWS credentials
session = boto3.Session(profile_name=PROFILE)
credentials = session.get_credentials()

# Verify credentials are available
if not credentials:
    raise ValueError(f"No credentials found for profile: {PROFILE}")

def get_auth_headers(method, url, body=None):
    """Generate SigV4 authentication headers for API Gateway"""
    request = AWSRequest(method=method, url=url, data=body, headers={"Content-Type": "application/json"})
    SigV4Auth(credentials, SERVICE, REGION).add_auth(request)
    return dict(request.headers)

# Override the standard requests.post method to include SigV4 authentication
def post_with_auth(url, json=None):
    import json as json_module
    body = json_module.dumps(json) if json else None
    auth_headers = get_auth_headers('POST', url, body=body)
    return requests.post(url, json=json, headers=auth_headers, verify=False)