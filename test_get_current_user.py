#!/usr/bin/env python
"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""Test get_current_user function"""
import asyncio
import logging
from core.services.auth import get_current_user

logger = logging.getLogger("lalo.test_get_current_user")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


async def test_auth():
    logger.info("Testing get_current_user in DEMO_MODE...")
    try:
        # In demo mode, this should return without needing credentials
        user_id = await get_current_user(credentials=None)
        logger.info("SUCCESS: user_id = %s", user_id)
    except Exception as e:
        logger.exception("ERROR: %s: %s", type(e).__name__, str(e))
        import traceback
        traceback.print_exc()


asyncio.run(test_auth())
