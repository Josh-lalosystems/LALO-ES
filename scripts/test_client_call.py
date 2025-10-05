"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from fastapi.testclient import TestClient
from app import app
import logging

logger = logging.getLogger('scripts.test_client_call')
client = TestClient(app)

# Get demo token
resp = client.post('/auth/demo-token')
logger.info('demo-token status %s', resp.status_code)
logger.info('token body %s', resp.json())

token = resp.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# Call models
logger.info('\nCalling /api/ai/models')
resp = client.get('/api/ai/models', headers=headers)
logger.info('%s %s', resp.status_code, resp.text)

# Call chat
logger.info('\nCalling /api/ai/chat')
resp = client.post('/api/ai/chat', json={'prompt':'Hello from test client','model':'gpt-3.5-turbo'}, headers=headers)
logger.info('%s %s', resp.status_code, resp.text)

# Call image
logger.info('\nCalling /api/ai/image')
resp = client.post('/api/ai/image', json={'prompt':'A red ball','model':'gpt-image-1'}, headers=headers)
logger.info('%s %s', resp.status_code, resp.text)
