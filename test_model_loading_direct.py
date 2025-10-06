#!/usr/bin/env python3
"""Direct test of llama-cpp model loading (bypasses server)"""
import sys
import os
import time
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("DIRECT MODEL LOADING TEST (llama-cpp-python)")
print("=" * 70)

# Check if llama-cpp-python is installed
print("\n1. Checking llama-cpp-python installation...")
try:
    from llama_cpp import Llama
    print("✓ llama-cpp-python is installed")
except ImportError as e:
    print(f"✗ llama-cpp-python NOT installed: {e}")
    print("\nInstall with: pip install llama-cpp-python")
    sys.exit(1)

# Find smallest model
models_dir = Path("c:/IT/LALOai-main/models")
print(f"\n2. Looking for models in {models_dir}...")

model_files = []
for model_path in models_dir.rglob("*.gguf"):
    size_mb = model_path.stat().st_size / (1024 * 1024)
    model_files.append((model_path, size_mb))
    print(f"   Found: {model_path.name} ({size_mb:.1f} MB)")

if not model_files:
    print("✗ No GGUF models found!")
    sys.exit(1)

# Use smallest model
model_files.sort(key=lambda x: x[1])
model_path, model_size = model_files[0]
print(f"\n3. Testing with SMALLEST model: {model_path.name} ({model_size:.1f} MB)")

# Test model loading with timeout
print("\n4. Attempting to load model...")
print("   Config: n_ctx=512, n_threads=4, verbose=False")
print("   Timeout: 60 seconds")

start_time = time.time()
try:
    print("   Loading... (this may take 10-30 seconds)")
    llm = Llama(
        model_path=str(model_path),
        n_ctx=512,  # Small context to load faster
        n_threads=4,  # Use 4 CPU threads
        verbose=False  # Suppress llama.cpp logs
    )
    load_time = time.time() - start_time
    print(f"✓ Model loaded successfully in {load_time:.1f} seconds!")

except Exception as e:
    load_time = time.time() - start_time
    print(f"✗ Model loading FAILED after {load_time:.1f} seconds")
    print(f"   Error: {e}")
    sys.exit(1)

# Test inference
print("\n5. Testing inference...")
print("   Prompt: 'Hello, how are you?'")
print("   Max tokens: 50")

try:
    start_time = time.time()
    output = llm(
        "Hello, how are you?",
        max_tokens=50,
        temperature=0.7,
        stop=["User:", "\n\n"]
    )
    inference_time = time.time() - start_time

    response_text = output['choices'][0]['text']
    print(f"\n✓ Inference completed in {inference_time:.2f} seconds")
    print(f"\nResponse:\n---\n{response_text}\n---")

except Exception as e:
    inference_time = time.time() - start_time
    print(f"✗ Inference FAILED after {inference_time:.2f} seconds")
    print(f"   Error: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("TEST RESULTS")
print("=" * 70)
print(f"Model: {model_path.name}")
print(f"Size: {model_size:.1f} MB")
print(f"Load Time: {load_time:.1f}s")
print(f"Inference Time: {inference_time:.2f}s")
print("\n✅ ALL TESTS PASSED!")
print("\nNext steps:")
print("  1. Update local_llm_service.py with successful config")
print("  2. Restart server")
print("  3. Test via HTTP endpoint")
print("=" * 70)
