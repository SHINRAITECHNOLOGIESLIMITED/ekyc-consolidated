import json
import os
import logging
import base64
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3_client = boto3.client('s3')

# Get bucket names from environment variables
KYC_DOCUMENTS_BUCKET = os.environ.get('KYCDOCUMENTSBUCKET_NAME')
FACE_LIVENESS_BUCKET = os.environ.get('LIVENESSCAPTUREBUCKET_BUCKET_NAME')
CERTIFICATION_BUCKET = os.environ.get('CERTIFICATION_BUCKET_NAME')

# Map bucket types to actual bucket names
BUCKET_MAPPING = {
    'kyc': KYC_DOCUMENTS_BUCKET,
    'liveness': FACE_LIVENESS_BUCKET,
    'certification': CERTIFICATION_BUCKET
}

# MIME type mapping
MIME_TYPES = {
    '.pdf': 'application/pdf',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.tiff': 'image/tiff',
    '.tif': 'image/tiff'
}

def get_mime_type(file_path):
    """Determine MIME type based on file extension"""
    file_ext = os.path.splitext(file_path.lower())[1]
    return MIME_TYPES.get(file_ext, 'application/octet-stream')

def make_error_response(status_code, message, error=None):
    """Create a standardized error response"""
    body = {
        'message': message
    }
    if error:
        body['error'] = str(error)
        
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,OPTIONS'
        },
        'body': json.dumps(body)
    }

def handler(event, context):
    """Lambda handler function"""
    try:
        # Extract path parameters
        path_parameters = event.get('pathParameters', {}) or {}
        bucket_type = path_parameters.get('bucketType')
        document_key = path_parameters.get('documentKey')
        
        # Validate parameters
        if not bucket_type or not document_key:
            return make_error_response(400, 'Missing required parameters', 
                                      'Both bucketType and documentKey are required')
        
        # Check if bucket type is valid
        if bucket_type not in BUCKET_MAPPING:
            return make_error_response(400, 'Invalid bucket type',
                                      f'Bucket type must be one of: {", ".join(BUCKET_MAPPING.keys())}')
        
        # Get the actual bucket name
        bucket_name = BUCKET_MAPPING[bucket_type]
        
        try:
            # Get the object from S3
            response = s3_client.get_object(Bucket=bucket_name, Key=document_key)
            
            # Read the content
            content = response['Body'].read()
            
            # Determine content type
            content_type = get_mime_type(document_key)
            
            # Return binary response
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': content_type,
                    'Content-Disposition': f'inline; filename="{os.path.basename(document_key)}"',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'GET,OPTIONS'
                },
                'body': base64.b64encode(content).decode('utf-8'),
                'isBase64Encoded': True
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return make_error_response(404, 'Document not found', 
                                          f'The requested document does not exist')
            else:
                logger.error(f"S3 error: {e}")
                return make_error_response(500, 'Error retrieving document', str(e))
            
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return make_error_response(500, 'Internal server error', str(e))