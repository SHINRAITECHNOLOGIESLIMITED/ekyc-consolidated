import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests

APIGW_URL = "https://k4m88497ad.execute-api.eu-west-1.amazonaws.com/Prod"
DOCUMENTS_URL = "s3://amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq/uploaded_kyc_docs/"

PROFILE = "shinrai.devpost"
REGION = "eu-west-1"
SERVICE = "execute-api"


# Create a session using your AWS credentials
session = boto3.Session(profile_name=PROFILE)
credentials = session.get_credentials()

def get_auth_headers(method, url, body=None):
    """Generate SigV4 authentication headers for API Gateway"""
    request = AWSRequest(method=method, url=url, data=body, headers={"Content-Type": "application/json"})
    SigV4Auth(credentials, SERVICE, REGION).add_auth(request)
    return dict(request.headers)

# Override the standard requests.post method to include SigV4 authentication
def post_with_auth(url, json=None):
    auth_headers = get_auth_headers('POST', url, body=json)
    return requests.post(url, json=json, headers=auth_headers)