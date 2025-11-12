"""
Pharmacy Revenue Management System - Main FastAPI Application
Version: 2.0
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
from contextlib import asynccontextmanager

from app.database import init_db, get_db
from app.auth import get_current_user
from app.database import User
from app.routes import auth, upload, analytics, admin, health, unmatched, export, advanced

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🏥 Starting Pharmacy Revenue Management System...")
    await init_db()
    print("✅ Database initialized")
    print("✅ Application ready")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down application...")

# Create FastAPI application
app = FastAPI(
    title="Pharmacy Revenue Management System",
    description="A comprehensive system for managing pharmacy revenue, doctor allocations, and sales analytics",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["File Upload"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administration"])
app.include_router(unmatched.router, prefix="/api/v1/unmatched", tags=["Unmatched Records"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Data Export"])
app.include_router(advanced.router, prefix="/api/v1/advanced", tags=["Advanced Features"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Pharmacy Revenue Management System API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pharmacy-revenue-api",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        ssl_keyfile="ssl/pharmacy.key",
        ssl_certfile="ssl/pharmacy.crt"
    )
