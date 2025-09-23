"""
Feature Flag Framework for KYC Orchestrator
SOW Day 3 Requirement: Gradual rollout and A/B testing capabilities

Enables controlled deployment of new action-based endpoint while maintaining
backward compatibility with existing workflow-based processing.
"""

import json
import boto3
from typing import Dict, Any, Optional, List
from enum import Enum
from aws_lambda_powertools import Logger
from datetime import datetime, timezone

logger = Logger()


class FeatureFlag(Enum):
    """Enumeration of available feature flags."""
    # Core API features
    ACTION_BASED_ROUTING = "action_based_routing"
    UNIFIED_KYC_ENDPOINT = "unified_kyc_endpoint"

    # Individual action features
    DOCUMENT_VALIDATION_ACTIONS = "document_validation_actions"
    GOVERNMENT_VERIFICATION_ACTIONS = "government_verification_actions"
    BACKGROUND_CHECK_ACTION = "background_check_action"
    FACE_LIVENESS_ACTION = "face_liveness_action"
    REGISTRATION_ACTIONS = "registration_actions"
    DOCUMENT_STREAMING_ACTION = "document_streaming_action"

    # Performance and optimization features
    ASYNC_PROCESSING = "async_processing"
    ENHANCED_VALIDATION = "enhanced_validation"
    CACHING_ENABLED = "caching_enabled"

    # Security features
    ENHANCED_2FA = "enhanced_2fa"
    STRICT_VALIDATION = "strict_validation"
    AUDIT_LOGGING = "audit_logging"

    # Testing and debugging
    DEBUG_MODE = "debug_mode"
    PERFORMANCE_MONITORING = "performance_monitoring"


class RolloutStrategy(Enum):
    """Rollout strategies for feature deployment."""
    DISABLED = "disabled"           # Feature completely disabled
    ENABLED = "enabled"             # Feature enabled for all users
    PERCENTAGE = "percentage"       # Feature enabled for percentage of users
    WHITELIST = "whitelist"         # Feature enabled for specific users/clients
    CANARY = "canary"              # Feature enabled for canary users
    GRADUAL = "gradual"            # Gradual rollout with time-based progression


