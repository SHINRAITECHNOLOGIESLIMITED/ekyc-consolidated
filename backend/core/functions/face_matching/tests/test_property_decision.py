"""
Property-based tests for Decision Calculator.

Tests universal properties for decision algorithm correctness.
"""

import pytest
from hypothesis import given, strategies as st, settings

from decision_calculator import DecisionCalculator
from models import ComparisonResult, MatchStatus, ComparisonMode


# Test settings
test_settings = settings(max_examples=50, deadline=None)


# ============================================================================
# Test Data Generators
# ============================================================================

# Generate similarity scores
similarity_score = st.floats(min_value=0.0, max_value=100.0, allow_nan=False)

# Generate scores that should result in APPROVED (all >= 70)
approved_scores = st.lists(
    st.floats(min_value=70.0, max_value=100.0, allow_nan=False),
    min_size=3, max_size=3
)

# Generate scores that should result in MANUAL_REVIEW (at least one in 50-69.99)
review_scores = st.lists(
    st.floats(min_value=50.0, max_value=100.0, allow_nan=False),
    min_size=3, max_size=3
).filter(lambda scores: any(50.0 <= s < 70.0 for s in scores) and all(s >= 50.0 for s in scores))

# Generate scores that should result in REJECTED (at least one < 50)
rejected_scores = st.lists(
    st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
    min_size=3, max_size=3
).filter(lambda scores: any(s < 50.0 for s in scores))


def create_comparison_results(scores: list[float]) -> dict[str, ComparisonResult]:
    """Create comparison results from a list of scores."""
    names = ['customer_vs_id_document', 'customer_vs_iprs', 'id_document_vs_iprs']
    return {
        name: ComparisonResult(
            comparison_name=name,
            similarity_score=score,
            confidence=99.0
        )
        for name, score in zip(names, scores)
    }


# ============================================================================
# Property 8: Decision Algorithm - Approval
# ============================================================================

class TestApprovalDecision:
    """
    Property 8: Decision Algorithm - Approval
    
    For any set of comparison results where ALL similarity scores are >= approval_threshold,
    the DecisionCalculator SHALL return Match_Status = APPROVED with an empty reasons array.
    
    Validates: Requirements 4.1
    """
    
    @test_settings
    @given(scores=approved_scores)
    def test_all_passing_scores_approved(self, scores):
        """
        Feature: face-matching-verification, Property 8: Decision Algorithm - Approval
        Validates: Requirements 4.1
        
        All scores >= 70% results in APPROVED status.
        """
        calculator = DecisionCalculator(approval_threshold=70.0, rejection_threshold=50.0)
        results = create_comparison_results(scores)
        
        decision = calculator.calculate_decision(results, ComparisonMode.THREE_WAY)
        
        assert decision.status == MatchStatus.APPROVED
        assert len(decision.reasons) == 0
    
    @test_settings
    @given(
        score1=st.floats(min_value=70.0, max_value=100.0, allow_nan=False),
        score2=st.floats(min_value=70.0, max_value=100.0, allow_nan=False),
        score3=st.floats(min_value=70.0, max_value=100.0, allow_nan=False)
    )
    def test_individual_passing_scores(self, score1, score2, score3):
        """Each individual score >= 70% contributes to APPROVED."""
        calculator = DecisionCalculator(approval_threshold=70.0, rejection_threshold=50.0)
        results = create_comparison_results([score1, score2, score3])
        
        decision = calculator.calculate_decision(results, ComparisonMode.THREE_WAY)
        
        assert decision.status == MatchStatus.APPROVED
        # All comparisons should be marked as PASS
        for status in decision.comparison_breakdown.values():
            assert status == 'PASS'


# ============================================================================
# Property 9: Decision Algorithm - Manual Review
# ============================================================================

