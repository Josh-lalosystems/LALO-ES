#!/usr/bin/env python3
"""Quick test script for local inference"""
import requests
import json

# Get demo token
print("Getting demo token...")
token_response = requests.post("http://localhost:8000/auth/demo-token")
token = token_response.json()["access_token"]
print(f"Token: {token[:20]}...")

# Test AI request
print("\nTesting AI request: 'What is 2+2?'")
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}
payload = {
    "prompt": "What is 2+2?",
    "model": "tinyllama",
    "max_tokens": 100
}

response = requests.post(
    "http://localhost:8000/api/ai/chat",
    headers=headers,
    json=payload
)

print(f"\nStatus Code: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Response: {result['response']}")
    print(f"Model: {result['model']}")
    print(f"Routing: {result.get('routing_info', {})}")
else:
    print(f"Error: {response.text}")
