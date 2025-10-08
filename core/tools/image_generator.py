"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

# © 2025 LALO AI, LLC. All Rights Reserved
# SPDX-License-Identifier: All-Rights-Reserved

"""
Image Generation Tool

Generates images using AI models:
- DALL-E 3 (OpenAI) - highest quality
- DALL-E 2 (OpenAI) - faster, cheaper
- Stable Diffusion (optional local model)
"""

import os
import base64
import hashlib
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path

from .base import BaseTool, ToolDefinition, ToolParameter, ToolExecutionResult


class ImageGeneratorTool(BaseTool):
    """Image generation tool using DALL-E"""

    def __init__(self):
        super().__init__()
        self._openai_client = None
        self._storage_path = Path(os.getenv("IMAGE_STORAGE_PATH", "./data/images"))
        self._storage_path.mkdir(parents=True, exist_ok=True)

        # Default model
        self._default_model = os.getenv("DALLE_MODEL", "dall-e-3")

    def _get_openai_client(self, user_api_key: Optional[str] = None):
        """Get OpenAI client (create if needed)"""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ValueError(
                "openai package not installed. "
                "Run: pip install openai"
            )

        # Use provided key or environment variable
        api_key = user_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not configured")

        return AsyncOpenAI(api_key=api_key)

    @property
    def tool_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="image_generator",
            description="Generate images from text descriptions using DALL-E. Creates high-quality images based on prompts.",
            parameters=[
                ToolParameter(
                    name="prompt",
                    type="string",
                    description="Detailed description of the image to generate",
                    required=True
                ),
                ToolParameter(
                    name="model",
                    type="string",
                    description="Model to use: 'dall-e-3' (highest quality) or 'dall-e-2' (faster, cheaper)",
                    required=False,
                    enum=["dall-e-3", "dall-e-2"]
                ),
                ToolParameter(
                    name="size",
                    type="string",
                    description="Image size. DALL-E 3: '1024x1024', '1792x1024', '1024x1792'. DALL-E 2: '256x256', '512x512', '1024x1024'",
                    required=False,
                    enum=["256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"]
                ),
                ToolParameter(
                    name="quality",
                    type="string",
                    description="Image quality: 'standard' or 'hd' (DALL-E 3 only, hd costs more)",
                    required=False,
                    enum=["standard", "hd"]
                ),
                ToolParameter(
                    name="style",
                    type="string",
                    description="Image style: 'vivid' (hyper-real) or 'natural' (more natural, less hyper-real). DALL-E 3 only.",
                    required=False,
                    enum=["vivid", "natural"]
                ),
                ToolParameter(
                    name="n",
                    type="integer",
                    description="Number of images to generate (1-10, default: 1). DALL-E 2 supports multiple, DALL-E 3 supports only 1.",
                    required=False
                ),
                ToolParameter(
                    name="user_api_key",
                    type="string",
                    description="User's OpenAI API key (if not using system default)",
                    required=False
                ),
                ToolParameter(
                    name="save_to_disk",
                    type="boolean",
                    description="Whether to save generated images to disk (default: true)",
                    required=False
                )
            ],
            returns={
                "type": "object",
                "description": "Generated image file paths, metadata, and revised prompt"
            }
        )

    async def execute(self, **kwargs) -> ToolExecutionResult:
        """Execute image generation"""
        prompt = kwargs.get("prompt")
        model = kwargs.get("model", self._default_model)
        size = kwargs.get("size")
        quality = kwargs.get("quality", "standard")
        style = kwargs.get("style", "vivid")
        n = kwargs.get("n", 1)
        user_api_key = kwargs.get("user_api_key")
        save_to_disk = kwargs.get("save_to_disk", True)

        # Validate parameters
        if model == "dall-e-3":
            if n != 1:
                return ToolExecutionResult(
                    success=False,
                    error="DALL-E 3 only supports generating 1 image at a time (n=1)"
                )
            if not size:
                size = "1024x1024"
            if size not in ["1024x1024", "1792x1024", "1024x1792"]:
                return ToolExecutionResult(
                    success=False,
                    error=f"DALL-E 3 only supports sizes: 1024x1024, 1792x1024, 1024x1792. Got: {size}"
                )
        elif model == "dall-e-2":
            if not size:
                size = "1024x1024"
            if size not in ["256x256", "512x512", "1024x1024"]:
                return ToolExecutionResult(
                    success=False,
                    error=f"DALL-E 2 only supports sizes: 256x256, 512x512, 1024x1024. Got: {size}"
                )
            # DALL-E 2 doesn't support quality and style
            quality = None
            style = None

        try:
            # Get OpenAI client
            client = self._get_openai_client(user_api_key)

            # Generate images
            generation_params = {
                "model": model,
                "prompt": prompt,
                "n": n,
                "size": size,
                "response_format": "b64_json"  # Get base64 encoded images
            }

            # Add DALL-E 3 specific parameters
            if model == "dall-e-3":
                generation_params["quality"] = quality
                generation_params["style"] = style

            response = await client.images.generate(**generation_params)

            # Process results
            images = []
            for idx, image_data in enumerate(response.data):
                # Decode base64 image
                image_bytes = base64.b64decode(image_data.b64_json)

                # Generate filename
                prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"{model}_{timestamp}_{prompt_hash}_{idx}.png"
                file_path = self._storage_path / filename

                # Save to disk if requested
                saved_path = None
                if save_to_disk:
                    with open(file_path, "wb") as f:
                        f.write(image_bytes)
                    saved_path = str(file_path)

                # Store image info
                images.append({
                    "index": idx,
                    "file_path": saved_path,
                    "filename": filename,
                    "size_bytes": len(image_bytes),
                    "revised_prompt": getattr(image_data, "revised_prompt", None),  # DALL-E 3 provides revised prompt
                    "format": "png"
                })

            return ToolExecutionResult(
                success=True,
                output={
                    "prompt": prompt,
                    "revised_prompt": images[0]["revised_prompt"] if images and images[0]["revised_prompt"] else None,
                    "model": model,
                    "size": size,
                    "quality": quality,
                    "style": style,
                    "images": images,
                    "count": len(images),
                    "timestamp": datetime.utcnow().isoformat()
                },
                metadata={
                    "model": model,
                    "size": size,
                    "quality": quality,
                    "style": style
                }
            )

        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=f"Image generation failed: {str(e)}",
                output={
                    "prompt": prompt,
                    "model": model,
                    "images": [],
                    "count": 0
                }
            )

    def is_enabled(self) -> bool:
        """Tool is enabled if OpenAI API key is available"""
        # Check if key exists (either in env or will be provided per-request)
        return True  # Allow per-request API keys


# Create singleton instance
image_generator_tool = ImageGeneratorTool()
