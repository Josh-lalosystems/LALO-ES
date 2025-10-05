import pytest

from core.services.workflow_state import (
    workflow_manager,
    WorkflowStatus,
    StepStatus
)


def test_create_and_start_workflow():
    steps = [
        {"id": "s1", "type": "task", "dependencies": []},
        {"id": "s2", "type": "task", "dependencies": ["s1"]},
        {"id": "s3", "type": "task", "dependencies": ["s2"]}
    ]

    wf_id = workflow_manager.create_workflow("testwf", steps)
    assert wf_id in workflow_manager.workflows

    wf = workflow_manager.get_workflow(wf_id)
    assert wf.status == WorkflowStatus.PENDING

    # Start workflow
    workflow_manager.start_workflow(wf_id)
    assert wf.status == WorkflowStatus.RUNNING

    # Get next step (should be s1)
    next_step = wf.get_next_step()
    assert next_step.id == "s1"

    # Execute s1
    next_step.start()
    next_step.complete({"ok": True})

    # Next step should be s2
    next_step = wf.get_next_step()
    assert next_step.id == "s2"

    # Complete s2 and s3
    next_step.start()
    next_step.complete({})
    s3 = wf.get_next_step()
    s3.start()
    s3.complete({})

    # After steps complete, mark workflow complete
    wf.complete()
    assert wf.status == WorkflowStatus.COMPLETED


def test_workflow_with_missing_dependency():
    # Step references a dependency that doesn't exist — should still calculate order
    steps = [
        {"id": "a", "type": "task", "dependencies": ["missing"]},
        {"id": "b", "type": "task", "dependencies": []}
    ]
    wf_id = workflow_manager.create_workflow("badwf", steps)
    wf = workflow_manager.get_workflow(wf_id)
    # Execution order should include both steps
    assert set(wf.execution_order) == {"a", "b"}
