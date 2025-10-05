from typing import Optional, Dict, Any, List, Union, AsyncGenerator
from abc import ABC, abstractmethod
import os
# Optional provider SDK imports
try:
    from openai import AsyncOpenAI  # type: ignore
    OPENAI_AVAILABLE = True
except Exception:
    AsyncOpenAI = None  # type: ignore
    OPENAI_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic  # type: ignore
    ANTHROPIC_AVAILABLE = True
except Exception:
    AsyncAnthropic = None  # type: ignore
    ANTHROPIC_AVAILABLE = False
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Try to import llama_cpp, but make it optional
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False

# Import local model wrapper
from core.models.local_model import LocalAIModel

class BaseAIModel(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        pass

class OpenAIModel(BaseAIModel):
    def __init__(self, model: str = "gpt-4", api_key: str = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package is not installed. Install it or remove OpenAI usage.")
        self.client = AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message.content

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

class AnthropicModel(BaseAIModel):
    def __init__(self, model: str = "claude-2", api_key: str = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package is not installed. Install it or remove Anthropic usage.")
        self.client = AsyncAnthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model = model

    async def generate(self, prompt: str, **kwargs) -> str:
        # Anthropic uses max_tokens parameter (not max_output_tokens)
        # Ensure we have max_tokens set
        if "max_tokens" not in kwargs:
            kwargs["max_tokens"] = 1024  # Default
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.content[0].text

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        # Anthropic uses max_tokens parameter (not max_output_tokens)
        # Ensure we have max_tokens set
        if "max_tokens" not in kwargs:
            kwargs["max_tokens"] = 1024  # Default
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs
        )
        async for chunk in response:
            if chunk.delta.text:
                yield chunk.delta.text

class LocalLLaMAModel(BaseAIModel):
    def __init__(self, model_path: str):
        if not LLAMA_AVAILABLE:
            raise ImportError("llama-cpp-python is not installed. Llama models are not available.")
            
        self.model = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=os.cpu_count()
        )

    async def generate(self, prompt: str, **kwargs) -> str:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: self.model(prompt, **kwargs)
        )
        return response['choices'][0]['text']

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        response = self.model(prompt, stream=True, **kwargs)
        for chunk in response:
            yield chunk['choices'][0]['text']

class AIService:
    def __init__(self, database_service=None):
        self.models: Dict[str, Dict[str, BaseAIModel]] = {}
        self.db = database_service
        
    def initialize_user_models(self, user_id: str, api_keys: dict, working_keys: dict = None):
        """Initialize models for a specific user with their API keys"""
        self.models[user_id] = {}

        # **LOCAL MODELS (Always available - no API keys needed)**
        # These run on-premise using llama.cpp
        self.models[user_id]["tinyllama-1.1b"] = LocalAIModel("tinyllama")
        self.models[user_id]["liquid-tool-1.2b"] = LocalAIModel("liquid-tool")
        self.models[user_id]["qwen-0.5b"] = LocalAIModel("qwen-0.5b")

        # Initialize OpenAI models only if key is working
        if api_keys.get("openai") and OPENAI_AVAILABLE and (working_keys is None or working_keys.get("openai", True)):
            # GPT-4 Turbo - Latest and most capable GPT-4 variant
            self.models[user_id]["gpt-4-turbo-preview"] = OpenAIModel(
                "gpt-4-turbo-preview",
                api_key=api_keys["openai"]
            )
            # GPT-3.5 Turbo - Fast and cost-effective
            self.models[user_id]["gpt-3.5-turbo"] = OpenAIModel(
                "gpt-3.5-turbo",
                api_key=api_keys["openai"]
            )

        # Initialize Anthropic models only if key is working
        if api_keys.get("anthropic") and ANTHROPIC_AVAILABLE and (working_keys is None or working_keys.get("anthropic", True)):
            # Claude 3.5 Sonnet - Latest and most capable Claude model
            self.models[user_id]["claude-3-5-sonnet-20241022"] = AnthropicModel(
                "claude-3-5-sonnet-20241022",
                api_key=api_keys["anthropic"]
            )
            # Claude 3 Opus - Most capable Claude 3 model
            self.models[user_id]["claude-3-opus-20240229"] = AnthropicModel(
                "claude-3-opus-20240229",
                api_key=api_keys["anthropic"]
            )
            # Claude 3 Haiku - Fastest and most cost-effective
            self.models[user_id]["claude-3-haiku-20240307"] = AnthropicModel(
                "claude-3-haiku-20240307",
                api_key=api_keys["anthropic"]
            )
            
    def get_available_models(self, user_id: str) -> List[str]:
        """Get list of available models for a user"""
        if user_id not in self.models:
            return []
        return list(self.models[user_id].keys())

    async def generate(
        self, 
        prompt: str, 
        model_name: str = "gpt-4",
        user_id: str = None,
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        if user_id not in self.models or model_name not in self.models[user_id]:
            raise ValueError(f"Model {model_name} not available for user {user_id}")

        if stream:
            return self.models[user_id][model_name].stream(prompt, **kwargs)
        else:
            return await self.models[user_id][model_name].generate(prompt, **kwargs)


# Create global service instance without database_service initially
# Database service will be set later to avoid circular imports
ai_service = AIService()
