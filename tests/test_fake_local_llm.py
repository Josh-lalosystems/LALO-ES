# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
Tests for FakeLocalInferenceServer

These tests verify that the fake LLM provides deterministic responses
suitable for CI testing without requiring native llama-cpp binaries.
"""

import os
import pytest
import json


# Only run these tests when USE_FAKE_LOCAL_LLM is set
pytestmark = pytest.mark.skipif(
    os.getenv("USE_FAKE_LOCAL_LLM") != "1",
    reason="Fake LLM tests only run when USE_FAKE_LOCAL_LLM=1"
)


@pytest.fixture
def fake_llm_service():
    """Get the fake LLM service"""
    from core.services.local_llm_service import local_llm_service
    return local_llm_service


class TestFakeLocalInferenceServer:
    """Test suite for FakeLocalInferenceServer"""

    def test_service_type(self, fake_llm_service):
        """Verify we're using the fake server when enabled"""
        assert type(fake_llm_service).__name__ == "FakeLocalInferenceServer"

    def test_is_available(self, fake_llm_service):
        """Fake server should always be available"""
        assert fake_llm_service.is_available() is True

    def test_model_loading(self, fake_llm_service):
        """Test model loading and unloading"""
        # Load a model
        assert fake_llm_service.load_model("tinyllama") is True
        assert "tinyllama" in fake_llm_service.get_loaded_models()
        
        # Unload the model
        fake_llm_service.unload_model("tinyllama")
        assert "tinyllama" not in fake_llm_service.get_loaded_models()

    def test_model_configs(self, fake_llm_service):
        """Test that expected models are configured"""
        models = ["tinyllama", "liquid-tool", "qwen-0.5b"]
        for model_name in models:
            assert model_name in fake_llm_service.model_configs

    def test_get_available_models(self, fake_llm_service):
        """Test getting available models list"""
        models = fake_llm_service.get_available_models()
        assert len(models) > 0
        
        for model in models:
            assert "name" in model
            assert "description" in model
            assert "path" in model
            assert "downloaded" in model
            assert "loaded" in model
            assert "n_ctx" in model

    @pytest.mark.asyncio
    async def test_basic_generation(self, fake_llm_service):
        """Test basic text generation"""
        result = await fake_llm_service.generate(
            "What is AI?",
            model_name="tinyllama"
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_routing_decision(self, fake_llm_service):
        """Test routing model returns proper JSON format"""
        # Simple request
        result = await fake_llm_service.generate(
            "What is the capital of France?",
            model_name="liquid-tool"
        )
        data = json.loads(result)
        assert "path" in data
        assert "complexity" in data
        assert "confidence" in data
        assert data["path"] in ["simple", "complex"]
        assert 0 <= data["complexity"] <= 1
        
        # Complex request
        result = await fake_llm_service.generate(
            "Design a microservices architecture for a fintech platform",
            model_name="liquid-tool"
        )
        data = json.loads(result)
        assert data["path"] == "complex"
        assert data["complexity"] > 0.6

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, fake_llm_service):
        """Test confidence model returns proper JSON format"""
        result = await fake_llm_service.generate(
            "Score the confidence of this output: This is a comprehensive and detailed answer.",
            model_name="qwen-0.5b"
        )
        data = json.loads(result)
        
        assert "confidence" in data
        assert "scores" in data
        assert "recommendation" in data
        assert "reasoning" in data
        assert 0 <= data["confidence"] <= 1
        assert data["recommendation"] in ["accept", "retry", "escalate", "human_review"]
        
        # Verify scores structure
        scores = data["scores"]
        assert "factual" in scores
        assert "consistent" in scores
        assert "complete" in scores
        assert "grounded" in scores

    @pytest.mark.asyncio
    async def test_low_quality_detection(self, fake_llm_service):
        """Test that fake LLM can detect low quality outputs"""
        result = await fake_llm_service.generate(
            "Score the confidence of this output: hmm",
            model_name="qwen-0.5b"
        )
        data = json.loads(result)
        
        # Low quality should have lower confidence
        assert data["confidence"] < 0.6

    @pytest.mark.asyncio
    async def test_streaming(self, fake_llm_service):
        """Test streaming generation"""
        chunks = []
        async for chunk in fake_llm_service.generate_stream(
            "What is machine learning?",
            model_name="tinyllama"
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_text = "".join(chunks)
        assert len(full_text) > 0

    @pytest.mark.asyncio
    async def test_deterministic_responses(self, fake_llm_service):
        """Test that responses are deterministic"""
        prompt = "What is 2 + 2?"
        
        result1 = await fake_llm_service.generate(prompt, model_name="tinyllama")
        result2 = await fake_llm_service.generate(prompt, model_name="tinyllama")
        
        # Same prompt should give same response
        assert result1 == result2

    def test_shutdown(self, fake_llm_service):
        """Test server shutdown"""
        # Load some models
        fake_llm_service.load_model("tinyllama")
        fake_llm_service.load_model("qwen-0.5b")
        
        # Shutdown should unload all
        fake_llm_service.shutdown()
        assert len(fake_llm_service.get_loaded_models()) == 0
