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
