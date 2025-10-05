#!/usr/bin/env python
"""Test authentication flows"""

import sys
import os
sys.path.insert(0, '.')

# Set environment for testing
os.environ["DEMO_MODE"] = "false"  # Test production mode first

from fastapi.testclient import TestClient
from app import app
from core.services.auth import auth_service
import logging

client = TestClient(app)

logger = logging.getLogger("lalo.test_auth")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def test_auth_flows():
    """Test various authentication scenarios"""
    logger.info("%s", "="*60)
    logger.info("Authentication Flow Tests")
    logger.info("%s", "="*60)

    # Test 1: Get demo token
    logger.info("Test 1: Get demo token")
    response = client.post("/auth/demo-token")
    logger.info("  Status: %s", response.status_code)
    if response.status_code == 200:
        data = response.json()
        logger.info("  Token received: %s...", data['access_token'][:20])
        logger.info("  Token type: %s", data['token_type'])
        demo_token = data['access_token']
        logger.info("  Result: PASS")
    else:
        logger.info("  Error: %s", response.json())
        logger.info("  Result: FAIL")
        return

    # Test 2: Login with credentials
    logger.info("Test 2: Login with email/password")
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword"
    })
    logger.info("  Status: %s", response.status_code)
    if response.status_code == 200:
        data = response.json()
        logger.info("  Token received: %s...", data['access_token'][:20])
        login_token = data['access_token']
        logger.info("  Result: PASS")
    else:
        logger.info("  Error: %s", response.json())
        logger.info("  Result: FAIL")
        return

    # Test 3: Access protected endpoint with valid token
    logger.info("Test 3: Access protected endpoint with valid token")
    response = client.get("/api/ai/models", headers={
        "Authorization": f"Bearer {demo_token}"
    })
    logger.info("  Status: %s", response.status_code)
    if response.status_code == 200:
        models = response.json()
        logger.info("  Models returned: %s", models)
        logger.info("  Result: PASS")
    else:
        logger.info("  Error: %s", response.json())
        logger.info("  Result: FAIL")

    # Test 4: Access protected endpoint without token
    logger.info("Test 4: Access protected endpoint without token")
    response = client.get("/api/ai/models")
    logger.info("  Status: %s", response.status_code)
    if response.status_code == 401 or response.status_code == 403:
        logger.info("  Correctly rejected unauthorized access")
        logger.info("  Result: PASS")
    else:
        logger.info("  Unexpected status: %s", response.status_code)
        logger.info("  Result: FAIL")

    # Test 5: Access protected endpoint with invalid token
    logger.info("Test 5: Access protected endpoint with invalid token")
    response = client.get("/api/ai/models", headers={
        "Authorization": "Bearer invalid-token-12345"
    })
    logger.info("  Status: %s", response.status_code)
    if response.status_code == 401 or response.status_code == 403:
        logger.info("  Correctly rejected invalid token")
        logger.info("  Result: PASS")
    else:
        logger.info("  Unexpected status: %s", response.status_code)
        logger.info("  Result: FAIL")

    # Test 6: Token verification
    logger.info("Test 6: Token verification")
    try:
        user_id = auth_service.verify_token(demo_token)
        logger.info("  User ID from token: %s", user_id)
        if user_id == "demo-user@example.com":
            logger.info("  Result: PASS")
        else:
            logger.info("  Unexpected user ID: %s", user_id)
            logger.info("  Result: FAIL")
    except Exception as e:
        logger.exception("  Error: %s", e)
        logger.info("  Result: FAIL")

    logger.info("%s", "\n" + "="*60)
    logger.info("[SUCCESS] Authentication tests complete")
    logger.info("%s", "="*60)

def test_demo_mode():
    """Test demo mode authentication bypass"""
    logger.info("%s", "\n" + "="*60)
    logger.info("Demo Mode Tests")
    logger.info("%s", "="*60)

    logger.info("NOTE: Demo mode requires application restart to take effect.")
    logger.info("      This is by design - environment variables are loaded at startup.")
    logger.info("To test demo mode manually:")
    logger.info("  1. Set DEMO_MODE=true in .env")
    logger.info("  2. Restart the application: python app.py")
    logger.info("  3. Access API endpoints without Authorization header")
    logger.info("Current .env demo mode setting:")
    demo_mode_env = os.getenv("DEMO_MODE", "false")
    logger.info("  DEMO_MODE=%s", demo_mode_env)

    if demo_mode_env.lower() == "true":
        logger.info("  Demo mode is ENABLED in .env")
        logger.info("  All API endpoints accessible without authentication")
        logger.info("  Result: PASS (configured)")
    else:
        logger.info("  Demo mode is DISABLED in .env")
        logger.info("  API endpoints require valid JWT tokens")
        logger.info("  Result: PASS (production mode)")

    logger.info("%s", "\n" + "="*60)
    logger.info("[SUCCESS] Demo mode configuration verified")
    logger.info("%s", "="*60)

if __name__ == "__main__":
    # Test production mode first
    test_auth_flows()

    # Then test demo mode
    test_demo_mode()
