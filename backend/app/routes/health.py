"""
Health check routes for Pharmacy Revenue Management System
Version: 2.0
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import redis
import logging

from app.database import get_db, check_db_health
from app.models import HealthCheck

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def check_redis_health():
    """Check Redis health"""
    try:
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        r.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return False

@router.get("/health", response_model=HealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    try:
        # Check database health
        db_healthy = check_db_health()
        
        # Check Redis health
        redis_healthy = check_redis_health()
        
        # Determine overall status
        overall_status = "healthy" if db_healthy and redis_healthy else "unhealthy"
        
        return HealthCheck(
            status=overall_status,
            service="pharmacy-revenue-api",
            version="2.0.0",
            database=db_healthy,
            redis=redis_healthy,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheck(
            status="unhealthy",
            service="pharmacy-revenue-api",
            version="2.0.0",
            database=False,
            redis=False,
            timestamp=datetime.utcnow()
        )

@router.get("/health/database")
async def database_health_check(db: Session = Depends(get_db)):
    """Database-specific health check"""
    try:
        db_healthy = check_db_health()
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "service": "database",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "database",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }

@router.get("/health/redis")
async def redis_health_check():
    """Redis-specific health check"""
    try:
        redis_healthy = check_redis_health()
        return {
            "status": "healthy" if redis_healthy else "unhealthy",
            "service": "redis",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "redis",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }
