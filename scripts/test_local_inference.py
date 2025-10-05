"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
LALO Local Inference Test Script

Tests local models with llama.cpp to verify:
- Model files are downloaded correctly
- Models load successfully
- Inference works (generates responses)
- Performance metrics (tokens/sec, memory usage)

Usage:
    python scripts/test_local_inference.py [--model MODEL_NAME] [--quick]

Examples:
    python scripts/test_local_inference.py --quick       # Test all models with short prompts
    python scripts/test_local_inference.py --model tinyllama
"""

import os
import sys
import time
import argparse
import psutil
from typing import Dict, Optional

# Check if llama-cpp-python is installed
try:
    from llama_cpp import Llama
except ImportError:
    print("✗ llama-cpp-python not installed!")
    print("\nInstall with:")
    print("  pip install llama-cpp-python")
    print("\nFor GPU support (if available):")
    print("  pip install llama-cpp-python --force-reinstall --no-cache-dir")
    sys.exit(1)

# Model directory
MODEL_DIR = "./models"

# Model configurations
MODELS = {
    "qwen-0.5b": {
        "path": "qwen-0.5b/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "n_ctx": 2048,
        "n_threads": 2,
        "description": "Qwen2.5-0.5B (Confidence scoring)"
    },
    "tinyllama": {
        "path": "tinyllama/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "n_ctx": 2048,
        "n_threads": 4,
        "description": "TinyLlama-1.1B (General purpose)"
    },
    "liquid-tool": {
        "path": "liquid-tool/Liquid-1.2B-Tool-Q4_K_M.gguf",
        "n_ctx": 2048,
        "n_threads": 4,
        "description": "Liquid-Tool-1.2B (Routing & function calling)"
    }
}

# Test prompts
TEST_PROMPTS = {
    "quick": "Hello, what can you do?",
    "normal": "Explain what Python is in 2-3 sentences.",
    "complex": "Write a short poem about artificial intelligence."
}


def check_system_resources():
    """Check system memory and CPU"""
    memory = psutil.virtual_memory()
    cpu_count = psutil.cpu_count()

    print("="*60)
    print("System Resources")
    print("="*60)
    print(f"Total RAM: {memory.total / (1024**3):.2f} GB")
    print(f"Available RAM: {memory.available / (1024**3):.2f} GB")
    print(f"CPU cores: {cpu_count}")
    print("="*60)

    if memory.available / (1024**3) < 2:
        print("⚠️  Warning: Less than 2GB RAM available")
        print("   Consider closing other applications")


def test_model(model_key: str, prompt: str = None, max_tokens: int = 128) -> Optional[Dict]:
    """Test a specific model"""
    if model_key not in MODELS:
        print(f"✗ Unknown model: {model_key}")
        return None

    config = MODELS[model_key]
    model_path = os.path.join(MODEL_DIR, config["path"])

    if not os.path.exists(model_path):
        print(f"\n✗ Model not found: {config['description']}")
        print(f"  Expected path: {model_path}")
        print(f"  Run: python scripts/download_models.py --model {model_key}")
        return None

    print(f"\n{'='*60}")
    print(f"Testing: {config['description']}")
    print(f"{'='*60}")
    print(f"Path: {model_path}")

    # Get process memory before loading
    process = psutil.Process()
    mem_before = process.memory_info().rss / (1024 ** 3)  # GB

    print(f"Memory before loading: {mem_before:.2f} GB")
    print("Loading model...")

    start_load = time.time()

    try:
        llm = Llama(
            model_path=model_path,
            n_ctx=config["n_ctx"],
            n_threads=config["n_threads"],
            verbose=False
        )

        load_time = time.time() - start_load
        mem_after = process.memory_info().rss / (1024 ** 3)
        mem_used = mem_after - mem_before

        print(f"✓ Model loaded in {load_time:.2f}s")
        print(f"Memory after loading: {mem_after:.2f} GB (+{mem_used:.2f} GB)")

        # Test inference
        test_prompt = prompt or TEST_PROMPTS["quick"]
        print(f"\nTesting inference...")
        print(f"Prompt: \"{test_prompt}\"")

        start_inference = time.time()

        output = llm(
            test_prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=0.95,
            echo=False
        )

        inference_time = time.time() - start_inference
        response = output['choices'][0]['text'].strip()
        tokens_generated = output['usage']['completion_tokens']
        tokens_per_second = tokens_generated / inference_time if inference_time > 0 else 0

        print(f"\n--- Response ---")
        print(response[:300] + ("..." if len(response) > 300 else ""))
        print(f"--- End Response ---")

        print(f"\nPerformance:")
        print(f"  Inference time: {inference_time:.2f}s")
        print(f"  Tokens generated: {tokens_generated}")
        print(f"  Speed: {tokens_per_second:.2f} tok/s")

        # Performance rating
        if tokens_per_second >= 10:
            rating = "Excellent ✓"
        elif tokens_per_second >= 5:
            rating = "Good ✓"
        elif tokens_per_second >= 2:
            rating = "Acceptable ✓"
        else:
            rating = "Slow ⚠"

        print(f"  Rating: {rating}")

        # Clean up
        del llm

        return {
            "model": model_key,
            "description": config["description"],
            "load_time": load_time,
            "memory_used": mem_used,
            "inference_time": inference_time,
            "tokens_generated": tokens_generated,
            "tokens_per_second": tokens_per_second,
            "response": response,
            "success": True
        }

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "model": model_key,
            "description": config["description"],
            "success": False,
            "error": str(e)
        }


def test_all_models(quick: bool = True):
    """Test all available models"""
    prompt_type = "quick" if quick else "normal"
    max_tokens = 64 if quick else 128

    print("\n" + "="*60)
    print("LALO Local Inference Test - All Models")
    print("="*60)
    print(f"Test mode: {'Quick' if quick else 'Normal'}")
    print(f"Prompt: \"{TEST_PROMPTS[prompt_type]}\"")
    print(f"Max tokens: {max_tokens}")
    print("="*60)

    # Test models in order of size (smallest first)
    models_to_test = ["qwen-0.5b", "tinyllama", "liquid-tool"]

    results = []
    for model_key in models_to_test:
        result = test_model(model_key, TEST_PROMPTS[prompt_type], max_tokens)
        if result:
            results.append(result)

        # Brief pause between tests
        time.sleep(1)

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    if successful:
        print("\n✓ Successful Models:")
        print(f"{'Model':<20} {'Load Time':<12} {'Memory':<12} {'Speed':<12}")
        print("-" * 60)
        for r in successful:
            print(f"{r['model']:<20} {r['load_time']:>8.2f}s    {r['memory_used']:>6.2f} GB    {r['tokens_per_second']:>6.2f} tok/s")

    if failed:
        print("\n✗ Failed Models:")
        for r in failed:
            print(f"  {r['model']}: {r.get('error', 'Unknown error')}")

    print("\n" + "="*60)
    print(f"Results: {len(successful)}/{len(results)} models working")

    if len(successful) == len(results):
        print("\n✓ All models working!")
        print("\nNext steps:")
        print("  1. Start backend: python app.py")
        print("  2. Test via API: http://localhost:8000")
        print("  3. Submit request in UI")
    elif len(successful) > 0:
        print(f"\n⚠  Some models failed, but {len(successful)} working")
        print("  You can proceed with working models")
    else:
        print("\n✗ All tests failed!")
        print("  Check errors above and verify:")
        print("  - llama-cpp-python is installed correctly")
        print("  - Model files are downloaded")
        print("  - Sufficient RAM available (>2GB free)")

    print("="*60)

    return len(successful) == len(results)


def main():
    parser = argparse.ArgumentParser(
        description="Test LALO local inference models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Quick test all models:
    python scripts/test_local_inference.py --quick

  Normal test all models:
    python scripts/test_local_inference.py

  Test specific model:
    python scripts/test_local_inference.py --model tinyllama
        """
    )

    parser.add_argument(
        "--model",
        type=str,
        help="Test specific model (qwen-0.5b, tinyllama, liquid-tool)"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick test (short prompts, less tokens)"
    )

    parser.add_argument(
        "--prompt",
        type=str,
        help="Custom prompt to test"
    )

    parser.add_argument(
        "--tokens",
        type=int,
        default=128,
        help="Max tokens to generate (default: 128)"
    )

    args = parser.parse_args()

    # Check system resources
    check_system_resources()

    # Execute test
    if args.model:
        # Test specific model
        prompt = args.prompt or TEST_PROMPTS["normal"]
        result = test_model(args.model, prompt, args.tokens)
        sys.exit(0 if result and result.get('success') else 1)
    else:
        # Test all models
        success = test_all_models(quick=args.quick)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
