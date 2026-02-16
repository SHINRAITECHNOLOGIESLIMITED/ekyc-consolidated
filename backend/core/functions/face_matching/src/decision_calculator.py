"""
Decision Calculator for Face Matching Service

Applies threshold-based decision logic to determine match outcomes.
"""

from typing import Optional
from aws_lambda_powertools import Logger

from models import (
    ComparisonResult,
    MatchDecision,
    MatchStatus,
    ComparisonMode,
)

logger = Logger()


class DecisionCalculator:
    """Calculates match decisions based on comparison results and thresholds."""
    
    def __init__(
        self,
        approval_threshold: float = 70.0,
        rejection_threshold: float = 50.0,
        aggregation_rule: str = 'fail-fast'
    ):
        """
        Initialize the decision calculator.
        
        Args:
            approval_threshold: Minimum score for automatic approval (default 70%)
            rejection_threshold: Score below which automatic rejection occurs (default 50%)
            aggregation_rule: One of 'fail-fast', 'minimum', 'weighted' (default 'fail-fast')
        """
        self.approval_threshold = approval_threshold
        self.rejection_threshold = rejection_threshold
        self.aggregation_rule = aggregation_rule
    
    def calculate_decision(
        self,
        comparison_results: dict[str, ComparisonResult],
        comparison_mode: ComparisonMode
    ) -> MatchDecision:
        """
        Calculate the overall match decision based on comparison results.
        
        Args:
            comparison_results: Dict of comparison name to result
            comparison_mode: '3-way' or '2-way'
            
        Returns:
            MatchDecision with status, reasons, and detailed breakdown
        """
        if not comparison_results:
            return MatchDecision(
                status=MatchStatus.REJECTED,
                reasons=['No comparison results available'],
                comparison_breakdown={}
            )
        
        # Calculate breakdown for each comparison
        breakdown = {}
        reasons = []
        
        for name, result in comparison_results.items():
            score = result.similarity_score
            
            if score >= self.approval_threshold:
                breakdown[name] = 'PASS'
            elif score >= self.rejection_threshold:
                breakdown[name] = 'REVIEW'
                reasons.append(
                    f'{name}: score {score:.1f}% is below approval threshold ({self.approval_threshold}%)'
                )
            else:
                breakdown[name] = 'FAIL'
                reasons.append(
                    f'{name}: score {score:.1f}% is below rejection threshold ({self.rejection_threshold}%)'
                )
        
        # Determine overall status based on aggregation rule
        status = self._calculate_status(breakdown, comparison_mode)
        
        # In 2-way mode, force MANUAL_REVIEW if not rejected
        if comparison_mode == ComparisonMode.TWO_WAY and status == MatchStatus.APPROVED:
            status = MatchStatus.MANUAL_REVIEW
            reasons.append('2-way comparison mode requires manual review (IPRS photo unavailable)')
        
        # Clear reasons for approved status
        if status == MatchStatus.APPROVED:
            reasons = []
        
        return MatchDecision(
            status=status,
            reasons=reasons,
            comparison_breakdown=breakdown
        )
    
    def _calculate_status(
        self,
        breakdown: dict[str, str],
        comparison_mode: ComparisonMode
    ) -> MatchStatus:
        """
        Calculate overall status based on breakdown and aggregation rule.
        
        Args:
            breakdown: Dict of comparison name to 'PASS'/'REVIEW'/'FAIL'
            comparison_mode: Comparison mode
            
        Returns:
            MatchStatus
        """
        if self.aggregation_rule == 'fail-fast':
            return self._fail_fast_status(breakdown)
        elif self.aggregation_rule == 'minimum':
            return self._minimum_score_status(breakdown)
        else:
            # Default to fail-fast
            return self._fail_fast_status(breakdown)
    
    def _fail_fast_status(self, breakdown: dict[str, str]) -> MatchStatus:
        """
        Fail-fast aggregation: any FAIL -> REJECTED, any REVIEW -> MANUAL_REVIEW.
        
        Args:
            breakdown: Dict of comparison name to status
            
        Returns:
            MatchStatus
        """
        statuses = list(breakdown.values())
        
        # Any FAIL -> REJECTED
        if 'FAIL' in statuses:
            return MatchStatus.REJECTED
        
        # Any REVIEW -> MANUAL_REVIEW
        if 'REVIEW' in statuses:
            return MatchStatus.MANUAL_REVIEW
        
        # All PASS -> APPROVED
        return MatchStatus.APPROVED
    
    def _minimum_score_status(self, breakdown: dict[str, str]) -> MatchStatus:
        """
        Minimum score aggregation: decision based on worst comparison.
        
        This is effectively the same as fail-fast for our threshold-based approach.
        """
        return self._fail_fast_status(breakdown)
