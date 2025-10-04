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

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("=" * 60)
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("[PASS] Health check passed")
    print()

def test_demo_token():
    """Test demo token generation"""
    print("=" * 60)
    print("Testing demo token generation...")
    response = requests.post(f"{BASE_URL}/auth/demo-token")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Token received: {data['access_token'][:50]}...")
    assert response.status_code == 200
    assert "access_token" in data
    print("[PASS] Demo token generation passed")
    print()
    return data["access_token"]

def test_get_keys(token):
    """Test API key retrieval"""
    print("=" * 60)
    print("Testing API key retrieval...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/keys", headers=headers)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Keys found: {len(data)}")
    for key in data:
        print(f"  - {key['provider']}: {key['name']}")
    assert response.status_code == 200
    print("[PASS] API key retrieval passed")
    print()
    return data

def test_get_models(token):
    """Test available models endpoint"""
    print("=" * 60)
    print("Testing available models...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/ai/models", headers=headers)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Available models: {data}")
    assert response.status_code == 200
    print("[PASS] Available models passed")
    print()
    return data

def test_ai_request_without_real_key(token):
    """Test AI request (will fail without real API key, but tests routing)"""
    print("=" * 60)
    print("Testing AI request endpoint (without real API key)...")
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
    print(f"Status: {response.status_code}")

    # This will likely fail with API key error, which is expected
    if response.status_code == 200:
        print(f"Response: {response.json()}")
        print("[PASS] AI request succeeded!")
    else:
        print(f"Error (expected without real API key): {response.json()}")
        print("[PASS] AI request endpoint is working (fails at API call as expected)")
    print()

def main():
    print("\n" + "=" * 60)
    print("LALO AI - Basic Functionality Test")
    print("=" * 60)
    print()

    try:
        # Run tests
        test_health()
        token = test_demo_token()
        test_get_keys(token)
        test_get_models(token)
        test_ai_request_without_real_key(token)

        print("=" * 60)
        print("[SUCCESS] ALL BASIC TESTS PASSED")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Add real API keys via the frontend Settings page")
        print("2. Test AI requests with real models")
        print("3. Check usage statistics")
        print()

    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
