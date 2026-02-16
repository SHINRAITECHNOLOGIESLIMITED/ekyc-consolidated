"""
Configuration Manager for Face Matching Service

Retrieves thresholds and feature flags from SSM Parameter Store.
"""

import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from aws_lambda_powertools import Logger

logger = Logger()

# Default threshold values
DEFAULT_APPROVAL_THRESHOLD = 70.0
DEFAULT_REJECTION_THRESHOLD = 50.0

# SSM parameter paths
SSM_APPROVAL_THRESHOLD = '/ekyc/face-matching/approval-threshold'
SSM_REJECTION_THRESHOLD = '/ekyc/face-matching/rejection-threshold'
SSM_AGGREGATION_RULE = '/ekyc/face-matching/aggregation-rule'
SSM_ENABLE_THIRD_COMPARISON = '/ekyc/face-matching/enable-third-comparison'


class ConfigManager:
    """Manages configuration retrieval from SSM Parameter Store."""
    
    def __init__(self, ssm_client: Optional[boto3.client] = None):
        self._ssm = ssm_client or boto3.client('ssm')
        self._cache = {}
        self._load_config()
    
    def _load_config(self):
        """Load all configuration values from SSM."""
        self._approval_threshold = self._get_parameter_float(
            SSM_APPROVAL_THRESHOLD,
            DEFAULT_APPROVAL_THRESHOLD
        )
        self._rejection_threshold = self._get_parameter_float(
            SSM_REJECTION_THRESHOLD,
            DEFAULT_REJECTION_THRESHOLD
        )
        self._aggregation_rule = self._get_parameter_string(
            SSM_AGGREGATION_RULE,
            'fail-fast'
        )
        self._enable_third_comparison = self._get_parameter_bool(
            SSM_ENABLE_THIRD_COMPARISON,
            True
        )
    
    def _get_parameter_float(self, name: str, default: float) -> float:
        """Get a float parameter from SSM with fallback to default."""
        try:
            response = self._ssm.get_parameter(Name=name)
            value = float(response['Parameter']['Value'])
            logger.info(f"Loaded config {name}={value}")
            return value
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                logger.warning(f"Parameter {name} not found, using default: {default}")
            else:
                logger.error(f"Error loading {name}: {e}")
            return default
        except (ValueError, KeyError) as e:
            logger.error(f"Invalid value for {name}: {e}, using default: {default}")
            return default
    
    def _get_parameter_string(self, name: str, default: str) -> str:
        """Get a string parameter from SSM with fallback to default."""
        try:
            response = self._ssm.get_parameter(Name=name)
            value = response['Parameter']['Value']
            logger.info(f"Loaded config {name}={value}")
            return value
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                logger.warning(f"Parameter {name} not found, using default: {default}")
            else:
                logger.error(f"Error loading {name}: {e}")
            return default
    
    def _get_parameter_bool(self, name: str, default: bool) -> bool:
        """Get a boolean parameter from SSM with fallback to default."""
        try:
            response = self._ssm.get_parameter(Name=name)
            value = response['Parameter']['Value'].lower() in ('true', '1', 'yes')
            logger.info(f"Loaded config {name}={value}")
            return value
        except ClientError as e:
            if e.response['Error']['Code'] == 'ParameterNotFound':
                logger.warning(f"Parameter {name} not found, using default: {default}")
            else:
                logger.error(f"Error loading {name}: {e}")
            return default
    
    @property
    def approval_threshold(self) -> float:
        """Get the approval threshold (default 70%)."""
        return self._approval_threshold
    
    @property
    def rejection_threshold(self) -> float:
        """Get the rejection threshold (default 50%)."""
        return self._rejection_threshold
    
    @property
    def aggregation_rule(self) -> str:
        """Get the aggregation rule (fail-fast, minimum, weighted)."""
        return self._aggregation_rule
    
    @property
    def enable_third_comparison(self) -> bool:
        """Check if third comparison (ID vs IPRS) is enabled."""
        return self._enable_third_comparison
