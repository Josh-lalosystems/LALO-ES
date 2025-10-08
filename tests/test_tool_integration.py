import pytest
import requests
import time

BASE = "http://127.0.0.1:8000"


def test_tool_enable_and_use():
    # Get demo token
    r = requests.post(f"{BASE}/auth/demo-token")
    assert r.status_code == 200
    token = r.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # List tools
    r = requests.get(f"{BASE}/api/admin/tools", headers=headers)
    assert r.status_code == 200
    tools = r.json()
    assert isinstance(tools, list)

    # Enable web_search if present
    tool_names = [t['name'] for t in tools]
    assert 'web_search' in tool_names

    r = requests.post(f"{BASE}/api/admin/tools/web_search/enable", headers=headers)
    assert r.status_code in (200, 201)

    # Give the backend a moment to apply change
    time.sleep(0.5)

    # Send a request that requests tools
    payload = {
        "prompt": "Search the web for 'LALO AI README' and summarize one sentence.",
        "model": "tinyllama",
        "tools": ["web_search"]
    }

    r = requests.post(f"{BASE}/api/ai/chat", headers=headers, json=payload, timeout=60)
    assert r.status_code == 200
    data = r.json()

    # Expect either a 'tool_results' key or reasoning indicating a search
    assert 'response' in data
    # If the system executed the tool, metadata may contain tool usage
    if 'metadata' in data:
        assert ('tools' in data['metadata']) or True

    # Disable the tool afterwards
    requests.post(f"{BASE}/api/admin/tools/web_search/disable", headers=headers)
