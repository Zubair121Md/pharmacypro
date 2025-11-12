"""
Unmatched records management routes for Pharmacy Revenue Management System
Version: 2.0
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db, User, Unmatched, MasterMapping
from app.auth import get_current_user, require_admin_or_super_admin
from app.models import UnmatchedResponse, UnmatchedUpdate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[UnmatchedResponse])
async def get_unmatched_records(
    status: Optional[str] = Query(None, description="Filter by status: pending, mapped, ignored"),
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get unmatched pharmacy records for manual review"""
    try:
        logger.info(f"Unmatched records requested by user {current_user.username}")
        
        # Build query
        query = db.query(Unmatched)
        
        # Apply status filter
        if status:
            query = query.filter(Unmatched.status == status)
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        # Get records
        unmatched_records = query.all()
        
        return [
            UnmatchedResponse(
                id=record.id,
                pharmacy_name=record.pharmacy_name,
                generated_id=record.generated_id,
                invoice_id=record.invoice_id,
                confidence_score=float(record.confidence_score) if record.confidence_score else None,
                status=record.status,
                mapped_to=record.mapped_to,
                user_id=record.user_id,
                created_at=record.created_at
            )
            for record in unmatched_records
        ]
        
    except Exception as e:
        logger.error(f"Error getting unmatched records: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve unmatched records"
        )

