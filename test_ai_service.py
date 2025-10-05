#!/usr/bin/env python
"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""Test AI service model initialization"""

import sys
sys.path.insert(0, '.')

from core.services.ai_service import AIService
from core.services.database_service import database_service
import logging

logger = logging.getLogger("lalo.test_ai_service")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def test_model_initialization():
    """Test that AI service initializes models correctly"""
    logger.info("%s", "="*60)
    logger.info("AI Service Model Initialization Test")
    logger.info("%s", "="*60)

    ai_service = AIService(database_service)

    # Test 1: Empty initialization
    logger.info("Test 1: Initialize with no API keys")
    ai_service.initialize_user_models("test-user-1", {})
    models = ai_service.get_available_models("test-user-1")
    logger.info("  Available models: %s", models)
    logger.info("  Result: %s", 'PASS' if len(models) == 0 else 'FAIL')

    # Test 2: OpenAI only
    logger.info("Test 2: Initialize with OpenAI key")
    ai_service.initialize_user_models("test-user-2", {"openai": "fake-key"})
    models = ai_service.get_available_models("test-user-2")
    logger.info("  Available models: %s", models)
    expected_openai = ["gpt-4-turbo-preview", "gpt-3.5-turbo"]
    has_expected = all(m in models for m in expected_openai)
    logger.info("  Expected: %s", expected_openai)
    logger.info("  Result: %s", 'PASS' if has_expected else 'FAIL')

    # Test 3: Anthropic only
    logger.info("Test 3: Initialize with Anthropic key")
    ai_service.initialize_user_models("test-user-3", {"anthropic": "fake-key"})
    models = ai_service.get_available_models("test-user-3")
    logger.info("  Available models: %s", models)
    expected_anthropic = [
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307"
    ]
    has_expected = all(m in models for m in expected_anthropic)
    logger.info("  Expected: %s", expected_anthropic)
    logger.info("  Result: %s", 'PASS' if has_expected else 'FAIL')

    # Test 4: Both providers
    logger.info("Test 4: Initialize with both OpenAI and Anthropic keys")
    ai_service.initialize_user_models("test-user-4", {
        "openai": "fake-openai-key",
        "anthropic": "fake-anthropic-key"
    })
    models = ai_service.get_available_models("test-user-4")
    logger.info("  Available models: %s", models)
    all_expected = expected_openai + expected_anthropic
    has_all = all(m in models for m in all_expected)
    logger.info("  Expected count: %d", len(all_expected))
    logger.info("  Actual count: %d", len(models))
    logger.info("  Result: %s", 'PASS' if has_all and len(models) == len(all_expected) else 'FAIL')

    # Test 5: No deprecated models
    logger.info("Test 5: Check for deprecated models")
    deprecated = ["claude-instant-1", "gpt-4"]  # gpt-4 without version is deprecated
    found_deprecated = [m for m in models if m in deprecated]
    logger.info("  Deprecated models found: %s", found_deprecated)
    logger.info("  Result: %s", 'PASS' if len(found_deprecated) == 0 else 'FAIL')

    logger.info("%s", "\n" + "="*60)
    logger.info("[SUCCESS] AI Service tests complete")
    logger.info("%s", "="*60)


if __name__ == "__main__":
    test_model_initialization()
