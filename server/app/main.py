"""
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config import get_settings
from app.api.v1.api import api_router
from app.ml.scheduler import start_ml_scheduler, stop_ml_scheduler

# Get application settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    # Startup
    print("=" * 50)
    print(f"{settings.app_name} v{settings.app_version}")
    print("=" * 50)
    print("Supabase connection initialized")
    print(f"API documentation: http://localhost:8000/docs")
    print(f"API v1 prefix: {settings.api_v1_prefix}")
    
    # Start ML background scheduler
    print("Starting ML recommendation engine...")
    try:
        start_ml_scheduler()
        print("✓ ML scheduler started successfully")
    except Exception as e:
        print(f"✗ Failed to start ML scheduler: {e}")
    
    print("Server ready to accept requests")
    print("=" * 50)
    
    yield
    
    # Shutdown
    print(f"Shutting down {settings.app_name}...")
    try:
        stop_ml_scheduler()
        print("✓ ML scheduler stopped")
    except Exception as e:
        print(f"✗ Error stopping ML scheduler: {e}")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Backend API for Fora",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)


# ==================== ROOT ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
    }
