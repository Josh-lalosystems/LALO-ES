#!/usr/bin/env python
"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""Test OpenAI API key directly"""
import os
import asyncio
import logging
from dotenv import load_dotenv
load_dotenv()

from core.services.key_management import key_manager

logger = logging.getLogger("lalo.test_openai_direct")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


async def test_openai():
    user_id = "demo-user@example.com"

    # Get keys from key manager
    keys = key_manager.get_keys(user_id)
    logger.info("Keys from key_manager: %s", list(keys.keys()))

    if "openai" in keys:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=keys["openai"])

        try:
            logger.info("Testing OpenAI API...")
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say hello in 5 words"}],
                max_tokens=20
            )
            logger.info("SUCCESS: %s", response.choices[0].message.content)
        except Exception as e:
            logger.exception("OpenAI API error: %s", e)
    else:
        logger.warning("No OpenAI key found")


asyncio.run(test_openai())
