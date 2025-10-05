import os
import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def get_demo_token():
    resp = client.post("/auth/demo-token", json={})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_demo_chat_and_image_endpoints():
    # Ensure DEMO_MODE is true for this test
    os.environ["DEMO_MODE"] = "true"
    token = get_demo_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Chat
    chat_resp = client.post("/api/ai/chat", json={"prompt": "Hello demo"}, headers=headers)
    assert chat_resp.status_code == 200, chat_resp.text
    body = chat_resp.json()
    assert "response" in body and isinstance(body["response"], str)
    assert body.get("model") in ("demo-model",) or body.get("model") is not None

    # Image
    img_resp = client.post("/api/ai/image", json={"prompt": "a red ball"}, headers=headers)
    assert img_resp.status_code == 200, img_resp.text
    img_body = img_resp.json()
    assert "images" in img_body and isinstance(img_body["images"], list)
    assert len(img_body["images"]) >= 1


if __name__ == "__main__":
    pytest.main([__file__])
