"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

import pytest


def get_demo_token(client):
    # Call demo token endpoint if present or return a placeholder
    resp = client.post('/auth/demo-token', json={})
    if resp.status_code == 200:
        # TokenResponse has access_token field in auth.py
        return resp.json().get('access_token') or resp.json().get('token')
    return None


@pytest.mark.order(1)
def test_workflow_happy_path(client):
    token = get_demo_token(client)
    headers = {'Authorization': f'Bearer {token}'} if token else {}

    # Start workflow
    resp = client.post('/api/workflow/start', json={'user_request': 'Summarize quarterly sales'}, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert 'session_id' in data
    session_id = data['session_id']

    # Get status
    resp = client.get(f'/api/workflow/{session_id}/status', headers=headers)
    assert resp.status_code == 200

    # Submit approve feedback (simulate user approval)
    resp = client.post(f'/api/workflow/{session_id}/feedback', json={'feedback_type': 'approve', 'message': 'Looks good'}, headers=headers)
    assert resp.status_code == 200

    # Advance workflow
    resp = client.post(f'/api/workflow/{session_id}/advance', headers=headers)
    assert resp.status_code == 200
