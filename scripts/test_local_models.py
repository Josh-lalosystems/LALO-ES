"""
Quick smoke-test loader for local models (GGUF) using llama-cpp-python.
Usage:
  .\venv\Scripts\python.exe scripts\test_local_models.py --max 2

What it does:
 - Scans ./models for .gguf files
 - Sorts by file size (smallest first)
 - Attempts to load up to --max models with llama-cpp-python and generate a short response
 - Reports success/failure and timing

Note: This should be run in the project's venv. Loading large models may be slow or OOM.
"""
import os
import sys
import time
import argparse
from pathlib import Path

try:
    from llama_cpp import Llama
except Exception as e:
    print("llama-cpp-python is not available or failed to import:", e)
    sys.exit(2)

MODEL_ROOT = Path("./models")

parser = argparse.ArgumentParser(description="Test local GGUF models with llama-cpp-python")
parser.add_argument("--max", type=int, default=1, help="Maximum number of models to test (default 1)")
parser.add_argument("--timeout", type=int, default=30, help="Per-model generation timeout in seconds")
args = parser.parse_args()

# Find gguf files
gguf_files = list(MODEL_ROOT.rglob("*.gguf"))

if not gguf_files:
    print("No .gguf files found under ./models. Nothing to test.")
    sys.exit(0)

# Sort by file size (ascending) to prefer smaller models
gguf_files.sort(key=lambda p: p.stat().st_size)

to_test = gguf_files[: args.max]

print(f"Found {len(gguf_files)} .gguf files, testing {len(to_test)} (smallest first):")
for p in to_test:
    size_gb = p.stat().st_size / (1024 ** 3)
    print(f" - {p} ({size_gb:.2f} GB)")


def attempt_load_and_generate(model_path: Path, timeout: int = 30):
    print('\n' + '='*60)
    print(f"Testing model: {model_path}")
    start = time.time()
    try:
        print("Loading model into llama-cpp-python (this may take a few seconds)...")
        llm = Llama(model_path=str(model_path))
        load_time = time.time() - start
        print(f"Loaded model in {load_time:.2f}s")

        prompt = "Hello from LALO test. Say hi and give a 6-word response."
        print(f"Generating a short sample (timeout {timeout}s)...")
        gen_start = time.time()

        # Try common API variants
        resp = None
        try:
            resp = llm.create_completion(prompt=prompt, max_tokens=16, temperature=0.7)
            text = resp.get('choices', [{}])[0].get('text') if isinstance(resp, dict) else str(resp)
        except Exception:
            try:
                # older/newer APIs
                out = llm(prompt=prompt, max_tokens=16, temperature=0.7)
                # when called, llama-cpp-python may return object with 'choices'
                if isinstance(out, dict):
                    text = out.get('choices', [{}])[0].get('text')
                else:
                    text = str(out)
            except Exception as e:
                print("Generation failed:", e)
                return False

        gen_time = time.time() - gen_start
        print(f"Generated in {gen_time:.2f}s")
        print("--- Sample output ---")
        print(text)
        print("--- End sample ---")
        return True
    except Exception as e:
        print(f"Failed to load or generate with model {model_path}: {e}")
        return False

# Run tests
results = []
for p in to_test:
    ok = attempt_load_and_generate(p, timeout=args.timeout)
    results.append((p, ok))

print('\n' + '='*60)
print('Summary:')
for p, ok in results:
    print(f" - {p.name}: {'OK' if ok else 'FAIL'}")

failed = [p for p, ok in results if not ok]
if failed:
    print("Some models failed to load/generate. Inspect logs above or try a smaller model or more memory.")
    sys.exit(1)
else:
    print("All tested models loaded and generated successfully.")
    sys.exit(0)
