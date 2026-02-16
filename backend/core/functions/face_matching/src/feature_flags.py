"""
Feature Flags for Face Matching Verification.

Provides runtime configuration for:
- Threshold values (approval, rejection)
- Aggregation rule selection
- Third comparison toggle (ID ↔ IPRS)
- Configuration change logging

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger

logger = Logger()


class AggregationRule(Enum):
    """Aggregation rules for 3-way comparison scoring."""
    FAIL_FAST = "fail_fast"  # Minimum score determines outcome (default)
    WEIGHTED_AVERAGE = "weighted_average"  # Weighted average of all scores
    MAJORITY = "majority"  # Majority of comparisons must pass


@dataclass
class FeatureFlagConfig:
    """Configuration from feature flags."""
    approval_threshold: float
    rejection_threshold: float
    aggregation_rule: AggregationRule
    enable_third_comparison: bool
    enable_quality_gates: bool
    enable_roc_logging: bool
    last_updated: str
    version: str


class FeatureFlagManager:
    """
    Manages feature flags for face matching via SSM Parameter Store.
    
    Supports runtime configuration changes without code deployment.
    """
    
    # SSM Parameter paths
    PARAM_PREFIX = "/ekyc/face-matching"
    PARAM_APPROVAL_THRESHOLD = f"{PARAM_PREFIX}/approval-threshold"
    PARAM_REJECTION_THRESHOLD = f"{PARAM_PREFIX}/rejection-threshold"
    PARAM_AGGREGATION_RULE = f"{PARAM_PREFIX}/aggregation-rule"
    PARAM_ENABLE_THIRD_COMPARISON = f"{PARAM_PREFIX}/enable-third-comparison"
    PARAM_ENABLE_QUALITY_GATES = f"{PARAM_PREFIX}/enable-quality-gates"
    PARAM_ENABLE_ROC_LOGGING = f"{PARAM_PREFIX}/enable-roc-logging"
    PARAM_CONFIG_VERSION = f"{PARAM_PREFIX}/config-version"
    
    # Default values
    DEFAULT_APPROVAL_THRESHOLD = 70.0
    DEFAULT_REJECTION_THRESHOLD = 50.0
    DEFAULT_AGGREGATION_RULE = AggregationRule.FAIL_FAST
    DEFAULT_ENABLE_THIRD_COMPARISON = True
    DEFAULT_ENABLE_QUALITY_GATES = True
    DEFAULT_ENABLE_ROC_LOGGING = True
    
    def __init__(self):
        self.ssm = boto3.client('ssm')
        self._cache: Optional[FeatureFlagConfig] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 60  # Cache for 1 minute
    
    def get_config(self, force_refresh: bool = False) -> FeatureFlagConfig:
        """
        Get current feature flag configuration.
        
        Uses caching to reduce SSM API calls.
        
        Args:
            force_refresh: Force refresh from SSM
            
        Returns:
            FeatureFlagConfig with current settings
        """
        # Check cache
        if not force_refresh and self._is_cache_valid():
            return self._cache
        
        # Fetch from SSM
        config = self._fetch_config()
        
        # Update cache
        self._cache = config
        self._cache_timestamp = datetime.utcnow()
        
        return config
    
    def _is_cache_valid(self) -> bool:
        """Check if cached config is still valid."""
        if self._cache is None or self._cache_timestamp is None:
            return False
        
        elapsed = (datetime.utcnow() - self._cache_timestamp).total_seconds()
        return elapsed < self._cache_ttl_seconds
    
    def _fetch_config(self) -> FeatureFlagConfig:
        """Fetch configuration from SSM Parameter Store."""
        try:
            # Fetch all parameters in one call
            response = self.ssm.get_parameters(
                Names=[
                    self.PARAM_APPROVAL_THRESHOLD,
                    self.PARAM_REJECTION_THRESHOLD,
                    self.PARAM_AGGREGATION_RULE,
                    self.PARAM_ENABLE_THIRD_COMPARISON,
                    self.PARAM_ENABLE_QUALITY_GATES,
                    self.PARAM_ENABLE_ROC_LOGGING,
                    self.PARAM_CONFIG_VERSION
                ],
                WithDecryption=False
            )
            
            # Parse parameters into dict
            params = {p['Name']: p['Value'] for p in response.get('Parameters', [])}
            
            # Build config with defaults for missing params
            config = FeatureFlagConfig(
                approval_threshold=float(params.get(
                    self.PARAM_APPROVAL_THRESHOLD,
                    str(self.DEFAULT_APPROVAL_THRESHOLD)
                )),
                rejection_threshold=float(params.get(
                    self.PARAM_REJECTION_THRESHOLD,
                    str(self.DEFAULT_REJECTION_THRESHOLD)
                )),
                aggregation_rule=self._parse_aggregation_rule(
                    params.get(self.PARAM_AGGREGATION_RULE, self.DEFAULT_AGGREGATION_RULE.value)
                ),
                enable_third_comparison=self._parse_bool(
                    params.get(self.PARAM_ENABLE_THIRD_COMPARISON, 'true')
                ),
                enable_quality_gates=self._parse_bool(
                    params.get(self.PARAM_ENABLE_QUALITY_GATES, 'true')
                ),
                enable_roc_logging=self._parse_bool(
                    params.get(self.PARAM_ENABLE_ROC_LOGGING, 'true')
                ),
                last_updated=datetime.utcnow().isoformat(),
                version=params.get(self.PARAM_CONFIG_VERSION, '1.0.0')
            )
            
            logger.info("Loaded feature flag config", extra={
                "approval_threshold": config.approval_threshold,
                "rejection_threshold": config.rejection_threshold,
                "aggregation_rule": config.aggregation_rule.value,
                "enable_third_comparison": config.enable_third_comparison,
                "version": config.version
            })
            
            return config
            
        except ClientError as e:
            logger.warning(f"Error fetching feature flags from SSM: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> FeatureFlagConfig:
        """Get default configuration when SSM is unavailable."""
        return FeatureFlagConfig(
            approval_threshold=self.DEFAULT_APPROVAL_THRESHOLD,
            rejection_threshold=self.DEFAULT_REJECTION_THRESHOLD,
            aggregation_rule=self.DEFAULT_AGGREGATION_RULE,
            enable_third_comparison=self.DEFAULT_ENABLE_THIRD_COMPARISON,
            enable_quality_gates=self.DEFAULT_ENABLE_QUALITY_GATES,
            enable_roc_logging=self.DEFAULT_ENABLE_ROC_LOGGING,
            last_updated=datetime.utcnow().isoformat(),
            version='default'
        )
    
    def _parse_aggregation_rule(self, value: str) -> AggregationRule:
        """Parse aggregation rule from string."""
        try:
            return AggregationRule(value.lower())
        except ValueError:
            logger.warning(f"Invalid aggregation rule '{value}', using default")
            return self.DEFAULT_AGGREGATION_RULE
    
    def _parse_bool(self, value: str) -> bool:
        """Parse boolean from string."""
        return value.lower() in ('true', '1', 'yes', 'enabled')
    
    def update_threshold(
        self,
        threshold_type: str,
        new_value: float,
        reason: str
    ) -> bool:
        """
        Update a threshold value with audit logging.
        
        Args:
            threshold_type: 'approval' or 'rejection'
            new_value: New threshold value
            reason: Reason for the change
            
        Returns:
            True if update successful
        """
        param_name = (
            self.PARAM_APPROVAL_THRESHOLD if threshold_type == 'approval'
            else self.PARAM_REJECTION_THRESHOLD
        )
        
        try:
            # Get current value for logging
            current_config = self.get_config(force_refresh=True)
            current_value = (
                current_config.approval_threshold if threshold_type == 'approval'
                else current_config.rejection_threshold
            )
            
            # Update parameter
            self.ssm.put_parameter(
                Name=param_name,
                Value=str(new_value),
                Type='String',
                Overwrite=True,
                Description=f"Face matching {threshold_type} threshold"
            )
            
            # Log the change (Requirement 10.6)
            self._log_config_change(
                parameter=threshold_type + '_threshold',
                old_value=current_value,
                new_value=new_value,
                reason=reason
            )
            
            # Invalidate cache
            self._cache = None
            
            return True
            
        except ClientError as e:
            logger.error(f"Error updating threshold: {e}")
            return False
    
    def _log_config_change(
        self,
        parameter: str,
        old_value: Any,
        new_value: Any,
        reason: str
    ) -> None:
        """
        Log configuration change for audit trail.
        
        Requirement 10.6: Log threshold changes with timestamp and previous values.
        """
        logger.info("Configuration change", extra={
            "event_type": "CONFIG_CHANGE",
            "parameter": parameter,
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "changed_by": "system"  # Could be enhanced with user context
        })


# Module-level singleton
_manager = FeatureFlagManager()


def get_feature_flags() -> FeatureFlagConfig:
    """Get current feature flag configuration."""
    return _manager.get_config()


def get_thresholds() -> tuple[float, float]:
    """Get approval and rejection thresholds."""
    config = _manager.get_config()
    return config.approval_threshold, config.rejection_threshold


def get_aggregation_rule() -> AggregationRule:
    """Get current aggregation rule."""
    config = _manager.get_config()
    return config.aggregation_rule


def is_third_comparison_enabled() -> bool:
    """Check if third comparison (ID ↔ IPRS) is enabled."""
    config = _manager.get_config()
    return config.enable_third_comparison


def is_quality_gates_enabled() -> bool:
    """Check if quality gates are enabled."""
    config = _manager.get_config()
    return config.enable_quality_gates


def is_roc_logging_enabled() -> bool:
    """Check if ROC logging for UAT is enabled."""
    config = _manager.get_config()
    return config.enable_roc_logging


def update_approval_threshold(new_value: float, reason: str) -> bool:
    """Update approval threshold with audit logging."""
    return _manager.update_threshold('approval', new_value, reason)


def update_rejection_threshold(new_value: float, reason: str) -> bool:
    """Update rejection threshold with audit logging."""
    return _manager.update_threshold('rejection', new_value, reason)
