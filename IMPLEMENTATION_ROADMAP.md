# Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of LALO AI Platform and is protected by copyright law.
# Unauthorized copying, modification, distribution, or use of this software,
# via any medium, is strictly prohibited without the express written permission
# of LALO AI SYSTEMS, LLC.
#

# LALO Implementation Roadmap - Local Inference

**Target:** Fully functional local LALO in 2 weeks
**Current Hardware:** 8GB RAM, CPU-only
**Future Hardware:** RTX 4090+ via Intel/NVIDIA connections

---

## Day-by-Day Plan

### Day 1: Setup & Installation (Friday)

#### Morning: Install Inference Engine

**Task 1.1: Install llama.cpp with Python bindings**

```bash
# Windows (PowerShell as Administrator)
# Install Visual Studio Build Tools if not present
# Download from: https://visualstudio.microsoft.com/downloads/

# Install llama-cpp-python (CPU version)
pip install llama-cpp-python

# Verify installation
python -c "from llama_cpp import Llama; print('✓ llama-cpp-python installed')"
```

**Task 1.2: Create model download script**

```python
# File: scripts/download_models.py

from huggingface_hub import hf_hub_download
import os

MODEL_DIR = "./models"
os.makedirs(MODEL_DIR, exist_ok=True)

def download_liquid_tool():
    """Download Liquid-1.2B-Tool (GGUF quantized)"""
    print("Downloading Liquid-1.2B-Tool...")

    model_path = hf_hub_download(
        repo_id="LiquidAI/LiquidFoundry-1.2B-Tool-GGUF",
        filename="liquid-tool-1.2b-q4_k_m.gguf",
        local_dir=f"{MODEL_DIR}/liquid-tool",
        local_dir_use_symlinks=False
    )

    print(f"✓ Downloaded to: {model_path}")
    return model_path

def download_tinyllama():
    """Download TinyLlama for testing on 8GB RAM"""
    print("Downloading TinyLlama-1.1B...")

    model_path = hf_hub_download(
        repo_id="TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        filename="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        local_dir=f"{MODEL_DIR}/tinyllama",
        local_dir_use_symlinks=False
    )

    print(f"✓ Downloaded to: {model_path}")
    return model_path

def download_qwen_small():
    """Download Qwen2.5-0.5B for confidence checking"""
    print("Downloading Qwen2.5-0.5B...")

    model_path = hf_hub_download(
        repo_id="Qwen/Qwen2.5-0.5B-Instruct-GGUF",
        filename="qwen2.5-0.5b-instruct-q4_k_m.gguf",
        local_dir=f"{MODEL_DIR}/qwen-0.5b",
        local_dir_use_symlinks=False
    )

    print(f"✓ Downloaded to: {model_path}")
    return model_path

if __name__ == "__main__":
    print("=" * 60)
    print("LALO Model Downloader")
    print("=" * 60)

    # Download models for 8GB RAM CPU-only machine
    models = {
        "TinyLlama (testing)": download_tinyllama,
        "Liquid Tool (router)": download_liquid_tool,
        "Qwen 0.5B (confidence)": download_qwen_small
    }

    for name, func in models.items():
        print(f"\n[{name}]")
        try:
            func()
        except Exception as e:
            print(f"✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Download complete!")
    print("Total size: ~2-3 GB")
    print("=" * 60)
```

**Task 1.3: Download models**

```bash
python scripts/download_models.py
```

**Expected Output:**
```
============================================================
LALO Model Downloader
============================================================

[TinyLlama (testing)]
Downloading TinyLlama-1.1B...
✓ Downloaded to: ./models/tinyllama/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf

[Liquid Tool (router)]
Downloading Liquid-1.2B-Tool...
✓ Downloaded to: ./models/liquid-tool/liquid-tool-1.2b-q4_k_m.gguf

[Qwen 0.5B (confidence)]
Downloading Qwen2.5-0.5B...
✓ Downloaded to: ./models/qwen-0.5b/qwen2.5-0.5b-instruct-q4_k_m.gguf

============================================================
Download complete!
Total size: ~2-3 GB
============================================================
```

#### Afternoon: Test Basic Inference

**Task 1.4: Create test script**

