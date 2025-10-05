"""
Local AI Model Wrapper

Implements BaseAIModel interface for local inference models.
Provides consistent API for both cloud and local models.
"""

from typing import Optional
from core.models.base import BaseAIModel
from core.services.local_llm_service import local_llm_service
import logging

logger = logging.getLogger(__name__)


class LocalAIModel(BaseAIModel):
    """
    Wrapper for local inference models using llama.cpp

    Provides same interface as cloud models (OpenAI, Anthropic) but uses
    local inference server instead.
    """

    def __init__(self, model_name: str):
        """
        Initialize local model wrapper

        Args:
            model_name: Name of local model (qwen-0.5b, tinyllama, liquid-tool)
        """
        self.model_name = model_name
        self.server = local_llm_service
        logger.info(f"LocalAIModel initialized: {model_name}")

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion

        Args:
            prompt: Input text
            max_tokens: Maximum tokens to generate (default: 512)
            temperature: Sampling temperature (default: 0.7)
            **kwargs: Additional parameters for llama.cpp

        Returns:
            Generated text

        Raises:
            RuntimeError: If generation fails
        """
        try:
            response = await self.server.generate(
                prompt=prompt,
                model_name=self.model_name,
                max_tokens=max_tokens or 512,
                temperature=temperature or 0.7,
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"Generation failed for {self.model_name}: {e}")
            raise RuntimeError(f"Local model generation failed: {e}")

    async def stream(self, prompt: str, **kwargs):
        """
        Stream generation (yields text chunks)

        Args:
            prompt: Input text
            **kwargs: Additional parameters

        Yields:
            Text chunks as they're generated
        """
        try:
            async for chunk in self.server.generate_stream(
                prompt=prompt,
                model_name=self.model_name,
                **kwargs
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Streaming failed for {self.model_name}: {e}")
            raise RuntimeError(f"Local model streaming failed: {e}")

    def is_available(self) -> bool:
        """Check if this model is available (downloaded and can be loaded)"""
        return self.server.is_available()

    def get_model_info(self) -> dict:
        """Get information about this model"""
        models = self.server.get_available_models()
        for model in models:
            if model["name"] == self.model_name:
                return model
        return {"name": self.model_name, "available": False}
