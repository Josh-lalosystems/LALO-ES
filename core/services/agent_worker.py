"""
Simple demo worker to simulate execution of tasks assigned to runtime agents.

Behavior:
- Polls `runtime_agent_manager.agents` for tasks with status "in_progress".
- Waits `AGENT_WORKER_DELAY_SECS` seconds and marks the task completed with a simple result.
- Controlled by `AGENT_WORKER_ENABLED` env var (defaults to true for demo).
"""
import os
import time
import threading
import logging
from datetime import datetime

from core.services.agent_runtime import runtime_agent_manager

logger = logging.getLogger(__name__)

AGENT_WORKER_ENABLED = os.getenv("AGENT_WORKER_ENABLED", "true").lower() == "true"
AGENT_WORKER_DELAY_SECS = int(os.getenv("AGENT_WORKER_DELAY_SECS", "1"))


def _worker_loop(stop_event: threading.Event):
    logger.info("Agent worker started (demo mode: %s)", AGENT_WORKER_ENABLED)
    while not stop_event.is_set():
        try:
            for agent in list(runtime_agent_manager.agents.values()):
                # Find tasks in progress
                for task in list(agent.task_history):
                    if task.get("status") == "in_progress":
                        task_id = task.get("id")
                        logger.info("Worker: executing task %s for agent %s", task_id, agent.id)
                        # Simulate work
                        time.sleep(AGENT_WORKER_DELAY_SECS)
                        # Mark complete with a demo result
                        agent.complete_task(task_id, result={"completed_at": datetime.utcnow().isoformat(), "demo": True})
        except Exception as e:
            logger.exception("Agent worker loop error: %s", e)

        # Small sleep to avoid busy loop
        time.sleep(0.2)


def start_worker_thread() -> threading.Event:
    stop_event = threading.Event()
    if AGENT_WORKER_ENABLED:
        t = threading.Thread(target=_worker_loop, args=(stop_event,), daemon=True)
        t.start()
    return stop_event


# Start worker on import in demo/dev mode. Tests can rely on this behavior.
_stop_event = start_worker_thread()