```python
# File: scripts/test_local_inference.py

from llama_cpp import Llama
import time
import psutil
import os

def test_model(model_path: str, model_name: str):
    """Test a model and measure performance"""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"Path: {model_path}")
    print(f"{'='*60}")

    if not os.path.exists(model_path):
        print(f"✗ Model not found at {model_path}")
        return

    # Measure memory before loading
    process = psutil.Process()
    mem_before = process.memory_info().rss / (1024 ** 3)  # GB

    print(f"\nMemory before loading: {mem_before:.2f} GB")
    print("Loading model...")

    start_load = time.time()

    try:
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,         # Context window
            n_threads=4,        # CPU threads
            verbose=False
        )

        load_time = time.time() - start_load
        mem_after = process.memory_info().rss / (1024 ** 3)
        mem_used = mem_after - mem_before

        print(f"✓ Model loaded in {load_time:.2f}s")
        print(f"Memory after loading: {mem_after:.2f} GB (+{mem_used:.2f} GB)")

        # Test inference
        print("\nTesting inference...")
        prompt = "Hello, what can you do?"

        start_inference = time.time()

        output = llm(
            prompt,
            max_tokens=128,
            temperature=0.7,
            echo=False
        )

        inference_time = time.time() - start_inference
        response = output['choices'][0]['text']
        tokens_generated = output['usage']['completion_tokens']
        tokens_per_second = tokens_generated / inference_time if inference_time > 0 else 0

        print(f"\nPrompt: {prompt}")
        print(f"Response: {response[:200]}..." if len(response) > 200 else f"Response: {response}")
        print(f"\nPerformance:")
        print(f"  Time: {inference_time:.2f}s")
        print(f"  Tokens generated: {tokens_generated}")
        print(f"  Speed: {tokens_per_second:.2f} tok/s")

        # Unload model to free memory
        del llm

        return {
            "model": model_name,
            "load_time": load_time,
            "memory_used": mem_used,
            "inference_time": inference_time,
            "tokens_per_second": tokens_per_second,
            "success": True
        }

    except Exception as e:
        print(f"✗ Error: {e}")
        return {
            "model": model_name,
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    print("=" * 60)
    print("LALO Local Inference Test")
    print("=" * 60)

    # Test models in order of size (smallest first)
    models_to_test = [
        ("./models/qwen-0.5b/qwen2.5-0.5b-instruct-q4_k_m.gguf", "Qwen2.5-0.5B"),
        ("./models/tinyllama/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf", "TinyLlama-1.1B"),
        ("./models/liquid-tool/liquid-tool-1.2b-q4_k_m.gguf", "Liquid-Tool-1.2B"),
    ]

    results = []
    for model_path, model_name in models_to_test:
        result = test_model(model_path, model_name)
        if result:
            results.append(result)

        # Brief pause between tests
        time.sleep(2)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    if successful:
        print("\n✓ Successful Models:")
        for r in successful:
            print(f"  {r['model']}")
            print(f"    Load: {r['load_time']:.2f}s | Memory: {r['memory_used']:.2f}GB")
            print(f"    Speed: {r['tokens_per_second']:.2f} tok/s")

    if failed:
        print("\n✗ Failed Models:")
        for r in failed:
            print(f"  {r['model']}: {r.get('error', 'Unknown error')}")

    print("\n" + "=" * 60)
    print(f"Total: {len(successful)}/{len(results)} models working")
    print("=" * 60)
```

**Task 1.5: Run tests**

```bash
python scripts/test_local_inference.py
```

**Expected Results (8GB RAM):**
- Qwen-0.5B: 2-4 tok/s, ~800MB RAM
- TinyLlama-1.1B: 2-3 tok/s, ~1.2GB RAM
- Liquid-Tool-1.2B: 1-3 tok/s, ~1.5GB RAM

---

### Day 2: Create Inference Service (Saturday)

#### Morning: Implement LocalInferenceServer

**Task 2.1: Create service class**

