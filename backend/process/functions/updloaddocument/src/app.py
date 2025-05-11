import json
import os

import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.validation import validate, SchemaValidationError

from portal import Portal
NEWDOCUMENTREGISTRATION_STATE_MACHINE_ARN = os.environ.get('NEWDOCUMENTREGISTRATION_STATE_MACHINE_ARN', None)
assert NEWDOCUMENTREGISTRATION_STATE_MACHINE_ARN is not None, "NEWDOCUMENTREGISTRATION_STATE_MACHINE_ARN is not defined"

KYCDOCUMENTSBUCKET_NAME = os.environ.get('KYCDOCUMENTSBUCKET_NAME', None)
assert KYCDOCUMENTSBUCKET_NAME is not None, "KYCDOCUMENTSBUCKET_NAME is not set"

AMPLIFY_S3_BUCKET_NAME = os.environ.get('AMPLIFY_S3_BUCKET_NAME', None)
assert AMPLIFY_S3_BUCKET_NAME is not None, "AMPLIFY_S3_BUCKET_NAME is not set"


logger = Logger()
tracer = Tracer()

sfn_client = boto3.client('stepfunctions')
s3_client = boto3.client('s3')

portal = Portal()
headers = {
        'Access-Control-Allow-Origin': 'https://main.d2896e60a8d7f8.amplifyapp.com',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'POST,OPTIONS'
    }

@tracer.capture_method
def handler(event, context):
    logger.info(event)
    
    schema = {
                "type": "object",
                "properties": {
                    "body": {
                        "type": "string",
                        "description": "Request body containing document metadata"
                    }
                },
                "required": ["body"]
            }
    
    try:
        validate(event=event, schema=schema)  
    except SchemaValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        validation_errors = e.validation_message if hasattr(e, 'validation_message') else str(e)
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'error': 'Invalid request format',
                'details': validation_errors
            })
        }
    
    schema = {
                "type": "object",
                       "properties": {
                            "s3Path": {
                                "type": "string",
                                "description": "S3 path to the document"
                            },
                            "documentType": {
                                "type": "string",
                                "description": "Type of document being uploaded"
                            },
                            "customerId": {
                                "type": "string",
                                "description": "Customer identifier"
                            }
                        },
                        "required": ["s3Path", "documentType", "customerId"],
                        "description": "Request body containing document metadata"
                    }
    document_request = json.loads(event["body"])  
    try:
        validate(event=document_request, schema=schema)  
    except SchemaValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        validation_errors = e.validation_message if hasattr(e, 'validation_message') else str(e)
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'error': 'Invalid request format',
                'details': validation_errors
            })
        }
    
    # Validate document_metadata structure
    if 'invocation_number' in document_request:
        logger.error("Invalid document metadata: 'invocation_number' should not be present in request")
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': "Invalid document metadata: 'invocation_number' should not be present in request"})
        }
    
    logger.info(document_request)
    s3Path = document_request["s3Path"]
    document_type = document_request["documentType"]
    customer_Id = document_request["customerId"]
    newS3Path = f"{customer_Id}/{s3Path.split('/')[-1]}"

    try:
        # Check if object exists first
        s3_client.head_object(
            Bucket=AMPLIFY_S3_BUCKET_NAME,
            Key=s3Path
        )
    except s3_client.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404' or error_code == 'NoSuchKey':
            logger.error(f"File {s3Path} does not exist in bucket {AMPLIFY_S3_BUCKET_NAME}")
            return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': f"File {s3Path} not found in source bucket"})
                }
        else:
            return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({'error': e.message})
                }
    try:
        # copy object from source url to destination bucket
        logger.info(f"Copying document {s3Path} from {AMPLIFY_S3_BUCKET_NAME} to {KYCDOCUMENTSBUCKET_NAME}")
        s3_client.copy_object(
            Bucket=KYCDOCUMENTSBUCKET_NAME,
            CopySource={
                'Bucket': AMPLIFY_S3_BUCKET_NAME,
                'Key': s3Path
            },
            Key=newS3Path
        )
        document_request["s3Path"] = newS3Path
        document_request["bucket"] = KYCDOCUMENTSBUCKET_NAME
        documentId = f"{customer_Id}-{document_type}"
        document_request["documentId"]=documentId
        logger.info(f"Document {newS3Path} copied from {AMPLIFY_S3_BUCKET_NAME} to {KYCDOCUMENTSBUCKET_NAME}")
        document_request["document"] = {
            "documentId": documentId,
            "customerId": customer_Id,
            "documentType": document_type,
            "documentStatus": 'UPLOADED',
            "s3Path": newS3Path
        }
        # Update or create the KYC document
        result = portal.update_kyc_document(document_request["document"])
        if result is None:
            logger.error(f"Failed to update or create KYC document: {documentId}")
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': 'Failed to update or create KYC document'})
            }
            
        #Start step function execution
        document_request['invocation_number']=0
        response = sfn_client.start_execution(
            stateMachineArn=NEWDOCUMENTREGISTRATION_STATE_MACHINE_ARN,
            input=json.dumps(document_request)
        )
        #log the sfn execution identifier
        logger.info(f"Started SFN execution {response['executionArn']} with payload {document_request}")

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
