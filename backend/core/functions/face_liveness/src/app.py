from decimal import Decimal
import json
import os
import datetime

import boto3
from aws_lambda_powertools import Logger, Tracer
from botocore.exceptions import ClientError
from portal import Portal,DOCUMENT_TYPE


FACELIVENESSRESULTS_TABLE_NAME = os.getenv('FACELIVENESSRESULTS_TABLE_NAME', None)
assert FACELIVENESSRESULTS_TABLE_NAME is not None, 'FACELIVENESSRESULTS_TABLE_NAME env variable is missing'
        
LIVENESSCAPTUREBUCKET_BUCKET_NAME= os.getenv('LIVENESSCAPTUREBUCKET_BUCKET_NAME', None)
assert LIVENESSCAPTUREBUCKET_BUCKET_NAME is not None, 'LIVENESSCAPTUREBUCKET_BUCKET_NAME env variable is missing'

FACE_LIVENESS_CONFIDENCE_THRESHOLD = os.getenv('FACE_LIVENESS_CONFIDENCE_THRESHOLD',90)  # Adjust this threshold as needed

logger = Logger()
tracer = Tracer()
portal = Portal()
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
        item = {
            'session_id': session_id,
            'status': 'CREATED',
            'timestamp': datetime.datetime.now().isoformat(),
            'request_id_create': context.aws_request_id
        }
        put_response = table.put_item(Item=item)
        logger.info(f"Created face liveness session: {session_id} DynamoDB put_item response: {put_response}")
        
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
        logger.info(f"Seacrching session ID: {session_id}")
        if not session_id:
            logger.error("Session ID is missing/required")
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
        liveness_document = dict(session_id=session_id,
            confidence=confidence,
            status=status,
            is_live=is_live,
            request_id=context.aws_request_id)
        logger.info(f"Face liveness results for session {session_id}: Confidence: {confidence}, Status: {status}")
        
        # Extract ReferenceImage and AuditImages if available and save them to S3 bucket
        s3_client = boto3.client('s3')
        reference_image_key = None
        audit_image_keys = []
        
        # Save ReferenceImage if available
        if 'ReferenceImage' in response and 'Bytes' in response['ReferenceImage']:
            reference_image_key = f"{session_id}/reference_image.jpg"
            s3_client.put_object(
                Bucket=LIVENESSCAPTUREBUCKET_BUCKET_NAME,
                Key=reference_image_key,
                Body=response['ReferenceImage']['Bytes']
            )
            liveness_document['reference_image'] = reference_image_key
            logger.info(f"Saved reference image to S3: {reference_image_key}")
        
        # Save AuditImages if available
        if 'AuditImages' in response:
            for i, audit_image in enumerate(response['AuditImages']):
                if 'Bytes' in audit_image:
                    audit_image_key = f"{session_id}/audit_image_{i}.jpg"
                    s3_client.put_object(
                        Bucket=LIVENESSCAPTUREBUCKET_BUCKET_NAME,
                        Key=audit_image_key,
                        Body=audit_image['Bytes']
                    )
                    audit_image_keys.append(audit_image_key)
            if audit_image_keys:
                liveness_document['audit_images'] = json.dumps(audit_image_keys)
                logger.info(f"Saved {len(audit_image_keys)} audit images to S3")
        
        logger.info(f"Full response: {liveness_document}")
        # Update session results in DynamoDB
        # Prepare update expression and attributes for DynamoDB
        update_expression = 'SET confidence = :conf, status = :stat, updated_at = :time'
        expression_attr_values = {
            ':conf': Decimal(confidence) if confidence is not None else None,
            ':stat': status,
            ':time': datetime.datetime.now().isoformat(),
            ':request_id_results': context.aws_request_id
        }
        
        # Add image paths to DynamoDB if available
        if reference_image_key or audit_image_keys:
            update_expression += ', images = :images'
            expression_attr_values[':images'] = {
                'reference_image': reference_image_key,
                'audit_images': audit_image_keys
            }
            
        update_response = table.update_item(
            Key={'session_id': session_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attr_values,
            ReturnValues='ALL_NEW'
        )
        logger.info(f"DynamoDB update_item response: {update_response}")

        # Determine if the liveness check passed based on confidence threshold
        is_live = confidence >= FACE_LIVENESS_CONFIDENCE_THRESHOLD if confidence is not None else False
        portal.capture_face_liveness(
            liveness_document
        )
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
        try:
            body = json.loads(event.get('body', '{}'))
            if not body:
                logger.error("Empty request body")
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({
                        'message': 'Empty request body'
                    })
                }
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request body")
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
