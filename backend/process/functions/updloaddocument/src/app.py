import json
import os

import boto3
from aws_lambda_powertools import Logger, Tracer
from portal import Portal
DOCUMENTTEXTRACT_FUNCTION_NAME = os.environ.get('DOCUMENTTEXTRACT_FUNCTION_NAME', None)
assert DOCUMENTTEXTRACT_FUNCTION_NAME is not None, "DOCUMENTTEXTRACT_FUNCTION_NAME is not defined"

KYCDOCUMENTSBUCKET_NAME = os.environ.get('KYCDOCUMENTSBUCKET_NAME', None)
assert KYCDOCUMENTSBUCKET_NAME is not None, "KYCDOCUMENTSBUCKET_NAME is not set"

logger = Logger()
tracer = Tracer()

lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')

portal = Portal()

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': 'https://main.d2896e60a8d7f8.amplifyapp.com',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }
    document_metadata = event["body"]
    logger.info(document_metadata)
    s3Path = document_metadata["s3Path"]
    document_type = document_metadata["documentType"]
    customer_Id = document_metadata["customerId"]
    newS3Path = f"{customer_Id}/{s3Path.split('/')[-1]}"
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
        document_projection = {
            "documentId": f"{customer_Id}-{document_type}",
            "customerId": customer_Id,
            "documentType": document_type,
            "documentStatus": 'UPLOADED',
            "s3Path": newS3Path
        }
        portal.update_kyc_document(document_projection)


        # logger.info(f"Invoking Document Extractor Lambda @{DOCUMENTTEXTRACT_FUNCTION_NAME}")

        lambda_client.invoke(
            FunctionName=DOCUMENTTEXTRACT_FUNCTION_NAME,
            InvocationType='Event',
            Payload=json.dumps(document_metadata)
        )
        logger.info(f"Invoked {DOCUMENTTEXTRACT_FUNCTION_NAME} with payload {document_metadata}")
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
