# Copyright (c) 2025 LALO AI LLC. All rights reserved.
"""
Model Management Routes

Endpoints for managing local AI models:
- List available models
- Download models
- Get download status
- Load/unload models
- System stats
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
import os
import logging
import psutil
import asyncio
import subprocess

from ..services.auth import get_current_user
from ..services.local_llm_service import local_llm_service

logger = logging.getLogger("lalo.model_management")

router = APIRouter(prefix="/api/admin/models", tags=["Model Management"])

# Model metadata
MODELS_METADATA = {
    "tinyllama": {
        "display_name": "TinyLlama 1.1B Chat",
        "size": "669 MB",
        "repo_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
        "description": "Fast, lightweight general-purpose chat model. Excellent for quick responses.",
        "recommended_use": "Quick Q&A, simple tasks, chat",
        "license": "Apache 2.0",
        "memory_required": "~800 MB",
        "speed_rating": 5,
    },
    "liquid-tool": {
        "display_name": "Liquid Tool 1.2B",
        "size": "752 MB",
        "repo_id": "second-state/Liquid-1.2B-Tool-GGUF",
        "filename": "Liquid-1.2B-Tool-Q4_K_M.gguf",
        "description": "Specialized in function calling and tool use. Optimized for routing decisions.",
        "recommended_use": "Request routing, tool selection, planning",
        "license": "Apache 2.0",
        "memory_required": "~900 MB",
        "speed_rating": 4,
    },
    "qwen-0.5b": {
        "display_name": "Qwen 0.5B",
        "size": "352 MB",
        "repo_id": "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
        "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "description": "Ultra-fast model for confidence scoring and validation. Minimal resource usage.",
        "recommended_use": "Confidence validation, quick checks",
        "license": "Apache 2.0",
        "memory_required": "~500 MB",
        "speed_rating": 5,
    },
}

# Global download status tracker
download_status: Dict[str, Dict] = {}


class ModelInfo(BaseModel):
    name: str
    display_name: str
    size: str
    status: str  # not_downloaded, downloading, downloaded, loaded, error
    download_progress: Optional[float] = None
    error_message: Optional[str] = None
    repo_id: str
    filename: str
    description: str
    recommended_use: str
    license: str
    memory_required: str
    speed_rating: int


class SystemStats(BaseModel):
    total_models: int
    downloaded_models: int
    loaded_models: int
    disk_space_used: str
    available_space: str
    total_memory: str
    available_memory: str


def get_model_status(model_name: str) -> str:
    """Get the current status of a model."""
    # Check if downloading
    if model_name in download_status and download_status[model_name].get("status") == "downloading":
        return "downloading"

    # Check if loaded in memory
    if model_name in local_llm_service.models:
        return "loaded"

    # Check if file exists (downloaded)
    model_dir = os.path.join("models")
    if model_name in MODELS_METADATA:
        filename = MODELS_METADATA[model_name]["filename"]
        model_path = os.path.join(model_dir, filename)
        if os.path.exists(model_path):
            return "downloaded"

    return "not_downloaded"


def get_disk_usage(path: str = "./models") -> tuple[str, str]:
    """Get disk space used by models and available space."""
    total_size = 0
    if os.path.exists(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)

    # Format size
    def format_bytes(bytes_val):
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} TB"

    # Get available disk space
    disk = psutil.disk_usage(os.path.abspath(path if os.path.exists(path) else "."))
    available = format_bytes(disk.free)

    return format_bytes(total_size), available


async def download_model_background(model_name: str):
    """Background task to download a model using the download script."""
    try:
        download_status[model_name] = {"status": "downloading", "progress": 0}

        # Run download script
        script_path = os.path.join("scripts", "download_models.py")
        process = await asyncio.create_subprocess_exec(
            "python",
            script_path,
            "--model",
            model_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Monitor progress (simplified - in production would parse output)
        while True:
            await asyncio.sleep(2)
            if process.returncode is not None:
                break
            # Update progress (simplified - real implementation would parse download progress)
            current_progress = download_status[model_name].get("progress", 0)
            download_status[model_name]["progress"] = min(current_progress + 10, 90)

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            download_status[model_name] = {"status": "downloaded", "progress": 100}
            logger.info(f"Model {model_name} downloaded successfully")
        else:
            error_msg = stderr.decode() if stderr else "Download failed"
            download_status[model_name] = {
                "status": "error",
                "error": error_msg,
                "progress": 0,
            }
            logger.error(f"Model {model_name} download failed: {error_msg}")

    except Exception as e:
        logger.error(f"Error downloading model {model_name}: {e}")
        download_status[model_name] = {
            "status": "error",
            "error": str(e),
            "progress": 0,
        }


@router.get("")
async def list_models(current_user: str = Depends(get_current_user)) -> Dict:
    """List all available models with their current status."""
    models = []

    for model_name, metadata in MODELS_METADATA.items():
        status = get_model_status(model_name)
        progress = None
        error_msg = None

        if model_name in download_status:
            status = download_status[model_name].get("status", status)
            progress = download_status[model_name].get("progress")
            error_msg = download_status[model_name].get("error")

        models.append(
            ModelInfo(
                name=model_name,
                display_name=metadata["display_name"],
                size=metadata["size"],
                status=status,
                download_progress=progress,
                error_message=error_msg,
                repo_id=metadata["repo_id"],
                filename=metadata["filename"],
                description=metadata["description"],
                recommended_use=metadata["recommended_use"],
                license=metadata["license"],
                memory_required=metadata["memory_required"],
                speed_rating=metadata["speed_rating"],
            )
        )

    return {"models": models}


@router.get("/stats")
async def get_system_stats(current_user: str = Depends(get_current_user)) -> SystemStats:
    """Get system statistics for models."""
    total_models = len(MODELS_METADATA)
    downloaded_models = sum(1 for name in MODELS_METADATA if get_model_status(name) in ["downloaded", "loaded"])
    loaded_models = sum(1 for name in MODELS_METADATA if get_model_status(name) == "loaded")

    disk_used, disk_available = get_disk_usage()

    # Memory stats
    mem = psutil.virtual_memory()
    total_mem = f"{mem.total / (1024**3):.1f} GB"
    available_mem = f"{mem.available / (1024**3):.1f} GB"

    return SystemStats(
        total_models=total_models,
        downloaded_models=downloaded_models,
        loaded_models=loaded_models,
        disk_space_used=disk_used,
        available_space=disk_available,
        total_memory=total_mem,
        available_memory=available_mem,
    )


@router.post("/{model_name}/download")
async def download_model(
    model_name: str,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user),
):
    """Start downloading a model."""
    if model_name not in MODELS_METADATA:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_name} not found",
        )

    current_status = get_model_status(model_name)
    if current_status == "downloading":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model {model_name} is already downloading",
        )

    if current_status in ["downloaded", "loaded"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model {model_name} is already downloaded",
        )

    # Start download in background
    background_tasks.add_task(download_model_background, model_name)

    return {"message": f"Started downloading {model_name}", "status": "downloading"}


@router.get("/{model_name}/status")
async def get_model_status_endpoint(
    model_name: str, current_user: str = Depends(get_current_user)
):
    """Get the current status of a specific model."""
    if model_name not in MODELS_METADATA:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_name} not found",
        )

    status_str = get_model_status(model_name)
    progress = None
    error = None

    if model_name in download_status:
        status_str = download_status[model_name].get("status", status_str)
        progress = download_status[model_name].get("progress")
        error = download_status[model_name].get("error")

    return {"status": status_str, "progress": progress, "error": error}


@router.post("/{model_name}/load")
async def load_model(model_name: str, current_user: str = Depends(get_current_user)):
    """Load a model into memory."""
    if model_name not in MODELS_METADATA:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_name} not found",
        )

    current_status = get_model_status(model_name)
    if current_status == "not_downloaded":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model {model_name} must be downloaded first",
        )

    if current_status == "loaded":
        return {"message": f"Model {model_name} is already loaded"}

    try:
        # Load the model
        await local_llm_service._load_model(model_name)
        logger.info(f"Model {model_name} loaded successfully")
        return {"message": f"Model {model_name} loaded successfully"}
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model: {str(e)}",
        )


@router.post("/{model_name}/unload")
async def unload_model(model_name: str, current_user: str = Depends(get_current_user)):
    """Unload a model from memory."""
    if model_name not in MODELS_METADATA:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_name} not found",
        )

    if model_name not in local_llm_service.models:
        return {"message": f"Model {model_name} is not loaded"}

    try:
        # Unload the model
        del local_llm_service.models[model_name]
        logger.info(f"Model {model_name} unloaded successfully")
        return {"message": f"Model {model_name} unloaded successfully"}
    except Exception as e:
        logger.error(f"Failed to unload model {model_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unload model: {str(e)}",
        )


@router.delete("/{model_name}")
async def delete_model(model_name: str, current_user: str = Depends(get_current_user)):
    """Delete a downloaded model to free disk space."""
    if model_name not in MODELS_METADATA:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_name} not found",
        )

    # Unload if loaded
    if model_name in local_llm_service.models:
        del local_llm_service.models[model_name]

    # Delete file
    model_dir = os.path.join("models")
    filename = MODELS_METADATA[model_name]["filename"]
    model_path = os.path.join(model_dir, filename)

    if os.path.exists(model_path):
        try:
            os.remove(model_path)
            logger.info(f"Model {model_name} deleted successfully")
            return {"message": f"Model {model_name} deleted successfully"}
        except Exception as e:
            logger.error(f"Failed to delete model {model_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete model: {str(e)}",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model file not found: {model_path}",
        )
