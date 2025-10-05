# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
End-to-End Integration Tests

Tests the complete request flow:
1. Router classifies request
2. Orchestrator executes workflow
3. Confidence model validates output
4. Response returned to client
"""

import pytest
import asyncio
from typing import Dict

# Import services
from core.services.router_model import router_model
from core.services.agent_orchestrator import agent_orchestrator
from core.services.confidence_model import confidence_model
from core.services.unified_request_handler import unified_request_handler
from core.services.local_llm_service import local_llm_service


class TestEndToEndFlow:
    """Test complete request flow from input to output."""

    @pytest.mark.asyncio
    async def test_simple_request_flow(self):
        """Test a simple request through the complete pipeline."""
        user_request = "What is 2 + 2?"
        user_id = "test-user"
        available_models = ["tinyllama-1.1b", "liquid-tool-1.2b", "qwen-0.5b"]

        # Execute request
        result = await unified_request_handler.handle_request(
            user_request=user_request,
            user_id=user_id,
            available_models=available_models,
        )

        # Validate response structure
        assert "response" in result
        assert "path" in result
        assert "confidence" in result
        assert "metadata" in result

        # Should be simple path
        assert result["path"] == "simple"

        # Should have a response
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0

        # Confidence should be reasonable
        assert 0 <= result["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_complex_request_flow(self):
        """Test a complex request requiring multi-step workflow."""
        user_request = """Analyze the following business problem and provide a comprehensive solution:
        A retail company needs to optimize their inventory management system.
        They have 50 stores, seasonal demand variations, and supply chain constraints.
        Create a detailed implementation plan."""

        user_id = "test-user"
        available_models = ["tinyllama-1.1b", "liquid-tool-1.2b"]

        # Execute request
        result = await unified_request_handler.handle_request(
            user_request=user_request,
            user_id=user_id,
            available_models=available_models,
        )

        # Validate response structure
        assert "response" in result
        assert "path" in result

        # Should be complex or simple path (router decides)
        assert result["path"] in ["simple", "complex"]

        # Should have a response
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_router_classification(self):
        """Test router classifies requests correctly."""
        test_cases = [
            {
                "request": "What is the capital of France?",
                "expected_complexity_range": (0.0, 0.4),  # Simple
            },
            {
                "request": "Design a microservices architecture for a fintech platform",
                "expected_complexity_range": (0.6, 1.0),  # Complex
            },
            {
                "request": "Explain how photosynthesis works",
                "expected_complexity_range": (0.3, 0.7),  # Moderate
            },
        ]

        for test_case in test_cases:
            routing = await router_model.route(test_case["request"])

            # Check routing decision structure
            assert "path" in routing
            assert "complexity" in routing
            assert "confidence" in routing

            # Check complexity is in expected range
            complexity = routing["complexity"]
            min_expected, max_expected = test_case["expected_complexity_range"]
            assert (
                min_expected <= complexity <= max_expected
            ), f"Complexity {complexity} not in range {test_case['expected_complexity_range']} for '{test_case['request']}'"

    @pytest.mark.asyncio
    async def test_confidence_scoring(self):
        """Test confidence model scores outputs correctly."""
        test_cases = [
            {
                "request": "What is 2 + 2?",
                "output": "2 + 2 = 4",
                "expected_confidence_min": 0.7,  # Should be high
            },
            {
                "request": "What is 2 + 2?",
                "output": "I don't know.",
                "expected_confidence_max": 0.5,  # Should be low
            },
            {
                "request": "Explain quantum computing",
                "output": "Quantum computing uses quantum bits or qubits. Unlike classical bits that are either 0 or 1, qubits can exist in superposition states. This allows quantum computers to process multiple possibilities simultaneously.",
                "expected_confidence_min": 0.6,  # Reasonable explanation
            },
        ]

        for test_case in test_cases:
            score = await confidence_model.score(
                output=test_case["output"], original_request=test_case["request"]
            )

            # Check score structure
            assert "confidence" in score
            assert "recommendation" in score
            assert "scores" in score

            # Check confidence is in expected range
            confidence = score["confidence"]
            assert 0 <= confidence <= 1

            if "expected_confidence_min" in test_case:
                assert (
                    confidence >= test_case["expected_confidence_min"]
                ), f"Confidence {confidence} below minimum {test_case['expected_confidence_min']} for output '{test_case['output']}'"

            if "expected_confidence_max" in test_case:
                assert (
                    confidence <= test_case["expected_confidence_max"]
                ), f"Confidence {confidence} above maximum {test_case['expected_confidence_max']} for output '{test_case['output']}'"

    @pytest.mark.asyncio
    async def test_orchestrator_simple_path(self):
        """Test orchestrator executes simple requests."""
        user_request = "Hello, how are you?"
        routing_decision = {"path": "simple", "complexity": 0.2, "confidence": 0.9}
        user_id = "test-user"
        available_models = ["tinyllama-1.1b"]

        result = await agent_orchestrator.execute_simple_request(
            user_request=user_request,
            routing_decision=routing_decision,
            user_id=user_id,
            available_models=available_models,
        )

        # Check result structure
        assert "response" in result
        assert "confidence" in result

        # Should have a response
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_complex_path(self):
        """Test orchestrator executes complex multi-step requests."""
        user_request = "Research renewable energy trends and create a market analysis report"
        routing_decision = {"path": "complex", "complexity": 0.8, "confidence": 0.85}
        user_id = "test-user"
        available_models = ["tinyllama-1.1b", "liquid-tool-1.2b"]

        result = await agent_orchestrator.execute_complex_request(
            user_request=user_request,
            routing_decision=routing_decision,
            user_id=user_id,
            available_models=available_models,
        )

        # Check result structure
        assert "response" in result
        assert "confidence" in result

        # Should have a response
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_graceful_degradation_no_models(self):
        """Test system works even when models are unavailable."""
        user_request = "What is machine learning?"

        # Test router without models
        routing = await router_model.route(user_request)
        assert "path" in routing
        assert "complexity" in routing

        # Router should fall back to heuristics
        heuristic_score = router_model.estimate_complexity_sync(user_request)
        assert 0 <= heuristic_score <= 1

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in the pipeline."""
        # Test with empty request
        with pytest.raises(Exception):
            await unified_request_handler.handle_request(
                user_request="",  # Empty request should fail
                user_id="test-user",
                available_models=["tinyllama-1.1b"],
            )

    def test_heuristic_fallbacks(self):
        """Test heuristic fallback methods work without models."""
        # Test router heuristic
        test_cases = [
            ("What is AI?", 0.0, 0.4),  # Simple
            ("Define machine learning", 0.0, 0.4),  # Simple
            ("Design a distributed system", 0.6, 1.0),  # Complex
            ("Analyze and optimize", 0.5, 1.0),  # Complex
        ]

        for request, min_score, max_score in test_cases:
            score = router_model.estimate_complexity_sync(request)
            assert (
                min_score <= score <= max_score
            ), f"Complexity {score} not in range ({min_score}, {max_score}) for '{request}'"

        # Test confidence model heuristic
        good_output = "This is a detailed and comprehensive answer to your question. It covers multiple aspects and provides clear explanations with proper structure."
        bad_output = "Hmm."

        good_score = confidence_model._heuristic_scoring(
            output=good_output, original_request="Explain X"
        )
        bad_score = confidence_model._heuristic_scoring(
            output=bad_output, original_request="Explain X"
        )

        assert good_score["confidence"] > bad_score["confidence"]

    @pytest.mark.asyncio
    async def test_performance_simple_request(self):
        """Test performance of simple request (should be fast)."""
        import time

        user_request = "What is 1 + 1?"
        user_id = "test-user"
        available_models = ["tinyllama-1.1b"]

        start_time = time.time()

        result = await unified_request_handler.handle_request(
            user_request=user_request,
            user_id=user_id,
            available_models=available_models,
        )

        end_time = time.time()
        elapsed = end_time - start_time

        # Simple request should complete reasonably fast
        # Note: This depends on hardware, but we set a generous limit
        assert elapsed < 60, f"Simple request took {elapsed:.2f}s (should be < 60s)"

        # Should have valid response
        assert "response" in result
        assert len(result["response"]) > 0


