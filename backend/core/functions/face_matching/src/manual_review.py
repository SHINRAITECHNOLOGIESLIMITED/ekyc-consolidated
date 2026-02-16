"""
Manual Review Workflow for Face Matching Verification.

Implements:
- Review task queue integration
- SLA tracking
- Reviewer audit logging

Requirements: 11.1, 11.2, 11.3, 11.4, 11.6
"""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum

import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit

logger = Logger()
metrics = Metrics(namespace="JubileeEKYC/FaceMatching")


class ReviewStatus(Enum):
    """Status of a manual review task."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"


class ReviewPriority(Enum):
    """Priority levels for review tasks."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


@dataclass
class ReviewTask:
    """Manual review task for face matching."""
    task_id: str
    request_id: str
    customer_id: str
    created_at: str
    status: ReviewStatus = ReviewStatus.PENDING
    priority: ReviewPriority = ReviewPriority.MEDIUM
    
    # Face matching data
    comparison_scores: Dict[str, float] = field(default_factory=dict)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    thresholds_used: Dict[str, float] = field(default_factory=dict)
    comparison_mode: str = "THREE_WAY"
    
    # Image references
    customer_photo_key: str = ""
    id_document_key: str = ""
    iprs_photo_available: bool = False
    
    # Review metadata
    assigned_to: Optional[str] = None
    assigned_at: Optional[str] = None
    sla_deadline: Optional[str] = None
    
    # Resolution data
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_decision: Optional[str] = None
    resolution_rationale: Optional[str] = None
    
    # TTL for DynamoDB (30 days)
    ttl: int = field(default_factory=lambda: int((datetime.utcnow() + timedelta(days=30)).timestamp()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReviewTask':
        """Create from dictionary."""
        data['status'] = ReviewStatus(data.get('status', 'PENDING'))
        data['priority'] = ReviewPriority(data.get('priority', 'MEDIUM'))
        return cls(**data)


class ManualReviewManager:
    """
    Manages manual review workflow for face matching.
    
    Uses DynamoDB for task storage and CloudWatch for metrics.
    """
    
    # SLA thresholds (in hours)
    SLA_URGENT = 1
    SLA_HIGH = 4
    SLA_MEDIUM = 24
    SLA_LOW = 72
    
    def __init__(self):
        self.dynamodb = boto3.client('dynamodb')
        self.table_name = os.environ.get('MANUAL_REVIEW_TABLE', 'FaceMatchingManualReview')
    
    def create_review_task(
        self,
        request_id: str,
        customer_id: str,
        comparison_scores: Dict[str, float],
        quality_metrics: Dict[str, Any],
        thresholds_used: Dict[str, float],
        comparison_mode: str,
        customer_photo_key: str,
        id_document_key: str,
        iprs_photo_available: bool
    ) -> ReviewTask:
        """
        Create a new manual review task.
        
        Requirement 11.1: Create review task when Match_Status is MANUAL_REVIEW
        Requirement 11.2: Include all scores, image references, quality metrics
        
        Args:
            request_id: Original face matching request ID
            customer_id: Customer identifier
            comparison_scores: Dictionary of comparison scores
            quality_metrics: Quality metrics for each image
            thresholds_used: Thresholds used for decision
            comparison_mode: THREE_WAY or TWO_WAY
            customer_photo_key: S3 key for customer photo
            id_document_key: S3 key for ID document
            iprs_photo_available: Whether IPRS photo was available
            
        Returns:
            Created ReviewTask
        """
        # Determine priority based on scores
        priority = self._calculate_priority(comparison_scores, thresholds_used)
        
        # Calculate SLA deadline
        sla_deadline = self._calculate_sla_deadline(priority)
        
        task = ReviewTask(
            task_id=str(uuid.uuid4()),
            request_id=request_id,
            customer_id=customer_id,
            created_at=datetime.utcnow().isoformat(),
            status=ReviewStatus.PENDING,
            priority=priority,
            comparison_scores=comparison_scores,
            quality_metrics=quality_metrics,
            thresholds_used=thresholds_used,
            comparison_mode=comparison_mode,
            customer_photo_key=customer_photo_key,
            id_document_key=id_document_key,
            iprs_photo_available=iprs_photo_available,
            sla_deadline=sla_deadline
        )
        
        # Store in DynamoDB
        self._store_task(task)
        
        # Emit metrics
        self._emit_task_created_metrics(task)
        
        logger.info("Created manual review task", extra={
            "task_id": task.task_id,
            "request_id": request_id,
            "customer_id": customer_id,
            "priority": priority.value,
            "sla_deadline": sla_deadline
        })
        
        return task
    
    def _calculate_priority(
        self,
        scores: Dict[str, float],
        thresholds: Dict[str, float]
    ) -> ReviewPriority:
        """
        Calculate review priority based on scores.
        
        Higher priority for scores closer to rejection threshold.
        """
        if not scores:
            return ReviewPriority.MEDIUM
        
        min_score = min(scores.values())
        rejection_threshold = thresholds.get('rejection', 50.0)
        approval_threshold = thresholds.get('approval', 70.0)
        
        # Calculate how close to rejection
        range_size = approval_threshold - rejection_threshold
        if range_size <= 0:
            return ReviewPriority.MEDIUM
        
        position = (min_score - rejection_threshold) / range_size
        
        if position < 0.25:  # Very close to rejection
            return ReviewPriority.URGENT
        elif position < 0.5:
            return ReviewPriority.HIGH
        elif position < 0.75:
            return ReviewPriority.MEDIUM
        else:
            return ReviewPriority.LOW
    
    def _calculate_sla_deadline(self, priority: ReviewPriority) -> str:
        """Calculate SLA deadline based on priority."""
        sla_hours = {
            ReviewPriority.URGENT: self.SLA_URGENT,
            ReviewPriority.HIGH: self.SLA_HIGH,
            ReviewPriority.MEDIUM: self.SLA_MEDIUM,
            ReviewPriority.LOW: self.SLA_LOW
        }
        
        hours = sla_hours.get(priority, self.SLA_MEDIUM)
        deadline = datetime.utcnow() + timedelta(hours=hours)
        return deadline.isoformat()
    
    def _store_task(self, task: ReviewTask) -> None:
        """Store review task in DynamoDB."""
        try:
            item = {
                'task_id': {'S': task.task_id},
                'request_id': {'S': task.request_id},
                'customer_id': {'S': task.customer_id},
                'created_at': {'S': task.created_at},
                'status': {'S': task.status.value},
                'priority': {'S': task.priority.value},
                'comparison_scores': {'S': json.dumps(task.comparison_scores)},
                'quality_metrics': {'S': json.dumps(task.quality_metrics)},
                'thresholds_used': {'S': json.dumps(task.thresholds_used)},
                'comparison_mode': {'S': task.comparison_mode},
                'customer_photo_key': {'S': task.customer_photo_key},
                'id_document_key': {'S': task.id_document_key},
                'iprs_photo_available': {'BOOL': task.iprs_photo_available},
                'ttl': {'N': str(task.ttl)}
            }
            
            if task.sla_deadline:
                item['sla_deadline'] = {'S': task.sla_deadline}
            
            self.dynamodb.put_item(
                TableName=self.table_name,
                Item=item
            )
            
        except ClientError as e:
            logger.error(f"Error storing review task: {e}")
            raise
    
    def resolve_task(
        self,
        task_id: str,
        reviewer_id: str,
        decision: str,
        rationale: str
    ) -> ReviewTask:
        """
        Resolve a manual review task.
        
        Requirement 11.6: Log manual review decisions with reviewer ID
        
        Args:
            task_id: Task to resolve
            reviewer_id: ID of the reviewer
            decision: APPROVED or REJECTED
            rationale: Reason for the decision
            
        Returns:
            Updated ReviewTask
        """
        resolved_at = datetime.utcnow().isoformat()
        
        try:
            # Update task in DynamoDB
            response = self.dynamodb.update_item(
                TableName=self.table_name,
                Key={'task_id': {'S': task_id}},
                UpdateExpression="""
                    SET #status = :status,
                        resolved_at = :resolved_at,
                        resolved_by = :resolved_by,
                        resolution_decision = :decision,
                        resolution_rationale = :rationale
                """,
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': {'S': ReviewStatus.APPROVED.value if decision == 'APPROVED' else ReviewStatus.REJECTED.value},
                    ':resolved_at': {'S': resolved_at},
                    ':resolved_by': {'S': reviewer_id},
                    ':decision': {'S': decision},
                    ':rationale': {'S': rationale}
                },
                ReturnValues='ALL_NEW'
            )
            
            # Log audit trail
            self._log_review_decision(
                task_id=task_id,
                reviewer_id=reviewer_id,
                decision=decision,
                rationale=rationale,
                resolved_at=resolved_at
            )
            
            # Emit metrics
            self._emit_resolution_metrics(task_id, decision)
            
            logger.info("Resolved manual review task", extra={
                "task_id": task_id,
                "reviewer_id": reviewer_id,
                "decision": decision
            })
            
            # Return updated task (simplified)
            return self.get_task(task_id)
            
        except ClientError as e:
            logger.error(f"Error resolving review task: {e}")
            raise
    
    def get_task(self, task_id: str) -> Optional[ReviewTask]:
        """Get a review task by ID."""
        try:
            response = self.dynamodb.get_item(
                TableName=self.table_name,
                Key={'task_id': {'S': task_id}}
            )
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            return ReviewTask(
                task_id=item['task_id']['S'],
                request_id=item['request_id']['S'],
                customer_id=item['customer_id']['S'],
                created_at=item['created_at']['S'],
                status=ReviewStatus(item['status']['S']),
                priority=ReviewPriority(item['priority']['S']),
                comparison_scores=json.loads(item.get('comparison_scores', {}).get('S', '{}')),
                quality_metrics=json.loads(item.get('quality_metrics', {}).get('S', '{}')),
                thresholds_used=json.loads(item.get('thresholds_used', {}).get('S', '{}')),
                comparison_mode=item.get('comparison_mode', {}).get('S', 'THREE_WAY'),
                customer_photo_key=item.get('customer_photo_key', {}).get('S', ''),
                id_document_key=item.get('id_document_key', {}).get('S', ''),
                iprs_photo_available=item.get('iprs_photo_available', {}).get('BOOL', False),
                sla_deadline=item.get('sla_deadline', {}).get('S'),
                resolved_at=item.get('resolved_at', {}).get('S'),
                resolved_by=item.get('resolved_by', {}).get('S'),
                resolution_decision=item.get('resolution_decision', {}).get('S'),
                resolution_rationale=item.get('resolution_rationale', {}).get('S')
            )
            
        except ClientError as e:
            logger.error(f"Error getting review task: {e}")
            return None
    
    def get_pending_tasks(self, limit: int = 100) -> List[ReviewTask]:
        """Get pending review tasks ordered by priority and SLA."""
        try:
            # Note: In production, use a GSI on status for efficient querying
            response = self.dynamodb.scan(
                TableName=self.table_name,
                FilterExpression='#status = :pending',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':pending': {'S': ReviewStatus.PENDING.value}},
                Limit=limit
            )
            
            tasks = []
            for item in response.get('Items', []):
                task = self.get_task(item['task_id']['S'])
                if task:
                    tasks.append(task)
            
            # Sort by priority (URGENT first) then by SLA deadline
            priority_order = {
                ReviewPriority.URGENT: 0,
                ReviewPriority.HIGH: 1,
                ReviewPriority.MEDIUM: 2,
                ReviewPriority.LOW: 3
            }
            
            tasks.sort(key=lambda t: (
                priority_order.get(t.priority, 2),
                t.sla_deadline or ''
            ))
            
            return tasks
            
        except ClientError as e:
            logger.error(f"Error getting pending tasks: {e}")
            return []
    
    def _log_review_decision(
        self,
        task_id: str,
        reviewer_id: str,
        decision: str,
        rationale: str,
        resolved_at: str
    ) -> None:
        """
        Log review decision for audit trail.
        
        Requirement 11.6: Log manual review decisions with reviewer ID,
        timestamp, and decision rationale.
        """
        logger.info("Manual review decision", extra={
            "event_type": "MANUAL_REVIEW_DECISION",
            "task_id": task_id,
            "reviewer_id": reviewer_id,
            "decision": decision,
            "rationale": rationale,
            "resolved_at": resolved_at,
            "audit_timestamp": datetime.utcnow().isoformat()
        })
    
    def _emit_task_created_metrics(self, task: ReviewTask) -> None:
        """Emit metrics when a review task is created."""
        metrics.add_metric(
            name="ManualReview.TaskCreated",
            unit=MetricUnit.Count,
            value=1
        )
        
        metrics.add_metric(
            name=f"ManualReview.Priority.{task.priority.value}",
            unit=MetricUnit.Count,
            value=1
        )
    
    def _emit_resolution_metrics(self, task_id: str, decision: str) -> None:
        """
        Emit metrics when a task is resolved.
        
        Requirement 11.3, 11.4: Emit metrics for queue depth and resolution time.
        """
        metrics.add_metric(
            name="ManualReview.TaskResolved",
            unit=MetricUnit.Count,
            value=1
        )
        
        metrics.add_metric(
            name=f"ManualReview.Decision.{decision}",
            unit=MetricUnit.Count,
            value=1
        )
    
    def get_queue_metrics(self) -> Dict[str, Any]:
        """
        Get current queue metrics.
        
        Requirement 11.3, 11.4: Track queue depth and SLA compliance.
        """
        try:
            # Count pending tasks
            response = self.dynamodb.scan(
                TableName=self.table_name,
                FilterExpression='#status = :pending',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':pending': {'S': ReviewStatus.PENDING.value}},
                Select='COUNT'
            )
            
            pending_count = response.get('Count', 0)
            
            # Count SLA breaches
            now = datetime.utcnow().isoformat()
            breach_response = self.dynamodb.scan(
                TableName=self.table_name,
                FilterExpression='#status = :pending AND sla_deadline < :now',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':pending': {'S': ReviewStatus.PENDING.value},
                    ':now': {'S': now}
                },
                Select='COUNT'
            )
            
            sla_breaches = breach_response.get('Count', 0)
            
            # Emit metrics
            metrics.add_metric(
                name="ManualReview.QueueDepth",
                unit=MetricUnit.Count,
                value=pending_count
            )
            
            metrics.add_metric(
                name="ManualReview.SLABreaches",
                unit=MetricUnit.Count,
                value=sla_breaches
            )
            
            return {
                'pending_count': pending_count,
                'sla_breaches': sla_breaches,
                'timestamp': now
            }
            
        except ClientError as e:
            logger.error(f"Error getting queue metrics: {e}")
            return {'error': str(e)}


