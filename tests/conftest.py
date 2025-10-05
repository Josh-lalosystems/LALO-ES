"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import os
import pytest
from fastapi.testclient import TestClient

# Test user id used by fixtures
TEST_USER_ID = "test-user@example.com"


@pytest.fixture(scope="session", autouse=True)
def test_app_overrides():
    """
    Autouse fixture to set up a minimal environment for tests:
    - ensure frontend build/static dir exists so app.mount doesn't fail
    - lazily import app
    - override get_current_user
    - patch key_manager and ai_service with deterministic behavior
    """

    # Ensure minimal frontend build/static path exists
    build_static_dir = os.path.join("lalo-frontend", "build", "static")
    created_dir = False
    if not os.path.exists(build_static_dir):
        os.makedirs(build_static_dir, exist_ok=True)
        created_dir = True

    # Ensure tool package doesn't instantiate heavy tools during tests
    os.environ.setdefault("SKIP_TOOL_INIT", "true")

    # Lazy imports after filesystem and env setup
    from app import app
    from core.services.auth import get_current_user
    from core.services import key_management
    from core.services.ai_service import ai_service

    # Override authentication to return a test user
    async def _override_get_current_user():
        return TEST_USER_ID

    app.dependency_overrides[get_current_user] = _override_get_current_user

    # Patch key_manager functions
    original_get_keys = key_management.key_manager.get_keys
    original_validate_keys = key_management.key_manager.validate_keys

    def fake_get_keys(user_id: str):
        if user_id == TEST_USER_ID:
            return {"openai": "test-key"}
        return {}

    async def fake_validate_keys(user_id: str):
        return {"openai": True}

    key_management.key_manager.get_keys = fake_get_keys
    key_management.key_manager.validate_keys = fake_validate_keys

    # Patch ai_service for deterministic responses
    original_models = dict(ai_service.models)
    ai_service.models[TEST_USER_ID] = {"gpt-3.5-turbo": None}

    def fake_get_available_models(user_id: str):
        return list(ai_service.models.get(user_id, {}).keys())

    async def fake_generate(prompt: str, model_name: str = None, user_id: str = None, **kwargs):
        return f"[mocked response] {prompt}"

    ai_service.get_available_models = fake_get_available_models
    ai_service.generate = fake_generate

    # Yield to tests
    yield

    # Teardown
    app.dependency_overrides.pop(get_current_user, None)
    key_management.key_manager.get_keys = original_get_keys
    key_management.key_manager.validate_keys = original_validate_keys
    ai_service.models = original_models

    # Remove temporary build/static dirs if we created them (ignore errors)
    try:
        if created_dir:
            os.rmdir(build_static_dir)
            build_dir = os.path.join("lalo-frontend", "build")
            if os.path.exists(build_dir) and not os.listdir(build_dir):
                os.rmdir(build_dir)
    except Exception:
        pass


@pytest.fixture()
def client():
    """Provide a TestClient instance for tests."""
    from app import app

    return TestClient(app)
