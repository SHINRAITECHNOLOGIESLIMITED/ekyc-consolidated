"""
Result Storage for Face Matching Service

Stores verification results in DynamoDB and updates KYC status.
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger

from models import FaceMatchingResult, FaceMatchingRequest, MatchStatus

logger = Logger()

# DynamoDB configuration
RESULTS_TABLE = os.environ.get('FACE_MATCHING_RESULTS_TABLE', 'FaceMatchingResults')
KYC_STATUS_TABLE = os.environ.get('KYC_STATUS_TABLE', 'KYCStatus')
TTL_DAYS = 30


class ResultStorage:
    """Stores face matching results and updates KYC status."""
    
    def __init__(self, dynamodb_client: Optional[boto3.client] = None):
        self._dynamodb = dynamodb_client or boto3.resource('dynamodb')
        self._results_table = self._dynamodb.Table(RESULTS_TABLE)
    
    def store_result(
        self,
        result: FaceMatchingResult,
        request: FaceMatchingRequest
    ) -> bool:
        """
        Store face matching result in DynamoDB.
        
        Args:
            result: FaceMatchingResult to store
            request: Original request for image references
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Calculate TTL
            ttl = int((datetime.utcnow() + timedelta(days=TTL_DAYS)).timestamp())
            
            item = {
                'request_id': result.request_id,
                'customer_id': result.customer_id,
                'timestamp': result.timestamp.isoformat(),
                'match_status': result.match_status.value,
                'comparison_mode': result.comparison_mode.value,
                'comparisons': {
                    c.comparison_name: {
                        'similarity_score': str(c.similarity_score),
                        'confidence': str(c.confidence)
                    }
                    for c in result.comparisons
                },
                'quality_metrics': {
                    source: {
                        'brightness': str(metrics.brightness_score),
                        'sharpness': str(metrics.sharpness_score),
                        'face_confidence': str(metrics.face_confidence)
                    }
                    for source, metrics in result.quality_metrics.items()
                },
                'thresholds': {
                    'approval': str(result.thresholds_used.get('approval', 70)),
                    'rejection': str(result.thresholds_used.get('rejection', 50))
                },
                'image_references': {
                    'customer_photo': request.customer_photo_key,
                    'id_document': request.id_document_key,
                    'iprs_reference': f'iprs:{request.iprs_id_number}'
                },
                'processing_time_ms': str(result.processing_time_ms),
                'ttl': ttl
            }
            
            self._results_table.put_item(Item=item)
            logger.info(f"Stored result for request {result.request_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to store result: {e}")
            return False
    
    def update_kyc_status(
        self,
        customer_id: str,
        match_status: MatchStatus
    ) -> bool:
        """
        Update customer's KYC status based on match outcome.
        
        Args:
            customer_id: Customer ID
            match_status: Face matching outcome
            
        Returns:
            True if updated successfully, False otherwise
        """
        # Map match status to KYC status
        kyc_status_map = {
            MatchStatus.APPROVED: 'Verified',
            MatchStatus.MANUAL_REVIEW: 'PendingReview',
            MatchStatus.REJECTED: 'Failed'
        }
        
        kyc_status = kyc_status_map.get(match_status, 'Unknown')
        
        try:
            # TODO: Update actual KYC status table
            # For now, just log the status update
            logger.info(f"KYC status update: customer={customer_id}, status={kyc_status}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to update KYC status: {e}")
            return False
