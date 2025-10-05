# Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This file is part of LALO AI Platform and is protected by copyright law.
# Unauthorized copying, modification, distribution, or use of this software,
# via any medium, is strictly prohibited without the express written permission
# of LALO AI SYSTEMS, LLC.
#

# Start Here: Local Inference on Your 8GB Machine

## What We're Building

A **100% local, 100% open-source** inference engine for LALO that:
- ✅ Runs on your 8GB RAM, CPU-only Windows machine
- ✅ Uses only MIT/Apache licensed components (can sell!)
- ✅ No Ollama (proprietary)
- ✅ No cloud APIs (OpenAI/Anthropic)
- ✅ Latency doesn't matter (accuracy does)

## The Stack

1. **llama.cpp** (MIT) - Inference engine
2. **llama-cpp-python** (MIT) - Python bindings
3. **Liquid Nanos** (Apache 2.0) - Small, capable models
4. **Your LALO platform** - Proprietary wrapper you sell

## Week 1 Tasks: Get It Running

### Day 1: Install llama.cpp

#### On Windows (Your Machine):
```bash
# Install build tools first
# Download from: https://visualstudio.microsoft.com/downloads/
# Get "Build Tools for Visual Studio 2022"
# Select: C++ build tools

# OR use pre-built binaries
# Download from: https://github.com/ggerganov/llama.cpp/releases
# Look for: llama-*-windows.zip

# OR build from source with CMake
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build with CMake
mkdir build
cd build
cmake ..
cmake --build . --config Release

# Test it
cd ..
build\bin\Release\main.exe --help
```

**Success check:** You see help output listing command options

### Day 2: Install Python Bindings

```bash
# Install llama-cpp-python
pip install llama-cpp-python

# Test it
python -c "import logging; logging.basicConfig(level=logging.INFO); from llama_cpp import Llama; logging.getLogger('lalo.docs').info('✓ llama-cpp-python installed')"
```

**Success check:** No errors, prints "✓ llama-cpp-python installed"

### Day 3: Download Small Model

```python
# File: test_download.py
from huggingface_hub import hf_hub_download
import os

# Create models directory
os.makedirs("./models", exist_ok=True)

# Download TinyLlama 1.1B (good for testing on 8GB)
print("Downloading TinyLlama 1.1B (4-bit, ~700MB)...")
model_path = hf_hub_download(
    repo_id="TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
    filename="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
    local_dir="./models"
)

print(f"✓ Downloaded to: {model_path}")
print(f"✓ File size: {os.path.getsize(model_path) / 1024**2:.0f} MB")
```

Run it:
```bash
python test_download.py
```

**Success check:** Model downloads, ~700MB file in `./models/` directory

### Day 4: Test Inference

```python
# File: test_inference.py
from llama_cpp import Llama
import time

print("Loading model...")
start = time.time()

llm = Llama(
    model_path="./models/models--TheBloke--TinyLlama-1.1B-Chat-v1.0-GGUF/snapshots/.../tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
    n_ctx=2048,       # Context window
    n_threads=4,      # CPU threads (adjust for your CPU)
    verbose=False
)

load_time = time.time() - start
print(f"✓ Model loaded in {load_time:.1f}s")
print(f"✓ RAM usage: Check Task Manager (should be 1-2GB)")

# Test generation
print("\nGenerating response...")
start = time.time()

output = llm(
    "Q: What is Python? A:",
    max_tokens=128,
    temperature=0.7,
    stop=["Q:", "\n\n"]
)

gen_time = time.time() - start
text = output['choices'][0]['text']
tokens = output['usage']['completion_tokens']

print(f"✓ Generated in {gen_time:.1f}s")
print(f"✓ Speed: {tokens/gen_time:.1f} tokens/sec")
print(f"\nResponse:\n{text}")
```

Run it:
```bash
python test_inference.py
```

**Success check:**
- Model loads (5-10s on CPU)
- Generates response (10-20s)
- Speed: 2-10 tokens/sec (CPU-only is normal)
- RAM usage: <3GB total

### Day 5: Integrate with LALO

Create the service:
```python
# File: core/services/local_llm_service.py

from llama_cpp import Llama
from typing import Optional, Dict
import asyncio
from pathlib import Path

class LocalLLMService:
    """
    Local LLM inference using llama.cpp

    License: MIT (llama.cpp) + Apache 2.0 (models)
    Can be sold/distributed commercially!
    """

    def __init__(self):
        self.models: Dict[str, Llama] = {}
        self.models_dir = Path("./models")

    def load_model(self, model_name: str, model_path: str, n_threads: int = 4):
        """Load a GGUF model"""
        print(f"Loading {model_name}...")

        self.models[model_name] = Llama(
            model_path=str(model_path),
            n_ctx=2048,
            n_threads=n_threads,
            verbose=False
        )

        print(f"✓ {model_name} loaded")

    async def generate(
        self,
        prompt: str,
        model_name: str = "default",
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response asynchronously"""

        model = self.models.get(model_name)
        if not model:
            raise ValueError(f"Model '{model_name}' not loaded. Available: {list(self.models.keys())}")

        # Run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: model(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
        )

        return result['choices'][0]['text']

    def list_models(self) -> list:
        """List loaded models"""
        return list(self.models.keys())


# Global instance
local_llm_service = LocalLLMService()

# Load default model on startup
def initialize_local_models():
    """Initialize models at startup"""
    try:
        # Load TinyLlama as default
        tiny_path = Path("./models/models--TheBloke--TinyLlama-1.1B-Chat-v1.0-GGUF/snapshots")

        # Find the actual file
        gguf_files = list(tiny_path.glob("**/*.gguf"))
        if gguf_files:
            local_llm_service.load_model("tinyllama", gguf_files[0])
            print("✓ Local models initialized")
        else:
            print("⚠️  No models found. Run: python test_download.py")
    except Exception as e:
        print(f"⚠️  Could not load local models: {e}")
        print("Run: python test_download.py")
```

