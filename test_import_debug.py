#!/usr/bin/env python
"""Debug import issue"""

import sys

print("Step 1: Import FastAPI components")
sys.stdout.flush()
from fastapi import APIRouter, Depends
print("  OK")
sys.stdout.flush()

print("Step 2: Import services individually")
sys.stdout.flush()

print("  2a: auth")
sys.stdout.flush()
from core.services.auth import get_current_user
print("  OK")
sys.stdout.flush()

print("  2b: ai_service")
sys.stdout.flush()
from core.services.ai_service import ai_service
print("  OK")
sys.stdout.flush()

print("  2c: key_manager")
sys.stdout.flush()
from core.services.key_management import key_manager
print("  OK")
sys.stdout.flush()

print("  2d: database_service")
sys.stdout.flush()
from core.services.database_service import database_service
print("  OK")
sys.stdout.flush()

print("Step 3: Create a test router")
sys.stdout.flush()
test_router = APIRouter(prefix="/test")
print("  OK")
sys.stdout.flush()

print("Step 4: Add a route with dependency")
sys.stdout.flush()

@test_router.get("/test")
async def test_endpoint(current_user: str = Depends(get_current_user)):
    return {"user": current_user}

print("  OK")
sys.stdout.flush()

print("\nAll steps successful - no hang detected")
print("\nNow trying to import the actual ai_routes module...")
sys.stdout.flush()

from core.routes import ai_routes as ai_routes_module
print("  Module imported OK")
sys.stdout.flush()

print("\nNow trying to import router from ai_routes...")
sys.stdout.flush()
from core.routes.ai_routes import router
print("  Router imported OK!")
