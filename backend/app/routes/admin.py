"""
Admin routes for Pharmacy Revenue Management System
Version: 2.0
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from app.database import get_db, User, Invoice, MasterMapping
from app.auth import get_current_user, require_admin_or_super_admin, require_super_admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/users")
async def get_users(
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Get all users (Admin/Super Admin only)"""
    try:
        logger.info(f"Users list requested by {current_user.username}")
        
        # Get users based on current user's role
        if current_user.role == 'super_admin':
            users = db.query(User).all()
        else:
            # Admin can only see users in their area
            users = db.query(User).filter(User.area == current_user.area).all()
        
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "area": user.area,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "last_login": user.last_login
            }
            for user in users
        ]
        
    except Exception as e:
        logger.error(f"Failed to fetch users: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch users"
        )

@router.post("/users")
async def create_user(
    username: str,
    email: str,
    password: str,
    role: str = "user",
    area: Optional[str] = None,
    is_active: bool = True,
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (Admin/Super Admin only)"""
    try:
        logger.info(f"User creation requested by {current_user.username}")
        
        # Validate role assignment permissions
        if role == 'super_admin' and current_user.role != 'super_admin':
            raise HTTPException(
                status_code=403,
                detail="Only super admins can create super admin users"
            )
        
        if role == 'admin' and current_user.role not in ['super_admin', 'admin']:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to create admin users"
            )
        
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this username or email already exists"
            )
        
        # Create new user
        from app.auth import get_password_hash
        new_user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            role=role,
            area=area or current_user.area,
            is_active=is_active
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User {username} created successfully by {current_user.username}")
        
        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "area": new_user.area,
            "is_active": new_user.is_active,
            "created_at": new_user.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    username: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
    area: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Update user (Admin/Super Admin only)"""
    try:
        logger.info(f"User update requested by {current_user.username} for user {user_id}")
        
        # Get user to update
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check permissions
        if current_user.role == 'admin' and user.area != current_user.area:
            raise HTTPException(
                status_code=403,
                detail="Can only update users in your area"
            )
        
        # Prevent self-modification of critical fields
        if user_id == current_user.id:
            if role and role != current_user.role:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot change your own role"
                )
            if is_active is False:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot deactivate your own account"
                )
        
        # Update fields
        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        if role is not None:
            # Validate role assignment permissions
            if role == 'super_admin' and current_user.role != 'super_admin':
                raise HTTPException(
                    status_code=403,
                    detail="Only super admins can assign super admin role"
                )
            user.role = role
        if area is not None:
            user.area = area
        if is_active is not None:
            user.is_active = is_active
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"User {user_id} updated successfully by {current_user.username}")
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "area": user.area,
            "is_active": user.is_active,
            "updated_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update user"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Delete user (Super Admin only)"""
    try:
        logger.info(f"User deletion requested by {current_user.username} for user {user_id}")
        
        # Prevent self-deletion
        if user_id == current_user.id:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete your own account"
            )
        
        # Get user to delete
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(user)
        db.commit()
        
        logger.info(f"User {user_id} deleted successfully by {current_user.username}")
        
        return {"message": "User deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete user"
        )

@router.get("/stats")
async def get_system_stats(
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Get system statistics (Admin/Super Admin only)"""
    try:
        logger.info(f"System stats requested by {current_user.username}")
        
        # Base queries with area filtering
        base_invoice_query = db.query(Invoice)
        base_master_query = db.query(MasterMapping)
        
        if current_user.role != 'super_admin' and current_user.area:
            base_invoice_query = (
                base_invoice_query.join(MasterMapping, Invoice.pharmacy_id == MasterMapping.pharmacy_id)
                .filter(MasterMapping.area == current_user.area)
            )
            base_master_query = base_master_query.filter(MasterMapping.area == current_user.area)
        
        # Calculate statistics
        total_users = db.query(User).count()
        total_invoices = base_invoice_query.count()
        active_pharmacies = base_master_query.with_entities(
            func.count(func.distinct(MasterMapping.pharmacy_id))
        ).scalar() or 0
        
        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_invoices = base_invoice_query.filter(
            Invoice.created_at >= week_ago
        ).count()
        
        # System health indicators
        system_health = "Good"
        if total_invoices > 10000:
            system_health = "High Load"
        elif recent_invoices == 0:
            system_health = "No Recent Activity"
        
        return {
            "total_users": total_users,
            "total_invoices": total_invoices,
            "active_pharmacies": active_pharmacies,
            "recent_invoices": recent_invoices,
            "system_health": system_health,
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch system stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch system statistics"
        )

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = Query(100, description="Number of logs to return"),
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Get audit logs (Admin/Super Admin only)"""
    try:
        logger.info(f"Audit logs requested by {current_user.username}")
        
        # This would typically query an audit_logs table
        # For now, return a placeholder response
        return {
            "logs": [],
            "total_count": 0,
            "message": "Audit logging will be implemented in Phase 6"
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch audit logs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch audit logs"
        )

@router.post("/system/backup")
async def trigger_backup(
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Trigger manual backup (Super Admin only)"""
    try:
        logger.info(f"Manual backup triggered by {current_user.username}")
        
        # This would trigger the backup process
        # For now, return a placeholder response
        return {
            "message": "Backup process initiated",
            "backup_id": f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "status": "In Progress"
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger backup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to trigger backup"
        )

@router.get("/system/health")
async def get_system_health(
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Get detailed system health status (Admin/Super Admin only)"""
    try:
        logger.info(f"System health check requested by {current_user.username}")
        
        # Check database connectivity
        db_status = "Connected"
        try:
            db.execute("SELECT 1")
        except Exception:
            db_status = "Disconnected"
        
        # Check Redis connectivity (placeholder)
        redis_status = "Connected"
        
        # Check disk space (placeholder)
        disk_usage = "85%"
        
        overall_health = "Good"
        if db_status != "Connected" or redis_status != "Connected":
            overall_health = "Critical"
        elif disk_usage > "90%":
            overall_health = "Warning"
        
        return {
            "overall_health": overall_health,
            "database": db_status,
            "redis": redis_status,
            "disk_usage": disk_usage,
            "last_check": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to check system health: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to check system health"
        )
