#!/usr/bin/env python3
"""Direct test of unified_request_handler without HTTP layer"""
import asyncio
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

from core.services.unified_request_handler import unified_request_handler
from core.services.local_llm_service import local_llm_service

async def test_simple_request():
    """Test a simple request directly"""
    print("\n=== Testing Simple Request: 'What is 2+2?' ===\n")

    try:
        result = await unified_request_handler.handle_request(
            user_request="What is 2+2?",
            user_id="test-user",
            available_models=["tinyllama", "qwen-0.5b"],
            context=None,
            stream=False
        )

        print(f"\n✅ SUCCESS!")
        print(f"Response: {result.get('response', '')}")
        print(f"Model: {result.get('model', '')}")
        print(f"Path: {result.get('path', '')}")
        print(f"Routing: {result.get('routing_decision', {})}")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

async def test_model_loading():
    """Test if we can load and use a model"""
    print("\n=== Testing Model Loading ===\n")

    print(f"LLAMA_CPP available: {local_llm_service.is_available()}")

    # Try to load tinyllama
    print("Loading TinyLlama...")
    success = local_llm_service.load_model("tinyllama")
    print(f"TinyLlama loaded: {success}")

    if success:
        # Try direct generation
        print("\nTesting direct generation...")
        try:
            response = await local_llm_service.generate(
                prompt="What is 2+2?",
                model_name="tinyllama",
                max_tokens=50
            )
            print(f"Direct generation response: {response}")
        except Exception as e:
            print(f"Direct generation failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("LALO AI - Direct Inference Test")
    print("=" * 60)

    # Test model loading first
    asyncio.run(test_model_loading())

    # Then test full request flow
    asyncio.run(test_simple_request())
