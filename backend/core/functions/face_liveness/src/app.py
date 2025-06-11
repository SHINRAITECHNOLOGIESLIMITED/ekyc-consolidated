import json
import os

import boto3
from aws_lambda_powertools import Logger, Tracer
from botocore.exceptions import ClientError

FACELIVENESSRESULTS_TABLE_NAME = os.getenv('FACELIVENESSRESULTS_TABLE_NAME', None)
FACE_LIVENESS_CONFIDENCE_THRESHOLD = os.getenv('FACE_LIVENESS_CONFIDENCE_THRESHOLD',
                                               90)  # Adjust this threshold as needed
logger = Logger()
tracer = Tracer()
rekognition_client = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(FACELIVENESSRESULTS_TABLE_NAME)

headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'POST,OPTIONS'
}
def create_face_liveness_session(event, context):
    """
    Creates a face liveness session and returns the session ID
    """
    try:
        # Create a face liveness session
        response = rekognition_client.create_face_liveness_session(
            ClientRequestToken=context.aws_request_id,  # Using Lambda request ID as unique token
            Settings={
                'AuditImagesLimit': 3  # Number of audit images to store
            }
        )

        session_id = response['SessionId']

        # Store session information in DynamoDB
        table.put_item(
            Item={
                'session_id': session_id,
                'status': 'CREATED',
                'timestamp': context.get_remaining_time_in_millis(),
                'request_id': context.aws_request_id
            }
        )
        logger.info(f"Created face liveness session: {session_id}")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'sessionId': session_id,
                'message': 'Face liveness session created successfully'
            })
        }

    except ClientError as e:
        logger.error(f"Error creating face liveness session: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': str(e),
                'message': 'Error creating face liveness session'
            })
        }


def get_face_liveness_results(event, context):
    """
    Gets the results of a face liveness session
    """
    try:
        # Extract session ID from the event
        body = json.loads(event.get('body', '{}'))
        session_id = body.get('sessionId')

        if not session_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Session ID is required'
                })
            }

        # Get the face liveness session results
        response = rekognition_client.get_face_liveness_session_results(
            SessionId=session_id
        )

        # Extract relevant information
        confidence = response.get('Confidence')
        status = response.get('Status')

        # Update session results in DynamoDB
        table.update_item(
            Key={'session_id': session_id},
            UpdateExpression='SET confidence = :conf, status = :stat, updated_at = :time',
            ExpressionAttributeValues={
                ':conf': confidence,
                ':stat': status,
                ':time': context.get_remaining_time_in_millis()
            }
        )

        # Determine if the liveness check passed based on confidence threshold
        is_live = confidence >= FACE_LIVENESS_CONFIDENCE_THRESHOLD if confidence is not None else False
        logger.info(
            f"Face liveness check completed for session: {session_id}, Confidence: {confidence}, Status: {status}, IsLive: {is_live}")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'sessionId': session_id,
                'confidence': confidence,
                'status': status,
                'isLive': is_live,
                'message': 'Face liveness check completed'
            })
        }

    except ClientError as e:
        logger.error(f"Error getting face liveness results: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': str(e),
                'message': 'Error getting face liveness results'
            })
        }


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event, context):
    """
    Main handler that routes to appropriate function based on action
    """
    logger.info(event["body"])
    try:
        # ensure that environmental variables should have been loaded
        assert FACELIVENESSRESULTS_TABLE_NAME is not None, 'FACELIVENESSRESULTS_TABLE_NAME env variable is missing'

        try:
            body = json.loads(event.get('body', '{}'))
            if not body:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'message': 'Empty request body'
                    })
                }
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Invalid JSON in request body'
                })
            }

        action = body.get('action', '')

        if action == 'create':
            return create_face_liveness_session(event, context)
        elif action == 'get_results':
            return get_face_liveness_results(event, context)
        else:
            logger.error("Invalid action specified")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Invalid action specified'
                })
            }

    except Exception as e:
        logger.error(f"Error while handling: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'message': f'Internal server error: {str(e)}'
            })
        }
