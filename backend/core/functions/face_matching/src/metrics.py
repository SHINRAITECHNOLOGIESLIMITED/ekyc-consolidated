"""
CloudWatch Metrics Emitter for Face Matching Verification.

Implements metrics collection for:
- Decision outcomes (APPROVED, MANUAL_REVIEW, REJECTED)
- Comparison latencies
- Quality gate failures
- ROC metrics for UAT threshold tuning

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
metrics = Metrics(namespace="JubileeEKYC/FaceMatching")


class MetricName(Enum):
    """Metric names for face matching."""
    # Decision metrics
    APPROVED_COUNT = "ApprovedCount"
    MANUAL_REVIEW_COUNT = "ManualReviewCount"
    REJECTED_COUNT = "RejectedCount"
    TOTAL_REQUESTS = "TotalRequests"
    
    # Rate metrics
    MANUAL_REVIEW_RATE = "ManualReviewRate"
    APPROVAL_RATE = "ApprovalRate"
    REJECTION_RATE = "RejectionRate"
    
    # Latency metrics
    COMPARISON_LATENCY = "ComparisonLatency"
    TOTAL_PROCESSING_TIME = "TotalProcessingTime"
    IMAGE_ACQUISITION_TIME = "ImageAcquisitionTime"
    PREPROCESSING_TIME = "PreprocessingTime"
    
    # Quality metrics
    QUALITY_GATE_FAILURES = "QualityGateFailures"
    LOW_BRIGHTNESS_FAILURES = "LowBrightnessFailures"
    LOW_SHARPNESS_FAILURES = "LowSharpnessFailures"
    LOW_RESOLUTION_FAILURES = "LowResolutionFailures"
    NO_FACE_DETECTED = "NoFaceDetected"
    MULTIPLE_FACES_DETECTED = "MultipleFacesDetected"
    
    # ROC metrics for UAT
    FALSE_ACCEPT_INDICATOR = "FalseAcceptIndicator"
    FALSE_REJECT_INDICATOR = "FalseRejectIndicator"
    
    # Comparison mode metrics
    THREE_WAY_COMPARISON = "ThreeWayComparison"
    TWO_WAY_COMPARISON = "TwoWayComparison"
    
    # Error metrics
    IPRS_PHOTO_UNAVAILABLE = "IPRSPhotoUnavailable"
    REKOGNITION_ERRORS = "RekognitionErrors"
    PROCESSING_ERRORS = "ProcessingErrors"


@dataclass
class TimingContext:
    """Context manager for timing operations."""
    metric_name: str
    start_time: float = field(default_factory=time.time)
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.time() - self.start_time) * 1000
        emit_latency_metric(self.metric_name, elapsed_ms)
        return False


class MetricsEmitter:
    """
    Emits CloudWatch metrics for face matching operations.
    
    Uses AWS Lambda Powertools for structured metric emission.
    """
    
    def __init__(self):
        self.metrics = metrics
        self._decision_counts = {
            'APPROVED': 0,
            'MANUAL_REVIEW': 0,
            'REJECTED': 0
        }
    
    def emit_decision_metric(self, decision: str, scores: Dict[str, float]) -> None:
        """
        Emit metric for a face matching decision.
        
        Args:
            decision: The decision outcome (APPROVED, MANUAL_REVIEW, REJECTED)
            scores: Dictionary of comparison scores
        """
        try:
            # Emit decision count
            if decision == 'APPROVED':
                self.metrics.add_metric(
                    name=MetricName.APPROVED_COUNT.value,
                    unit=MetricUnit.Count,
                    value=1
                )
            elif decision == 'MANUAL_REVIEW':
                self.metrics.add_metric(
                    name=MetricName.MANUAL_REVIEW_COUNT.value,
                    unit=MetricUnit.Count,
                    value=1
                )
            elif decision == 'REJECTED':
                self.metrics.add_metric(
                    name=MetricName.REJECTED_COUNT.value,
                    unit=MetricUnit.Count,
                    value=1
                )
            
            # Emit total requests
            self.metrics.add_metric(
                name=MetricName.TOTAL_REQUESTS.value,
                unit=MetricUnit.Count,
                value=1
            )
            
            # Add dimensions for detailed analysis
            self.metrics.add_dimension(name="Decision", value=decision)
            
            # Log scores for analysis
            min_score = min(scores.values()) if scores else 0
            self.metrics.add_metadata(key="min_score", value=min_score)
            self.metrics.add_metadata(key="scores", value=scores)
            
            logger.info(f"Emitted decision metric: {decision}", extra={
                "decision": decision,
                "scores": scores,
                "min_score": min_score
            })
            
        except Exception as e:
            logger.error(f"Error emitting decision metric: {e}")
    
    def emit_latency_metric(
        self,
        metric_name: str,
        latency_ms: float,
        comparison_type: Optional[str] = None
    ) -> None:
        """
        Emit latency metric for an operation.
        
        Args:
            metric_name: Name of the metric
            latency_ms: Latency in milliseconds
            comparison_type: Optional comparison type for dimension
        """
        try:
            self.metrics.add_metric(
                name=metric_name,
                unit=MetricUnit.Milliseconds,
                value=latency_ms
            )
            
            if comparison_type:
                self.metrics.add_dimension(name="ComparisonType", value=comparison_type)
            
            logger.debug(f"Emitted latency metric: {metric_name}={latency_ms}ms")
            
        except Exception as e:
            logger.error(f"Error emitting latency metric: {e}")
    
    def emit_quality_failure(
        self,
        failure_type: str,
        image_source: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Emit metric for quality gate failure.
        
        Args:
            failure_type: Type of quality failure
            image_source: Source of the image (SELFIE, ID_DOCUMENT, IPRS)
            details: Optional failure details
        """
        try:
            # Map failure type to metric name
            metric_map = {
                'low_brightness': MetricName.LOW_BRIGHTNESS_FAILURES.value,
                'low_sharpness': MetricName.LOW_SHARPNESS_FAILURES.value,
                'low_resolution': MetricName.LOW_RESOLUTION_FAILURES.value,
                'no_face': MetricName.NO_FACE_DETECTED.value,
                'multiple_faces': MetricName.MULTIPLE_FACES_DETECTED.value
            }
            
            metric_name = metric_map.get(failure_type, MetricName.QUALITY_GATE_FAILURES.value)
            
            self.metrics.add_metric(
                name=metric_name,
                unit=MetricUnit.Count,
                value=1
            )
            
            self.metrics.add_dimension(name="ImageSource", value=image_source)
            self.metrics.add_dimension(name="FailureType", value=failure_type)
            
            if details:
                self.metrics.add_metadata(key="failure_details", value=details)
            
            logger.warning(f"Quality gate failure: {failure_type} for {image_source}", extra={
                "failure_type": failure_type,
                "image_source": image_source,
                "details": details
            })
            
        except Exception as e:
            logger.error(f"Error emitting quality failure metric: {e}")
    
    def emit_comparison_mode(self, mode: str) -> None:
        """
        Emit metric for comparison mode used.
        
        Args:
            mode: Comparison mode (THREE_WAY or TWO_WAY)
        """
        try:
            if mode == 'THREE_WAY':
                self.metrics.add_metric(
                    name=MetricName.THREE_WAY_COMPARISON.value,
                    unit=MetricUnit.Count,
                    value=1
                )
            else:
                self.metrics.add_metric(
                    name=MetricName.TWO_WAY_COMPARISON.value,
                    unit=MetricUnit.Count,
                    value=1
                )
            
            logger.info(f"Comparison mode: {mode}")
            
        except Exception as e:
            logger.error(f"Error emitting comparison mode metric: {e}")
    
    def emit_roc_indicator(
        self,
        indicator_type: str,
        decision: str,
        scores: Dict[str, float],
        thresholds: Dict[str, float]
    ) -> None:
        """
        Emit ROC indicator for UAT threshold tuning.
        
        This logs potential false accepts/rejects for later analysis.
        
        Args:
            indicator_type: 'false_accept' or 'false_reject'
            decision: The actual decision made
            scores: The comparison scores
            thresholds: The thresholds used
        """
        try:
            if indicator_type == 'false_accept':
                self.metrics.add_metric(
                    name=MetricName.FALSE_ACCEPT_INDICATOR.value,
                    unit=MetricUnit.Count,
                    value=1
                )
            elif indicator_type == 'false_reject':
                self.metrics.add_metric(
                    name=MetricName.FALSE_REJECT_INDICATOR.value,
                    unit=MetricUnit.Count,
                    value=1
                )
            
            # Log detailed info for analysis
            logger.info(f"ROC indicator: {indicator_type}", extra={
                "indicator_type": indicator_type,
                "decision": decision,
                "scores": scores,
                "thresholds": thresholds
            })
            
        except Exception as e:
            logger.error(f"Error emitting ROC indicator: {e}")
    
    def emit_error_metric(self, error_type: str, error_message: str) -> None:
        """
        Emit metric for processing errors.
        
        Args:
            error_type: Type of error
            error_message: Error message
        """
        try:
            metric_map = {
                'iprs_unavailable': MetricName.IPRS_PHOTO_UNAVAILABLE.value,
                'rekognition_error': MetricName.REKOGNITION_ERRORS.value
            }
            
            metric_name = metric_map.get(error_type, MetricName.PROCESSING_ERRORS.value)
            
            self.metrics.add_metric(
                name=metric_name,
                unit=MetricUnit.Count,
                value=1
            )
            
            self.metrics.add_dimension(name="ErrorType", value=error_type)
            self.metrics.add_metadata(key="error_message", value=error_message)
            
            logger.error(f"Error metric: {error_type} - {error_message}")
            
        except Exception as e:
            logger.error(f"Error emitting error metric: {e}")
    
    def flush(self) -> None:
        """Flush all pending metrics to CloudWatch."""
        try:
            # Lambda Powertools handles flushing automatically
            # but we can force it if needed
            logger.debug("Metrics flushed")
        except Exception as e:
            logger.error(f"Error flushing metrics: {e}")


