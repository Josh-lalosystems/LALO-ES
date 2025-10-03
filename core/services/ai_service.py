from typing import Optional, Dict, Any, List, Union, AsyncGenerator
from abc import ABC, abstractmethod
import os
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Try to import llama_cpp, but make it optional
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False

class BaseAIModel(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        pass

class OpenAIModel(BaseAIModel):
    def __init__(self, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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
    def __init__(self, model: str = "claude-2"):
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model

    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.messages.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.content[0].text

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
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
    def __init__(self, database_service):
        self.models: Dict[str, Dict[str, BaseAIModel]] = {}
        self.db = database_service
        
    def initialize_user_models(self, user_id: str, api_keys: dict):
        """Initialize models for a specific user with their API keys"""
        self.models[user_id] = {}
        
        # Initialize OpenAI models
        if api_keys.get("openai"):
            self.models[user_id]["gpt-3.5-turbo"] = OpenAIModel(
                "gpt-3.5-turbo",
                api_key=api_keys["openai"]
            )

        # Initialize Anthropic models
        if api_keys.get("anthropic"):
            self.models[user_id]["claude-instant-1"] = AnthropicModel(
                "claude-instant-1",
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
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not available")

        if stream:
            return self.models[model_name].stream(prompt, **kwargs)
        else:
            return await self.models[model_name].generate(prompt, **kwargs)
