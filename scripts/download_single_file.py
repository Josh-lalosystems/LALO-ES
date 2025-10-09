"""
Download a single file from a Hugging Face repo into ./models/<repo-slug>
Usage:
  .\venv\Scripts\python.exe scripts\download_single_file.py <repo_id> <filename>
Example:
  .\venv\Scripts\python.exe scripts\download_single_file.py silveroxides/flux1-nf4-weights flux1-bitte-guidance-bnb-nf4.safetensors
"""
import sys
from huggingface_hub import hf_hub_download
import os

if len(sys.argv) != 3:
    print("Usage: download_single_file.py <repo_id> <filename>")
    sys.exit(2)

repo = sys.argv[1]
filename = sys.argv[2]

model_dir = os.path.join('.', 'models', repo.split('/')[-1])
os.makedirs(model_dir, exist_ok=True)

try:
    print(f"Downloading {filename} from {repo} to {model_dir}...")
    path = hf_hub_download(repo_id=repo, filename=filename, local_dir=model_dir, local_dir_use_symlinks=False)
    size_gb = os.path.getsize(path) / (1024**3)
    print(f"✓ Downloaded: {path} ({size_gb:.2f} GB)")
    sys.exit(0)
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(3)
