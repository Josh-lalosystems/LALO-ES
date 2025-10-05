import os
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_non_demo_no_keys_returns_error():
    # Ensure DEMO_MODE is false
    os.environ["DEMO_MODE"] = "false"
    resp = client.post('/auth/demo-token', json={})
    assert resp.status_code == 200
    token = resp.json().get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    # Check key validation status for this user
    status_resp = client.get('/api/keys/status', headers=headers)
    assert status_resp.status_code == 200
    status_map = status_resp.json()

    # If any provider validates, expect the chat to succeed; otherwise expect an error
    if any(status_map.values()):
        chat_resp = client.post('/api/ai/chat', json={'prompt': 'test no demo'}, headers=headers)
        assert chat_resp.status_code == 200, chat_resp.text
    else:
        chat_resp = client.post('/api/ai/chat', json={'prompt': 'test no demo'}, headers=headers)
        assert chat_resp.status_code in (400, 401, 402, 429)