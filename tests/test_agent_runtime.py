"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import pytest

from core.services.agent_runtime import runtime_agent_manager


def test_create_and_assign_agent():
    # Create agent
    agent_id = runtime_agent_manager.create_agent("tester", config={"foo": "bar"})
    assert agent_id in runtime_agent_manager.agents

    # Check status
    status = runtime_agent_manager.get_agent_status(agent_id)
    assert status["id"] == agent_id
    assert status["type"] == "tester"
    assert status["state"] == "idle"

    # Assign a task
    agent = runtime_agent_manager.agents[agent_id]
    task = {"action": "echo", "payload": "hello"}
    task_id = agent.assign_task(task)
    assert isinstance(task_id, str)

    # After assign, agent should be working and have one in_progress task
    status = runtime_agent_manager.get_agent_status(agent_id)
    assert status["state"] == "working"
    assert status["tasks_in_progress"] == 1

    # Complete the task
    agent.complete_task(task_id, result={"ok": True})
    status = runtime_agent_manager.get_agent_status(agent_id)
    assert status["state"] == "idle"
    assert status["tasks_completed"] == 1


def test_get_missing_agent_status():
    res = runtime_agent_manager.get_agent_status("non-existent")
    assert "error" in res


def test_shutdown_agent():
    agent_id = runtime_agent_manager.create_agent("transient")
    assert agent_id in runtime_agent_manager.agents
    runtime_agent_manager.shutdown_agent(agent_id)
    assert agent_id not in runtime_agent_manager.agents