```python
# File: core/services/local_llm_service.py

from llama_cpp import Llama
from typing import Dict, Optional, List, Any
import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class LocalInferenceServer:
    """
    Manages local model inference using llama.cpp

    Optimized for 8GB RAM CPU-only machine
    """

    def __init__(self, model_dir: str = "./models"):
        self.model_dir = model_dir
        self.models: Dict[str, Llama] = {}
        self.model_configs = {
            # Small models for 8GB RAM
            "qwen-0.5b": {
                "path": "qwen-0.5b/qwen2.5-0.5b-instruct-q4_k_m.gguf",
                "n_ctx": 2048,
                "n_threads": 2,
                "description": "Fast confidence scoring"
            },
            "tinyllama-1.1b": {
                "path": "tinyllama/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
                "n_ctx": 2048,
                "n_threads": 4,
                "description": "General purpose chat"
            },
            "liquid-tool-1.2b": {
                "path": "liquid-tool/liquid-tool-1.2b-q4_k_m.gguf",
                "n_ctx": 2048,
                "n_threads": 4,
                "description": "Function calling & routing"
            }
        }

        # Thread pool for async execution
        self.executor = ThreadPoolExecutor(max_workers=2)

        logger.info("LocalInferenceServer initialized")

    def load_model(self, model_name: str) -> bool:
        """Load a model into memory"""
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

    async def generate(
        self,
        prompt: str,
        model_name: str = "tinyllama-1.1b",
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Generate text completion asynchronously
        """
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

        result = await loop.run_in_executor(self.executor, _generate)

        return result['choices'][0]['text']

    async def generate_stream(
        self,
        prompt: str,
        model_name: str = "tinyllama-1.1b",
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Generate text with streaming (for real-time UI updates)
        """
        if model_name not in self.models:
            if not self.load_model(model_name):
                raise ValueError(f"Failed to load model: {model_name}")

        model = self.models[model_name]

        # Note: llama-cpp-python doesn't support true async streaming
        # This is a workaround that yields chunks
        loop = asyncio.get_event_loop()

        def _generate_stream():
            return model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                **kwargs
            )

        stream = await loop.run_in_executor(self.executor, _generate_stream)

        for chunk in stream:
            text = chunk['choices'][0]['text']
            yield text

    def get_available_models(self) -> List[Dict[str, Any]]:
        """List all available models"""
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
                "loaded": loaded
            })

        return available

    def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down LocalInferenceServer...")

        # Unload all models
        for model_name in list(self.models.keys()):
            self.unload_model(model_name)

        # Shutdown executor
        self.executor.shutdown(wait=True)

        logger.info("LocalInferenceServer shutdown complete")


# Global instance
local_llm_service = LocalInferenceServer()
```

**Task 2.2: Test the service**

```python
# File: scripts/test_service.py

import asyncio
from core.services.local_llm_service import local_llm_service

async def test_inference_service():
    print("Testing LocalInferenceServer...")

    # List available models
    models = local_llm_service.get_available_models()
    print("\nAvailable models:")
    for m in models:
        status = "✓" if m['downloaded'] else "✗"
        print(f"  {status} {m['name']}: {m['description']}")

    # Test generation
    print("\nTesting generation with TinyLlama...")
    response = await local_llm_service.generate(
        prompt="What is Python?",
        model_name="tinyllama-1.1b",
        max_tokens=100
    )

    print(f"Response: {response}")

    # Test streaming
    print("\nTesting streaming...")
    full_response = ""
    async for chunk in local_llm_service.generate_stream(
        prompt="Count to 5:",
        model_name="tinyllama-1.1b",
        max_tokens=50
    ):
        full_response += chunk
        print(chunk, end="", flush=True)

    print(f"\n\nFull response: {full_response}")

if __name__ == "__main__":
    asyncio.run(test_inference_service())
```

```bash
python scripts/test_service.py
```

#### Afternoon: Integrate with AIService

**Task 2.3: Create LocalAIModel wrapper**

```python
# File: core/models/local_model.py

from core.models.base import BaseAIModel
from core.services.local_llm_service import local_llm_service
from typing import Optional

class LocalAIModel(BaseAIModel):
    """Wrapper for local inference models"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.server = local_llm_service

    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """Generate using local model"""
        return await self.server.generate(
            prompt=prompt,
            model_name=self.model_name,
            max_tokens=max_tokens or 512,
            temperature=temperature or 0.7,
            **kwargs
        )

    async def stream(self, prompt: str, **kwargs):
        """Stream generation"""
        async for chunk in self.server.generate_stream(
            prompt=prompt,
            model_name=self.model_name,
            **kwargs
        ):
            yield chunk
```

**Task 2.4: Update AIService to include local models**

