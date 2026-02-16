---
inclusion: fileMatch
fileMatchPattern: "**/functions/**/app.py"
---

# Lambda Function Patterns

This steering file is automatically included when working with Lambda function handlers.

## Handler Structure

All Lambda handlers should follow this pattern:

```python
import json
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer

logger = Logger()
tracer = Tracer()

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    """
    Lambda handler for [function purpose].
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    
    if http_method == 'POST':
        try:
            data = event.get('body', {})
            while isinstance(data, str):
                data = json.loads(data)
            
            # Route to appropriate handler
            return process_request(data)
            
        except json.JSONDecodeError:
            return make_response(400, {'message': 'Invalid JSON body'})
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return make_response(500, {'message': 'Internal Server Error'})
    else:
        return make_response(405, {'message': 'Method Not Allowed'})
```

## Response Helper

```python
def make_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            # Security headers
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY'
        },
        'body': json.dumps(body, default=str)
    }
```

## Schema Validation

Use aws-lambda-powertools validation:

```python
from aws_lambda_powertools.utilities.validation import validate

schema = {
    "type": "object",
    "properties": {
        "idNumber": {"type": "string"},
        "fullNames": {"type": "string"}
    },
    "required": ["idNumber"]
}

try:
    validate(event=data, schema=schema)
except Exception as e:
    return make_response(400, {'message': 'Validation failed', 'error': str(e)})
```

## Environment Variables

Access environment variables with defaults:

```python
import os

TABLE_NAME = os.environ.get('TABLE_NAME', 'DefaultTable')
BUCKET_NAME = os.environ.get('BUCKET_NAME')
assert BUCKET_NAME is not None, "BUCKET_NAME is required"
```

## DynamoDB Operations

```python
import boto3

dynamodb = boto3.client('dynamodb')

# Get item
response = dynamodb.get_item(
    TableName=TABLE_NAME,
    Key={'customerId': {'S': customer_id}}
)

# Update item
dynamodb.update_item(
    TableName=TABLE_NAME,
    Key={'customerId': {'S': customer_id}},
    UpdateExpression='SET #status = :status',
    ExpressionAttributeNames={'#status': 'status'},
    ExpressionAttributeValues={':status': {'S': 'Verified'}}
)
```

## S3 Operations

```python
import boto3
from io import BytesIO

s3_client = boto3.client('s3')

# Download
s3_client.download_file(bucket, key, local_path)

# Upload
s3_client.upload_fileobj(
    BytesIO(binary_data),
    bucket,
    key,
    ExtraArgs={'ContentType': 'application/pdf'}
)
```

## Invoking Other Lambdas

```python
import boto3
import json

lambda_client = boto3.client('lambda')

# Synchronous invocation (waits for result)
response = lambda_client.invoke(
    FunctionName=os.environ['TARGET_FUNCTION'],
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

result = json.loads(response['Payload'].read())
```

## Async Lambda Invocation Pattern

For long-running operations that exceed API Gateway's 29s timeout (e.g., PDF validation with IPRS cross-validation), use the async job pattern:

```python
import boto3
import json

lambda_client = boto3.client('lambda')

# 1. Create job record in DynamoDB (PROCESSING)
job_id = async_job_service.create_job(action=action, data=data)

# 2. Build event payload with asyncJobId so Lambda can write results back
event_payload = {
    'httpMethod': 'POST',
    'path': '/document/alienid',
    'body': json.dumps(data),
    'headers': {'Content-Type': 'application/json'},
    'requestContext': {
        'requestId': f'async-{job_id}',
        'asyncJobId': job_id
    }
}

# 3. Invoke Lambda asynchronously (fire-and-forget)
response = lambda_client.invoke(
    FunctionName=os.environ['TARGET_FUNCTION'],
    InvocationType='Event',  # Async — returns immediately
    Payload=json.dumps(event_payload)
)

# 4. Return 202 Accepted with jobId for client polling
return make_response(202, {'jobId': job_id, 'status': 'PROCESSING'})
```

### Writing Async Results from the Target Lambda

```python
# In the target Lambda handler, detect async invocation and write result to DynamoDB
async_job_id = event.get('requestContext', {}).get('asyncJobId')

result = process_document(data)

if async_job_id:
    _write_async_result(async_job_id, result)  # Mark job COMPLETED in DynamoDB
```

Currently used by: `validate_alienid`, `validate_militaryid`
Key files: `async_job_service.py`, `action_router.py`, `document_validation/src/app.py`

## Error Classes

Define custom exceptions for clear error handling:

```python
class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class ExternalAPIError(Exception):
    """Raised when external API call fails."""
    pass

class DocumentProcessingError(Exception):
    """Raised when document processing fails."""
    pass
```
