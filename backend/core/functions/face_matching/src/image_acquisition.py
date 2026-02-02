"""
Image Acquisition for Face Matching Service

Fetches images from S3, Textract, and IPRS API.
"""

import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger

logger = Logger()

# S3 bucket configuration
CUSTOMER_PHOTOS_BUCKET = os.environ.get('CUSTOMER_PHOTOS_BUCKET', 'maisha-verification-dev-686255958278')
DOCUMENTS_BUCKET = os.environ.get('DOCUMENTS_BUCKET', 'kyc-raw-documents-jubilee-ekyc-dev-686255958278')


class ImageAcquisition:
    """Acquires images from various sources for face matching."""
    
    def __init__(
        self,
        s3_client: Optional[boto3.client] = None,
        textract_client: Optional[boto3.client] = None
    ):
        self._s3 = s3_client or boto3.client('s3')
        self._textract = textract_client or boto3.client('textract')
    
    def acquire_all_images(
        self,
        customer_photo_key: str,
        id_document_key: str,
        iprs_id_number: str
    ) -> dict[str, Optional[bytes]]:
        """
        Acquire images from all sources.
        
        Args:
            customer_photo_key: S3 key for customer photo
            id_document_key: S3 key for ID document
            iprs_id_number: ID number for IPRS lookup
            
        Returns:
            Dict with 'customer', 'id_document', 'iprs' keys
            Values are image bytes or None if unavailable
        """
        images = {}
        
        # Get customer photo from S3
        images['customer'] = self.get_customer_photo(customer_photo_key)
        
        # Extract ID document photo
        images['id_document'] = self.extract_id_document_photo(id_document_key)
        
        # Get IPRS photo
        images['iprs'] = self.get_iprs_photo(iprs_id_number)
        
        return images
    
    def get_customer_photo(self, s3_key: str) -> Optional[bytes]:
        """
        Get customer photo from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Image bytes or None if not found
        """
        try:
            # Handle full S3 URI or just key
            if s3_key.startswith('s3://'):
                parts = s3_key.replace('s3://', '').split('/', 1)
                bucket = parts[0]
                key = parts[1] if len(parts) > 1 else ''
            else:
                bucket = CUSTOMER_PHOTOS_BUCKET
                key = s3_key
            
            response = self._s3.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"Failed to get customer photo from S3: {e}")
            return None
    
    def extract_id_document_photo(self, s3_key: str) -> Optional[bytes]:
        """
        Extract face photo from ID document using Textract.
        
        For now, this returns the full document image.
        In production, this would use Textract AnalyzeID to extract the face region.
        
        Args:
            s3_key: S3 object key for the ID document
            
        Returns:
            Image bytes or None if extraction failed
        """
        try:
            # Handle full S3 URI or just key
            if s3_key.startswith('s3://'):
                parts = s3_key.replace('s3://', '').split('/', 1)
                bucket = parts[0]
                key = parts[1] if len(parts) > 1 else ''
            else:
                bucket = DOCUMENTS_BUCKET
                key = s3_key
            
            # For now, just get the document image
            # TODO: Use Textract AnalyzeID to extract face region
            response = self._s3.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"Failed to extract ID document photo: {e}")
            return None
    
    def get_iprs_photo(self, id_number: str) -> Optional[bytes]:
        """
        Get photo from IPRS API.
        
        This is a placeholder - actual implementation depends on ESB team
        confirming the photo field is available in IPRS response.
        
        Args:
            id_number: National ID number
            
        Returns:
            Image bytes or None if unavailable
        """
        # TODO: Implement IPRS photo retrieval once ESB confirms photo field
        # For now, return None to trigger 2-way comparison mode
        logger.warning(f"IPRS photo retrieval not yet implemented for ID: {id_number}")
        return None
