"""
Data export routes for Pharmacy Revenue Management System
Version: 2.0
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
import os
import uuid
from datetime import datetime, timedelta
import logging
from io import BytesIO
import tempfile

from app.database import get_db, User, Invoice, MasterMapping
from app.auth import get_current_user, require_admin_or_super_admin
from app.analytics_engine import AnalyticsEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/analytics-excel")
async def export_analytics_excel(
    background_tasks: BackgroundTasks,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export analytics data to Excel"""
    try:
        logger.info(f"Excel export requested by user {current_user.username}")
        
        # Initialize analytics engine
        analytics_engine = AnalyticsEngine(db, current_user)
        dashboard_data = analytics_engine.get_comprehensive_dashboard_data()
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_filename = temp_file.name
        temp_file.close()
        
        # Create Excel writer
        with pd.ExcelWriter(temp_filename, engine='openpyxl') as writer:
            # Summary metrics
            summary_df = pd.DataFrame([dashboard_data['summary_metrics']])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Pharmacy revenue
            if dashboard_data['revenue_analytics']['pharmacy_revenue']:
                pharmacy_df = pd.DataFrame(dashboard_data['revenue_analytics']['pharmacy_revenue'])
                pharmacy_df.to_excel(writer, sheet_name='Pharmacy Revenue', index=False)
            
            # Doctor revenue
            if dashboard_data['revenue_analytics']['doctor_revenue']:
                doctor_df = pd.DataFrame(dashboard_data['revenue_analytics']['doctor_revenue'])
                doctor_df.to_excel(writer, sheet_name='Doctor Revenue', index=False)
            
            # Rep revenue
            if dashboard_data['revenue_analytics']['rep_revenue']:
                rep_df = pd.DataFrame(dashboard_data['revenue_analytics']['rep_revenue'])
                rep_df.to_excel(writer, sheet_name='Rep Revenue', index=False)
            
            # Monthly trends
            if dashboard_data['monthly_trends']:
                monthly_df = pd.DataFrame(dashboard_data['monthly_trends'])
                monthly_df.to_excel(writer, sheet_name='Monthly Trends', index=False)
        
        # Schedule file cleanup
        background_tasks.add_task(cleanup_temp_file, temp_filename)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pharmacy_analytics_{timestamp}.xlsx"
        
        return FileResponse(
            path=temp_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Excel export failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Excel export failed"
        )