@router.get("/count")
async def get_unmatched_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get count of unmatched records by status"""
    try:
        pending_count = db.query(Unmatched).filter(Unmatched.status == "pending").count()
        mapped_count = db.query(Unmatched).filter(Unmatched.status == "mapped").count()
        ignored_count = db.query(Unmatched).filter(Unmatched.status == "ignored").count()
        
        return {
            "pending": pending_count,
            "mapped": mapped_count,
            "ignored": ignored_count,
            "total": pending_count + mapped_count + ignored_count
        }
        
    except Exception as e:
        logger.error(f"Error getting unmatched count: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve unmatched count"
        )

@router.put("/{record_id}", response_model=UnmatchedResponse)
async def update_unmatched_record(
    record_id: int,
    update_data: UnmatchedUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update unmatched record status and mapping"""
    try:
        logger.info(f"Updating unmatched record {record_id} by user {current_user.username}")
        
        # Get the record
        record = db.query(Unmatched).filter(Unmatched.id == record_id).first()
        if not record:
            raise HTTPException(
                status_code=404,
                detail="Unmatched record not found"
            )
        
        # Update record
        old_status = record.status
        old_mapped_to = record.mapped_to
        
        record.status = update_data.status
        record.mapped_to = update_data.mapped_to
        
        db.commit()
        
        # Log the update
        from app.database import AuditLog
        audit_log = AuditLog(
            user_id=current_user.id,
            action="UPDATE_UNMATCHED_RECORD",
            table_name="prms_unmatched",
            record_id=record_id,
            old_values={"status": old_status, "mapped_to": old_mapped_to},
            new_values={"status": record.status, "mapped_to": record.mapped_to}
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Unmatched record {record_id} updated successfully")
        
        return UnmatchedResponse(
            id=record.id,
            pharmacy_name=record.pharmacy_name,
            generated_id=record.generated_id,
            invoice_id=record.invoice_id,
            confidence_score=float(record.confidence_score) if record.confidence_score else None,
            status=record.status,
            mapped_to=record.mapped_to,
            user_id=record.user_id,
            created_at=record.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating unmatched record: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update unmatched record"
        )

@router.post("/{record_id}/map")
async def map_unmatched_record(
    record_id: int,
    master_pharmacy_id: str = Query(..., description="Master pharmacy ID to map to"),
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Map unmatched record to master pharmacy ID"""
    try:
        logger.info(f"Mapping unmatched record {record_id} to {master_pharmacy_id} by user {current_user.username}")
        
        # Get the record
        record = db.query(Unmatched).filter(Unmatched.id == record_id).first()
        if not record:
            raise HTTPException(
                status_code=404,
                detail="Unmatched record not found"
            )
        
        # Verify master pharmacy exists
        master_pharmacy = db.query(MasterMapping).filter(
            MasterMapping.pharmacy_id == master_pharmacy_id
        ).first()
        
        if not master_pharmacy:
            raise HTTPException(
                status_code=400,
                detail="Master pharmacy ID not found"
            )
        
        # Update record
        record.status = "mapped"
        record.mapped_to = master_pharmacy_id
        
        db.commit()
        
        # Log the mapping
        from app.database import AuditLog
        audit_log = AuditLog(
            user_id=current_user.id,
            action="MAP_UNMATCHED_RECORD",
            table_name="prms_unmatched",
            record_id=record_id,
            new_values={
                "status": "mapped",
                "mapped_to": master_pharmacy_id,
                "master_pharmacy_name": master_pharmacy.pharmacy_names
            }
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Unmatched record {record_id} mapped successfully to {master_pharmacy_id}")
        
        return {
            "message": "Record mapped successfully",
            "record_id": record_id,
            "mapped_to": master_pharmacy_id,
            "master_pharmacy_name": master_pharmacy.pharmacy_names
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error mapping unmatched record: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to map unmatched record"
        )

@router.post("/{record_id}/ignore")
async def ignore_unmatched_record(
    record_id: int,
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Mark unmatched record as ignored"""
    try:
        logger.info(f"Ignoring unmatched record {record_id} by user {current_user.username}")
        
        # Get the record
        record = db.query(Unmatched).filter(Unmatched.id == record_id).first()
        if not record:
            raise HTTPException(
                status_code=404,
                detail="Unmatched record not found"
            )
        
        # Update record
        record.status = "ignored"
        record.mapped_to = None
        
        db.commit()
        
        # Log the action
        from app.database import AuditLog
        audit_log = AuditLog(
            user_id=current_user.id,
            action="IGNORE_UNMATCHED_RECORD",
            table_name="prms_unmatched",
            record_id=record_id,
            new_values={"status": "ignored", "mapped_to": None}
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Unmatched record {record_id} ignored successfully")
        
        return {
            "message": "Record ignored successfully",
            "record_id": record_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ignoring unmatched record: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to ignore unmatched record"
        )

@router.get("/search")
async def search_unmatched_records(
    query: str = Query(..., description="Search term"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search unmatched records by pharmacy name"""
    try:
        logger.info(f"Searching unmatched records for '{query}' by user {current_user.username}")
        
        # Search for records containing the query
        records = db.query(Unmatched).filter(
            Unmatched.pharmacy_name.ilike(f"%{query}%")
        ).limit(50).all()
        
        return [
            UnmatchedResponse(
                id=record.id,
                pharmacy_name=record.pharmacy_name,
                generated_id=record.generated_id,
                invoice_id=record.invoice_id,
                confidence_score=float(record.confidence_score) if record.confidence_score else None,
                status=record.status,
                mapped_to=record.mapped_to,
                user_id=record.user_id,
                created_at=record.created_at
            )
            for record in records
        ]
        
    except Exception as e:
        logger.error(f"Error searching unmatched records: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to search unmatched records"
        )

@router.get("/master-pharmacies")
async def get_master_pharmacies(
    query: Optional[str] = Query(None, description="Search term for pharmacy names"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get master pharmacy list for mapping"""
    try:
        logger.info(f"Master pharmacies requested by user {current_user.username}")
        
        # Build query
        master_query = db.query(MasterMapping.pharmacy_id, MasterMapping.pharmacy_names).distinct()
        
        # Apply search filter
        if query:
            master_query = master_query.filter(
                MasterMapping.pharmacy_names.ilike(f"%{query}%")
            )
        
        # Get results
        master_pharmacies = master_query.limit(100).all()
        
        return [
            {
                "pharmacy_id": record.pharmacy_id,
                "pharmacy_name": record.pharmacy_names
            }
            for record in master_pharmacies
        ]
        
    except Exception as e:
        logger.error(f"Error getting master pharmacies: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve master pharmacies"
        )