class FeatureFlagManager:
    """
    Manages feature flags for the KYC system.
    Supports multiple rollout strategies and real-time configuration updates.
    """

    def __init__(self, ssm_parameter_prefix: str = "/jubilee/kyc/feature-flags"):
        self.ssm_client = boto3.client('ssm')
        self.parameter_prefix = ssm_parameter_prefix
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._last_cache_update = {}

    def is_enabled(self, flag: FeatureFlag, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if a feature flag is enabled for the given context.

        Args:
            flag: The feature flag to check
            context: Optional context containing user_id, client_id, request_id, etc.

        Returns:
            Boolean indicating if the feature is enabled
        """
        try:
            flag_config = self._get_flag_config(flag)

            if not flag_config:
                logger.warning(f"Feature flag {flag.value} not found, defaulting to disabled")
                return False

            strategy = flag_config.get('strategy', RolloutStrategy.DISABLED.value)

            if strategy == RolloutStrategy.DISABLED.value:
                return False
            elif strategy == RolloutStrategy.ENABLED.value:
                return True
            elif strategy == RolloutStrategy.PERCENTAGE.value:
                return self._check_percentage_rollout(flag_config, context)
            elif strategy == RolloutStrategy.WHITELIST.value:
                return self._check_whitelist(flag_config, context)
            elif strategy == RolloutStrategy.CANARY.value:
                return self._check_canary(flag_config, context)
            elif strategy == RolloutStrategy.GRADUAL.value:
                return self._check_gradual_rollout(flag_config, context)
            else:
                logger.warning(f"Unknown rollout strategy: {strategy}")
                return False

        except Exception as e:
            logger.error(f"Error checking feature flag {flag.value}: {str(e)}")
            # Fail safe - return False if there's an error
            return False

    def get_flag_value(self, flag: FeatureFlag, default_value: Any = None,
                      context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Get the value of a feature flag (for flags that return values, not just boolean).

        Args:
            flag: The feature flag to get value for
            default_value: Default value if flag is not found or disabled
            context: Optional context for evaluation

        Returns:
            The flag value or default_value
        """
        try:
            if not self.is_enabled(flag, context):
                return default_value

            flag_config = self._get_flag_config(flag)
            return flag_config.get('value', default_value)

        except Exception as e:
            logger.error(f"Error getting feature flag value {flag.value}: {str(e)}")
            return default_value

    def _get_flag_config(self, flag: FeatureFlag) -> Optional[Dict[str, Any]]:
        """Get flag configuration from cache or SSM Parameter Store."""
        flag_name = flag.value
        cache_key = f"{self.parameter_prefix}/{flag_name}"

        # Check cache first
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)

        try:
            # Fetch from SSM Parameter Store
            response = self.ssm_client.get_parameter(
                Name=cache_key,
                WithDecryption=False
            )

            config = json.loads(response['Parameter']['Value'])

            # Update cache
            self._cache[cache_key] = config
            self._last_cache_update[cache_key] = datetime.now(timezone.utc)

            return config

        except self.ssm_client.exceptions.ParameterNotFound:
            logger.info(f"Feature flag parameter not found: {cache_key}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in feature flag parameter {cache_key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error fetching feature flag {cache_key}: {str(e)}")
            return None

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self._cache or cache_key not in self._last_cache_update:
            return False

        last_update = self._last_cache_update[cache_key]
        now = datetime.now(timezone.utc)
        return (now - last_update).total_seconds() < self._cache_ttl

    def _check_percentage_rollout(self, config: Dict[str, Any],
                                context: Optional[Dict[str, Any]]) -> bool:
        """Check percentage-based rollout."""
        percentage = config.get('percentage', 0)
        if percentage <= 0:
            return False
        if percentage >= 100:
            return True

        # Use consistent hashing based on user/client ID
        hash_key = self._get_hash_key(context)
        if not hash_key:
            return False

        # Simple hash-based percentage check
        hash_value = hash(hash_key) % 100
        return hash_value < percentage

    def _check_whitelist(self, config: Dict[str, Any],
                        context: Optional[Dict[str, Any]]) -> bool:
        """Check whitelist-based rollout."""
        whitelist = config.get('whitelist', [])
        if not whitelist or not context:
            return False

        user_id = context.get('user_id')
        client_id = context.get('client_id')
        request_id = context.get('request_id')

        return (user_id in whitelist or
                client_id in whitelist or
                request_id in whitelist)

    def _check_canary(self, config: Dict[str, Any],
                     context: Optional[Dict[str, Any]]) -> bool:
        """Check canary rollout (specific canary users/clients)."""
        canary_users = config.get('canary_users', [])
        canary_clients = config.get('canary_clients', [])

        if not context:
            return False

        user_id = context.get('user_id')
        client_id = context.get('client_id')

        return (user_id in canary_users or client_id in canary_clients)

    def _check_gradual_rollout(self, config: Dict[str, Any],
                             context: Optional[Dict[str, Any]]) -> bool:
        """Check gradual rollout based on time progression."""
        start_time = config.get('start_time')
        end_time = config.get('end_time')
        start_percentage = config.get('start_percentage', 0)
        end_percentage = config.get('end_percentage', 100)

        if not start_time or not end_time:
            return False

        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)

            if now < start_dt:
                return False
            elif now >= end_dt:
                current_percentage = end_percentage
            else:
                # Calculate current percentage based on time progression
                total_duration = (end_dt - start_dt).total_seconds()
                elapsed_duration = (now - start_dt).total_seconds()
                progress = elapsed_duration / total_duration

                current_percentage = start_percentage + (
                    (end_percentage - start_percentage) * progress
                )

            # Apply percentage check
            hash_key = self._get_hash_key(context)
            if not hash_key:
                return False

            hash_value = hash(hash_key) % 100
            return hash_value < current_percentage

        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing gradual rollout times: {str(e)}")
            return False

    def _get_hash_key(self, context: Optional[Dict[str, Any]]) -> Optional[str]:
        """Get a consistent hash key from context."""
        if not context:
            return None

        # Prefer user_id, then client_id, then request_id
        return (context.get('user_id') or
                context.get('client_id') or
                context.get('request_id'))

    def invalidate_cache(self, flag: Optional[FeatureFlag] = None):
        """Invalidate feature flag cache."""
        if flag:
            cache_key = f"{self.parameter_prefix}/{flag.value}"
            self._cache.pop(cache_key, None)
            self._last_cache_update.pop(cache_key, None)
        else:
            self._cache.clear()
            self._last_cache_update.clear()

    def get_all_flags_status(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get status of all feature flags for debugging/monitoring."""
        status = {}
        for flag in FeatureFlag:
            try:
                status[flag.value] = {
                    'enabled': self.is_enabled(flag, context),
                    'config': self._get_flag_config(flag)
                }
            except Exception as e:
                status[flag.value] = {
                    'enabled': False,
                    'error': str(e)
                }
        return status


# Global feature flag manager instance
feature_flag_manager = FeatureFlagManager()


def is_feature_enabled(flag: FeatureFlag, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Convenience function to check if a feature flag is enabled.

    Args:
        flag: The feature flag to check
        context: Optional context for evaluation

    Returns:
        Boolean indicating if the feature is enabled
    """
    return feature_flag_manager.is_enabled(flag, context)


def should_use_action_routing(context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if action-based routing should be used for this request.

    Args:
        context: Request context containing user/client information

    Returns:
        Boolean indicating if action-based routing should be used
    """
    return is_feature_enabled(FeatureFlag.ACTION_BASED_ROUTING, context)


def should_use_unified_endpoint(context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if the unified KYC endpoint should be used.

    Args:
        context: Request context containing user/client information

    Returns:
        Boolean indicating if unified endpoint should be used
    """
    return is_feature_enabled(FeatureFlag.UNIFIED_KYC_ENDPOINT, context)


def is_action_enabled(action: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if a specific KYC action is enabled.

    Args:
        action: The KYC action name
        context: Request context

    Returns:
        Boolean indicating if the action is enabled
    """
    # Map actions to feature flags
    action_flag_mapping = {
        'validate_nationalid': FeatureFlag.DOCUMENT_VALIDATION_ACTIONS,
        'validate_passport': FeatureFlag.DOCUMENT_VALIDATION_ACTIONS,
        'validate_krapincertificate': FeatureFlag.DOCUMENT_VALIDATION_ACTIONS,
        'validate_cr12': FeatureFlag.DOCUMENT_VALIDATION_ACTIONS,

        'government_verify_nationalid': FeatureFlag.GOVERNMENT_VERIFICATION_ACTIONS,
        'government_verify_passport': FeatureFlag.GOVERNMENT_VERIFICATION_ACTIONS,
        'government_verify_kra': FeatureFlag.GOVERNMENT_VERIFICATION_ACTIONS,

        'background_check': FeatureFlag.BACKGROUND_CHECK_ACTION,
        'face_liveness': FeatureFlag.FACE_LIVENESS_ACTION,

        'agent_registration': FeatureFlag.REGISTRATION_ACTIONS,
        'customer_registration': FeatureFlag.REGISTRATION_ACTIONS,

        'stream_document': FeatureFlag.DOCUMENT_STREAMING_ACTION,
    }

    flag = action_flag_mapping.get(action)
    if not flag:
        # If no specific flag, check general action routing
        return should_use_action_routing(context)

    return is_feature_enabled(flag, context)


class FeatureFlagDecorator:
    """Decorator for feature flag-controlled functions."""

    @staticmethod
    def feature_flag(flag: FeatureFlag, fallback_function: Optional[callable] = None):
        """
        Decorator to control function execution based on feature flag.

        Args:
            flag: Feature flag to check
            fallback_function: Function to call if feature is disabled
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Extract context if available
                context = kwargs.get('context') or (args[1] if len(args) > 1 else None)

                if is_feature_enabled(flag, context):
                    return func(*args, **kwargs)
                elif fallback_function:
                    return fallback_function(*args, **kwargs)
                else:
                    raise RuntimeError(f"Feature {flag.value} is disabled and no fallback provided")

            return wrapper
        return decorator