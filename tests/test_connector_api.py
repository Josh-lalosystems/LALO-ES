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
