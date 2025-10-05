#!/usr/bin/env python
"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

"""Debug import issue"""

import sys
import logging

logger = logging.getLogger("lalo.test_import_debug")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

logger.info("Step 1: Import FastAPI components")
from fastapi import APIRouter, Depends
logger.info("  OK")

logger.info("Step 2: Import services individually")

logger.info("  2a: auth")
from core.services.auth import get_current_user
logger.info("  OK")

logger.info("  2b: ai_service")
from core.services.ai_service import ai_service
logger.info("  OK")

logger.info("  2c: key_manager")
from core.services.key_management import key_manager
logger.info("  OK")

logger.info("  2d: database_service")
from core.services.database_service import database_service
logger.info("  OK")

logger.info("Step 3: Create a test router")
test_router = APIRouter(prefix="/test")
logger.info("  OK")

logger.info("Step 4: Add a route with dependency")

@test_router.get("/test")
async def test_endpoint(current_user: str = Depends(get_current_user)):
    return {"user": current_user}

logger.info("  OK")

logger.info("All steps successful - no hang detected")
logger.info("Now trying to import the actual ai_routes module...")

from core.routes import ai_routes as ai_routes_module
logger.info("  Module imported OK")

logger.info("Now trying to import router from ai_routes...")
from core.routes.ai_routes import router
logger.info("  Router imported OK!")
