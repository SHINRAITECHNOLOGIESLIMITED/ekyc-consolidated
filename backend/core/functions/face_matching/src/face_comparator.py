"""
Face Comparator for Face Matching Service

Executes AWS Rekognition CompareFaces API calls with retry logic.
"""

import time
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger

from models import (
    ComparisonResult,
    ComparisonMode,
    NoFaceDetectedError,
    MultipleFacesError,
    ComparisonError,
)

logger = Logger()

# Retry configuration
MAX_RETRIES = 1
BASE_DELAY_MS = 100
MAX_DELAY_MS = 1000
RETRYABLE_ERRORS = [
    'ThrottlingException',
    'ProvisionedThroughputExceededException',
    'ServiceUnavailableException'
]

# Comparison names
COMPARISON_CUSTOMER_VS_ID = 'customer_vs_id_document'
COMPARISON_CUSTOMER_VS_IPRS = 'customer_vs_iprs'
COMPARISON_ID_VS_IPRS = 'id_document_vs_iprs'


class FaceComparator:
    """Executes face comparisons using AWS Rekognition."""
    
    def __init__(self, rekognition_client: Optional[boto3.client] = None):
        self._client = rekognition_client or boto3.client('rekognition')
    
    def compare_faces(
        self,
        source_image: bytes,
        target_image: bytes,
        comparison_name: str,
        similarity_threshold: float = 0.0
    ) -> ComparisonResult:
        """
        Compare two face images using Rekognition.
        
        Args:
            source_image: Source face image bytes
            target_image: Target face image bytes
            comparison_name: Name for this comparison (e.g., 'customer_vs_id_document')
            similarity_threshold: Minimum similarity to return matches
            
        Returns:
            ComparisonResult with similarity score and confidence
            
        Raises:
            NoFaceDetectedError: If no face found in either image
            MultipleFacesError: If multiple faces detected
            ComparisonError: If Rekognition API fails
        """
        return self._execute_with_retry(
            source_image,
            target_image,
            comparison_name,
            similarity_threshold
        )
    
    def _execute_with_retry(
        self,
        source_image: bytes,
        target_image: bytes,
        comparison_name: str,
        similarity_threshold: float
    ) -> ComparisonResult:
        """Execute comparison with retry logic for transient errors."""
        last_error = None
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                return self._do_compare(
                    source_image,
                    target_image,
                    comparison_name,
                    similarity_threshold
                )
            except ClientError as e:
                error_code = e.response['Error']['Code']
                
                if error_code in RETRYABLE_ERRORS and attempt < MAX_RETRIES:
                    delay = min(BASE_DELAY_MS * (2 ** attempt), MAX_DELAY_MS) / 1000.0
                    logger.warning(f"Retryable error {error_code}, retrying in {delay}s")
                    time.sleep(delay)
                    last_error = e
                    continue
                
                # Handle specific error codes
                if error_code == 'InvalidParameterException':
                    error_msg = e.response['Error']['Message']
                    if 'no face' in error_msg.lower():
                        # Determine which image failed
                        source = comparison_name.split('_vs_')[0]
                        raise NoFaceDetectedError(source)
                    raise ComparisonError(comparison_name, error_msg)
                
                raise ComparisonError(comparison_name, str(e))
        
        # If we exhausted retries
        raise ComparisonError(comparison_name, f"Failed after {MAX_RETRIES + 1} attempts: {last_error}")
    
    def _do_compare(
        self,
        source_image: bytes,
        target_image: bytes,
        comparison_name: str,
        similarity_threshold: float
    ) -> ComparisonResult:
        """Execute the actual Rekognition CompareFaces call."""
        response = self._client.compare_faces(
            SourceImage={'Bytes': source_image},
            TargetImage={'Bytes': target_image},
            SimilarityThreshold=similarity_threshold
        )
        
        # Check for face matches
        face_matches = response.get('FaceMatches', [])
        
        if not face_matches:
            # No match found - return 0 similarity
            return ComparisonResult(
                comparison_name=comparison_name,
                similarity_score=0.0,
                confidence=0.0,
                source_face_confidence=response.get('SourceImageFace', {}).get('Confidence', 0.0),
                target_face_confidence=0.0
            )
        
        # Get the best match
        best_match = face_matches[0]
        
        return ComparisonResult(
            comparison_name=comparison_name,
            similarity_score=best_match.get('Similarity', 0.0),
            confidence=best_match.get('Face', {}).get('Confidence', 0.0),
            source_face_confidence=response.get('SourceImageFace', {}).get('Confidence', 0.0),
            target_face_confidence=best_match.get('Face', {}).get('Confidence', 0.0)
        )
    
    def compare_faces_parallel(
        self,
        images: dict[str, bytes],
        comparison_mode: ComparisonMode
    ) -> dict[str, ComparisonResult]:
        """
        Execute multiple face comparisons in parallel.
        
        Args:
            images: Dict mapping source type to image bytes
                   {'customer': bytes, 'id_document': bytes, 'iprs': bytes}
            comparison_mode: THREE_WAY or TWO_WAY
            
        Returns:
            Dict mapping comparison_name to ComparisonResult
        """
        comparisons_to_run = []
        
        # Always run customer vs ID document
        if 'customer' in images and 'id_document' in images:
            comparisons_to_run.append((
                images['customer'],
                images['id_document'],
                COMPARISON_CUSTOMER_VS_ID
            ))
        
        # Run IPRS comparisons only in 3-way mode
        if comparison_mode == ComparisonMode.THREE_WAY and 'iprs' in images:
            if 'customer' in images:
                comparisons_to_run.append((
                    images['customer'],
                    images['iprs'],
                    COMPARISON_CUSTOMER_VS_IPRS
                ))
            if 'id_document' in images:
                comparisons_to_run.append((
                    images['id_document'],
                    images['iprs'],
                    COMPARISON_ID_VS_IPRS
                ))
        
        # Execute comparisons in parallel
        results = {}
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    self.compare_faces,
                    source,
                    target,
                    name
                ): name
                for source, target, name in comparisons_to_run
            }
            
            for future in as_completed(futures):
                comparison_name = futures[future]
                try:
                    result = future.result()
                    results[comparison_name] = result
                except Exception as e:
                    logger.error(f"Comparison {comparison_name} failed: {e}")
                    raise
        
        return results
