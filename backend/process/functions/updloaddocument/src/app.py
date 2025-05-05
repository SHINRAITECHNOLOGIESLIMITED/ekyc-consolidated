import json
import os

import boto3

DOCUMENTTEXTRACT_FUNCTION_NAME = os.environ.get('DOCUMENTTEXTRACT_FUNCTION_NAME', None)
assert DOCUMENTTEXTRACT_FUNCTION_NAME is not None, "DOCUMENTTEXTRACT_FUNCTION_NAME is not defined"

lambda_client = boto3.client('lambda')


def handler(event, context):
    print(event["body"])
    headers = {
        'Access-Control-Allow-Origin': 'https://main.d2896e60a8d7f8.amplifyapp.com',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    try:
        payload = json.dumps(event["body"])
        lambda_client.invoke(
            FunctionName=DOCUMENTTEXTRACT_FUNCTION_NAME,
            InvocationType='Event',
            Payload=payload
        )
        # TODO: project to portal
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'Document uploaded successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
