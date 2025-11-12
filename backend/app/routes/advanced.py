"""
Advanced Features Routes for Pharmacy Revenue Management System
Version: 2.0
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import tempfile
import os

from app.database import get_db, User, MasterMapping
from app.auth import get_current_user, require_admin_or_super_admin, require_super_admin
from app.ml_models import MLModelManager, PharmacyMatcher, AnomalyDetector
from app.reporting_engine import ReportGenerator
from app.audit_logger import AuditLogger, AuditAction, AuditSeverity
from app.backup_system import BackupManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize ML models manager
ml_manager = MLModelManager()

@router.post("/ml/initialize")
async def initialize_ml_models(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Initialize ML models (Admin/Super Admin only)"""
    try:
        logger.info(f"ML model initialization requested by {current_user.username}")
        
        # Get master pharmacy names
        master_pharmacies = db.query(MasterMapping.pharmacy_names).distinct().all()
        pharmacy_names = [pharmacy[0] for pharmacy in master_pharmacies if pharmacy[0]]
        
        # Get revenue data for anomaly detection
        from app.database import Invoice
        invoices = db.query(Invoice).limit(1000).all()  # Sample for training
        
        revenue_data = []
        for invoice in invoices:
            revenue_data.append({
                'amount': float(invoice.amount),
                'quantity': invoice.quantity,
                'pharmacy_count': 1,  # Simplified
                'daily_avg': float(invoice.amount)  # Simplified
            })
        
        import pandas as pd
        revenue_df = pd.DataFrame(revenue_data)
        
        # Initialize models
        success = ml_manager.initialize_models(pharmacy_names, revenue_df)
        
        if success:
            # Save models
            ml_manager.save_all_models()
            
            # Log action
            audit_logger = AuditLogger(db)
            audit_logger.log_action(
                user_id=current_user.id,
                action=AuditAction.SETTINGS_UPDATE,
                details={'event': 'ml_models_initialized'},
                severity=AuditSeverity.MEDIUM
            )
            
            return {
                "success": True,
                "message": "ML models initialized successfully",
                "pharmacy_names_count": len(pharmacy_names),
                "revenue_records_count": len(revenue_data)
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize ML models"
            )
            
    except Exception as e:
        logger.error(f"ML model initialization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ML model initialization failed: {str(e)}"
        )

@router.get("/ml/status")
async def get_ml_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ML models status"""
    try:
        # Load models if not already loaded
        if not ml_manager.pharmacy_matcher.is_trained:
            ml_manager.load_all_models()
        
        status = ml_manager.get_model_status()
        
        return {
            "ml_models": status,
            "available_features": [
                "pharmacy_matching",
                "anomaly_detection",
                "confidence_scoring"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting ML status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get ML status"
        )

@router.post("/ml/pharmacy-match")
async def match_pharmacy_ml(
    pharmacy_name: str,
    threshold: float = Query(0.7, description="Similarity threshold"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Match pharmacy using ML (fallback)"""
    try:
        # Load models if not already loaded
        if not ml_manager.pharmacy_matcher.is_trained:
            ml_manager.load_all_models()
        
        if not ml_manager.pharmacy_matcher.is_trained:
            raise HTTPException(
                status_code=400,
                detail="ML models not trained. Please initialize models first."
            )
        
        # Find best match
        match = ml_manager.pharmacy_matcher.find_best_match(pharmacy_name, threshold)
        
        if match:
            # Log action
            audit_logger = AuditLogger(db)
            audit_logger.log_pharmacy_mapping(
                user_id=current_user.id,
                pharmacy_name=pharmacy_name,
                mapped_pharmacy_id=match['matched_name'],
                action='ml_match',
                confidence_score=match['similarity'],
                ip_address=None
            )
        
        return {
            "pharmacy_name": pharmacy_name,
            "match": match,
            "threshold_used": threshold
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML pharmacy matching failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ML pharmacy matching failed: {str(e)}"
        )

