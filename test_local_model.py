#!/usr/bin/env python3
"""Test local model availability"""
import sys
import requests
import json

# Force UTF-8 encoding on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Testing Local Model Availability")
print("=" * 60)

# Step 1: Get demo token
print("\n1. Getting demo token...")
try:
    response = requests.post("http://127.0.0.1:8000/auth/demo-token")
    response.raise_for_status()
    token_data = response.json()
    token = token_data["access_token"]
    print(f"✓ Got token: {token[:20]}...")
except Exception as e:
    print(f"✗ Failed to get token: {e}")
    exit(1)

# Step 2: Get available models
print("\n2. Getting available models...")
try:
    response = requests.get(
        "http://127.0.0.1:8000/api/ai/models",
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    models = response.json()
    print(f"✓ Available models: {models}")
except Exception as e:
    print(f"✗ Failed to get models: {e}")
    print(f"  Response: {response.text if 'response' in locals() else 'N/A'}")
    exit(1)

# Step 3: Test chat request with tinyllama
print("\n3. Testing chat request with tinyllama...")
try:
    response = requests.post(
        "http://127.0.0.1:8000/api/ai/chat",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "prompt": "What is 2+2?",
            "model": "tinyllama"
        },
        timeout=30
    )

    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text}")

    if response.status_code == 200:
        data = response.json()
        print(f"✓ SUCCESS!")
        print(f"  Model used: {data.get('model')}")
        print(f"  Response: {data.get('response')}")
    else:
        print(f"✗ Request failed with status {response.status_code}")

except Exception as e:
    print(f"✗ Request failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
