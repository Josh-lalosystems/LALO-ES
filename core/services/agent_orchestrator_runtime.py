"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
Lightweight Agent Orchestrator runtime used by routes.

Selects a pluggable executor implementation based on environment variable
`USE_REAL_EXECUTOR`. Default is demo executor for local/dev.
"""
import os
import logging
from typing import Dict, Any, Tuple

from core.services.agent_runtime import runtime_agent_manager
from core.services.executor import default_executor, start_executor_worker

logger = logging.getLogger(__name__)

# Lazy import RealExecutor to avoid heavy dependencies at module import time
USE_REAL = os.getenv("USE_REAL_EXECUTOR", "false").lower() == "true"
if USE_REAL:
    try:
        from core.services.real_executor import RealExecutor
        executor_instance = RealExecutor()
        logger.info("Using RealExecutor for runtime orchestrator")
    except Exception:
        logger.exception("Failed to initialize RealExecutor, falling back to demo executor")
        executor_instance = default_executor
else:
    executor_instance = default_executor


class AgentOrchestratorRuntime:
    def __init__(self, start_worker: bool = True):
        self.executor_stop_event = None
        if start_worker:
            self.executor_stop_event = start_executor_worker(executor_instance)
            logger.info("AgentOrchestratorRuntime started executor worker")

    def assign_task(self, agent_type: str, task: Dict[str, Any]) -> Tuple[str, str]:
        agent_id, task_id = runtime_agent_manager.assign_task(agent_type, task)
        logger.info("RuntimeOrchestrator assigned task %s to agent %s", task_id, agent_id)
        return agent_id, task_id


# Global instance for routes to import
agent_orchestrator = AgentOrchestratorRuntime()
