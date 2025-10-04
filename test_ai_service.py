#!/usr/bin/env python
"""Test AI service model initialization"""

import sys
sys.path.insert(0, '.')

from core.services.ai_service import AIService
from core.services.database_service import database_service

def test_model_initialization():
    """Test that AI service initializes models correctly"""
    print("="* 60)
    print("AI Service Model Initialization Test")
    print("="* 60)

    ai_service = AIService(database_service)

    # Test 1: Empty initialization
    print("\nTest 1: Initialize with no API keys")
    ai_service.initialize_user_models("test-user-1", {})
    models = ai_service.get_available_models("test-user-1")
    print(f"  Available models: {models}")
    print(f"  Result: {'PASS' if len(models) == 0 else 'FAIL'}")

    # Test 2: OpenAI only
    print("\nTest 2: Initialize with OpenAI key")
    ai_service.initialize_user_models("test-user-2", {"openai": "fake-key"})
    models = ai_service.get_available_models("test-user-2")
    print(f"  Available models: {models}")
    expected_openai = ["gpt-4-turbo-preview", "gpt-3.5-turbo"]
    has_expected = all(m in models for m in expected_openai)
    print(f"  Expected: {expected_openai}")
    print(f"  Result: {'PASS' if has_expected else 'FAIL'}")

    # Test 3: Anthropic only
    print("\nTest 3: Initialize with Anthropic key")
    ai_service.initialize_user_models("test-user-3", {"anthropic": "fake-key"})
    models = ai_service.get_available_models("test-user-3")
    print(f"  Available models: {models}")
    expected_anthropic = [
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
        "claude-3-haiku-20240307"
    ]
    has_expected = all(m in models for m in expected_anthropic)
    print(f"  Expected: {expected_anthropic}")
    print(f"  Result: {'PASS' if has_expected else 'FAIL'}")

    # Test 4: Both providers
    print("\nTest 4: Initialize with both OpenAI and Anthropic keys")
    ai_service.initialize_user_models("test-user-4", {
        "openai": "fake-openai-key",
        "anthropic": "fake-anthropic-key"
    })
    models = ai_service.get_available_models("test-user-4")
    print(f"  Available models: {models}")
    all_expected = expected_openai + expected_anthropic
    has_all = all(m in models for m in all_expected)
    print(f"  Expected count: {len(all_expected)}")
    print(f"  Actual count: {len(models)}")
    print(f"  Result: {'PASS' if has_all and len(models) == len(all_expected) else 'FAIL'}")

    # Test 5: No deprecated models
    print("\nTest 5: Check for deprecated models")
    deprecated = ["claude-instant-1", "gpt-4"]  # gpt-4 without version is deprecated
    found_deprecated = [m for m in models if m in deprecated]
    print(f"  Deprecated models found: {found_deprecated}")
    print(f"  Result: {'PASS' if len(found_deprecated) == 0 else 'FAIL'}")

    print("\n" + "="* 60)
    print("[SUCCESS] AI Service tests complete")
    print("="* 60)

if __name__ == "__main__":
    test_model_initialization()
