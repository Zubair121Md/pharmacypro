"""
Analytics routes for Pharmacy Revenue Management System
Version: 2.0
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.database import get_db, User
from app.auth import get_current_user
from app.models import RevenueAnalytics
from app.analytics_engine import AnalyticsEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard analytics data"""
    try:
        logger.info(f"Dashboard analytics requested by user {current_user.username}")
        
        # Initialize analytics engine
        analytics_engine = AnalyticsEngine(db, current_user)
        
        # Get comprehensive dashboard data
        dashboard_data = analytics_engine.get_comprehensive_dashboard_data()
        
        # Convert to legacy format for backward compatibility
        return {
            "total_revenue": dashboard_data["summary_metrics"]["total_revenue"],
            "pharmacy_revenue": dashboard_data["revenue_analytics"]["pharmacy_revenue"],
            "doctor_revenue": dashboard_data["revenue_analytics"]["doctor_revenue"],
            "rep_revenue": dashboard_data["revenue_analytics"]["rep_revenue"],
            "hq_revenue": dashboard_data["revenue_analytics"]["hq_revenue"],
            "area_revenue": dashboard_data["revenue_analytics"]["area_revenue"],
            "monthly_revenue": dashboard_data["monthly_trends"],
            "summary_metrics": dashboard_data["summary_metrics"],
            "trend_analysis": dashboard_data["trend_analysis"],
            "performance_metrics": dashboard_data["performance_metrics"],
            "allocation_breakdown": dashboard_data["allocation_breakdown"],
            "top_performers": dashboard_data["top_performers"]
        }
        
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Analytics retrieval failed"
        )

@router.get("/pharmacy-revenue")
async def get_pharmacy_revenue(
    limit: int = Query(20, description="Number of top pharmacies to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed pharmacy revenue breakdown"""
    try:
        logger.info(f"Pharmacy revenue requested by user {current_user.username}")
        
        analytics_engine = AnalyticsEngine(db, current_user)
        pharmacy_revenue = analytics_engine.get_revenue_by_pharmacy(limit)
        
        return {
            "pharmacy_revenue": pharmacy_revenue,
            "total_count": len(pharmacy_revenue)
        }
        
    except Exception as e:
        logger.error(f"Pharmacy revenue retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Pharmacy revenue retrieval failed"
        )

@router.get("/doctor-revenue")
async def get_doctor_revenue(
    limit: int = Query(15, description="Number of top doctors to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed doctor revenue breakdown"""
    try:
        logger.info(f"Doctor revenue requested by user {current_user.username}")
        
        analytics_engine = AnalyticsEngine(db, current_user)
        doctor_revenue = analytics_engine.get_revenue_by_doctor(limit)
        
        return {
            "doctor_revenue": doctor_revenue,
            "total_count": len(doctor_revenue)
        }
        
    except Exception as e:
        logger.error(f"Doctor revenue retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Doctor revenue retrieval failed"
        )

@router.get("/rep-revenue")
async def get_rep_revenue(
    limit: int = Query(15, description="Number of top reps to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed sales rep revenue breakdown"""
    try:
        logger.info(f"Rep revenue requested by user {current_user.username}")
        
        analytics_engine = AnalyticsEngine(db, current_user)
        rep_revenue = analytics_engine.get_revenue_by_rep(limit)
        
        return {
            "rep_revenue": rep_revenue,
            "total_count": len(rep_revenue)
        }
        
    except Exception as e:
        logger.error(f"Rep revenue retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Rep revenue retrieval failed"
        )

@router.get("/trends")
async def get_trend_analysis(
    months: int = Query(12, description="Number of months for trend analysis"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive trend analysis"""
    try:
        logger.info(f"Trend analysis requested by user {current_user.username}")
        
        analytics_engine = AnalyticsEngine(db, current_user)
        monthly_trends = analytics_engine.get_monthly_trends(months)
        trend_analysis = analytics_engine.get_trend_analysis()
        
        return {
            "monthly_trends": monthly_trends,
            "trend_analysis": trend_analysis,
            "period_months": months
        }
        
    except Exception as e:
        logger.error(f"Trend analysis retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Trend analysis retrieval failed"
        )

@router.get("/summary")
async def get_summary_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get high-level summary metrics"""
    try:
        logger.info(f"Summary metrics requested by user {current_user.username}")
        
        analytics_engine = AnalyticsEngine(db, current_user)
        summary_metrics = analytics_engine.get_summary_metrics()
        performance_metrics = analytics_engine.get_performance_metrics()
        
        return {
            "summary_metrics": summary_metrics,
            "performance_metrics": performance_metrics
        }
        
    except Exception as e:
        logger.error(f"Summary metrics retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Summary metrics retrieval failed"
        )

@router.get("/unmatched-records")
async def get_unmatched_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get unmatched pharmacy records for manual review"""
    try:
        logger.info(f"Unmatched records requested by user {current_user.username}")
        
        from app.database import Unmatched
        
        # Get unmatched records
        unmatched_records = db.query(Unmatched).filter(
            Unmatched.status == "pending"
        ).all()
        
        return {
            "unmatched_records": [
                {
                    "id": record.id,
                    "pharmacy_name": record.pharmacy_name,
                    "generated_id": record.generated_id,
                    "confidence_score": float(record.confidence_score) if record.confidence_score else None,
                    "created_at": record.created_at
                }
                for record in unmatched_records
            ],
            "total_count": len(unmatched_records)
        }
        
    except Exception as e:
        logger.error(f"Unmatched records retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Unmatched records retrieval failed"
        )