# Module-level singleton
_manager = ManualReviewManager()


def create_review_task(
    request_id: str,
    customer_id: str,
    comparison_scores: Dict[str, float],
    quality_metrics: Dict[str, Any],
    thresholds_used: Dict[str, float],
    comparison_mode: str,
    customer_photo_key: str,
    id_document_key: str,
    iprs_photo_available: bool
) -> ReviewTask:
    """Create a new manual review task."""
    return _manager.create_review_task(
        request_id=request_id,
        customer_id=customer_id,
        comparison_scores=comparison_scores,
        quality_metrics=quality_metrics,
        thresholds_used=thresholds_used,
        comparison_mode=comparison_mode,
        customer_photo_key=customer_photo_key,
        id_document_key=id_document_key,
        iprs_photo_available=iprs_photo_available
    )


def resolve_task(
    task_id: str,
    reviewer_id: str,
    decision: str,
    rationale: str
) -> ReviewTask:
    """Resolve a manual review task."""
    return _manager.resolve_task(task_id, reviewer_id, decision, rationale)


def get_pending_tasks(limit: int = 100) -> List[ReviewTask]:
    """Get pending review tasks."""
    return _manager.get_pending_tasks(limit)


def get_queue_metrics() -> Dict[str, Any]:
    """Get current queue metrics."""
    return _manager.get_queue_metrics()
