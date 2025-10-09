"""
Download FLUX model files (GGUF or safetensors) from Hugging Face repos.
Usage:
  .\venv\Scripts\python.exe scripts\download_flux_models.py

Requires HF auth (huggingface-cli login or HUGGINGFACE_HUB_TOKEN env var).
"""
from huggingface_hub import list_repo_files, hf_hub_download
import os
import sys

MODEL_DIR = "./models"
REPOS = [
    "black-forest-labs/FLUX.1-schnell",
    "silveroxides/flux1-nf4-weights",
]

os.makedirs(MODEL_DIR, exist_ok=True)

success = []
failures = []

for repo in REPOS:
    print('\n' + '='*60)
    print(f"Repo: {repo}")
    try:
        files = list_repo_files(repo_id=repo)
    except Exception as e:
        print(f"✗ Failed to list files for {repo}: {e}")
        failures.append((repo, str(e)))
        continue

    # Filter for likely model files
    model_files = [f for f in files if f.lower().endswith(('.gguf', '.safetensors', '.pt', '.bin'))]
    if not model_files:
        print(f"✗ No model files (.gguf/.safetensors/.pt/.bin) found in {repo}")
        failures.append((repo, 'no model files found'))
        continue

    repo_slug = repo.split('/')[-1]
    dest_dir = os.path.join(MODEL_DIR, repo_slug)
    os.makedirs(dest_dir, exist_ok=True)

    for fname in model_files:
        print(f"-> Found: {fname}")
        try:
            print(f"   Downloading {fname} to {dest_dir} ...")
            path = hf_hub_download(repo_id=repo, filename=fname, local_dir=dest_dir, local_dir_use_symlinks=False)
            size_gb = os.path.getsize(path) / (1024**3)
            print(f"   ✓ Downloaded: {path} ({size_gb:.2f} GB)")
            success.append((repo, fname, path))
        except Exception as e:
            print(f"   ✗ Failed to download {fname}: {e}")
            failures.append((repo, fname, str(e)))

print('\n' + '='*60)
print('Download summary')
print('='*60)
print(f"Successful files: {len(success)}")
if success:
    for s in success:
        print(f" - {s[0]} : {s[1]} -> {s[2]}")
print(f"Failures: {len(failures)}")
if failures:
    for f in failures:
        print(f" - {f}")

if failures:
    sys.exit(2)
else:
    sys.exit(0)
