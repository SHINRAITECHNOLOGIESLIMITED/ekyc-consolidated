import json
import os

import boto3
import requests
from aws_lambda_powertools import Logger, Tracer

DOCUMENTTEXTRACT_FUNCTION_NAME = os.environ.get('DOCUMENTTEXTRACT_FUNCTION_NAME', None)
assert DOCUMENTTEXTRACT_FUNCTION_NAME is not None, "DOCUMENTTEXTRACT_FUNCTION_NAME is not defined"

KYCDOCUMENTSBUCKET_NAME = os.environ.get('KYCDOCUMENTSBUCKET_NAME', None)
assert KYCDOCUMENTSBUCKET_NAME is not None, "KYCDOCUMENTSBUCKET_NAME is not set"

PORTAL_GRAPHQL_SECRET_ARN = os.getenv('PORTAL_GRAPHQL_SECRET_ARN', None)
assert PORTAL_GRAPHQL_SECRET_ARN, "PORTAL_GRAPHQL_SECRET_ARN environment variable is not set"

logger = Logger()
tracer = Tracer()

lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')

portal_credentials_response = secrets_client.get_secret_value(
    SecretId=PORTAL_GRAPHQL_SECRET_ARN
)
if 'SecretString' not in portal_credentials_response:
    logger.error("Failed to load Portal Connection credentials: SecretString not found")
    raise Exception("Failed to load Portal service")
_portal_credentials = json.loads(portal_credentials_response['SecretString'])
PORTAL_GRAPHQL_URL = _portal_credentials['url']
PORTAL_GRAPHQL_API_KEY = _portal_credentials['api_key']

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def project_kyc_document_portal(customer_id, document_type, document_url):
    mutation = """
        mutation CreateKYCDocument($input: CreateKYCDocumentInput!) {
            createKYCDocument(input: $input) {
                documentId
            }
        }
    """
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': PORTAL_GRAPHQL_API_KEY
    }
    variables = {
        "input": {
            "documentId": f"{customer_id}-{document_type}",
            "customerId": customer_id,
            "documentType": document_type,
            "documentStatus": "UPLOADED",
            "url": document_url
        }
    }

    # Prepare the request body
    payload = {
        'query': mutation,
        'variables': variables
    }
    try:
        # Make the request to AppSync
        response = requests.post(
            PORTAL_GRAPHQL_URL,
            headers=headers,
            json=payload
        )

        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            if 'errors' in result:
                print(f"GraphQL Errors: {result['errors']}")
                return None
            return result['data']['createAPICall']
        else:
            print(f"HTTP Error: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error making API call: {str(e)}")
        return None


def handler(event, context):

    headers = {
        'Access-Control-Allow-Origin': 'https://main.d2896e60a8d7f8.amplifyapp.com',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    document_metadata = json.loads(event["body"])
    logger.info(document_metadata)
    s3Path = document_metadata["s3Path"]
    customerId = document_metadata["customerId"]
    newS3Path = f"{customerId}/{s3Path.split('/')[-1]}"
    source_bucket_name = "amplify-d2896e60a8d7f8-ma-kycdocumentsbucketa4bf11-aae1vuopf1xq"

    try:
        # Check if object exists first
        s3_client.head_object(
            Bucket=source_bucket_name,
            Key=s3Path
        )
    except s3_client.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404' or error_code == 'NoSuchKey':
            logger.error(f"File {s3Path} does not exist in bucket {source_bucket_name}")
            raise FileNotFoundError(f"File {s3Path} not found in source bucket")
        else:
            raise e

    try:
        # copy object from source url to destination bucket
        logger.info(f"Copying document {s3Path} from {source_bucket_name} to {KYCDOCUMENTSBUCKET_NAME}")
        s3_client.copy_object(
            Bucket=KYCDOCUMENTSBUCKET_NAME,
            CopySource={
                'Bucket': source_bucket_name,
                'Key': s3Path
            },
            Key=newS3Path
        )
        document_metadata["s3Path"] = newS3Path
        document_metadata["bucket"] = KYCDOCUMENTSBUCKET_NAME
        logger.info(f"Document {newS3Path} copied from {source_bucket_name} to {KYCDOCUMENTSBUCKET_NAME}")
        project_kyc_document_portal(customerId, document_metadata["documentType"], s3Path)
        lambda_client.invoke(
            FunctionName=DOCUMENTTEXTRACT_FUNCTION_NAME,
            InvocationType='Event',
            Payload=document_metadata
        )
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'Document uploaded successfully'})
        }
    except Exception as e:
        logger.error(e)
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
