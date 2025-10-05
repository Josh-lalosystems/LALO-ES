"""
Base model interface used by model wrappers in core.models.*

This file provides a lightweight abstract base class so modules can import
`BaseAIModel` without importing heavy service modules. It mirrors the
interface expected by `core.services.ai_service` and `core.models.local_model`.
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator


class BaseAIModel(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        raise NotImplementedError()
