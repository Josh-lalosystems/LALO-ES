#!/usr/bin/env python3
"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.

LALO AI - Production Model Downloader
Downloads all specialized models for local inference:
- Math & Finance
- Code Generation
- Research & Analysis
- Routing & Orchestration
- RAG & Embeddings
- General Purpose

Total size: ~15-25 GB (adjust based on your needs)
"""

import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Model directory
MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

# ============================================================================
# PRODUCTION MODEL CATALOG
# ============================================================================

MODELS = {
    # ========================================================================
    # ROUTING & ORCHESTRATION (Critical for multi-model workflows)
    # ========================================================================
    "liquid-tool": {
        "repo_id": "second-state/Liquid-1.2B-Tool-GGUF",
        "filename": "Liquid-1.2B-Tool-Q4_K_M.gguf",
        "size": "752 MB",
        "description": "Function calling, tool use, and request routing",
        "specialty": "routing",
        "priority": 1,
        "license": "Apache 2.0"
    },

    # ========================================================================
    # MATH & REASONING (Finance calculations, math problems)
    # ========================================================================
    "deepseek-math": {
        "repo_id": "TheBloke/deepseek-math-7B-instruct-GGUF",
        "filename": "deepseek-math-7b-instruct.Q4_K_M.gguf",
        "size": "4.37 GB",
        "description": "Mathematical reasoning, finance calculations, quantitative analysis",
        "specialty": "math",
        "priority": 1,
        "license": "MIT"
    },

    "metamath": {
        "repo_id": "TheBloke/MetaMath-7B-V1.0-GGUF",
        "filename": "metamath-7b-v1.0.Q4_K_M.gguf",
        "size": "4.37 GB",
        "description": "Advanced mathematics, word problems, step-by-step reasoning",
        "specialty": "math",
        "priority": 2,
        "license": "Apache 2.0"
    },

    # ========================================================================
    # CODE GENERATION (Programming, software development)
    # ========================================================================
    "deepseek-coder": {
        "repo_id": "TheBloke/deepseek-coder-6.7B-instruct-GGUF",
        "filename": "deepseek-coder-6.7b-instruct.Q4_K_M.gguf",
        "size": "4.0 GB",
        "description": "Code generation, debugging, refactoring (Python, JS, Java, etc.)",
        "specialty": "coding",
        "priority": 1,
        "license": "Deepseek License"
    },

    "codellama": {
        "repo_id": "TheBloke/CodeLlama-7B-Instruct-GGUF",
        "filename": "codellama-7b-instruct.Q4_K_M.gguf",
        "size": "4.24 GB",
        "description": "Code completion, documentation, testing",
        "specialty": "coding",
        "priority": 2,
        "license": "Llama 2 Community License"
    },

    # ========================================================================
    # RESEARCH & ANALYSIS (Business intelligence, market research)
    # ========================================================================
    "openchat": {
        "repo_id": "TheBloke/openchat-3.5-0106-GGUF",
        "filename": "openchat-3.5-0106.Q4_K_M.gguf",
        "size": "4.37 GB",
        "description": "Research synthesis, analysis, business intelligence",
        "specialty": "research",
        "priority": 1,
        "license": "Apache 2.0"
    },

    "mistral-instruct": {
        "repo_id": "TheBloke/Mistral-7B-Instruct-v0.2-GGUF",
        "filename": "mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        "size": "4.37 GB",
        "description": "General reasoning, analysis, report generation",
        "specialty": "research",
        "priority": 1,
        "license": "Apache 2.0"
    },

    # ========================================================================
    # GENERAL PURPOSE (Chat, Q&A, content generation)
    # ========================================================================
    "tinyllama": {
        "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "size": "669 MB",
        "description": "Fast general-purpose chat, quick responses",
        "specialty": "general",
        "priority": 1,
        "license": "Apache 2.0"
    },

    "phi-2": {
        "repo_id": "TheBloke/phi-2-GGUF",
        "filename": "phi-2.Q4_K_M.gguf",
        "size": "1.60 GB",
        "description": "Common sense reasoning, general knowledge",
        "specialty": "general",
        "priority": 2,
        "license": "MIT"
    },

    # ========================================================================
    # CONFIDENCE & VALIDATION (Output quality scoring)
    # ========================================================================
    "qwen-0.5b": {
        "repo_id": "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
        "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "size": "352 MB",
        "description": "Ultra-fast confidence scoring and validation",
        "specialty": "validation",
        "priority": 1,
        "license": "Apache 2.0"
    },

    # ========================================================================
    # EMBEDDINGS (RAG, semantic search, document retrieval)
    # ========================================================================
    "bge-small": {
        "repo_id": "BAAI/bge-small-en-v1.5",
        "filename": "model.safetensors",
        "size": "133 MB",
        "description": "Text embeddings for RAG and semantic search",
        "specialty": "embeddings",
        "priority": 1,
        "license": "MIT",
        "model_type": "sentence-transformers"
    },

    # ========================================================================
    # LIQUID AI MODELS (Edge-optimized, ultra-fast)
    # ========================================================================
    "liquid-lfm2-1.2b": {
        "repo_id": "LiquidAI/LFM2-1.2B-GGUF",
        "filename": "lfm2-1.2b.Q4_K_M.gguf",
        "size": "731 MB",
        "description": "General purpose edge AI model (Liquid AI LFM2)",
        "specialty": "general",
        "priority": 1,
        "license": "Liquid AI License"
    },

    "liquid-lfm2-350m": {
        "repo_id": "LiquidAI/LFM2-350M-GGUF",
        "filename": "lfm2-350m.Q4_K_M.gguf",
        "size": "229 MB",
        "description": "Ultra-fast edge AI model (Liquid AI LFM2)",
        "specialty": "routing",
        "priority": 1,
        "license": "Liquid AI License"
    },

    "liquid-lfm2-vision": {
        "repo_id": "LiquidAI/LFM2-VL-1.6B-GGUF",
        "filename": "lfm2-vl-1.6b.Q4_K_M.gguf",
        "size": "~1.0 GB",
        "description": "Vision-to-language model (Liquid AI LFM2-VL)",
        "specialty": "vision",
        "priority": 2,
        "license": "Liquid AI License"
    },

    # ========================================================================
    # OPTIONAL: LARGER MODELS (if you have GPU or lots of RAM)
    # ========================================================================
    "mixtral-8x7b": {
        "repo_id": "TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF",
        "filename": "mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf",
        "size": "26.4 GB",
        "description": "Advanced reasoning, complex tasks (requires 32GB+ RAM or GPU)",
        "specialty": "advanced",
        "priority": 3,
        "license": "Apache 2.0",
        "optional": True
    },
}


def get_model_size_gb(size_str: str) -> float:
    """Convert size string to GB for sorting"""
    if "GB" in size_str:
        return float(size_str.split()[0])
    elif "MB" in size_str:
        return float(size_str.split()[0]) / 1024
    return 0


def download_model(model_name: str, config: dict, force: bool = False) -> bool:
    """
    Download a single model from HuggingFace

    Args:
        model_name: Key from MODELS dict
        config: Model configuration dict
        force: Re-download even if exists

    Returns:
        True if successful, False otherwise
    """
    # Create model subdirectory
    model_dir = MODELS_DIR / model_name
    model_dir.mkdir(exist_ok=True)

    model_path = model_dir / config["filename"]

    # Check if already downloaded
    if model_path.exists() and not force:
        logger.info(f"✓ {model_name} already downloaded ({config['size']})")
        return True

    try:
        logger.info(f"⬇ Downloading {model_name} ({config['size']})...")
        logger.info(f"   Specialty: {config['specialty']}")
        logger.info(f"   Purpose: {config['description']}")

        # Download from HuggingFace
        downloaded_path = hf_hub_download(
            repo_id=config["repo_id"],
            filename=config["filename"],
            local_dir=str(model_dir),
            local_dir_use_symlinks=False,
            resume_download=True
        )

        logger.info(f"✓ {model_name} downloaded successfully")
        logger.info(f"   Location: {downloaded_path}")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to download {model_name}: {e}")
        return False


def main():
    """Main download orchestrator"""
    import argparse

    parser = argparse.ArgumentParser(description="Download LALO AI production models")
    parser.add_argument(
        "--models",
        nargs="+",
        help="Specific models to download (space-separated). If not specified, downloads all priority 1 models."
    )
    parser.add_argument(
        "--priority",
        type=int,
        choices=[1, 2, 3],
        default=1,
        help="Download models up to this priority level (1=critical, 2=recommended, 3=optional)"
    )
    parser.add_argument(
        "--specialty",
        choices=["routing", "math", "coding", "research", "general", "validation", "embeddings", "advanced", "all"],
        help="Download only models of this specialty"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download models even if they exist"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available models and exit"
    )

    args = parser.parse_args()

    # List models and exit
    if args.list:
        logger.info("=" * 80)
        logger.info("AVAILABLE MODELS")
        logger.info("=" * 80)

        by_specialty = {}
        for name, config in MODELS.items():
            specialty = config["specialty"]
            if specialty not in by_specialty:
                by_specialty[specialty] = []
            by_specialty[specialty].append((name, config))

        for specialty, models in sorted(by_specialty.items()):
            logger.info(f"\n{specialty.upper()}")
            logger.info("-" * 80)
            for name, config in sorted(models, key=lambda x: x[1]["priority"]):
                optional = " [OPTIONAL]" if config.get("optional") else ""
                logger.info(f"  {name:<20} P{config['priority']} {config['size']:<10} {config['description']}{optional}")

        logger.info("\n" + "=" * 80)
        total_size = sum(get_model_size_gb(c["size"]) for c in MODELS.values() if not c.get("optional"))
        logger.info(f"Total required size: ~{total_size:.1f} GB (excluding optional models)")
        logger.info("=" * 80)
        return

    # Determine which models to download
    to_download = []

    if args.models:
        # Specific models requested
        for model_name in args.models:
            if model_name in MODELS:
                to_download.append((model_name, MODELS[model_name]))
            else:
                logger.warning(f"Unknown model: {model_name}")
    else:
        # Download by priority and/or specialty
        for name, config in MODELS.items():
            # Skip optional models unless explicitly requested
            if config.get("optional") and args.priority < 3:
                continue

            # Filter by priority
            if config["priority"] > args.priority:
                continue

            # Filter by specialty
            if args.specialty and args.specialty != "all" and config["specialty"] != args.specialty:
                continue

            to_download.append((name, config))

    if not to_download:
        logger.warning("No models selected for download. Use --list to see available models.")
        return

    # Sort by priority, then size (download critical small models first)
    to_download.sort(key=lambda x: (x[1]["priority"], get_model_size_gb(x[1]["size"])))

    # Display download plan
    logger.info("=" * 80)
    logger.info("DOWNLOAD PLAN")
    logger.info("=" * 80)
    total_size_gb = 0
    for name, config in to_download:
        logger.info(f"  {name:<20} P{config['priority']} {config['size']:<10} [{config['specialty']}]")
        total_size_gb += get_model_size_gb(config["size"])

    logger.info("=" * 80)
    logger.info(f"Total download size: ~{total_size_gb:.1f} GB")
    logger.info(f"Download location: {MODELS_DIR.absolute()}")
    logger.info("=" * 80)

    # Confirm
    if not args.force:
        response = input("\nProceed with download? [y/N]: ")
        if response.lower() != 'y':
            logger.info("Download cancelled.")
            return

    # Download models
    logger.info("\nStarting downloads...\n")

    success_count = 0
    failed_models = []

    for name, config in to_download:
        if download_model(name, config, args.force):
            success_count += 1
        else:
            failed_models.append(name)
        logger.info("")  # Blank line between models

    # Summary
    logger.info("=" * 80)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("=" * 80)
    logger.info(f"✓ Successful: {success_count}/{len(to_download)}")
    if failed_models:
        logger.info(f"✗ Failed: {', '.join(failed_models)}")
    logger.info(f"Location: {MODELS_DIR.absolute()}")
    logger.info("=" * 80)

    if success_count > 0:
        logger.info("\n✓ Models ready for local inference!")
        logger.info("Next steps:")
        logger.info("  1. Install llama-cpp-python: pip install llama-cpp-python")
        logger.info("  2. Update local_llm_service.py with model configs")
        logger.info("  3. Start server: python app.py")


if __name__ == "__main__":
    main()