```python
# File: core/services/ai_service.py (additions)

from core.models.local_model import LocalAIModel

class AIService:
    def __init__(self):
        # ... existing code ...

        # Add local models for demo user
        self.models["demo-user@example.com"] = {
            # Local models (always available)
            "tiny llama-1.1b": LocalAIModel("tinyllama-1.1b"),
            "liquid-tool-1.2b": LocalAIModel("liquid-tool-1.2b"),
            "qwen-0.5b": LocalAIModel("qwen-0.5b"),

            # Cloud models (if API keys configured)
            # ... existing cloud models ...
        }
```

---

### Day 3: Router Model Implementation (Sunday)

#### All Day: Implement Intelligent Routing

**Task 3.1: Create RouterModel service**

```python
# File: core/services/router_model.py

from core.services.local_llm_service import local_llm_service
from typing import Dict, Literal
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

PathType = Literal["simple", "complex", "specialized"]

class RouterModel:
    """
    First-touch router that classifies requests and determines execution path

    Uses Liquid-Tool-1.2B for fast classification
    """

    def __init__(self):
        self.model_name = "liquid-tool-1.2b"
        self.server = local_llm_service

    async def route(self, user_request: str, context: Dict = None) -> Dict:
        """
        Analyze request and determine optimal execution path

        Returns:
        {
            "path": "simple" | "complex" | "specialized",
            "complexity": 0.0-1.0,
            "confidence": 0.0-1.0,
            "reasoning": str,
            "recommended_model": str,
            "requires_tools": bool,
            "requires_workflow": bool
        }
        """

        # Construct routing prompt
        prompt = f"""<|system|>
You are a router model. Analyze the user request and determine the optimal execution path.

Classify:
1. Complexity (0-1): How complex is this request?
   - 0.0-0.3: Simple factual question, direct answer
   - 0.3-0.6: Moderate, may need specialized model
   - 0.6-1.0: Complex, multi-step reasoning/workflow needed

2. Confidence (0-1): How confident are you about handling this?
   - <0.7: Need specialized model or validation
   - 0.7-0.9: Can handle with standard LLM
   - >0.9: Simple, direct answer

3. Path: simple | complex | specialized

Respond ONLY with valid JSON:
{{
  "complexity": <float 0-1>,
  "confidence": <float 0-1>,
  "path": "<simple|complex|specialized>",
  "reasoning": "<brief explanation>",
  "recommended_model": "<model name>",
  "requires_tools": <boolean>,
  "requires_workflow": <boolean>
}}
<|user|>
Request: {user_request}
Context: {context or "None"}
<|assistant|>
"""

        try:
            # Get routing decision
            result = await self.server.generate(
                prompt=prompt,
                model_name=self.model_name,
                max_tokens=256,
                temperature=0.3,  # Low temp for consistent routing
                stop=["<|user|>", "\n\n"]
            )

            # Parse JSON response
            decision = json.loads(result.strip())

            logger.info(f"Routing decision: {decision['path']} (complexity={decision['complexity']:.2f}, confidence={decision['confidence']:.2f})")

            return decision

        except json.JSONDecodeError:
            logger.warning(f"Failed to parse routing decision, using fallback")
            # Fallback to simple heuristic
            return await self._fallback_routing(user_request)
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return await self._fallback_routing(user_request)

    async def _fallback_routing(self, request: str) -> Dict:
        """Fallback routing using simple heuristics"""
        complexity = self.estimate_complexity_sync(request)

        return {
            "complexity": complexity,
            "confidence": 0.6,
            "path": "simple" if complexity < 0.5 else "complex",
            "reasoning": "Fallback heuristic routing",
            "recommended_model": "tinyllama-1.1b",
            "requires_tools": False,
            "requires_workflow": complexity > 0.6
        }

    def estimate_complexity_sync(self, request: str) -> float:
        """Quick complexity estimation using heuristics"""
        request_lower = request.lower()

        # Complexity indicators
        simple_keywords = ['what is', 'define', 'who is', 'when did']
        medium_keywords = ['how to', 'compare', 'explain', 'summarize']
        complex_keywords = ['design', 'analyze', 'research', 'create plan', 'optimize']

        if any(kw in request_lower for kw in complex_keywords):
            base_score = 0.8
        elif any(kw in request_lower for kw in medium_keywords):
            base_score = 0.5
        elif any(kw in request_lower for kw in simple_keywords):
            base_score = 0.2
        else:
            base_score = 0.4

        # Adjust based on length
        length_factor = min(len(request.split()) / 100, 0.3)

        return min(base_score + length_factor, 1.0)


# Global instance
router_model = RouterModel()
```

