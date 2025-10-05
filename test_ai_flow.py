#!/usr/bin/env python
"""Test the complete AI request flow"""
import asyncio
import logging

from core.services.ai_service import AIService
from core.services.key_management import key_manager

logger = logging.getLogger("lalo.test_ai_flow")
if not logger.handlers:
    # configure basic logging only if no handlers are present
    logging.basicConfig(level=logging.INFO)


async def test_ai_flow():
    user_id = "demo-user@example.com"

    # Get API keys
    logger.info("1. Getting API keys from key_manager...")
    api_keys = key_manager.get_keys(user_id)
    logger.info("   Keys: %s", list(api_keys.keys()))

    # Initialize AI service
    logger.info("\n2. Initializing AI service...")
    ai_service = AIService()

    # Initialize models
    logger.info("\n3. Initializing user models...")
    ai_service.initialize_user_models(user_id, api_keys)

    # Check available models
    logger.info("\n4. Checking available models...")
    available = ai_service.get_available_models(user_id)
    logger.info("   Available models: %s", available)

    # Make a request
    if available:
        model = "gpt-3.5-turbo"
        if model in available:
            logger.info("\n5. Testing %s...", model)
            try:
                result = await ai_service.generate(
                    "Say hello in 5 words",
                    model_name=model,
                    user_id=user_id,
                    max_tokens=20,
                )
                logger.info("   SUCCESS: %s", result)
            except Exception as e:
                logger.error("   ERROR: %s: %s", type(e).__name__, str(e))
        else:
            logger.warning("\n5. Model %s not in available models!", model)
    else:
        logger.warning("\n5. No models available!")


if __name__ == "__main__":
    asyncio.run(test_ai_flow())
