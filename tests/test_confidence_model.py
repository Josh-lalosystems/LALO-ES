"""
Tests for ConfidenceModel

Validates output quality scoring and recommendation logic.
"""

import pytest
import asyncio
from core.services.confidence_model import confidence_model


class TestConfidenceModel:
    """Test ConfidenceModel functionality"""

    @pytest.mark.asyncio
    async def test_heuristic_scoring_short_output(self):
        """Test heuristic scoring for very short outputs"""
        result = confidence_model._heuristic_scoring(
            output="Yes.",
            original_request="Is Python a programming language?"
        )

        assert "confidence" in result
        assert result["confidence"] < 0.7  # Short output = low completeness
        assert "scores" in result
        assert result["scores"]["complete"] < 0.5

    @pytest.mark.asyncio
    async def test_heuristic_scoring_generic_output(self):
        """Test detection of generic AI responses"""
        result = confidence_model._heuristic_scoring(
            output="As an AI, I don't have personal experiences...",
            original_request="What do you think about Python?"
        )

        assert result["scores"]["grounded"] <= 0.6  # Generic phrase detected

    @pytest.mark.asyncio
    async def test_heuristic_scoring_good_output(self):
        """Test scoring of quality output"""
        result = confidence_model._heuristic_scoring(
            output="Python is a high-level, interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
            original_request="What is Python?"
        )

        assert result["confidence"] > 0.6  # Good length and structure
        assert result["scores"]["complete"] > 0.6

    def test_recommendation_thresholds(self):
        """Test recommendation based on confidence scores"""
        assert confidence_model._get_recommendation(0.9) == "accept"
        assert confidence_model._get_recommendation(0.75) == "retry"
        assert confidence_model._get_recommendation(0.5) == "escalate"
        assert confidence_model._get_recommendation(0.3) == "human_review"

    def test_should_retry(self):
        """Test retry logic"""
        assert not confidence_model.should_retry(0.8)  # High confidence
        assert confidence_model.should_retry(0.5)      # Low confidence

    def test_should_escalate(self):
        """Test escalation logic"""
        assert not confidence_model.should_escalate(0.8)  # Too high
        assert confidence_model.should_escalate(0.5)      # In range
        assert not confidence_model.should_escalate(0.3)  # Too low

    def test_needs_human_review(self):
        """Test human review threshold"""
        assert not confidence_model.needs_human_review(0.6)  # Above threshold
        assert confidence_model.needs_human_review(0.3)      # Below threshold

    @pytest.mark.asyncio
    async def test_validate_multi_output(self):
        """Test selection of best output from multiple options"""
        outputs = [
            {"text": "Short", "model": "model-a"},
            {"text": "This is a much more detailed and comprehensive answer that provides substantial information.", "model": "model-b"},
            {"text": "Medium answer here.", "model": "model-c"}
        ]

        result = await confidence_model.validate_multi_output(
            outputs=outputs,
            original_request="Explain something"
        )

        assert "best_output" in result
        assert "best_model" in result
        assert "confidence" in result
        assert len(result["all_scores"]) == 3
        # Best should be model-b (longest, most complete)
        assert result["best_model"] == "model-b"
