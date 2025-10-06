#!/usr/bin/env python3
"""Test uvicorn startup to diagnose hang"""
import sys
import logging
import os

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

print("=" * 60)
print("UVICORN STARTUP DIAGNOSTIC")
print("=" * 60)

print("\n1. Testing imports...")
try:
    print("   - Importing FastAPI...")
    from fastapi import FastAPI
    print("   [OK] FastAPI imported")

    print("   - Importing uvicorn...")
    import uvicorn
    print(f"   [OK] uvicorn imported (version: {uvicorn.__version__})")

    print("   - Importing app module...")
    from app import app
    print("   [OK] app module imported")

except Exception as e:
    print(f"   [FAIL] Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n2. Testing app creation...")
try:
    print(f"   - App title: {app.title}")
    print(f"   - App version: {app.version}")
    print("   [OK] App created successfully")
except Exception as e:
    print(f"   [FAIL] App creation failed: {e}")
    sys.exit(1)

print("\n3. Attempting to start uvicorn...")
print("   NOTE: This will start the server. Press Ctrl+C to stop.")
print("   If it hangs here, the issue is in uvicorn.run()")
print()

try:
    # Start with debug logging
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        log_level="debug",
        access_log=True,
        timeout_keep_alive=5
    )
except KeyboardInterrupt:
    print("\n\n✓ Server stopped by user (Ctrl+C)")
    print("✓ NO HANG - Server started and stopped cleanly")
except Exception as e:
    print(f"\n\n✗ Server crashed: {e}")
    import traceback
    traceback.print_exc()
