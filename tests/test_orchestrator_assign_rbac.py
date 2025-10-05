def test_orchestrator_assign_with_and_without_permission(client):
    from tests.conftest import TEST_USER_ID
    from core.services.rbac import rbac_service

    # Ensure permission granted to test user
    role = "assign-role"
    perm = "agent.assign"
    rbac_service.grant_permission_to_role(role, perm)
    rbac_service.assign_role_to_user(TEST_USER_ID, role)

    # Assign via orchestrator endpoint
    resp = client.post("/api/runtime/agents/assign?agent_type=worker", json={"task": {"prompt": "hello"}})
    assert resp.status_code == 200
    data = resp.json()
    assert "agent_id" in data and "task_id" in data

    # Now override current user to one without permission
    from app import app
    async def _no_perm_user():
        return "no-perm@example.com"

    app.dependency_overrides.clear()
    from core.services.auth import get_current_user
    app.dependency_overrides[get_current_user] = _no_perm_user

    resp = client.post("/api/runtime/agents/assign?agent_type=worker", json={"task": {"prompt": "hello"}})
    assert resp.status_code == 403

    # Clean up override
    app.dependency_overrides.clear()
