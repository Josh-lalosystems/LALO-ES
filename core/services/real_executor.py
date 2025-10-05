"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
Real executor that delegates task execution to the AIService.

This executor expects tasks to contain at least a `prompt` key. It will
call `ai_service.generate` to produce a result. The call is run synchronously
via `asyncio.run` because the executor runs in a worker thread.
"""
import logging
from typing import Any, Dict

from core.services.ai_service import ai_service

logger = logging.getLogger(__name__)


class RealExecutor:
    def __init__(self, default_model: str = None):
        self.default_model = default_model

    async def execute(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Asynchronous execute method that calls the ai_service.generate coroutine.

        Returns a dict with either `result` or `error`.
        """
        prompt = task.get("prompt")
        model = task.get("model") or self.default_model
        if not prompt:
            # Signal caller about missing required field
            raise ValueError("missing prompt")

        try:
            result = await ai_service.generate(prompt=prompt, model_name=model)
            return {"result": result}
        except Exception as e:
            logger.exception("RealExecutor failed: %s", e)
            # Bubble up exception for the worker loop to capture and mark task as error
            raise
