"""
Local LLM Service - Manages local model inference using llama.cpp

Handles model loading, generation, and resource management for on-premise AI.
Optimized for 8GB RAM CPU-only development, scales to enterprise GPU clusters.
"""

import os
import logging
import asyncio
import json
from typing import Dict, Optional, List, Any
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Try to import llama-cpp-python
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama-cpp-python not installed. Local inference unavailable.")
    logger.warning("Install with: pip install llama-cpp-python")


class LocalInferenceServer:
    """
    Manages local model inference using llama.cpp

    Features:
    - Model loading/unloading for memory management
    - Async generation with thread pool
    - Streaming support
    - Automatic model selection
    - Performance monitoring
    """

    def __init__(self, model_dir: str = "./models"):
        self.model_dir = model_dir
        self.models: Dict[str, Any] = {}  # Loaded model instances
        self.model_configs = {
            # Models optimized for 8GB RAM CPU-only
            "qwen-0.5b": {
                "path": "qwen-0.5b/qwen2.5-0.5b-instruct-q4_k_m.gguf",
                "n_ctx": 2048,
                "n_threads": 2,
                "description": "Fast confidence scoring & validation"
            },
            "tinyllama": {
                "path": "tinyllama/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                "n_ctx": 2048,
                "n_threads": 4,
                "description": "General purpose chat"
            },
            "liquid-tool": {
                "path": "liquid-tool/Liquid-1.2B-Tool-Q4_K_M.gguf",
                "n_ctx": 2048,
                "n_threads": 4,
                "description": "Function calling & routing"
            }
        }

        # Thread pool for async execution (llama.cpp is blocking)
        self.executor = ThreadPoolExecutor(max_workers=2)

        logger.info(f"LocalInferenceServer initialized (llama.cpp available: {LLAMA_CPP_AVAILABLE})")

    def is_available(self) -> bool:
        """Check if local inference is available"""
        return LLAMA_CPP_AVAILABLE

    def load_model(self, model_name: str) -> bool:
        """
        Load a model into memory

        Args:
            model_name: Name of model to load (qwen-0.5b, tinyllama, liquid-tool)

        Returns:
            True if successful, False otherwise
        """
        if not LLAMA_CPP_AVAILABLE:
            logger.error("Cannot load model: llama-cpp-python not installed")
            return False

        if model_name in self.models:
            logger.info(f"Model {model_name} already loaded")
            return True

        if model_name not in self.model_configs:
            logger.error(f"Unknown model: {model_name}")
            return False

        config = self.model_configs[model_name]
        model_path = os.path.join(self.model_dir, config["path"])

        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            logger.error(f"Run: python scripts/download_models.py --model {model_name}")
            return False

        try:
            logger.info(f"Loading {model_name} from {model_path}")

            self.models[model_name] = Llama(
                model_path=model_path,
                n_ctx=config["n_ctx"],
                n_threads=config["n_threads"],
                verbose=False
            )

            logger.info(f"✓ {model_name} loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load {model_name}: {e}")
            return False

    def unload_model(self, model_name: str):
        """Unload a model to free memory"""
        if model_name in self.models:
            del self.models[model_name]
            logger.info(f"Unloaded {model_name}")

    def unload_all_models(self):
        """Unload all models"""
        for model_name in list(self.models.keys()):
            self.unload_model(model_name)

    async def generate(
        self,
        prompt: str,
        model_name: str = "tinyllama",
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion asynchronously

        Args:
            prompt: Input text prompt
            model_name: Model to use (qwen-0.5b, tinyllama, liquid-tool)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            top_p: Top-p sampling (0-1)
            stop: Stop sequences
            **kwargs: Additional llama.cpp parameters

        Returns:
            Generated text

        Raises:
            ValueError: If model not available
            RuntimeError: If generation fails
        """
        if not LLAMA_CPP_AVAILABLE:
            raise RuntimeError("llama-cpp-python not installed. Install with: pip install llama-cpp-python")

        # Load model if not already loaded
        if model_name not in self.models:
            if not self.load_model(model_name):
                raise ValueError(f"Failed to load model: {model_name}")

        model = self.models[model_name]

        # Run inference in thread pool (llama.cpp is blocking)
        loop = asyncio.get_event_loop()

        def _generate():
            return model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stop=stop or [],
                echo=False,
                **kwargs
            )

        try:
            result = await loop.run_in_executor(self.executor, _generate)
            return result['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Generation failed with {model_name}: {e}")
            raise RuntimeError(f"Generation failed: {e}")

    async def generate_stream(
        self,
        prompt: str,
        model_name: str = "tinyllama",
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Generate text with streaming (for real-time UI updates)

        Args:
            prompt: Input text prompt
            model_name: Model to use
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Yields:
            Text chunks as they're generated
        """
        if not LLAMA_CPP_AVAILABLE:
            raise RuntimeError("llama-cpp-python not installed")

        if model_name not in self.models:
            if not self.load_model(model_name):
                raise ValueError(f"Failed to load model: {model_name}")

        model = self.models[model_name]
        loop = asyncio.get_event_loop()

        def _generate_stream():
            return model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                **kwargs
            )

        try:
            stream = await loop.run_in_executor(self.executor, _generate_stream)

            for chunk in stream:
                text = chunk['choices'][0]['text']
                if text:  # Only yield non-empty chunks
                    yield text

        except Exception as e:
            logger.error(f"Streaming failed with {model_name}: {e}")
            raise RuntimeError(f"Streaming failed: {e}")

    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available models

        Returns:
            List of model info dicts with status
        """
        available = []
        for name, config in self.model_configs.items():
            model_path = os.path.join(self.model_dir, config["path"])
            exists = os.path.exists(model_path)
            loaded = name in self.models

            available.append({
                "name": name,
                "description": config["description"],
                "path": model_path,
                "downloaded": exists,
                "loaded": loaded,
                "n_ctx": config["n_ctx"]
            })

        return available

    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded model names"""
        return list(self.models.keys())

    def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down LocalInferenceServer...")

        # Unload all models
        self.unload_all_models()

        # Shutdown executor
        self.executor.shutdown(wait=True)

        logger.info("LocalInferenceServer shutdown complete")