**Task 3.2: Update AI routes to use router**

```python
# File: core/routes/ai_routes.py (modifications)

from core.services.router_model import router_model
from core.services.local_llm_service import local_llm_service

@router.post("/ai/chat")
async def send_ai_request(
    request: AIRequest,
    current_user: str = Depends(get_current_user)
) -> AIResponse:
    """Send AI request with intelligent routing"""

    # Step 1: Route the request
    routing_decision = await router_model.route(request.prompt)

    logger.info(f"Request routed to {routing_decision['path']} path")

    # Step 2: Execute based on path
    if routing_decision['path'] == 'simple':
        # Direct local LLM response
        model_name = routing_decision.get('recommended_model', 'tinyllama-1.1b')

        response_text = await local_llm_service.generate(
            prompt=request.prompt,
            model_name=model_name,
            max_tokens=request.max_tokens or 512,
            temperature=request.temperature or 0.7
        )

        return AIResponse(
            id=str(uuid4()),
            response=response_text,
            model=model_name,
            usage={
                "prompt_tokens": len(request.prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(request.prompt.split()) + len(response_text.split())
            },
            created_at=datetime.now().isoformat(),
            routing_info=routing_decision  # Include routing metadata
        )

    else:
        # Complex path - will implement agent orchestrator later
        # For now, use best available model
        response_text = await local_llm_service.generate(
            prompt=request.prompt,
            model_name="liquid-tool-1.2b",
            max_tokens=request.max_tokens or 1024,
            temperature=request.temperature or 0.7
        )

        return AIResponse(
            id=str(uuid4()),
            response=response_text,
            model="liquid-tool-1.2b",
            usage={
                "prompt_tokens": len(request.prompt.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(request.prompt.split()) + len(response_text.split())
            },
            created_at=datetime.now().isoformat(),
            routing_info=routing_decision
        )
```

**Task 3.3: End-to-end test**

```bash
# Start backend
python app.py

# In browser: http://localhost:8000
# Login with demo token
# Submit request: "What is Python?"
# Should get response from local model
```

---

### Day 4-5: Weekend Testing & Bug Fixes (Monday-Tuesday)

- Test all request flows
- Measure performance
- Fix any issues
- Document findings
- Optimize memory usage

---

### Week 2: Frontend Integration & Polish

**Day 6-7: Update Frontend**
- Update model selector to show local models
- Remove cloud API key requirements
- Add model status indicators

**Day 8-9: Streaming Support**
- Implement streaming responses in frontend
- Add loading states
- Test with various request types

**Day 10: Documentation**
- Update user guide
- Create deployment guide
- Document performance benchmarks

---

## Success Criteria

### Day 1 Complete
- [ ] llama.cpp installed
- [ ] 3 models downloaded (TinyLlama, Liquid-Tool, Qwen)
- [ ] Basic inference working (2-5 tok/s)

### Day 2 Complete
- [ ] LocalInferenceServer implemented
- [ ] Service tests passing
- [ ] Integration with AIService complete

### Day 3 Complete
- [ ] RouterModel implemented
- [ ] End-to-end flow working: User → Router → Local LLM → Response
- [ ] No cloud API dependencies

### Week 2 Complete
- [ ] Frontend updated for local models
- [ ] Streaming working
- [ ] Documentation complete
- [ ] Ready for production testing

---

## Performance Targets

**8GB RAM CPU-only:**
- Simple requests: <5 seconds
- Complex requests: <30 seconds
- Memory usage: <6GB peak
- Models: 3 small models loaded

**RTX 4090+ (future):**
- Simple requests: <2 seconds
- Complex requests: <10 seconds
- Memory usage: <20GB VRAM
- Models: All models available

---

## Next Actions

1. **Install llama.cpp:** `pip install llama-cpp-python`
2. **Download models:** `python scripts/download_models.py`
3. **Test inference:** `python scripts/test_local_inference.py`
4. **Follow Day 2 tasks** tomorrow

**Let's build local LALO! 🚀**
