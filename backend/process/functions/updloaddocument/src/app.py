import json
import os
import mimetypes
from typing import Dict, Any

import boto3
from botocore.exceptions import ClientError

# Constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
DOCUMENTSUPLOAD_BUCKET_NAME = os.getenv('DOCUMENTSUPLOAD_BUCKET_NAME', None)

# Validation

# Initialize AWS clients
s3 = boto3.resource('s3')

def get_content_type(filename: str) -> str:
    """
    Determine the content type of a file based on its extension
    """
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or 'application/octet-stream'

def validate_file_extension(filename: str) -> bool:
    """
    Validate if the file extension is allowed
    """
    file_ext = os.path.splitext(filename)[1].lower()
    return file_ext in ALLOWED_EXTENSIONS

def validate_input(body: Dict[str, Any]) -> None:
    """
    Validate the input parameters
    Raises ValueError if validation fails
    """
    if not body.get('document'):
        raise ValueError("Document content is required")

    if not body.get('document_name'):
        raise ValueError("Document name is required")

    document = body['document']
    document_name = body['document_name']

    # Validate file size
    if len(document) > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum limit of {MAX_FILE_SIZE/1024/1024}MB")

    # Validate file extension
    if not validate_file_extension(document_name):
        raise ValueError(f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")

def create_response(status_code: int, message: str, request_id: str = None,
                   additional_data: Dict = None) -> Dict:
    """
    Create a standardized API response
    """
    response_body = {
        'message': message,
        'requestId': request_id
    }

    if additional_data:
        response_body.update(additional_data)

    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'  # CORS support
        },
        'body': json.dumps(response_body)
    }

def upload_to_s3(bucket: str, key: str, body: str, content_type: str) -> None:
    """
    Upload a file to S3 with error handling
    """
    try:
        s3.Object(bucket, key).put(
            Body=body,
            ContentType=content_type,
            ServerSideEncryption='AES256'  # Enable server-side encryption
        )
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        raise Exception(f"S3 upload failed: {error_code} - {error_message}")

def handler(event, context):
    """
    Lambda handler to process document uploads to S3
    """
    #ensure enviromental variables have been loaded
    assert DOCUMENTSUPLOAD_BUCKET_NAME is not None, 'DOCUMENTSUPLOAD_BUCKET_NAME env variable is missing'

    print(f"Processing request: {context.aws_request_id}")
    print(f"Event: {json.dumps(event)}")

    try:
        # Parse and validate input
        if not event.get('body'):
            return create_response(400, "Missing request body", context.aws_request_id)

        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return create_response(400, "Invalid JSON in request body", context.aws_request_id)

        try:
            validate_input(body)
        except ValueError as e:
            return create_response(400, str(e), context.aws_request_id)

        document = body['document']
        document_name = body['document_name']

        # Generate a unique filename to prevent overwrites
        timestamp = context.get_remaining_time_in_millis()
        unique_filename = f"{timestamp}_{document_name}"

        # Get content type
        content_type = get_content_type(document_name)

        # Upload to S3
        upload_to_s3(
            bucket=DOCUMENTSUPLOAD_BUCKET_NAME,
            key=unique_filename,
            body=document,
            content_type=content_type
        )

        # Return success response
        return create_response(
            status_code=200,
            message="Document uploaded successfully",
            request_id=context.aws_request_id,
            additional_data={
                'filename': unique_filename,
                'contentType': content_type
            }
        )

    except ClientError as e:
        print(f"AWS Error: {str(e)}")
        return create_response(
            status_code=500,
            message=f"AWS Service Error: {str(e)}",
            request_id=context.aws_request_id
        )

    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        return create_response(
            status_code=500,
            message=f"Internal server error: {str(e)}",
            request_id=context.aws_request_id
        )