Update app.py startup:
```python
# File: app.py (add to startup)

from core.services.local_llm_service import initialize_local_models

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("="*50)
    print("LALO AI Platform - Starting Local Inference")
    print("="*50)

    # Load local models
    initialize_local_models()

    print("✓ Startup complete")
```

Test endpoint:
```python
# File: core/routes/ai_routes.py (add test endpoint)

from core.services.local_llm_service import local_llm_service

@router.get("/api/ai/local/models")
async def list_local_models():
    """List available local models"""
    return {
        "models": local_llm_service.list_models(),
        "backend": "llama.cpp (MIT licensed)",
        "status": "ready"
    }

@router.post("/api/ai/local/test")
async def test_local_inference(prompt: str = "Hello, who are you?"):
    """Test local inference"""
    models = local_llm_service.list_models()
    if not models:
        return {"error": "No models loaded"}

    result = await local_llm_service.generate(
        prompt=prompt,
        model_name=models[0],
        max_tokens=128
    )

    return {
        "prompt": prompt,
        "response": result,
        "model": models[0]
    }
```

Test it:
```bash
# Start LALO
python app.py

# In browser or curl:
# http://localhost:8000/api/ai/local/models
# http://localhost:8000/api/ai/local/test?prompt=What+is+AI
```

## What You'll Have After Week 1

✅ llama.cpp installed and working
✅ Python bindings functional
✅ Small model (TinyLlama) running on CPU
✅ LocalLLMService integrated with LALO
✅ Test endpoint confirming it works
✅ ~2-5 tokens/sec generation (acceptable for development)
✅ NO cloud dependencies
✅ NO API keys needed
✅ 100% local, 100% sellable

## Memory Usage Breakdown (8GB Machine)

- Windows OS: 2-3GB
- LALO Backend: 500MB
- TinyLlama 1.1B (4-bit): 1-2GB
- **Total: 4-6GB** ✓ Fits comfortably!

You'll have 2-4GB free for browser, IDE, etc.

## Next Steps (Week 2)

Once Week 1 works:

1. Download Liquid Nanos models (better quality)
2. Add model router (auto-select best model)
3. Remove OpenAI/Anthropic code completely
4. Update frontend to show "Local Model"
5. Test tool calling with Liquid Tool 1.2B

## Troubleshooting

### Issue: Model loads slowly
**Expected:** 5-15 seconds on CPU is normal
**Solution:** Use 4-bit quantized models (.Q4_K_M.gguf)

### Issue: Out of memory
**Solution:** Use smaller model (TinyLlama 1.1B) or close other apps

### Issue: Generation is slow
**Expected:** 2-5 tok/s on CPU is normal for development
**Note:** Clients will have better hardware (GPUs)

### Issue: Model file not found
**Solution:** Check path with: `dir models /s /b`

## Cost Analysis

### Development (Your Machine):
- Hardware: $0 (existing computer)
- Software: $0 (all open source)
- Models: $0 (free download)
- API costs: $0 (no cloud!)

### Client Deployment:
- Entry tier: $500 (8-core CPU, 16GB RAM)
- Standard tier: $2,000 (12-core + GPU)
- Enterprise: $10,000+ (server hardware)

### What You Can Charge:
- Per-seat license: $50-200/user/year
- One-time: $5,000-50,000 (based on size)
- Support contract: $1,000-10,000/year
- Custom training: $10,000-100,000

**Your IP:** The LALO platform, not the models!

## Legal: What You Can Sell

✅ **LALO platform code** - Your proprietary software
✅ **Integration layer** - Your unique architecture
✅ **Bundled models** - Liquid/Llama (with attribution)
✅ **Support services** - Training, customization
✅ **Managed hosting** - Run LALO for clients
✅ **Custom fine-tuning** - Client-specific models

You're building a **platform**, not just wrapping APIs!

## Questions?

Before proceeding, make sure:
- [ ] llama.cpp compiles/runs on your machine
- [ ] Python bindings import successfully
- [ ] Small model downloads and loads
- [ ] Generation works (even if slow)
- [ ] You understand licensing (MIT + Apache = sellable!)

Once these work, you're ready for Week 2!

---

**Start with Day 1 and let me know when you hit any blockers.** We'll solve them step by step.
