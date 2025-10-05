"""
Lightweight in-memory Agent Manager for runtime/ephemeral agents.

This is intentionally separate from the DB-backed `AgentManager` service so
it does not conflict with persistent agent definitions. It provides a small
pool of workers usable by the Agent Orchestration workstream while the
core inference team focuses on model integration.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class Agent:
    """Individual agent instance (ephemeral)"""

    def __init__(self, agent_id: str, agent_type: str, config: Dict):
        self.id = agent_id
        self.type = agent_type
        self.config = config
        self.state = "idle"
        self.created_at = datetime.now()
        self.task_history: List[Dict] = []

    def assign_task(self, task: Dict) -> str:
        task_id = str(uuid4())
        self.state = "working"
        self.task_history.append({
            "id": task_id,
            "task": task,
            "started_at": datetime.now(),
            "status": "in_progress"
        })
        logger.info("Assigned task %s to agent %s", task_id, self.id)
        return task_id

    def complete_task(self, task_id: str, result: Any):
        for task in self.task_history:
            if task["id"] == task_id:
                task["status"] = "completed"
                task["completed_at"] = datetime.now()
                task["result"] = result
                break
        self.state = "idle"


class AgentManager:
    """In-memory manager for ephemeral agents"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        logger.info("Runtime AgentManager initialized")

    def create_agent(self, agent_type: str, config: Dict = None) -> str:
        agent_id = str(uuid4())
        agent = Agent(agent_id, agent_type, config or {})
        self.agents[agent_id] = agent
        logger.info("Created runtime agent: %s (%s)", agent_id, agent_type)
        return agent_id

    def get_available_agent(self, agent_type: str) -> Optional[Agent]:
        for agent in self.agents.values():
            if agent.type == agent_type and agent.state == "idle":
                return agent
        return None

    def get_or_create_agent(self, agent_type: str, config: Dict = None) -> Agent:
        agent = self.get_available_agent(agent_type)
        if agent is None:
            agent_id = self.create_agent(agent_type, config)
            agent = self.agents[agent_id]
        return agent

    def assign_task(self, agent_type: str, task: Dict) -> tuple[str, str]:
        agent = self.get_or_create_agent(agent_type)
        task_id = agent.assign_task(task)
        return agent.id, task_id

    def get_agent_status(self, agent_id: str) -> Dict:
        if agent_id not in self.agents:
            return {"error": "Agent not found"}

        agent = self.agents[agent_id]
        return {
            "id": agent.id,
            "type": agent.type,
            "state": agent.state,
            "created_at": agent.created_at.isoformat(),
            "tasks_completed": len([t for t in agent.task_history if t["status"] == "completed"]),
            "tasks_in_progress": len([t for t in agent.task_history if t["status"] == "in_progress"])
        }

    def shutdown_agent(self, agent_id: str):
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info("Shutdown runtime agent: %s", agent_id)


# Global runtime instance (used by the Agent Orchestration team)
runtime_agent_manager = AgentManager()

# Ensure the demo worker is imported so it starts in development/tests
try:
    # Import here to avoid circular imports if worker imports runtime manager
    from core.services import agent_worker  # noqa: F401
except Exception:
    # If worker cannot start (e.g., env/config), continue without it
    logger.debug("Agent worker module not started: %s", Exception)