@router.post("/ml/detect-anomalies")
async def detect_anomalies_ml(
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Detect anomalies in revenue data using ML"""
    try:
        # Load models if not already loaded
        if not ml_manager.anomaly_detector.is_trained:
            ml_manager.load_all_models()
        
        if not ml_manager.anomaly_detector.is_trained:
            raise HTTPException(
                status_code=400,
                detail="Anomaly detection model not trained. Please initialize models first."
            )
        
        # Get recent revenue data
        from app.database import Invoice
        recent_invoices = db.query(Invoice).filter(
            Invoice.created_at >= datetime.now() - timedelta(days=30)
        ).all()
        
        # Prepare data
        revenue_data = []
        for invoice in recent_invoices:
            revenue_data.append({
                'amount': float(invoice.amount),
                'quantity': invoice.quantity,
                'pharmacy_count': 1,
                'daily_avg': float(invoice.amount)
            })
        
        import pandas as pd
        revenue_df = pd.DataFrame(revenue_data)
        
        if revenue_df.empty:
            return {
                "anomalies": [],
                "total_records": 0,
                "anomaly_count": 0
            }
        
        # Detect anomalies
        anomalies_df = ml_manager.anomaly_detector.detect_anomalies(revenue_df)
        
        # Get anomalies
        anomalies = anomalies_df[anomalies_df['is_anomaly']].to_dict('records')
        
        return {
            "anomalies": anomalies,
            "total_records": len(revenue_df),
            "anomaly_count": len(anomalies),
            "anomaly_rate": len(anomalies) / len(revenue_df) * 100 if len(revenue_df) > 0 else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Anomaly detection failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Anomaly detection failed: {str(e)}"
        )

@router.post("/reports/generate")
async def generate_advanced_report(
    report_type: str = Query("comprehensive", description="Report type"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate advanced reports"""
    try:
        logger.info(f"Advanced report generation requested by {current_user.username}")
        
        # Parse dates
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now() - timedelta(days=30)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = datetime.now()
        
        # Initialize report generator
        report_generator = ReportGenerator(db)
        
        # Generate report
        report_result = report_generator.generate_comprehensive_report(
            start_date=start_dt,
            end_date=end_dt,
            user_id=current_user.id,
            report_type=report_type
        )
        
        if report_result['success']:
            # Log action
            audit_logger = AuditLogger(db)
            audit_logger.log_report_generation(
                user_id=current_user.id,
                report_type=report_type,
                report_format="multiple",
                record_count=len(report_result.get('reports', {})),
                ip_address=None
            )
        
        return report_result
        
    except Exception as e:
        logger.error(f"Advanced report generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )

@router.get("/reports/templates")
async def get_report_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available report templates"""
    try:
        report_generator = ReportGenerator(db)
        templates = report_generator.get_report_templates()
        
        return {
            "templates": templates,
            "total_count": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Error getting report templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get report templates"
        )

@router.get("/audit/logs")
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, description="Number of logs to return"),
    offset: int = Query(0, description="Offset for pagination"),
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Get audit logs (Admin/Super Admin only)"""
    try:
        audit_logger = AuditLogger(db)
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        # Get logs
        logs = audit_logger.get_audit_logs(
            user_id=user_id,
            action=action,
            severity=severity,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit,
            offset=offset
        )
        
        return {
            "logs": logs,
            "total_count": len(logs),
            "filters": {
                "user_id": user_id,
                "action": action,
                "severity": severity,
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get audit logs"
        )

@router.get("/audit/statistics")
async def get_audit_statistics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Get audit statistics (Admin/Super Admin only)"""
    try:
        audit_logger = AuditLogger(db)
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        # Get statistics
        stats = audit_logger.get_audit_statistics(
            start_date=start_dt,
            end_date=end_dt
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting audit statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get audit statistics"
        )

@router.post("/backup/create")
async def create_backup(
    backup_name: Optional[str] = Query(None, description="Custom backup name"),
    compress: bool = Query(True, description="Compress backup files"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Create system backup (Super Admin only)"""
    try:
        logger.info(f"Backup creation requested by {current_user.username}")
        
        # Get database and Redis config
        db_config = {
            'host': 'postgres',
            'port': 5432,
            'database': 'pharmacy_revenue',
            'user': 'pharmacy_user',
            'password': 'pharmacy_password'
        }
        
        redis_config = {
            'host': 'redis',
            'port': 6379,
            'password': None
        }
        
        # Initialize backup manager
        backup_manager = BackupManager(db_config, redis_config)
        
        # Create backup
        backup_result = backup_manager.create_full_backup(
            backup_name=backup_name,
            compress=compress
        )
        
        if backup_result['success']:
            # Log action
            audit_logger = AuditLogger(db)
            audit_logger.log_system_backup(
                user_id=current_user.id,
                backup_type="full",
                backup_size=sum(
                    component.get('file_size', 0) 
                    for component in backup_result.get('components', {}).values()
                ) // (1024 * 1024),  # Convert to MB
                success=True,
                ip_address=None
            )
        
        return backup_result
        
    except Exception as e:
        logger.error(f"Backup creation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Backup creation failed: {str(e)}"
        )

@router.get("/backup/list")
async def list_backups(
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """List available backups (Admin/Super Admin only)"""
    try:
        # Get database and Redis config
        db_config = {
            'host': 'postgres',
            'port': 5432,
            'database': 'pharmacy_revenue',
            'user': 'pharmacy_user',
            'password': 'pharmacy_password'
        }
        
        redis_config = {
            'host': 'redis',
            'port': 6379,
            'password': None
        }
        
        # Initialize backup manager
        backup_manager = BackupManager(db_config, redis_config)
        
        # List backups
        backups = backup_manager.list_backups()
        
        return {
            "backups": backups,
            "total_count": len(backups)
        }
        
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list backups"
        )

@router.post("/backup/restore/{backup_name}")
async def restore_backup(
    backup_name: str,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Restore from backup (Super Admin only)"""
    try:
        logger.info(f"Backup restore requested by {current_user.username} for: {backup_name}")
        
        # Get database and Redis config
        db_config = {
            'host': 'postgres',
            'port': 5432,
            'database': 'pharmacy_revenue',
            'user': 'pharmacy_user',
            'password': 'pharmacy_password'
        }
        
        redis_config = {
            'host': 'redis',
            'port': 6379,
            'password': None
        }
        
        # Initialize backup manager
        backup_manager = BackupManager(db_config, redis_config)
        
        # Restore backup
        restore_result = backup_manager.restore_backup(backup_name)
        
        if restore_result['success']:
            # Log action
            audit_logger = AuditLogger(db)
            audit_logger.log_system_backup(
                user_id=current_user.id,
                backup_type="restore",
                success=True,
                ip_address=None
            )
        
        return restore_result
        
    except Exception as e:
        logger.error(f"Backup restore failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Backup restore failed: {str(e)}"
        )

@router.delete("/backup/{backup_name}")
async def delete_backup(
    backup_name: str,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Delete backup (Super Admin only)"""
    try:
        logger.info(f"Backup deletion requested by {current_user.username} for: {backup_name}")
        
        # Get database and Redis config
        db_config = {
            'host': 'postgres',
            'port': 5432,
            'database': 'pharmacy_revenue',
            'user': 'pharmacy_user',
            'password': 'pharmacy_password'
        }
        
        redis_config = {
            'host': 'redis',
            'port': 6379,
            'password': None
        }
        
        # Initialize backup manager
        backup_manager = BackupManager(db_config, redis_config)
        
        # Delete backup
        success = backup_manager.delete_backup(backup_name)
        
        if success:
            # Log action
            audit_logger = AuditLogger(db)
            audit_logger.log_action(
                user_id=current_user.id,
                action=AuditAction.DATA_DELETE,
                details={'event': 'backup_deleted', 'backup_name': backup_name},
                severity=AuditSeverity.HIGH
            )
        
        return {
            "success": success,
            "backup_name": backup_name,
            "message": "Backup deleted successfully" if success else "Failed to delete backup"
        }
        
    except Exception as e:
        logger.error(f"Backup deletion failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Backup deletion failed: {str(e)}"
        )

@router.post("/backup/cleanup")
async def cleanup_old_backups(
    days_to_keep: int = Query(30, description="Days to keep backups"),
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Clean up old backups (Super Admin only)"""
    try:
        logger.info(f"Backup cleanup requested by {current_user.username}")
        
        # Get database and Redis config
        db_config = {
            'host': 'postgres',
            'port': 5432,
            'database': 'pharmacy_revenue',
            'user': 'pharmacy_user',
            'password': 'pharmacy_password'
        }
        
        redis_config = {
            'host': 'redis',
            'port': 6379,
            'password': None
        }
        
        # Initialize backup manager
        backup_manager = BackupManager(db_config, redis_config)
        
        # Cleanup old backups
        deleted_count = backup_manager.cleanup_old_backups(days_to_keep)
        
        # Log action
        audit_logger = AuditLogger(db)
        audit_logger.log_action(
            user_id=current_user.id,
            action=AuditAction.SYSTEM_BACKUP,
            details={'event': 'backup_cleanup', 'deleted_count': deleted_count},
            severity=AuditSeverity.MEDIUM
        )
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "days_kept": days_to_keep,
            "message": f"Cleaned up {deleted_count} old backups"
        }
        
    except Exception as e:
        logger.error(f"Backup cleanup failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Backup cleanup failed: {str(e)}"
        )
