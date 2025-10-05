"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""
Workflow State Machine - Manages multi-step workflow execution

This module provides a pure state-management system for workflows consisting
of ordered steps with dependencies. It is intentionally independent of any
model backend so the Agent team can progress in parallel with inference work.
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStep:
    """Individual step in a workflow"""

    def __init__(self, step_id: str, step_type: str, config: Dict):
        self.id = step_id
        self.type = step_type
        self.config = config
        self.status = StepStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.dependencies: List[str] = config.get("dependencies", [])

    def can_execute(self, completed_steps: set) -> bool:
        return all(dep in completed_steps for dep in self.dependencies)

    def start(self):
        self.status = StepStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, result: Any):
        self.status = StepStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now()

    def fail(self, error: str):
        self.status = StepStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()


class Workflow:
    """Workflow instance with state management"""

    def __init__(self, workflow_id: str, name: str, steps: List[Dict]):
        self.id = workflow_id
        self.name = name
        self.status = WorkflowStatus.PENDING
        self.steps: Dict[str, WorkflowStep] = {}
        self.execution_order: List[str] = []
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        for step_config in steps:
            step = WorkflowStep(
                step_id=step_config.get("id", str(uuid4())),
                step_type=step_config["type"],
                config=step_config
            )
            self.steps[step.id] = step

        self.execution_order = self._calculate_execution_order()

    def _calculate_execution_order(self) -> List[str]:
        visited = set()
        order: List[str] = []

        def visit(step_id: str):
            if step_id in visited:
                return
            visited.add(step_id)
            step = self.steps[step_id]
            for dep in step.dependencies:
                if dep in self.steps:
                    visit(dep)
            order.append(step_id)

        for step_id in list(self.steps.keys()):
            visit(step_id)

        return order

    def get_next_step(self) -> Optional[WorkflowStep]:
        completed = {sid for sid, s in self.steps.items() if s.status == StepStatus.COMPLETED}

        for step_id in self.execution_order:
            step = self.steps[step_id]
            if step.status == StepStatus.PENDING and step.can_execute(completed):
                return step

        return None

    def start(self):
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self):
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.now()

    def fail(self):
        self.status = WorkflowStatus.FAILED
        self.completed_at = datetime.now()

    def get_progress(self) -> Dict:
        total = len(self.steps)
        completed = sum(1 for s in self.steps.values() if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in self.steps.values() if s.status == StepStatus.FAILED)

        return {
            "total_steps": total,
            "completed_steps": completed,
            "failed_steps": failed,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
            "status": self.status.value
        }


class WorkflowManager:
    """Manages workflow instances"""

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        logger.info("WorkflowManager initialized")

    def create_workflow(self, name: str, steps: List[Dict]) -> str:
        workflow_id = str(uuid4())
        workflow = Workflow(workflow_id, name, steps)
        self.workflows[workflow_id] = workflow
        logger.info("Created workflow: %s (%s)", workflow_id, name)
        return workflow_id

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self.workflows.get(workflow_id)

    def start_workflow(self, workflow_id: str):
        if workflow_id in self.workflows:
            self.workflows[workflow_id].start()

    def get_workflow_status(self, workflow_id: str) -> Dict:
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}

        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "progress": workflow.get_progress(),
            "created_at": workflow.created_at.isoformat(),
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "steps": [
                {
                    "id": step.id,
                    "type": step.type,
                    "status": step.status.value,
                    "result": step.result
                }
                for step in workflow.steps.values()
            ]
        }


# Global instance used by the Agent frontend and orchestration APIs
workflow_manager = WorkflowManager()