class FakeLocalInferenceServer:
    """
    Test-friendly fake local LLM server for CI testing.
    
    Provides deterministic, fast responses that exercise the same code paths
    as the real LocalInferenceServer without requiring native llama-cpp binaries
    or model files.
    
    Activated via USE_FAKE_LOCAL_LLM=1 environment variable.
    """

    def __init__(self, model_dir: str = "./models"):
        self.model_dir = model_dir
        self.models: Dict[str, bool] = {}  # Track loaded models (just names)
        self.model_configs = {
            # Same config structure as real server
            "qwen-0.5b": {
                "path": "qwen-0.5b/qwen2.5-0.5b-instruct-q4_k_m.gguf",
                "n_ctx": 2048,
                "n_threads": 2,
                "description": "Fast confidence scoring & validation"
            },
            "tinyllama": {
                "path": "tinyllama/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                "n_ctx": 2048,
                "n_threads": 4,
                "description": "General purpose chat"
            },
            "liquid-tool": {
                "path": "liquid-tool/Liquid-1.2B-Tool-Q4_K_M.gguf",
                "n_ctx": 2048,
                "n_threads": 4,
                "description": "Function calling & routing"
            }
        }
        logger.info("FakeLocalInferenceServer initialized (test mode)")

    def is_available(self) -> bool:
        """Always available in test mode"""
        return True

    def load_model(self, model_name: str) -> bool:
        """Simulate model loading"""
        if model_name in self.models:
            logger.info(f"Fake model {model_name} already loaded")
            return True

        if model_name not in self.model_configs:
            logger.error(f"Unknown model: {model_name}")
            return False

        logger.info(f"Loading fake model {model_name}")
        self.models[model_name] = True
        logger.info(f"✓ Fake {model_name} loaded successfully")
        return True

    def unload_model(self, model_name: str):
        """Simulate model unloading"""
        if model_name in self.models:
            del self.models[model_name]
            logger.info(f"Unloaded fake {model_name}")

    def unload_all_models(self):
        """Unload all models"""
        for model_name in list(self.models.keys()):
            self.unload_model(model_name)

    async def generate(
        self,
        prompt: str,
        model_name: str = "tinyllama",
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Generate deterministic fake responses for testing.
        
        Returns JSON or text responses based on the model and prompt context.
        """
        # Load model if not already loaded
        if model_name not in self.models:
            self.load_model(model_name)

        # Simulate brief processing delay
        await asyncio.sleep(0.01)

        # Generate response based on model and prompt content
        if model_name == "liquid-tool":
            # Router model - always return routing decision
            # Parse complexity from prompt keywords
            complexity = 0.3
            if any(word in prompt.lower() for word in ["design", "analyze", "optimize", "architecture"]):
                complexity = 0.8
            elif any(word in prompt.lower() for word in ["explain", "research", "create"]):
                complexity = 0.5
            
            return json.dumps({
                "path": "complex" if complexity > 0.6 else "simple",
                "complexity": complexity,
                "confidence": 0.85,
                "reasoning": "Automated routing decision from fake LLM",
                "recommended_model": "tinyllama",
                "requires_tools": complexity > 0.6,
                "requires_workflow": complexity > 0.7
            })
        
        elif model_name == "qwen-0.5b":
            # Confidence model - always return confidence scores
            # Check output quality based on length and keywords
            output_quality = 0.7
            if "output" in prompt.lower():
                # Parse for quality indicators
                if len(prompt) > 500:
                    output_quality = 0.8
                if "comprehensive" in prompt.lower() or "detailed" in prompt.lower():
                    output_quality = 0.85
                if "hmm" in prompt.lower() or "i don't know" in prompt.lower():
                    output_quality = 0.3
            
            return json.dumps({
                "confidence": output_quality,
                "scores": {
                    "factual": output_quality,
                    "consistent": output_quality + 0.05,
                    "complete": output_quality - 0.05,
                    "grounded": output_quality
                },
                "issues": [] if output_quality > 0.6 else ["Low quality output detected"],
                "recommendation": "accept" if output_quality >= 0.8 else "retry" if output_quality >= 0.6 else "escalate",
                "reasoning": "Automated confidence scoring from fake LLM"
            })
        
        # Default response for general chat (tinyllama or unspecified)
        # Provide a reasonable answer based on the prompt
        if "what is" in prompt.lower():
            topic = prompt.lower().split("what is")[-1].strip().rstrip("?").strip()
            return f"The topic '{topic}' is an important concept. This is a test response from the fake local LLM."
        elif any(q in prompt.lower() for q in ["how", "why", "when", "where"]):
            return "This is a detailed explanation from the fake local LLM. It provides comprehensive information to answer the user's question with proper context and examples."
        else:
            return "This is a response generated by the fake local LLM for testing purposes. It simulates realistic output without requiring actual model inference."

    async def generate_stream(
        self,
        prompt: str,
        model_name: str = "tinyllama",
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Generate text with fake streaming for testing.
        
        Yields text chunks to simulate streaming behavior.
        """
        if model_name not in self.models:
            self.load_model(model_name)

        # Generate response and stream it in chunks
        response = await self.generate(
            prompt=prompt,
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

        # Stream in word chunks
        words = response.split()
        for i, word in enumerate(words):
            await asyncio.sleep(0.001)  # Tiny delay to simulate streaming
            if i < len(words) - 1:
                yield word + " "
            else:
                yield word

    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        List all available models (fake mode always shows as available)
        """
        available = []
        for name, config in self.model_configs.items():
            available.append({
                "name": name,
                "description": config["description"],
                "path": os.path.join(self.model_dir, config["path"]),
                "downloaded": True,  # Fake models are always "available"
                "loaded": name in self.models,
                "n_ctx": config["n_ctx"]
            })
        return available

    def get_loaded_models(self) -> List[str]:
        """Get list of currently loaded model names"""
        return list(self.models.keys())

    def shutdown(self):
        """Cleanup resources (no-op for fake server)"""
        logger.info("Shutting down FakeLocalInferenceServer...")
        self.unload_all_models()
        logger.info("FakeLocalInferenceServer shutdown complete")


# Global instance - use fake or real based on environment variable
USE_FAKE_LOCAL_LLM = os.getenv("USE_FAKE_LOCAL_LLM", "0") == "1"

if USE_FAKE_LOCAL_LLM:
    logger.info("Using FakeLocalInferenceServer (USE_FAKE_LOCAL_LLM=1)")
    local_llm_service = FakeLocalInferenceServer()
else:
    local_llm_service = LocalInferenceServer()
