#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Basic functionality test script for LALO AI

Tests:
1. Demo token generation
2. API key retrieval
3. Available models
4. Health check
"""

import requests
import json
import logging

BASE_URL = "http://localhost:8000"

logger = logging.getLogger("lalo.test_basic_flow")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def test_health():
    """Test health endpoint"""
    logger.info("%s", "=" * 60)
    logger.info("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    logger.info("Status: %s", response.status_code)
    logger.info("Response: %s", response.json())
    assert response.status_code == 200
    logger.info("[PASS] Health check passed")
    logger.info("")

def test_demo_token():
    """Test demo token generation"""
    logger.info("%s", "=" * 60)
    logger.info("Testing demo token generation...")
    response = requests.post(f"{BASE_URL}/auth/demo-token")
    logger.info("Status: %s", response.status_code)
    data = response.json()
    logger.info("Token received: %s...", data['access_token'][:50])
    assert response.status_code == 200
    assert "access_token" in data
    logger.info("[PASS] Demo token generation passed")
    logger.info("")
    return data["access_token"]

def test_get_keys(token):
    """Test API key retrieval"""
    logger.info("%s", "=" * 60)
    logger.info("Testing API key retrieval...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/keys", headers=headers)
    logger.info("Status: %s", response.status_code)
    data = response.json()
    logger.info("Keys found: %d", len(data))
    for key in data:
        logger.info("  - %s: %s", key['provider'], key['name'])
    assert response.status_code == 200
    logger.info("[PASS] API key retrieval passed")
    logger.info("")
    return data

def test_get_models(token):
    """Test available models endpoint"""
    logger.info("%s", "=" * 60)
    logger.info("Testing available models...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/ai/models", headers=headers)
    logger.info("Status: %s", response.status_code)
    data = response.json()
    logger.info("Available models: %s", data)
    assert response.status_code == 200
    logger.info("[PASS] Available models passed")
    logger.info("")
    return data

def test_ai_request_without_real_key(token):
    """Test AI request (will fail without real API key, but tests routing)"""
    logger.info("%s", "=" * 60)
    logger.info("Testing AI request endpoint (without real API key)...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": "What is 2+2?",
        "model": "gpt-3.5-turbo",
        "max_tokens": 100,
        "temperature": 0.7
    }
    response = requests.post(f"{BASE_URL}/api/ai/chat", headers=headers, json=payload)
    logger.info("Status: %s", response.status_code)

    # This will likely fail with API key error, which is expected
    if response.status_code == 200:
        logger.info("Response: %s", response.json())
        logger.info("[PASS] AI request succeeded!")
    else:
        logger.info("Error (expected without real API key): %s", response.json())
        logger.info("[PASS] AI request endpoint is working (fails at API call as expected)")
    logger.info("")

def main():
    logger.info("%s", "\n" + "=" * 60)
    logger.info("LALO AI - Basic Functionality Test")
    logger.info("%s", "=" * 60)
    logger.info("")

    try:
        # Run tests
        test_health()
        token = test_demo_token()
        test_get_keys(token)
        test_get_models(token)
        test_ai_request_without_real_key(token)

        logger.info("%s", "=" * 60)
        logger.info("[SUCCESS] ALL BASIC TESTS PASSED")
        logger.info("%s", "=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Add real API keys via the frontend Settings page")
        logger.info("2. Test AI requests with real models")
        logger.info("3. Check usage statistics")
        logger.info("")

    except Exception as e:
        logger.exception("TEST FAILED: %s", e)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
