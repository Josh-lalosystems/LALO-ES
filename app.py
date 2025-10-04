from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()

# Import our route modules
from core.routes.ai_routes import router as ai_router
from core.routes.workflow_routes import router as workflow_router
from core.services.auth import auth_router
from core.routes.admin_tools_routes import router as admin_tools_router

# Startup/shutdown event handler using lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    print("="* 60)
    print("LALO AI System - Startup Validation")
    print("="* 60)

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
        print("[OK] JWT_SECRET_KEY is configured")

    # Check encryption key
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if not encryption_key:
        warnings.append("ENCRYPTION_KEY not set - API keys will not be encrypted properly")
        warnings.append("   Run 'python scripts/init_db.py' to generate one")
    else:
        try:
            # Validate it's a valid Fernet key
            Fernet(encryption_key.encode())
            print("[OK] ENCRYPTION_KEY is valid")
        except Exception as e:
            errors.append(f"ENCRYPTION_KEY is invalid: {e}")

    # Check demo mode
    if DEMO_MODE:
        warnings.append("DEMO_MODE is enabled - authentication is bypassed!")
        warnings.append("   Set DEMO_MODE=false in .env for production")
        print("[WARNING] Running in DEMO MODE - authentication bypassed")
    else:
        print("[OK] DEMO_MODE is disabled")

    # Check database exists
    db_path = "lalo.db"
    if not os.path.exists(db_path):
        warnings.append(f"Database not found at {db_path}")
        warnings.append("   Run 'python scripts/init_db.py' to create it")
    else:
        print(f"[OK] Database found at {db_path}")

    # Environment info
    print(f"[INFO] Environment: {APP_ENV}")

    # Print warnings
    if warnings:
        print("\n" + "="* 60)
        print("WARNINGS:")
        for warning in warnings:
            print(f"  [!] {warning}")

    # Print errors and exit if critical
    if errors:
        print("\n" + "="* 60)
        print("ERRORS:")
        for error in errors:
            print(f"  [X] {error}")
        print("="* 60)
        raise RuntimeError("Configuration errors detected - see above")

    print("="* 60)
    print("[SUCCESS] Startup validation complete")
    print("="* 60)
    print()

    yield  # Server runs here

    # Shutdown
    print("Shutting down LALO AI System...")

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

# Include routers
app.include_router(ai_router, tags=["AI Services"])
app.include_router(workflow_router, tags=["LALO Workflow"])
app.include_router(auth_router, tags=["Authentication"])
app.include_router(admin_tools_router, tags=["Admin Tools"])

# Serve static files (React build)
if os.path.exists("lalo-frontend/build"):
    app.mount("/static", StaticFiles(directory="lalo-frontend/build/static"), name="static")

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
