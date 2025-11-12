"""
File upload routes for Pharmacy Revenue Management System
Version: 2.0
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import pandas as pd
import io
import uuid
import logging
from datetime import datetime

from app.database import get_db, User
from app.auth import get_current_user
from app.models import FileUploadResponse
from app.tasks_enhanced import process_pharmacies, process_master_data
from app.processing_enhanced import DataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/enhanced", response_model=FileUploadResponse)
async def upload_enhanced_files(
    master: UploadFile = File(...),
    invoice: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload master and invoice files for processing"""
    try:
        logger.info(f"File upload initiated by user {current_user.username}")
        
        # Validate file types
        if not master.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Master file must be an Excel file (.xlsx or .xls)"
            )
        
        if not invoice.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Invoice file must be an Excel file (.xlsx or .xls)"
            )
        
        # Read master data
        master_content = await master.read()
        master_df = pd.read_excel(io.BytesIO(master_content), engine='openpyxl')
        
        # Read invoice data
        invoice_content = await invoice.read()
        invoice_df = pd.read_excel(io.BytesIO(invoice_content), engine='openpyxl')
        
        logger.info(f"Master data: {len(master_df)} rows")
        logger.info(f"Invoice data: {len(invoice_df)} rows")
        
        # Use enhanced processing for large files
        processor = DataProcessor(db, current_user.id)
        
        # Validate data quality
        master_validation = processor.validate_data_quality(master_df, 'master')
        invoice_validation = processor.validate_data_quality(invoice_df, 'invoice')
        
        logger.info(f"Master data quality score: {master_validation['quality_score']:.2%}")
        logger.info(f"Invoice data quality score: {invoice_validation['quality_score']:.2%}")
        
        # Process master data (always use enhanced processor for better performance)
        master_results = processor.process_large_file(master_df, 'master')
        master_processed = master_results['total_processed']
        
        # Process invoice data (always use enhanced processor for better performance)
        invoice_results = processor.process_large_file(invoice_df, 'invoice')
        matched_count = invoice_results['total_matched']
        unmatched_count = invoice_results['total_unmatched']
        
        # Generate file ID
        file_id = str(uuid.uuid4())
        
        logger.info(f"File processing complete: {matched_count} matched, {unmatched_count} unmatched")
        
        return FileUploadResponse(
            message="Files processed successfully",
            file_id=file_id,
            rows_processed=len(invoice_df),
            matched_count=matched_count,
            unmatched_count=unmatched_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"File processing failed: {str(e)}"
        )

@router.post("/master-only", response_model=FileUploadResponse)
async def upload_master_only(
    master: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload only master data file"""
    try:
        logger.info(f"Master data upload initiated by user {current_user.username}")
        
        # Validate file type
        if not master.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Master file must be an Excel file (.xlsx or .xls)"
            )
        
        # Read master data
        master_content = await master.read()
        master_df = pd.read_excel(io.BytesIO(master_content), engine='openpyxl')
        
        logger.info(f"Master data: {len(master_df)} rows")
        
        # Process master data
        master_processed = process_master_data(master_df, current_user.id, db)
        
        # Generate file ID
        file_id = str(uuid.uuid4())
        
        logger.info(f"Master data processing complete: {master_processed} records processed")
        
        return FileUploadResponse(
            message="Master data processed successfully",
            file_id=file_id,
            rows_processed=master_processed,
            matched_count=master_processed,
            unmatched_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Master data upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Master data processing failed: {str(e)}"
        )

@router.post("/invoice-only", response_model=FileUploadResponse)
async def upload_invoice_only(
    invoice: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload only invoice data file"""
    try:
        logger.info(f"Invoice data upload initiated by user {current_user.username}")
        
        # Validate file type
        if not invoice.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Invoice file must be an Excel file (.xlsx or .xls)"
            )
        
        # Read invoice data
        invoice_content = await invoice.read()
        invoice_df = pd.read_excel(io.BytesIO(invoice_content), engine='openpyxl')
        
        logger.info(f"Invoice data: {len(invoice_df)} rows")
        
        # Process invoice data
        processed_invoice_df, matched_count, unmatched_count = process_pharmacies(
            invoice_df, current_user.id, db
        )
        
        # Generate file ID
        file_id = str(uuid.uuid4())
        
        logger.info(f"Invoice processing complete: {matched_count} matched, {unmatched_count} unmatched")
        
        return FileUploadResponse(
            message="Invoice data processed successfully",
            file_id=file_id,
            rows_processed=len(invoice_df),
            matched_count=matched_count,
            unmatched_count=unmatched_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Invoice data upload failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Invoice data processing failed: {str(e)}"
        )