# Module-level convenience functions
_emitter = MetricsEmitter()


def emit_decision_metric(decision: str, scores: Dict[str, float]) -> None:
    """Emit decision metric."""
    _emitter.emit_decision_metric(decision, scores)


def emit_latency_metric(
    metric_name: str,
    latency_ms: float,
    comparison_type: Optional[str] = None
) -> None:
    """Emit latency metric."""
    _emitter.emit_latency_metric(metric_name, latency_ms, comparison_type)


def emit_quality_failure(
    failure_type: str,
    image_source: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """Emit quality failure metric."""
    _emitter.emit_quality_failure(failure_type, image_source, details)


def emit_comparison_mode(mode: str) -> None:
    """Emit comparison mode metric."""
    _emitter.emit_comparison_mode(mode)


def emit_roc_indicator(
    indicator_type: str,
    decision: str,
    scores: Dict[str, float],
    thresholds: Dict[str, float]
) -> None:
    """Emit ROC indicator for UAT."""
    _emitter.emit_roc_indicator(indicator_type, decision, scores, thresholds)


def emit_error_metric(error_type: str, error_message: str) -> None:
    """Emit error metric."""
    _emitter.emit_error_metric(error_type, error_message)


def time_operation(metric_name: str) -> TimingContext:
    """
    Context manager for timing operations.
    
    Usage:
        with time_operation("ComparisonLatency") as timer:
            # do work
    """
    return TimingContext(metric_name)
