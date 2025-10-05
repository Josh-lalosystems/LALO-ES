"""
Copyright (c) 2025 LALO AI SYSTEMS, LLC. All rights reserved.

PROPRIETARY AND CONFIDENTIAL

This file is part of LALO AI Platform and is protected by copyright law.
Unauthorized copying, modification, distribution, or use of this software,
via any medium, is strictly prohibited without the express written permission
of LALO AI SYSTEMS, LLC.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import logging

# Central logging configuration for the application
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
)
app_logger = logging.getLogger("lalo.app")

# Load environment variables
load_dotenv()

# Import our route modules
from core.routes.ai_routes import router as ai_router
from core.routes.workflow_routes import router as workflow_router
from core.services.auth import auth_router
from core.routes.admin_tools_routes import router as admin_tools_router
from core.routes.agent_routes import router as agent_router
from core.middleware.auth_middleware import RBACMiddleware
from core.routes.rbac_routes import router as rbac_router
from core.routes.audit_routes import router as audit_router
from core.routes.connector_routes import router as connector_router
from core.routes.model_management_routes import router as model_management_router

# Startup/shutdown event handler using lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    app_logger.info("%s", "="*60)
    app_logger.info("LALO AI System - Startup Validation")
    app_logger.info("%s", "="*60)

    warnings = []
    errors = []

    # Environment-based configuration
    APP_ENV = os.getenv("APP_ENV", "development")
    DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

    # Check JWT secret key
    jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    if jwt_secret == "your-secret-key-here":
        if APP_ENV == "production":
            errors.append("JWT_SECRET_KEY must be changed from default in production")
        else:
            warnings.append("JWT_SECRET_KEY is using default value (OK for development)")
    else:
        app_logger.info("[OK] JWT_SECRET_KEY is configured")

    # Check encryption key
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if not encryption_key:
        warnings.append("ENCRYPTION_KEY not set - API keys will not be encrypted properly")
        warnings.append("   Run 'python scripts/init_db.py' to generate one")
    else:
        try:
            # Validate it's a valid Fernet key
            Fernet(encryption_key.encode())
            app_logger.info("[OK] ENCRYPTION_KEY is valid")
        except Exception as e:
            errors.append(f"ENCRYPTION_KEY is invalid: {e}")

    # Check demo mode
    if DEMO_MODE:
        warnings.append("DEMO_MODE is enabled - authentication is bypassed!")
        warnings.append("   Set DEMO_MODE=false in .env for production")
        app_logger.warning("Running in DEMO MODE - authentication bypassed")

        # DEMO_MODE: Seed demo API key for smoother first-run UX
        try:
            from core.database import SessionLocal, APIKeys
            db = SessionLocal()
            try:
                demo_user_id = "demo-user@example.com"
                existing_keys = db.query(APIKeys).filter(APIKeys.user_id == demo_user_id).first()

                if not existing_keys:
                    app_logger.info("[DEMO] Seeding demo API keys for first-run UX")
                    # Create placeholder API keys (empty but initialized)
                    # Users can add real keys via Settings page
                    demo_api_keys = APIKeys(user_id=demo_user_id)
                    demo_api_keys.keys = {}  # Empty keys dict
                    db.add(demo_api_keys)
                    db.commit()
                    app_logger.info("[DEMO] Demo API keys initialized (empty)")
                    app_logger.info("[DEMO] Add real API keys via Settings page")
                else:
                    app_logger.info("[DEMO] Demo API keys already exist")
            finally:
                db.close()
        except Exception as e:
            app_logger.warning(f"[DEMO] Failed to seed demo API keys: {e}")
            app_logger.warning("[DEMO] You may need to run: python scripts/init_db.py")
    else:
        app_logger.info("DEMO_MODE is disabled")

    # Check database exists
    db_path = "lalo.db"
    if not os.path.exists(db_path):
        warnings.append(f"Database not found at {db_path}")
        warnings.append("   Run 'python scripts/init_db.py' to create it")
    else:
        app_logger.info("[OK] Database found at %s", db_path)

    # Environment info
    app_logger.info("[INFO] Environment: %s", APP_ENV)

    # Print warnings
    if warnings:
        app_logger.info('\n' + '='*60)
        app_logger.info('WARNINGS:')
        for warning in warnings:
            app_logger.warning('  [!] %s', warning)

    # Print errors and exit if critical
    if errors:
        app_logger.error('\n' + '='*60)
        app_logger.error('ERRORS:')
        for error in errors:
            app_logger.error('  [X] %s', error)
        app_logger.error('%s', '='*60)
        raise RuntimeError("Configuration errors detected - see above")

    app_logger.info('%s', '='*60)
    app_logger.info('[SUCCESS] Startup validation complete')
    app_logger.info('%s', '='*60)
    app_logger.info('')

    yield  # Server runs here

    # Shutdown
    app_logger.info('Shutting down LALO AI System...')

# Create FastAPI app with lifespan
app = FastAPI(
    title="LALO AI System",
    description="Advanced AI-powered business automation platform",
    version="1.0.0",
    lifespan=lifespan
)

# Environment-based configuration
APP_ENV = os.getenv("APP_ENV", "development")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# CORS configuration based on environment
if APP_ENV == "production":
    # In production, restrict to specific domains
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
    if not allowed_origins or allowed_origins == [""]:
        # Fallback to safe default
        allowed_origins = ["https://your-production-domain.com"]
else:
    # Development: allow local frontend
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach RBAC middleware to enrich requests with permissions from RBAC service
app.add_middleware(RBACMiddleware)

# Include routers
app.include_router(ai_router, tags=["AI Services"])
app.include_router(workflow_router, tags=["LALO Workflow"])
app.include_router(auth_router, tags=["Authentication"])
app.include_router(admin_tools_router, tags=["Admin Tools"])
app.include_router(agent_router, tags=["Agents"])
app.include_router(rbac_router, tags=["RBAC"])
app.include_router(audit_router, tags=["Audit"])
app.include_router(connector_router, tags=["Connectors"])
app.include_router(model_management_router, tags=["Model Management"])

# Serve static files (React build) only if the static directory exists
static_dir = os.path.join("lalo-frontend", "build", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    """Serve SPA index if built; otherwise return API status."""
    index_path = os.path.join("lalo-frontend", "build", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return {
        "message": "LALO AI System API",
        "version": "1.0.0",
        "status": "operational",
        "note": "Frontend build not found; run npm run build in lalo-frontend."
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LALO AI"}

# Serve React app for any unmatched routes (SPA routing)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve SPA index for any unmatched routes (client-side routing)."""
    index_path = os.path.join("lalo-frontend", "build", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return {"message": "Frontend not built. Run 'npm run build' in lalo-frontend directory."}

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
