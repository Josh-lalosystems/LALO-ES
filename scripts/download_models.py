"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
LALO Model Downloader

Downloads quantized models optimized for 8GB RAM CPU-only development machine.
Models are downloaded from HuggingFace and stored in ./models directory.

Usage:
    python scripts/download_models.py [--all | --model MODEL_NAME]

Examples:
    python scripts/download_models.py --all
    python scripts/download_models.py --model tinyllama
"""

from huggingface_hub import hf_hub_download
import os
import argparse
import sys

# Model directory
MODEL_DIR = "./models"

# Model configurations
MODELS = {
    "tinyllama": {
        "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "size": "669 MB",
        "description": "TinyLlama 1.1B - Fast general-purpose chat model"
    },
    "liquid-tool": {
        "repo_id": "second-state/Liquid-1.2B-Tool-GGUF",
        "filename": "Liquid-1.2B-Tool-Q4_K_M.gguf",
        "size": "752 MB",
        "description": "Liquid Tool 1.2B - Function calling and routing"
    },
    "qwen-0.5b": {
        "repo_id": "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
        "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "size": "352 MB",
        "description": "Qwen 0.5B - Confidence scoring and validation"
    },
    "qwen-3b": {
        "repo_id": "Qwen/Qwen2.5-3B-Instruct-GGUF",
        "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "size": "1.9 GB",
        "description": "Qwen 3B - Better quality for complex tasks (optional)"
    }
}


def create_model_directory():
    """Create model directory if it doesn't exist"""
    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"✓ Model directory: {os.path.abspath(MODEL_DIR)}")


def download_model(model_key: str) -> bool:
    """Download a specific model"""
    if model_key not in MODELS:
        print(f"✗ Unknown model: {model_key}")
        print(f"Available models: {', '.join(MODELS.keys())}")
        return False

    config = MODELS[model_key]
    model_dir = os.path.join(MODEL_DIR, model_key)
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, config["filename"])

    # Check if already downloaded
    if os.path.exists(model_path):
        file_size = os.path.getsize(model_path) / (1024 ** 3)  # GB
        print(f"✓ {config['description']}")
        print(f"  Already downloaded: {model_path}")
        print(f"  Size: {file_size:.2f} GB")
        return True

    print(f"\n{'='*60}")
    print(f"Downloading: {config['description']}")
    print(f"Expected size: {config['size']}")
    print(f"{'='*60}")

    try:
        downloaded_path = hf_hub_download(
            repo_id=config["repo_id"],
            filename=config["filename"],
            local_dir=model_dir,
            local_dir_use_symlinks=False
        )

        file_size = os.path.getsize(downloaded_path) / (1024 ** 3)  # GB
        print(f"✓ Download complete!")
        print(f"  Path: {downloaded_path}")
        print(f"  Size: {file_size:.2f} GB")
        return True

    except Exception as e:
        print(f"✗ Download failed: {e}")
        return False


def download_all_models():
    """Download all recommended models"""
    # For 8GB RAM, only download essential models
    essential_models = ["tinyllama", "liquid-tool", "qwen-0.5b"]

    print("\n" + "="*60)
    print("LALO Model Downloader - 8GB RAM Configuration")
    print("="*60)
    print("\nDownloading essential models for CPU-only development:")
    for model in essential_models:
        print(f"  • {MODELS[model]['description']} ({MODELS[model]['size']})")

    print(f"\nTotal download size: ~1.8 GB")
    print(f"Disk space required: ~2.5 GB")
    print("="*60)

    success_count = 0
    for model_key in essential_models:
        if download_model(model_key):
            success_count += 1

    print("\n" + "="*60)
    print("Download Summary")
    print("="*60)
    print(f"Successful: {success_count}/{len(essential_models)}")

    if success_count == len(essential_models):
        print("\n✓ All models downloaded successfully!")
        print("\nNext steps:")
        print("  1. Test inference: python scripts/test_local_inference.py")
        print("  2. Start backend: python app.py")
        print("  3. Submit test request at http://localhost:8000")
    else:
        print("\n✗ Some downloads failed. Please check errors above.")

    print("="*60)


def list_models():
    """List all available models"""
    print("\n" + "="*60)
    print("Available Models")
    print("="*60)

    for model_key, config in MODELS.items():
        status = "✓ Downloaded" if check_model_downloaded(model_key) else "○ Not downloaded"
        print(f"\n{model_key}")
        print(f"  {config['description']}")
        print(f"  Size: {config['size']}")
        print(f"  Status: {status}")

    print("\n" + "="*60)


def check_model_downloaded(model_key: str) -> bool:
    """Check if a model is already downloaded"""
    if model_key not in MODELS:
        return False

    config = MODELS[model_key]
    model_path = os.path.join(MODEL_DIR, model_key, config["filename"])
    return os.path.exists(model_path)


def main():
    parser = argparse.ArgumentParser(
        description="Download LALO local inference models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Download all essential models:
    python scripts/download_models.py --all

  Download specific model:
    python scripts/download_models.py --model tinyllama

  List available models:
    python scripts/download_models.py --list
        """
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all essential models"
    )

    parser.add_argument(
        "--model",
        type=str,
        help="Download specific model (tinyllama, liquid-tool, qwen-0.5b, qwen-3b)"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available models"
    )

    args = parser.parse_args()

    # Create model directory
    create_model_directory()

    # Execute requested action
    if args.list:
        list_models()
    elif args.all:
        download_all_models()
    elif args.model:
        success = download_model(args.model)
        sys.exit(0 if success else 1)
    else:
        # Default: download all
        print("No arguments provided. Use --help for usage information.")
        print("Running default action: downloading all essential models...\n")
        download_all_models()


if __name__ == "__main__":
    main()