class TestManualReviewDecision:
    """
    Property 9: Decision Algorithm - Manual Review
    
    For any set of comparison results where at least one similarity score is in the range
    [rejection_threshold, approval_threshold) and no score is below rejection_threshold,
    the DecisionCalculator SHALL return Match_Status = MANUAL_REVIEW with a non-empty reasons array.
    
    Validates: Requirements 4.2
    """
    
    @test_settings
    @given(scores=review_scores)
    def test_borderline_scores_manual_review(self, scores):
        """
        Feature: face-matching-verification, Property 9: Decision Algorithm - Manual Review
        Validates: Requirements 4.2
        
        Scores in 50-69% range result in MANUAL_REVIEW status.
        """
        calculator = DecisionCalculator(approval_threshold=70.0, rejection_threshold=50.0)
        results = create_comparison_results(scores)
        
        decision = calculator.calculate_decision(results, ComparisonMode.THREE_WAY)
        
        assert decision.status == MatchStatus.MANUAL_REVIEW
        assert len(decision.reasons) > 0
    
    @test_settings
    @given(
        passing_score=st.floats(min_value=70.0, max_value=100.0, allow_nan=False),
        review_score=st.floats(min_value=50.0, max_value=69.99, allow_nan=False)
    )
    def test_one_review_score_triggers_review(self, passing_score, review_score):
        """One score in review range triggers MANUAL_REVIEW."""
        calculator = DecisionCalculator(approval_threshold=70.0, rejection_threshold=50.0)
        results = create_comparison_results([passing_score, review_score, passing_score])
        
        decision = calculator.calculate_decision(results, ComparisonMode.THREE_WAY)
        
        assert decision.status == MatchStatus.MANUAL_REVIEW


# ============================================================================
# Property 10: Decision Algorithm - Rejection
# ============================================================================

class TestRejectionDecision:
    """
    Property 10: Decision Algorithm - Rejection
    
    For any set of comparison results where at least one similarity score is < rejection_threshold,
    the DecisionCalculator SHALL return Match_Status = REJECTED with a non-empty reasons array.
    
    Validates: Requirements 4.3
    """
    
    @test_settings
    @given(scores=rejected_scores)
    def test_failing_scores_rejected(self, scores):
        """
        Feature: face-matching-verification, Property 10: Decision Algorithm - Rejection
        Validates: Requirements 4.3
        
        Any score < 50% results in REJECTED status.
        """
        calculator = DecisionCalculator(approval_threshold=70.0, rejection_threshold=50.0)
        results = create_comparison_results(scores)
        
        decision = calculator.calculate_decision(results, ComparisonMode.THREE_WAY)
        
        assert decision.status == MatchStatus.REJECTED
        assert len(decision.reasons) > 0
    
    @test_settings
    @given(
        passing_score=st.floats(min_value=70.0, max_value=100.0, allow_nan=False),
        failing_score=st.floats(min_value=0.0, max_value=49.99, allow_nan=False)
    )
    def test_one_failing_score_triggers_rejection(self, passing_score, failing_score):
        """One score below threshold triggers REJECTED."""
        calculator = DecisionCalculator(approval_threshold=70.0, rejection_threshold=50.0)
        results = create_comparison_results([passing_score, failing_score, passing_score])
        
        decision = calculator.calculate_decision(results, ComparisonMode.THREE_WAY)
        
        assert decision.status == MatchStatus.REJECTED


# ============================================================================
# Property 3: Graceful Degradation to 2-Way Mode
# ============================================================================

