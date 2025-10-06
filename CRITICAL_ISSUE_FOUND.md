# CRITICAL ISSUE: Model Loading Timeout

**Date**: 2025-10-05 17:25
**Severity**: BLOCKER
**Status**: IDENTIFIED

---

## Problem

**Model loading hangs indefinitely** when trying to load TinyLlama with llama-cpp-python.

### Evidence

1. **Direct test hangs** at model loading step
2. **API requests timeout** (500 error) because they wait for model to load
3. **Server appears functional** but all inference requests fail

### Root Cause

**llama-cpp-python model loading is blocking and takes too long (>60 seconds) or hangs completely**

Possible reasons:
1. CPU-only inference is extremely slow
2. Model file format incompatibility
3. Insufficient RAM
4. llama-cpp-python configuration issue
5. Windows-specific issue with file loading

---

## Impact

- ❌ **NO local inference working**
- ❌ **All AI requests fail**
- ❌ **Cannot test end-to-end flow**
- ❌ **Installer would ship broken product**

---

## Solutions

### Option 1: Fix llama-cpp-python Configuration (RECOMMENDED)
**Time**: 30-60 minutes

**Actions**:
1. Check llama-cpp-python is CPU-optimized build
2. Try smaller model first (Qwen 0.5B)
3. Add timeout and fallback to heuristics
4. Test with different n_threads settings

**Test**:
```python
# Try with minimal context and threads
model = Llama(
    model_path="models/qwen-0.5b/qwen2.5-0.5b-instruct-q4_k_m.gguf",
    n_ctx=512,  # Small context
    n_threads=2,  # Fewer threads
    n_batch=128,
    verbose=True
)
```

### Option 2: Use Heuristic Fallback for MVP (QUICK FIX)
**Time**: 15 minutes

**Actions**:
1. Disable actual model loading in DEMO_MODE
2. Use `_heuristic_generate()` for all requests
3. Return canned responses based on keywords
4. Document as "Demo Mode - Local models coming soon"

**Implementation**:
```python
# In local_llm_service.py
async def generate(...):
    if os.getenv("DEMO_MODE") == "true":
        # Always use heuristics in demo mode
        return self._heuristic_generate(prompt, model_name)

    # Try real model loading (production only)
    ...
```

### Option 3: Switch to Ollama Backend
**Time**: 2-3 hours

**Actions**:
1. Install Ollama
2. Download models via Ollama
3. Replace llama-cpp-python with Ollama API calls
4. Test integration

**Pros**:
- Faster inference
- Better model management
- Optimized binaries

**Cons**:
- Additional dependency
- Larger installer
- Need to bundle Ollama

### Option 4: Cloud-Only MVP
**Time**: 5 minutes

**Actions**:
1. Document that local models are optional
2. Require OpenAI/Anthropic API keys
3. Ship with cloud inference only
4. Add local models in v2

---

## Recommendation

**Use Option 2 (Heuristic Fallback) IMMEDIATELY for testing**

Then work on Option 1 (Fix llama-cpp) in parallel

**Why**:
- Unblocks testing and installer build NOW
- Can still demonstrate routing, tools, feedback
- Buy time to properly debug llama-cpp
- Users see working system even without models loaded

---

## Implementation Plan

### Step 1: Quick Heuristic Fallback (15 min)
```python
# core/services/local_llm_service.py

async def generate(self, prompt, model_name="tinyllama", **kwargs):
    """Generate with automatic fallback"""

    # DEMO MODE: Always use heuristics
    if os.getenv("DEMO_MODE", "false").lower() == "true":
        logger.info(f"[DEMO] Using heuristic generation for {model_name}")
        return self._heuristic_generate(prompt, model_name)

    # Production: Try real models with timeout
    try:
        # Existing model loading code
        ...
    except TimeoutError:
        logger.warning("Model loading timed out, falling back to heuristics")
        return self._heuristic_generate(prompt, model_name)
```

### Step 2: Enhance Heuristics (30 min)
Make `_heuristic_generate()` smarter:
- Better math detection and solving
- Code generation templates
- Research responses
- Sentiment-aware replies

### Step 3: Add Loading Indicator (15 min)
```python
# Show "Loading models..." in UI
# Document expected wait time
# Add progress bar if possible
```

### Step 4: Debug llama-cpp (1-2 hours)
- Test with smaller model
- Check CPU optimization flags
- Try different llama-cpp-python versions
- Monitor RAM usage during load
- Test on different machine

---

## Next Actions

**IMMEDIATE** (Do now):
1. Implement heuristic fallback
2. Test end-to-end with heuristics
3. Verify installer can be built

**PARALLEL** (Other team):
1. Debug llama-cpp-python
2. Test smaller models
3. Research Ollama alternative

**DECISION POINT** (Tomorrow):
- If llama-cpp fixed → Use real models
- If not → Ship with heuristics + cloud
- Document roadmap for local models

---

*Priority*: CRITICAL - BLOCKER
*Owner*: Immediate fix required
*Deadline*: Today (to unblock installer)
