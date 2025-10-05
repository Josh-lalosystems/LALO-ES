"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
AI Model Pricing Calculator

Provides cost estimates for AI model usage based on current provider pricing.
Prices are per 1,000 tokens.

Last updated: 2025-01
"""

from typing import Dict, Optional

# Pricing per 1,000 tokens (as of January 2025)
PRICING: Dict[str, Dict[str, float]] = {
    # OpenAI Models
    "gpt-4-turbo-preview": {
        "prompt": 0.01,      # $0.01 per 1K prompt tokens
        "completion": 0.03   # $0.03 per 1K completion tokens
    },
    "gpt-3.5-turbo": {
        "prompt": 0.0005,    # $0.0005 per 1K prompt tokens
        "completion": 0.0015 # $0.0015 per 1K completion tokens
    },

    # Anthropic Claude Models
    "claude-3-5-sonnet-20241022": {
        "prompt": 0.003,     # $0.003 per 1K prompt tokens
        "completion": 0.015  # $0.015 per 1K completion tokens
    },
    "claude-3-opus-20240229": {
        "prompt": 0.015,     # $0.015 per 1K prompt tokens
        "completion": 0.075  # $0.075 per 1K completion tokens
    },
    "claude-3-haiku-20240307": {
        "prompt": 0.00025,   # $0.00025 per 1K prompt tokens
        "completion": 0.00125 # $0.00125 per 1K completion tokens
    },

    # Google Models
    "gemini-pro": {
        "prompt": 0.00025,
        "completion": 0.0005
    },
    "gemini-pro-vision": {
        "prompt": 0.00025,
        "completion": 0.0005
    },
}


def calculate_cost(
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: Optional[int] = None
) -> float:
    """
    Calculate cost for AI model usage.

    Args:
        model: Name of the AI model
        prompt_tokens: Number of prompt tokens used
        completion_tokens: Number of completion tokens used
        total_tokens: If provided and individual counts aren't, will estimate as 30% prompt / 70% completion

    Returns:
        Estimated cost in USD

    Examples:
        >>> calculate_cost("gpt-3.5-turbo", prompt_tokens=100, completion_tokens=200)
        0.0003

        >>> calculate_cost("claude-3-haiku-20240307", total_tokens=1000)
        0.001
    """
    if model not in PRICING:
        # Unknown model, return 0
        return 0.0

    pricing = PRICING[model]

    # If only total_tokens provided, estimate split (30% prompt, 70% completion)
    if total_tokens is not None and prompt_tokens == 0 and completion_tokens == 0:
        prompt_tokens = int(total_tokens * 0.3)
        completion_tokens = int(total_tokens * 0.7)

    # Calculate cost (pricing is per 1000 tokens)
    prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * pricing["completion"]

    total_cost = prompt_cost + completion_cost

    # Round to 6 decimal places (nearest millionth of a dollar)
    return round(total_cost, 6)


def estimate_tokens(text: str) -> int:
    """
    Rough estimation of token count from text.

    Uses a simple heuristic: ~1.3 tokens per word.
    For accurate counts, use the provider's tokenizer.

    Args:
        text: Input text to estimate

    Returns:
        Estimated token count
    """
    words = len(text.split())
    return int(words * 1.3)


def get_model_pricing_info(model: str) -> Optional[Dict[str, float]]:
    """
    Get pricing information for a specific model.

    Args:
        model: Name of the AI model

    Returns:
        Dict with 'prompt' and 'completion' pricing, or None if model not found
    """
    return PRICING.get(model)


def list_available_models() -> list[str]:
    """
    Get list of all models with known pricing.

    Returns:
        List of model names
    """
    return list(PRICING.keys())


def format_cost(cost: float) -> str:
    """
    Format cost for display.

    Args:
        cost: Cost in USD

    Returns:
        Formatted string (e.g., "$0.0012" or "$0.00")
    """
    if cost < 0.0001:
        return "$0.00"
    elif cost < 0.01:
        return f"${cost:.4f}"
    else:
        return f"${cost:.2f}"
