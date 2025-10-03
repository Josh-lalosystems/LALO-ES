from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import os

# Import our route modules
from core.routes.ai_routes import router as ai_router
from core.services.auth import auth_router

# Create FastAPI app
app = FastAPI(
    title="LALO AI System",
    description="Advanced AI-powered business automation platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ai_router, tags=["AI Services"])
app.include_router(auth_router, tags=["Authentication"])

# Serve static files (React build)
if os.path.exists("lalo-frontend/build"):
    app.mount("/static", StaticFiles(directory="lalo-frontend/build/static"), name="static")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LALO AI System API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LALO AI"}

# Serve React app for any unmatched routes (SPA routing)
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React app for frontend routes"""
    if os.path.exists("lalo-frontend/build/index.html"):
        with open("lalo-frontend/build/index.html") as f:
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
