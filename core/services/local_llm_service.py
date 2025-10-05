"""
Local LLM Service - Manages local model inference using llama.cpp

Handles model loading, generation, and resource management for on-premise AI.
Optimized for 8GB RAM CPU-only development, scales to enterprise GPU clusters.
"""

import os
import logging
import asyncio
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


# Global instance
local_llm_service = LocalInferenceServer()
