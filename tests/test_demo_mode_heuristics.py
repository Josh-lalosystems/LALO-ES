"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

Smoke Test for DEMO_MODE Heuristic Routing

This test validates that the router correctly classifies requests in DEMO_MODE
when no actual AI models are available. It ensures the heuristic fallback logic
works as expected for common user queries.

Run with:
    pytest tests/test_demo_mode_heuristics.py -v
    python -m pytest tests/test_demo_mode_heuristics.py -v -s
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.services.router_model import RouterModel


class TestDemoModeHeuristics:
    """Test suite for DEMO_MODE heuristic routing fallback"""

    @pytest.fixture
    def router(self):
        """Create router instance in DEMO_MODE (no model loaded)"""
        # Force heuristic mode by not loading any model
        router = RouterModel()
        # Ensure model is None to trigger heuristic fallback
        router.model = None
        return router

    def test_simple_greetings(self, router):
        """Greetings should route to simple path"""
        simple_queries = [
            "Hello",
            "Hi there",
            "Good morning",
            "Hey",
            "What's up",
        ]

        for query in simple_queries:
            result = router.classify(query)
            assert result["path"] == "simple", f"'{query}' should be simple, got {result['path']}"
            assert result["routing_method"] == "heuristic"

    def test_simple_factual(self, router):
        """Simple factual questions should route to simple path"""
        simple_queries = [
            "What is 2+2?",
            "What is the capital of France?",
            "Who is the president?",
            "When was Python created?",
            "What time is it?",
        ]

        for query in simple_queries:
            result = router.classify(query)
            assert result["path"] == "simple", f"'{query}' should be simple, got {result['path']}"

    def test_complex_math(self, router):
        """Math problems should route to complex path"""
        complex_queries = [
            "Solve for x: 2x + 5 = 15",
            "Calculate the derivative of x^2 + 3x",
            "What is the integral of sin(x)?",
            "Find the limit as x approaches infinity",
            "Prove the Pythagorean theorem",
        ]

        for query in complex_queries:
            result = router.classify(query)
            assert result["path"] == "complex", f"'{query}' should be complex, got {result['path']}"

    def test_complex_code(self, router):
        """Code-related requests should route to complex path"""
        complex_queries = [
            "Write a Python function to sort a list",
            "Debug this code: print('hello'",
            "Implement a binary search algorithm",
            "Refactor this function to use list comprehension",
            "Explain this JavaScript code",
        ]

        for query in complex_queries:
            result = router.classify(query)
            assert result["path"] == "complex", f"'{query}' should be complex, got {result['path']}"

    def test_complex_analysis(self, router):
        """Analysis and reasoning should route to complex path"""
        complex_queries = [
            "Analyze the pros and cons of solar energy",
            "Compare Python and JavaScript for web development",
            "Explain how machine learning works",
            "What are the implications of climate change?",
            "Summarize this article: ...",
        ]

        for query in complex_queries:
            result = router.classify(query)
            assert result["path"] == "complex", f"'{query}' should be complex, got {result['path']}"

    def test_design_architecture_keywords(self, router):
        """Design/architecture keywords should route to complex path (Change #2)"""
        complex_queries = [
            "Design a database schema for an e-commerce site",
            "Architect a microservices system",
            "Plan the architecture for a mobile app",
            "Design an API for user authentication",
            "Create a system design for a chat application",
        ]

        for query in complex_queries:
            result = router.classify(query)
            assert result["path"] == "complex", f"'{query}' should be complex (design/architecture), got {result['path']}"

    def test_complexity_levels(self, router):
        """Verify complexity scores are reasonable"""
        test_cases = [
            ("Hello", 0.1),  # Very simple
            ("What is 2+2?", 0.15),  # Simple math (adjusted - correctly routed as simple)
            ("Calculate the derivative", 0.6),  # Complex math
            ("Design a microservices architecture", 0.7),  # Very complex
        ]

        for query, expected_min_complexity in test_cases:
            result = router.classify(query)
            assert result["complexity"] >= expected_min_complexity, \
                f"'{query}' complexity {result['complexity']} should be >= {expected_min_complexity}"

    def test_empty_request_handling(self, router):
        """Empty requests should be handled gracefully (Change #3)"""
        empty_queries = ["", "   ", "\n", "\t"]

        for query in empty_queries:
            # This should either raise an exception or route to simple with low confidence
            result = router.classify(query)
            # Empty queries should have very low confidence
            assert result["confidence"] < 0.5, \
                f"Empty query should have low confidence, got {result['confidence']}"

    def test_confidence_scores(self, router):
        """Heuristic routing should provide reasonable confidence scores"""
        # High confidence cases
        high_confidence = [
            "Hello",
            "What is 2+2?",
            "Calculate the derivative of x^2",
        ]

        for query in high_confidence:
            result = router.classify(query)
            assert result["confidence"] >= 0.5, \
                f"'{query}' should have high confidence, got {result['confidence']}"

        # Lower confidence cases (ambiguous)
        medium_confidence = [
            "Tell me more",
            "That's interesting",
            "Go on",
        ]

        for query in medium_confidence:
            result = router.classify(query)
            # These should still work but with lower confidence
            assert result["confidence"] >= 0.3, \
                f"'{query}' should have medium confidence, got {result['confidence']}"

    def test_routing_method_is_heuristic(self, router):
        """All results should indicate heuristic routing method"""
        queries = [
            "Hello",
            "What is 2+2?",
            "Design a database schema",
            "Write Python code",
        ]

        for query in queries:
            result = router.classify(query)
            assert result["routing_method"] == "heuristic", \
                f"'{query}' should use heuristic method, got {result['routing_method']}"

    def test_result_structure(self, router):
        """Verify result dictionary has all required keys"""
        result = router.classify("Test query")

        required_keys = ["path", "complexity", "confidence", "routing_method"]
        for key in required_keys:
            assert key in result, f"Result missing required key: {key}"

        # Verify types
        assert result["path"] in ["simple", "complex", "specialized"]
        assert 0.0 <= result["complexity"] <= 1.0
        assert 0.0 <= result["confidence"] <= 1.0
        assert isinstance(result["routing_method"], str)


def test_smoke_demo_mode_basic():
    """Minimal smoke test - just verify router works without crashing"""
    router = RouterModel()
    router.model = None  # Force heuristic mode

    # Should not crash
    result = router.classify("Hello")
    assert result is not None
    assert "path" in result
    assert "confidence" in result

    print("\n✓ DEMO_MODE heuristic routing smoke test passed")


if __name__ == "__main__":
    # Run smoke test directly
    print("="*60)
    print("DEMO_MODE Heuristic Routing Smoke Test")
    print("="*60)

    test_smoke_demo_mode_basic()

    print("\nRun full test suite with:")
    print("  pytest tests/test_demo_mode_heuristics.py -v")