class TestGracefulDegradation:
    """
    Property 3: Graceful Degradation to 2-Way Mode
    
    For any face matching request where IPRS photo is unavailable, the system SHALL
    set Match_Status to MANUAL_REVIEW regardless of the similarity score (if above rejection threshold).
    
    Validates: Requirements 1.6, 3.5, 4.4
    """
    
    @test_settings
    @given(score=st.floats(min_value=70.0, max_value=100.0, allow_nan=False))
    def test_two_way_mode_forces_manual_review(self, score):
        """
        Feature: face-matching-verification, Property 3: Graceful Degradation to 2-Way Mode
        Validates: Requirements 1.6, 3.5, 4.4
        
        2-way mode forces MANUAL_REVIEW even with passing scores.
        """
        calculator = DecisionCalculator(approval_threshold=70.0, rejection_threshold=50.0)
        
        # Only one comparison in 2-way mode
        results = {
            'customer_vs_id_document': ComparisonResult(
                comparison_name='customer_vs_id_document',
                similarity_score=score,
                confidence=99.0
            )
        }
        
        decision = calculator.calculate_decision(results, ComparisonMode.TWO_WAY)
        
        # Should be MANUAL_REVIEW, not APPROVED
        assert decision.status == MatchStatus.MANUAL_REVIEW
        assert any('2-way' in reason.lower() or 'iprs' in reason.lower() for reason in decision.reasons)
    
    @test_settings
    @given(score=st.floats(min_value=0.0, max_value=49.99, allow_nan=False))
    def test_two_way_mode_still_rejects_low_scores(self, score):
        """2-way mode still rejects scores below threshold."""
        calculator = DecisionCalculator(approval_threshold=70.0, rejection_threshold=50.0)
        
        results = {
            'customer_vs_id_document': ComparisonResult(
                comparison_name='customer_vs_id_document',
                similarity_score=score,
                confidence=99.0
            )
        }
        
        decision = calculator.calculate_decision(results, ComparisonMode.TWO_WAY)
        
        # Should still be REJECTED for low scores
        assert decision.status == MatchStatus.REJECTED


# ============================================================================
# Property 12: Reasons for Non-Approval
# ============================================================================

class TestReasonsForNonApproval:
    """
    Property 12: Reasons for Non-Approval
    
    For any face matching result where Match_Status is MANUAL_REVIEW or REJECTED,
    the response SHALL contain a non-empty reasons array.
    
    Validates: Requirements 5.6
    """
    
    @test_settings
    @given(scores=review_scores)
    def test_manual_review_has_reasons(self, scores):
        """
        Feature: face-matching-verification, Property 12: Reasons for Non-Approval
        Validates: Requirements 5.6
        
        MANUAL_REVIEW status includes reasons.
        """
        calculator = DecisionCalculator(approval_threshold=70.0, rejection_threshold=50.0)
        results = create_comparison_results(scores)
        
        decision = calculator.calculate_decision(results, ComparisonMode.THREE_WAY)
        
        if decision.status == MatchStatus.MANUAL_REVIEW:
            assert len(decision.reasons) > 0
    
    @test_settings
    @given(scores=rejected_scores)
    def test_rejected_has_reasons(self, scores):
        """REJECTED status includes reasons."""
        calculator = DecisionCalculator(approval_threshold=70.0, rejection_threshold=50.0)
        results = create_comparison_results(scores)
        
        decision = calculator.calculate_decision(results, ComparisonMode.THREE_WAY)
        
        assert decision.status == MatchStatus.REJECTED
        assert len(decision.reasons) > 0


# ============================================================================
# Additional Decision Calculator Properties
# ============================================================================

class TestComparisonBreakdown:
    """Tests for comparison breakdown in decisions."""
    
    @test_settings
    @given(scores=approved_scores)
    def test_breakdown_contains_all_comparisons(self, scores):
        """Breakdown contains entry for each comparison."""
        calculator = DecisionCalculator(approval_threshold=70.0, rejection_threshold=50.0)
        results = create_comparison_results(scores)
        
        decision = calculator.calculate_decision(results, ComparisonMode.THREE_WAY)
        
        assert len(decision.comparison_breakdown) == 3
        for name in results.keys():
            assert name in decision.comparison_breakdown
    
    @test_settings
    @given(
        score=st.floats(min_value=0.0, max_value=100.0, allow_nan=False)
    )
    def test_breakdown_status_matches_score(self, score):
        """Breakdown status correctly reflects score vs thresholds."""
        calculator = DecisionCalculator(approval_threshold=70.0, rejection_threshold=50.0)
        
        results = {
            'test': ComparisonResult(
                comparison_name='test',
                similarity_score=score,
                confidence=99.0
            )
        }
        
        decision = calculator.calculate_decision(results, ComparisonMode.THREE_WAY)
        
        expected_status = 'PASS' if score >= 70.0 else ('REVIEW' if score >= 50.0 else 'FAIL')
        assert decision.comparison_breakdown['test'] == expected_status