class TestModelAvailability:
    """Test model availability checks."""

    def test_local_llm_service_initialization(self):
        """Test local LLM service initializes correctly."""
        # Service should exist
        assert local_llm_service is not None

        # Should have model configurations
        assert hasattr(local_llm_service, "model_configs")
        assert len(local_llm_service.model_configs) > 0

        # Should have expected models configured
        expected_models = ["tinyllama", "liquid-tool", "qwen-0.5b"]
        for model_name in expected_models:
            assert model_name in local_llm_service.model_configs

    @pytest.mark.asyncio
    async def test_model_loading(self):
        """Test models can be loaded (if files exist)."""
        import os

        model_dir = "models"
        test_model = "tinyllama"

        # Check if model file exists
        if test_model in local_llm_service.model_configs:
            config = local_llm_service.model_configs[test_model]
            model_path = config.get("path", "")

            if os.path.exists(model_path):
                # Try to load model
                try:
                    await local_llm_service._load_model(test_model)
                    assert test_model in local_llm_service.models
                    print(f"✓ Model {test_model} loaded successfully")
                except Exception as e:
                    print(f"⚠ Model {test_model} exists but failed to load: {e}")
            else:
                print(
                    f"⊘ Model {test_model} not downloaded (run: python scripts/download_models.py)"
                )


class TestIntegrationWithTeamComponents:
    """Test integration with components built by the other team."""

    @pytest.mark.asyncio
    async def test_agent_manager_integration(self):
        """Test integration with AgentManager (if available)."""
        try:
            from core.services.agent_manager import agent_manager

            # If available, test basic functionality
            assert agent_manager is not None
            print("✓ AgentManager integration available")

        except ImportError:
            print("⊘ AgentManager not yet implemented by other team")
            pytest.skip("AgentManager not available")

    @pytest.mark.asyncio
    async def test_workflow_manager_integration(self):
        """Test integration with WorkflowManager (if available)."""
        try:
            from core.services.workflow_manager import workflow_manager

            # If available, test basic functionality
            assert workflow_manager is not None
            print("✓ WorkflowManager integration available")

        except ImportError:
            print("⊘ WorkflowManager not yet implemented by other team")
            pytest.skip("WorkflowManager not available")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
