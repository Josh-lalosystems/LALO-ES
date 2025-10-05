from core.services.rbac import rbac_service

TEST_USER = "test-user@example.com"


def test_rbac_assign_and_get_permissions():
    # Grant a permission to a role and assign role to user
    role = "test-admin"
    perm = "agent.assign"

    rbac_service.grant_permission_to_role(role, perm)
    rbac_service.assign_role_to_user(TEST_USER, role)

    perms = rbac_service.get_user_permissions(TEST_USER)
    assert perm in perms
