"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import asyncio
import logging
from core.services.key_management import key_manager
from core.services.ai_service import ai_service

logger = logging.getLogger('scripts.test_ai_call')

user = 'demo-user@example.com'
keys = key_manager.get_keys(user)
logger.info('keys: %s', keys)

async def run():
    logger.info('validating keys...')
    wk = await key_manager.validate_keys(user)
    logger.info('working keys: %s', wk)
    ai_service.initialize_user_models(user, keys, working_keys=wk)
    logger.info('initialized models: %s', ai_service.get_available_models(user))
    try:
        res = await ai_service.generate('Hello demo', model_name='gpt-3.5-turbo', user_id=user)
        logger.info('generated: %s', res)
    except Exception as e:
        logger.exception('generate failed: %s', e)

asyncio.get_event_loop().run_until_complete(run())
