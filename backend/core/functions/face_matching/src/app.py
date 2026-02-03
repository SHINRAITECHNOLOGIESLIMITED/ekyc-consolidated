"""
Face Matching Lambda Handler

Implements 3-way face comparison for identity verification using AWS Rekognition.
Compares customer selfie, ID document photo, and IPRS photo.
"""

import json
import os
import time
from typing import Optional

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

from models import (
    FaceMatchingRequest,
    FaceMatchingResult,
    FaceMatchingError,
    MatchStatus,
    ComparisonMode,
)
from image_preprocessor import ImagePreprocessor
from face_comparator import FaceComparator
from decision_calculator import DecisionCalculator
from image_acquisition import ImageAcquisition
from result_storage import ResultStorage
from config import ConfigManager
from metrics import (
    emit_decision_metric,
    emit_latency_metric,
    emit_quality_failure,
    emit_comparison_mode,
    emit_error_metric,
    time_operation,
    MetricName
)
from manual_review import create_review_task

logger = Logger()
tracer = Tracer()
metrics = Metrics(namespace="JubileeEKYC/FaceMatching")


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    """
    Main Lambda handler for face matching requests.
    
    Args:
        event: API Gateway event with face matching request
        context: Lambda context
        
    Returns:
        API Gateway response with match results
    """
    start_time = time.time()
    
    try:
        # Parse request
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        
        # Validate request
        request = _parse_request(body)
        if isinstance(request, dict):  # Error response
            return request
        
        # Process face matching
        result = process_face_matching(request)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Emit metrics
        _emit_metrics(result, processing_time_ms)
        
        return _make_response(200, {
            'success': True,
            'action': 'face_matching',
            'data': result.to_dict()
        })
        
    except Exception as e:
        logger.exception(f"Face matching error: {e}")
        return _make_response(500, {
            'success': False,
            'action': 'face_matching',
            'error': {
                'error_code': 'INTERNAL_ERROR',
                'message': str(e)
            }
        })


def process_face_matching(request: FaceMatchingRequest) -> FaceMatchingResult:
    """
    Process a face matching verification request.
    
    Args:
        request: FaceMatchingRequest with customer_id, photo references
        
    Returns:
        FaceMatchingResult with scores, status, and quality metrics
    """
    start_time = time.time()
    
    # Initialize components
    config = ConfigManager()
    preprocessor = ImagePreprocessor()
    comparator = FaceComparator()
    decision_calc = DecisionCalculator(
        approval_threshold=config.approval_threshold,
        rejection_threshold=config.rejection_threshold
    )
    acquisition = ImageAcquisition()
    storage = ResultStorage()
    
    # Acquire images from all sources
    logger.info("Acquiring images from sources")
    images = acquisition.acquire_all_images(
        customer_photo_key=request.customer_photo_key,
        id_document_key=request.id_document_key,
        iprs_id_number=request.iprs_id_number
    )
    
    # Preprocess images
    logger.info("Preprocessing images")
    preprocessed = {}
    quality_metrics = {}
    
    for source, image_bytes in images.items():
        if image_bytes is not None:
            result = preprocessor.preprocess(image_bytes, source)
            preprocessed[source] = result.image_bytes
            quality_metrics[source] = result.quality_metrics
    
    # Determine comparison mode
    comparison_mode = ComparisonMode.THREE_WAY if 'iprs' in preprocessed else ComparisonMode.TWO_WAY
    
    # Execute comparisons
    logger.info(f"Executing {comparison_mode.value} comparison")
    comparison_results = comparator.compare_faces_parallel(preprocessed, comparison_mode)
    
    # Calculate decision
    decision = decision_calc.calculate_decision(comparison_results, comparison_mode)
    
    # Build result
    processing_time_ms = (time.time() - start_time) * 1000
    
    result = FaceMatchingResult(
        request_id=request.request_id,
        customer_id=request.customer_id,
        match_status=decision.status,
        comparison_mode=comparison_mode,
        comparisons=list(comparison_results.values()),
        quality_metrics=quality_metrics,
        decision=decision,
        thresholds_used={
            'approval': config.approval_threshold,
            'rejection': config.rejection_threshold
        },
        processing_time_ms=processing_time_ms
    )
    
    # Store result
    storage.store_result(result, request)
    
    # Update KYC status
    storage.update_kyc_status(request.customer_id, decision.status)
    
    # Create manual review task if needed
    if decision.status == MatchStatus.MANUAL_REVIEW:
        try:
            scores = {c.comparison_name: c.similarity_score for c in result.comparisons}
            create_review_task(
                request_id=request.request_id,
                customer_id=request.customer_id,
                comparison_scores=scores,
                quality_metrics=quality_metrics,
                thresholds_used=result.thresholds_used,
                comparison_mode=comparison_mode.value,
                customer_photo_key=request.customer_photo_key,
                id_document_key=request.id_document_key,
                iprs_photo_available='iprs' in preprocessed
            )
            logger.info("Created manual review task for request", extra={
                "request_id": request.request_id,
                "customer_id": request.customer_id
            })
        except Exception as e:
            logger.warning(f"Failed to create manual review task: {e}")
    
    return result


def _parse_request(body: dict) -> FaceMatchingRequest | dict:
    """Parse and validate the incoming request."""
    required_fields = ['customer_id', 'customer_photo_key', 'id_document_key', 'iprs_id_number']
    
    missing = [f for f in required_fields if not body.get(f)]
    if missing:
        return _make_response(400, {
            'success': False,
            'error': {
                'error_code': 'VALIDATION_ERROR',
                'message': f'Missing required fields: {", ".join(missing)}',
                'details': {'missing_fields': missing}
            }
        })
    
    return FaceMatchingRequest(
        customer_id=body['customer_id'],
        customer_photo_key=body['customer_photo_key'],
        id_document_key=body['id_document_key'],
        iprs_id_number=body['iprs_id_number'],
        request_id=body.get('request_id')
    )


def _emit_metrics(result: FaceMatchingResult, processing_time_ms: float):
    """Emit CloudWatch metrics for the face matching operation."""
    # Extract scores for metrics
    scores = {}
    for comparison in result.comparisons:
        scores[comparison.comparison_name] = comparison.similarity_score
    
    # Emit decision metric with scores
    emit_decision_metric(result.match_status.value, scores)
    
    # Emit latency metric
    emit_latency_metric(
        MetricName.TOTAL_PROCESSING_TIME.value,
        processing_time_ms
    )
    
    # Emit comparison mode metric
    emit_comparison_mode(result.comparison_mode.value)
    
    # Legacy metrics for backward compatibility
    metrics.add_metric(
        name=f"FaceMatching.{result.match_status.value}",
        unit=MetricUnit.Count,
        value=1
    )
    
    metrics.add_metric(
        name="FaceMatching.ProcessingTime",
        unit=MetricUnit.Milliseconds,
        value=processing_time_ms
    )
    
    # Manual review percentage (tracked separately)
    if result.match_status == MatchStatus.MANUAL_REVIEW:
        metrics.add_metric(
            name="FaceMatching.ManualReviewCount",
            unit=MetricUnit.Count,
            value=1
        )


def _make_response(status_code: int, body: dict) -> dict:
    """Create API Gateway response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Api-Key',
            'Access-Control-Allow-Methods': 'POST, OPTIONS'
        },
        'body': json.dumps(body)
    }