@router.get("/analytics-csv")
async def export_analytics_csv(
    background_tasks: BackgroundTasks,
    data_type: str = Query("pharmacy", description="Data type: pharmacy, doctor, rep, summary"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export specific analytics data to CSV"""
    try:
        logger.info(f"CSV export requested by user {current_user.username} for {data_type}")
        
        # Initialize analytics engine
        analytics_engine = AnalyticsEngine(db, current_user)
        
        # Get data based on type
        if data_type == "pharmacy":
            data = analytics_engine.get_revenue_by_pharmacy(100)  # Get top 100
            df = pd.DataFrame(data)
        elif data_type == "doctor":
            data = analytics_engine.get_revenue_by_doctor(50)  # Get top 50
            df = pd.DataFrame(data)
        elif data_type == "rep":
            data = analytics_engine.get_revenue_by_rep(50)  # Get top 50
            df = pd.DataFrame(data)
        elif data_type == "summary":
            dashboard_data = analytics_engine.get_comprehensive_dashboard_data()
            df = pd.DataFrame([dashboard_data['summary_metrics']])
        else:
            raise HTTPException(status_code=400, detail="Invalid data type")
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available for export")
        
        # Apply data masking for regular users
        if current_user.role == 'user':
            revenue_columns = ['total_revenue', 'allocated_revenue']
            for col in revenue_columns:
                if col in df.columns:
                    df[col] = "***"
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        temp_filename = temp_file.name
        temp_file.close()
        
        # Save to CSV
        df.to_csv(temp_filename, index=False)
        
        # Schedule file cleanup
        background_tasks.add_task(cleanup_temp_file, temp_filename)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pharmacy_{data_type}_{timestamp}.csv"
        
        return FileResponse(
            path=temp_filename,
            media_type='text/csv',
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV export failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="CSV export failed"
        )

@router.get("/raw-data-excel")
async def export_raw_data_excel(
    background_tasks: BackgroundTasks,
    include_master: bool = Query(True, description="Include master data"),
    include_invoices: bool = Query(True, description="Include invoice data"),
    limit: int = Query(10000, description="Maximum number of records"),
    current_user: User = Depends(require_admin_or_super_admin),
    db: Session = Depends(get_db)
):
    """Export raw data to Excel (Admin/Super Admin only)"""
    try:
        logger.info(f"Raw data export requested by user {current_user.username}")
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_filename = temp_file.name
        temp_file.close()
        
        # Create Excel writer
        with pd.ExcelWriter(temp_filename, engine='openpyxl') as writer:
            
            if include_master:
                # Export master data
                master_query = db.query(MasterMapping)
                if current_user.role != 'super_admin' and current_user.area:
                    master_query = master_query.filter(MasterMapping.area == current_user.area)
                
                master_data = master_query.limit(limit).all()
                
                if master_data:
                    master_df = pd.DataFrame([
                        {
                            'rep_names': record.rep_names,
                            'doctor_names': record.doctor_names,
                            'doctor_id': record.doctor_id,
                            'pharmacy_names': record.pharmacy_names,
                            'pharmacy_id': record.pharmacy_id,
                            'product_names': record.product_names,
                            'product_id': record.product_id,
                            'product_price': float(record.product_price),
                            'hq': record.hq,
                            'area': record.area,
                            'created_at': record.created_at
                        }
                        for record in master_data
                    ])
                    master_df.to_excel(writer, sheet_name='Master Data', index=False)
            
            if include_invoices:
                # Export invoice data
                invoice_query = db.query(Invoice)
                if current_user.role != 'super_admin' and current_user.area:
                    invoice_query = (
                        invoice_query.join(MasterMapping, Invoice.pharmacy_id == MasterMapping.pharmacy_id)
                        .filter(MasterMapping.area == current_user.area)
                    )
                
                invoice_data = invoice_query.limit(limit).all()
                
                if invoice_data:
                    invoice_df = pd.DataFrame([
                        {
                            'pharmacy_id': record.pharmacy_id,
                            'pharmacy_name': record.pharmacy_name,
                            'product': record.product,
                            'quantity': record.quantity,
                            'amount': float(record.amount),
                            'invoice_date': record.invoice_date,
                            'user_id': record.user_id,
                            'created_at': record.created_at
                        }
                        for record in invoice_data
                    ])
                    invoice_df.to_excel(writer, sheet_name='Invoice Data', index=False)
        
        # Schedule file cleanup
        background_tasks.add_task(cleanup_temp_file, temp_filename)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"pharmacy_raw_data_{timestamp}.xlsx"
        
        return FileResponse(
            path=temp_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Raw data export failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Raw data export failed"
        )

@router.get("/template-excel")
async def download_template(
    template_type: str = Query("master", description="Template type: master, invoice"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Download Excel template for data upload"""
    try:
        logger.info(f"Template download requested: {template_type}")
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_filename = temp_file.name
        temp_file.close()
        
        if template_type == "master":
            # Create master data template
            template_data = {
                'REP_Names': ['VIKRAM', 'ANITA', 'RAHUL'],
                'Doctor_Names': ['DR SHAJIKUMAR', 'DR RADHAKRISHNAN', 'DR AJITH KUMAR'],
                'Doctor_ID': ['DR_SHA_733', 'DR_RAD_744', 'DR_AJI_755'],
                'Pharmacy_Names': ['Gayathri Medicals', 'City Care Pharmacy', 'MedPlus Calicut'],
                'Pharmacy_ID': ['GM_CAL_001', 'CCP_CAL_002', 'MP_CAL_003'],
                'Product_Names': ['ENDOL 650', 'BRETHNOL SYRUP', 'CLOZACT-100 TAB'],
                'Product_ID': ['PRD_6824', 'PRD_6825', 'PRD_6826'],
                'Product_Price': [13.46, 14.5, 57.0],
                'HQ': ['CL', 'CL', 'CL'],
                'AREA': ['CALICUT', 'CALICUT', 'CALICUT']
            }
            filename = "master_data_template.xlsx"
            
        elif template_type == "invoice":
            # Create invoice data template
            template_data = {
                'Pharmacy_Name': ['Gayathri Medicals, Calicut', 'City Care Pharmacy, Ernakulam', 'MedPlus Calicut'],
                'Product': ['ENDOL 650', 'BRETHNOL SYRUP', 'CLOZACT-100 TAB'],
                'Quantity': [20, 10, 12],
                'Amount': [269.2, 145.0, 684.0]
            }
            filename = "invoice_data_template.xlsx"
            
        else:
            raise HTTPException(status_code=400, detail="Invalid template type")
        
        # Create DataFrame and save
        df = pd.DataFrame(template_data)
        df.to_excel(temp_filename, index=False)
        
        # Schedule file cleanup
        background_tasks.add_task(cleanup_temp_file, temp_filename)
        
        return FileResponse(
            path=temp_filename,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template download failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Template download failed"
        )

def cleanup_temp_file(file_path: str):
    """Clean up temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up temporary file {file_path}: {str(e)}")

@router.get("/export-status")
async def get_export_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get export status and recent exports"""
    try:
        # This could be expanded to track export jobs
        return {
            "status": "ready",
            "available_formats": ["excel", "csv"],
            "max_records": 10000,
            "user_permissions": {
                "can_export_raw_data": current_user.role in ["admin", "super_admin"],
                "data_masking": current_user.role == "user"
            }
        }
        
    except Exception as e:
        logger.error(f"Export status check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Export status check failed"
        )
