#!/usr/bin/env python3
"""
Test login script for LALO AI local admin access

This script demonstrates how to log in to the LALO system and provides
credentials you can use in the web interface.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8080"

def test_login():
    """Test login with demo credentials"""
    print("Testing LALO AI Login System")
    print("=" * 40)
    
    # Test demo token endpoint
    print("1. Testing demo token endpoint...")
    try:
        response = requests.post(f"{BASE_URL}/auth/demo-token")
        if response.status_code == 200:
            token_data = response.json()
            print(f"✅ Demo token obtained: {token_data['access_token'][:20]}...")
        else:
            print(f"❌ Demo token failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting demo token: {e}")
        return
    
    # Test regular login endpoint  
    print("\n2. Testing regular login...")
    test_credentials = [
        {"email": "admin@lalo.ai", "password": "admin123"},
        {"email": "test@test.com", "password": "password"},
        {"email": "user@example.com", "password": "demo"}
    ]
    
    for creds in test_credentials:
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=creds)
            if response.status_code == 200:
                token_data = response.json()
                print(f"✅ Login successful with {creds['email']}")
                print(f"   Token: {token_data['access_token'][:20]}...")
                
                # Test accessing admin tools
                headers = {"Authorization": f"Bearer {token_data['access_token']}"}
                tools_response = requests.get(f"{BASE_URL}/api/admin/tools", headers=headers)
                if tools_response.status_code == 200:
                    tools = tools_response.json()
                    print(f"   ✅ Admin tools accessible ({len(tools)} tools available)")
                else:
                    print(f"   ❌ Admin tools failed: {tools_response.status_code}")
                    print(f"   Response: {tools_response.text}")
                break
            else:
                print(f"❌ Login failed for {creds['email']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing {creds['email']}: {e}")
    
    print("\n" + "=" * 40)
    print("WEB LOGIN INSTRUCTIONS:")
    print("=" * 40)
    print("Open your browser to: http://localhost:8000")
    print("")
    print("Use ANY of these credentials to log in:")
    print("  Email: admin@lalo.ai")
    print("  Password: admin123")
    print("")
    print("  Email: test@test.com") 
    print("  Password: password")
    print("")
    print("  Email: user@example.com")
    print("  Password: demo")
    print("")
    print("The system is in DEMO MODE and accepts any email/password!")
    print("=" * 40)

if __name__ == "__main__":
    test_login()