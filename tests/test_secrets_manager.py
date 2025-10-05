"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import pytest

from core.services.secrets_manager import secrets_manager


def test_secrets_crud_roundtrip():
    name = "test_api_key"
    value = "super-secret-value"
    user = "demo-user@example.com"

    # ensure clean state
    secrets_manager.delete_secret(name, user)

    meta = secrets_manager.set_secret(name, value, user)
    assert meta["name"] == name
    assert meta["user_id"] == user
    assert meta["version"] >= 1

    fetched = secrets_manager.get_secret(name, user)
    assert fetched == value

    # update
    secrets_manager.set_secret(name, value + "2", user)
    fetched2 = secrets_manager.get_secret(name, user)
    assert fetched2 == value + "2"

    # list
    items = secrets_manager.list_secrets(user)
    assert any(x["name"] == name for x in items)

    # delete
    ok = secrets_manager.delete_secret(name, user)
    assert ok is True
    assert secrets_manager.get_secret(name, user) is None
