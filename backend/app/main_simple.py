from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import os

# Simple models
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class HealthResponse(BaseModel):
    status: str
    message: str

# Create FastAPI app
app = FastAPI(
    title="Pharmacy Revenue Management System",
    description="Offline Revenue Analytics & Management Platform",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Simple authentication
def authenticate_user(username: str, password: str):
    # Simple hardcoded authentication for demo
    if username == "admin" and password == "admin123":
        return {"username": "admin", "role": "super_admin", "id": 1}
    return None

def create_access_token(data: dict):
    # Simple token creation for demo
    return "demo_token_12345"

# Routes
@app.get("/")
async def root():
    return {"message": "Pharmacy Revenue Management System API", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return HealthResponse(status="healthy", message="API is running")

@app.get("/api/v1/health")
async def health_check_api():
    return HealthResponse(status="healthy", message="API is running")

@app.post("/api/v1/auth/login")
async def login(user_credentials: UserLogin):
    user = authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return Token(access_token=access_token, token_type="bearer")

@app.get("/api/v1/dashboard")
async def get_dashboard():
    return {
        "total_revenue": 125000.50,
        "total_pharmacies": 45,
        "total_doctors": 23,
        "total_reps": 8,
        "monthly_trend": [
            {"month": "Jan", "revenue": 10000},
            {"month": "Feb", "revenue": 12000},
            {"month": "Mar", "revenue": 15000},
            {"month": "Apr", "revenue": 18000},
            {"month": "May", "revenue": 20000},
            {"month": "Jun", "revenue": 22000}
        ]
    }

@app.get("/api/v1/analytics/summary")
async def get_analytics_summary():
    return {
        "total_revenue": 125000.50,
        "total_pharmacies": 45,
        "total_doctors": 23,
        "total_reps": 8,
        "revenue_by_pharmacy": [
            {"pharmacy": "Gayathri Medicals", "revenue": 15000},
            {"pharmacy": "City Care Pharmacy", "revenue": 12000},
            {"pharmacy": "MedPlus Calicut", "revenue": 18000}
        ],
        "revenue_by_doctor": [
            {"doctor": "DR SHAJIKUMAR", "revenue": 25000},
            {"doctor": "DR RADHAKRISHNAN", "revenue": 20000},
            {"doctor": "DR AJITH KUMAR", "revenue": 15000}
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

