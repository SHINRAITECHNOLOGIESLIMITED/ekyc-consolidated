import json
import os
from collections import defaultdict

import boto3
import requests
from aws_lambda_powertools import Logger, Tracer

KYCDOCUMENTSBUCKET_NAME = os.environ.get('KYCDOCUMENTSBUCKET_NAME', None)
assert KYCDOCUMENTSBUCKET_NAME is not None, "KYCDOCUMENTSBUCKET_NAME is not set"

PORTAL_GRAPHQL_SECRET_ARN = os.getenv('PORTAL_GRAPHQL_SECRET_ARN', None)
assert PORTAL_GRAPHQL_SECRET_ARN, "PORTAL_GRAPHQL_SECRET_ARN environment variable is not set"

logger = Logger()
tracer = Tracer()

client = boto3.client('textract')
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


def project_kyc_document_portal(customer_id, document_type, document_url, status, extractedData=None):
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
            "documentStatus": status,
            "url": document_url,
            "extractedData": extractedData
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


def get_kv_map(s3Path):
    response = client.analyze_document(
        Document={'S3Object': {'Bucket': KYCDOCUMENTSBUCKET_NAME, 'Name': s3Path}},
        FeatureTypes=["FORMS"]
    )

    # Get the text blocks
    blocks = response['Blocks']

    # get key and value maps
    key_map = {}
    value_map = {}
    block_map = {}
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    return key_map, value_map, block_map


def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += 'X '

    return text.strip()


def get_kv_relationship(key_map, value_map, block_map):
    kvs = defaultdict(list)
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key].append(val)
    return kvs


def find_value_block(key_block, value_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
                return value_block
    return None


def handler(event, context):
    try:
        document_metadata = event
        customerID = document_metadata["customerID"]
        s3Path = document_metadata.['s3Path']
        document_type = document_metadata.['documentType']
        key_map, value_map, block_map = get_kv_map(s3Path)
        # append extracted key value pairs to event and pass all parameters along
        extractedData = get_kv_relationship(key_map, value_map, block_map)
        event['extractedData'] = extractedData
        project_kyc_document_portal(customerID, document_type, s3Path, 'EXTRACTED', extractedData)
        logger.info(f"Extracted key value pairs: {event['extracted']}")
        return {
            'statusCode': 200,
            'body': json.dumps(event)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error: {str(e)}'
            })
        }
