"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import pytest

from core.services.rbac import rbac_service
from core.services.rbac import RBACService


def test_runtime_endpoints_with_permission(client, request):
    # Test user from conftest is TEST_USER_ID
    from tests.conftest import TEST_USER_ID

    # Grant manage permission to test user via role
    role = "test-managers"
    perm = "agent.manage"
    rbac_service.grant_permission_to_role(role, perm)
    rbac_service.assign_role_to_user(TEST_USER_ID, role)

    # Create runtime agent
    resp = client.post("/api/runtime/agents/create", json={"agent_type": "int-test"})
    assert resp.status_code == 200
    agent_id = resp.json().get("agent_id")
    assert agent_id

    # List agents
    resp = client.get("/api/runtime/agents/list")
    assert resp.status_code == 200

    # Get agent status
    resp = client.get(f"/api/runtime/agents/{agent_id}/status")
    assert resp.status_code == 200

    # Create workflow
    wf_resp = client.post("/api/runtime/workflows/create", json={"name": "wf1", "steps": []})
    assert wf_resp.status_code == 200
    wf_id = wf_resp.json().get("workflow_id")

    # Get workflow status
    resp = client.get(f"/api/runtime/workflows/{wf_id}/status")
    assert resp.status_code == 200


def test_runtime_endpoints_without_permission(client):
    # Override current user to someone without permissions
    from app import app
    async def _no_perm_user():
        return "no-perm@example.com"

    app.dependency_overrides.clear()
    from core.services.auth import get_current_user
    app.dependency_overrides[get_current_user] = _no_perm_user

    # Calls should return 403
    resp = client.post("/api/runtime/agents/create", json={"agent_type": "int-test"})
    assert resp.status_code == 403

    # Clean up override
    app.dependency_overrides.clear()
