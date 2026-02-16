"""
Async Job Service for long-running KYC operations.

Manages job lifecycle for operations that exceed API Gateway's 29s timeout
(e.g., Alien ID and Military ID PDF validation with IPRS cross-validation).

Flow:
1. Orchestrator creates job record (PROCESSING) and invokes Lambda async
2. Lambda completes work and writes result to DynamoDB
3. Client polls get_job_status to retrieve result
"""

import json
import os
import uuid
import time
from typing import Dict, Any, Optional
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger

logger = Logger()

# Job statuses
JOB_STATUS_PROCESSING = "PROCESSING"
JOB_STATUS_COMPLETED = "COMPLETED"
JOB_STATUS_FAILED = "FAILED"

# TTL: 24 hours
JOB_TTL_SECONDS = 86400

# Actions that should be processed asynchronously
ASYNC_ACTIONS = {"validate_alienid", "validate_militaryid"}


class AsyncJobService:
    """Manages async job records in DynamoDB."""

    def __init__(self):
        self.dynamodb = boto3.client('dynamodb')
        self.table_name = os.environ.get('ASYNC_JOBS_TABLE_NAME', 'ekyc-async-jobs')

    def create_job(self, action: str, data: Dict[str, Any],
                   request_id: Optional[str] = None) -> str:
        """
        Create a new async job record.

        Args:
            action: The KYC action being processed
            data: The original request data
            request_id: Optional API Gateway request ID

        Returns:
            jobId (UUID string)
        """
        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + 'Z'
        ttl = int(time.time()) + JOB_TTL_SECONDS

        try:
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item={
                    'jobId': {'S': job_id},
                    'status': {'S': JOB_STATUS_PROCESSING},
                    'action': {'S': action},
                    'requestData': {'S': json.dumps(data, default=str)},
                    'createdAt': {'S': now},
                    'updatedAt': {'S': now},
                    'ttl': {'N': str(ttl)},
                    **(
                        {'requestId': {'S': request_id}}
                        if request_id else {}
                    )
                }
            )
            logger.info("Async job created", extra={
                "job_id": job_id,
                "action": action
            })
            return job_id

        except ClientError as e:
            logger.error(f"Failed to create async job: {e}")
            raise

    def complete_job(self, job_id: str, result: Dict[str, Any]) -> None:
        """
        Mark a job as completed with its result.

        Args:
            job_id: The job ID
            result: The Lambda response to store
        """
        now = datetime.utcnow().isoformat() + 'Z'
        try:
            self.dynamodb.update_item(
                TableName=self.table_name,
                Key={'jobId': {'S': job_id}},
                UpdateExpression=(
                    'SET #status = :status, '
                    '#result = :result, '
                    'updatedAt = :now'
                ),
                ExpressionAttributeNames={
                    '#status': 'status',
                    '#result': 'result'
                },
                ExpressionAttributeValues={
                    ':status': {'S': JOB_STATUS_COMPLETED},
                    ':result': {'S': json.dumps(result, default=str)},
                    ':now': {'S': now}
                }
            )
            logger.info("Async job completed", extra={"job_id": job_id})

        except ClientError as e:
            logger.error(f"Failed to complete async job {job_id}: {e}")
            raise

    def fail_job(self, job_id: str, error: str) -> None:
        """
        Mark a job as failed with an error message.

        Args:
            job_id: The job ID
            error: Error description
        """
        now = datetime.utcnow().isoformat() + 'Z'
        try:
            self.dynamodb.update_item(
                TableName=self.table_name,
                Key={'jobId': {'S': job_id}},
                UpdateExpression=(
                    'SET #status = :status, '
                    'errorMessage = :error, '
                    'updatedAt = :now'
                ),
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': {'S': JOB_STATUS_FAILED},
                    ':error': {'S': error},
                    ':now': {'S': now}
                }
            )
            logger.info("Async job failed", extra={
                "job_id": job_id,
                "error": error
            })

        except ClientError as e:
            logger.error(f"Failed to update job {job_id} as failed: {e}")
            raise

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a job record.

        Args:
            job_id: The job ID

        Returns:
            Job record dict or None if not found
        """
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={'jobId': {'S': job_id}}
            )

            if 'Item' not in response:
                return None

            item = response['Item']
            job = {
                'jobId': item['jobId']['S'],
                'status': item['status']['S'],
                'action': item['action']['S'],
                'createdAt': item['createdAt']['S'],
                'updatedAt': item['updatedAt']['S'],
            }

            if 'result' in item:
                job['result'] = json.loads(item['result']['S'])
            if 'errorMessage' in item:
                job['errorMessage'] = item['errorMessage']['S']
            if 'requestId' in item:
                job['requestId'] = item['requestId']['S']

            return job

        except ClientError as e:
            logger.error(f"Failed to get async job {job_id}: {e}")
            raise


def is_async_action(action: str) -> bool:
    """Check if an action should be processed asynchronously."""
    return action in ASYNC_ACTIONS
