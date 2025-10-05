"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_add_list_connector():
    payload = {"type": "dummy", "config": {}}
    resp = client.post("/api/connectors", json=payload)
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    resp = client.get("/api/connectors")
    assert "dummy" in resp.json()["connectors"]
