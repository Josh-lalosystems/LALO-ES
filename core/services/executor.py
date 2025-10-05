"""
Pluggable executor interface for executing tasks assigned to runtime agents.

Provides a DemoExecutor implementation for local/demo use which can be
replaced by a real executor that invokes model backends or tools.
"""
from abc import ABC, abstractmethod
from typing import Any
import time
import threading
import logging
import asyncio
import inspect
from datetime import datetime

from core.services.agent_runtime import runtime_agent_manager

logger = logging.getLogger(__name__)


# Synchronous executor interface (backwards compatible)
class Executor(ABC):
    @abstractmethod
    def execute(self, agent_id: str, task: dict) -> Any:
        """Execute a task and return a result (sync)"""


class DemoExecutor(Executor):
    """Simple demo executor that sleeps briefly and returns a demo result."""

    def __init__(self, delay: float = 1.0):
        self.delay = delay

    def execute(self, agent_id: str, task: dict) -> dict:
        logger.info("DemoExecutor executing task %s for agent %s", task.get("id"), agent_id)
        # Simulate work
        time.sleep(self.delay)
        return {"demo": True, "completed_at": datetime.utcnow().isoformat()}


def _sync_worker_loop(stop_event: threading.Event, executor: Executor):
    logger.info("Executor worker started using %s", executor.__class__.__name__)
    while not stop_event.is_set():
        try:
            for agent in list(runtime_agent_manager.agents.values()):
                for task in list(agent.task_history):
                    if task.get("status") == "in_progress":
                        task_id = task.get("id")
                        logger.debug("Executor worker processing %s for %s", task_id, agent.id)
                        try:
                            result = executor.execute(agent.id, task)
                        except Exception as e:
                            logger.exception("Sync executor failed: %s", e)
                            result = {"error": str(e)}
                        agent.complete_task(task_id, result=result)
        except Exception as e:
            logger.exception("Executor loop error: %s", e)
        time.sleep(0.2)


async def _async_worker_loop(stop_event: threading.Event, executor: Any):
    logger.info("Async executor worker started using %s", executor.__class__.__name__)
    while not stop_event.is_set():
        try:
            for agent in list(runtime_agent_manager.agents.values()):
                for task in list(agent.task_history):
                    if task.get("status") == "in_progress":
                        task_id = task.get("id")
                        logger.debug("Async executor processing %s for %s", task_id, agent.id)
                        try:
                            result = await executor.execute(agent.id, task)
                        except Exception as e:
                            logger.exception("Async executor failed: %s", e)
                            result = {"error": str(e)}
                        agent.complete_task(task_id, result=result)
        except Exception as e:
            logger.exception("Async executor loop error: %s", e)
        await asyncio.sleep(0.2)


def start_executor_worker(executor: Any = None) -> threading.Event:
    """Start a background worker for the provided executor.

    If the executor implements an async `execute` coroutine, an asyncio
    worker loop will be started in a dedicated thread and the coroutine
    will be awaited. Otherwise a synchronous worker thread will be used.
    Returns a threading.Event that can be set to stop the worker.
    """
    stop_event = threading.Event()
    exec_instance = executor or DemoExecutor()

    # Detect if executor.execute is a coroutine function
    is_async = False
    try:
        is_async = inspect.iscoroutinefunction(getattr(exec_instance, "execute"))
    except Exception:
        is_async = False

    if is_async:
        # Run asyncio worker loop in a separate thread
        def _runner():
            try:
                asyncio.run(_async_worker_loop(stop_event, exec_instance))
            except Exception as e:
                logger.exception("Async executor runner crashed: %s", e)

        t = threading.Thread(target=_runner, daemon=True)
        t.start()
    else:
        t = threading.Thread(target=_sync_worker_loop, args=(stop_event, exec_instance), daemon=True)
        t.start()

    return stop_event


# Default demo executor (module-level starter can be used by other modules)
default_executor = DemoExecutor()


def start_default_executor():
    return start_executor_worker(default_executor)
