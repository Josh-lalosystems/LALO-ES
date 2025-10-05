"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import time

from core.services.agent_runtime import runtime_agent_manager


def test_worker_completes_task():
    # Create agent and assign a task
    agent_id = runtime_agent_manager.create_agent("worker-test")
    agent = runtime_agent_manager.agents[agent_id]
    task_id = agent.assign_task({"action": "sleep", "payload": 1})

    # Wait for worker to run (AGENT_WORKER_DELAY_SECS defaults to 1)
    time.sleep(2)

    # Verify task completed
    status = runtime_agent_manager.get_agent_status(agent_id)
    assert status["tasks_completed"] >= 1
