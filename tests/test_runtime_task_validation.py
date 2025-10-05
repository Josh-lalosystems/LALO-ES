import time
import threading

from core.services.executor import start_executor_worker
from core.services.agent_runtime import runtime_agent_manager
from core.services.agent_runtime import runtime_agent_manager as manager


class BoomAsyncExecutor:
    """Async executor that raises an exception to simulate backend errors."""

    async def execute(self, agent_id: str, task: dict):
        raise Exception("boom")


def test_assign_task_missing_prompt_returns_400(client):
    # assign via orchestrator route without prompt should return 400
    resp = client.post("/api/runtime/agents/assign?agent_type=test", json={"task": {}})
    assert resp.status_code == 400
    assert "prompt" in resp.json().get("detail", "")


def test_async_executor_error_marks_task_with_error():
    # start a boom async executor worker
    executor = BoomAsyncExecutor()
    stop_event = start_executor_worker(executor)

    try:
        agent_id = runtime_agent_manager.create_agent("test", {})
        task = {"prompt": "hello"}
        agent_id, task_id = runtime_agent_manager.assign_task("test", task)

        # Wait a short time for worker to run
        time.sleep(0.5)

        agent = runtime_agent_manager.agents[agent_id]
        # Find task by id
        found = None
        for t in agent.task_history:
            if t["id"] == task_id:
                found = t
                break

        assert found is not None
        assert found["status"] == "completed"
        assert isinstance(found.get("result"), dict)
        assert "boom" in str(found["result"].get("error", "")) or "boom" in str(found["result"]) 
    finally:
        stop_event.set()
