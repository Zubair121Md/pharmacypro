from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Body
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
import pandas as pd
import json
from datetime import datetime, timedelta
import uuid
import os
import tempfile
import logging
from app.file_processor import FileProcessor
from fastapi import BackgroundTasks
from app.database import init_db as _init_db
from app.database import ensure_unmatched_schema as _ensure_unmatched_schema

# Setup logger
logger = logging.getLogger(__name__)
# from app.routes import advanced  # Temporarily disabled

app = FastAPI(
    title="Pharmacy Revenue Management System API",
    description="Complete API for Pharmacy Revenue Management System",
    version="2.0.0"
)

# Ensure DB tables and critical schema adjustments are present on startup
@app.on_event("startup")
async def _startup_db_prepare():
    try:
        await _init_db()
    except Exception:
        # init_db may be sync in some setups; best-effort call
        try:
            _init_db()  # type: ignore
        except Exception:
            pass
    # Ensure unmatched columns (product/quantity/amount) exist
    try:
        _ensure_unmatched_schema()
    except Exception:
        pass

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:80",
        "tauri://localhost"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "user"
    disabled: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class FileUploadResponse(BaseModel):
    message: str
    filename: str
    processed_rows: int
    status: str

class RevenueData(BaseModel):
    pharmacy_name: str
    revenue: float
    doctor_name: Optional[str] = None
    rep_name: Optional[str] = None

class IdGenerationRequest(BaseModel):
    name: str
    type: str  # 'pharmacy', 'product', 'doctor'

class IdGenerationResponse(BaseModel):
    original_name: str
    generated_id: str
    type: str
    timestamp: str
    metadata: Optional[Dict] = None  # For product: price and matched_original

class DashboardData(BaseModel):
    total_revenue: float
    total_pharmacies: int
    total_doctors: int
    growth_rate: float
    recent_activity: List[dict]

class UnmatchedRecord(BaseModel):
    id: int
    pharmacy_name: str
    generated_id: str
    product: Optional[str] = None
    quantity: Optional[int] = 0
    amount: Optional[float] = 0.0
    status: str
    created_at: str

# Mock data storage
mock_data = {
    "users": [
        {"id": 1, "username": "admin", "email": "admin@pharmacy.com", "full_name": "Admin User", "role": "super_admin", "disabled": False},
        {"id": 2, "username": "user1", "email": "user1@pharmacy.com", "full_name": "Regular User", "role": "user", "disabled": False}
    ],
    "revenue_data": [
        {
            "pharmacy_name": "Gayathri Medicals",
            "revenue": 456.7,
            "doctor_name": "DR SHAJIKUMAR",
            "rep_name": "VIKRAM",
            "area": "CALICUT",
            "hq": "CL"
        },
        {
            "pharmacy_name": "City Care Pharmacy",
            "revenue": 357.0,
            "doctor_name": "DR RADHAKRISHNAN",
            "rep_name": "ANITA",
            "area": "CALICUT",
            "hq": "CL"
        },
        {
            "pharmacy_name": "MedPlus Calicut",
            "revenue": 1169.1,
            "doctor_name": "DR AJITH KUMAR",
            "rep_name": "RAHUL",
            "area": "CALICUT",
            "hq": "CL"
        }
    ],
    "unmatched_records": [
        {"id": 1, "pharmacy_name": "Gayatree Medicals", "generated_id": "GM-CAL-001", "status": "pending", "created_at": "2024-01-15T10:30:00Z"},
        {"id": 2, "pharmacy_name": "City Care Medical", "generated_id": "CC-CAL-002", "status": "pending", "created_at": "2024-01-15T11:15:00Z"},
        {"id": 3, "pharmacy_name": "MedPlus Kozhikode", "generated_id": "MP-KOZ-001", "status": "mapped", "created_at": "2024-01-15T12:00:00Z"}
    ],
    "analysis_timestamp": "2024-01-15T20:00:00Z",
    "analysis_summary": {
        "total_revenue": 1982.8,
        "total_pharmacies": 3,
        "total_doctors": 3,
        "total_unmatched": 0
    },
    "invoice_uploads": {},
    "master_uploads": {},
    "enhanced_uploads": {},
    "transactions": [
        {
            "id": 1,
            "pharmacy_name": "Apollo Pharmacy",
            "product": "Paracetamol 500mg",
            "quantity": 100,
            "amount": 1500.0,
            "doctor_name": "Dr. John Smith",
            "rep_name": "Alice Johnson",
            "area": "Downtown",
            "hq": "Mumbai",
            "created_at": "2024-01-15T10:00:00Z",
            "created_by": "admin"
        },
        {
            "id": 2,
            "pharmacy_name": "MedPlus Calicut",
            "product": "Amoxicillin 250mg",
            "quantity": 50,
            "amount": 750.0,
            "doctor_name": "Dr. Sarah Wilson",
            "rep_name": "Bob Brown",
            "area": "Calicut",
            "hq": "Kerala",
            "created_at": "2024-01-15T11:30:00Z",
            "created_by": "admin"
        }
    ]
}

# Helper: compute growth rate safely
def _compute_growth_rate(current: float, previous: float) -> float:
    try:
        current_val = float(current or 0)
        previous_val = float(previous or 0)
        if previous_val == 0:
            # No reliable baseline: use a conservative fallback rather than a spike
            return 0.0 if current_val == 0 else 15.5
        rate = ((current_val - previous_val) / previous_val) * 100.0
        # Cap extremes to keep UI readable
        if rate > 150.0:
            rate = 150.0
        if rate < -100.0:
            rate = -100.0
        return rate
    except Exception:
        return 0.0

# ID Generation utility functions
def normalize_text(text: str) -> str:
    """Normalize text for ID generation"""
    if not text:
        return ""
    import re
    # Keep dots as valid characters
    return re.sub(r'[^A-Z0-9\.]', '', text.upper())[:8].ljust(8, '-')

def generate_id(name: str, id_type: str, db: Session = None) -> str:
    """Generate standardized ID based on type"""
    import re

    if id_type == 'pharmacy':
        # Use full name for both facility and location (no splitting)
        # - Remove ALL special chars (including . and ,)
        # - Facility code: first 10 chars (spaces removed)
        # - Location code: last 10 chars (spaces removed)
        raw = (name or "").strip()
        if not raw:
            return "INVALID"
        
        # Remove ALL special chars (including . and ,)
        cleaned = re.sub(r'[^\w\s]', '', raw).strip().lower()
        if not cleaned:
            return "INVALID"
        
        # Remove spaces
        no_spaces = cleaned.replace(" ", "")
        
        # Get first 10 and last 10 characters
        facility_code = no_spaces[:10].upper().ljust(10, "_")
        location_code = no_spaces[-10:].upper().ljust(10, "_")
        
        return f"{facility_code}-{location_code}"
    
    elif id_type == 'doctor':
        # Use doctor ID generator
        if db is None:
            from app.database import get_db
            db = next(get_db())
            should_close = True
        else:
            should_close = False
        
        try:
            from app.doctor_id_generator import generate_doctor_id
            result = generate_doctor_id(name, db, 0)
            return result
        finally:
            if should_close:
                db.close()
    
    elif id_type == 'product':
        # Product ID requires reference table - handled separately via API
        # This is a fallback
        normalized = normalize_text(name)
        return f"PX-{normalized}"

    # Default for other types
    normalized = normalize_text(name)
    prefixes = {
        'product': 'PX-',
        'doctor': 'DR-'
    }
    return f"{prefixes.get(id_type, 'ID-')}{normalized}"

# Authentication functions
def get_current_user(token: str = Depends(oauth2_scheme)):
    if token == "demo_token_12345":
        return User(id=1, username="admin", email="admin@pharmacy.com", full_name="Admin User", role="super_admin")
    elif token == "demo_token_user_12345":
        return User(id=2, username="user", email="user@pharmacy.com", full_name="Regular User", role="user")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Root endpoint
@app.get("/")
async def read_root():
    return {"message": "Pharmacy Revenue Management System API", "version": "2.0.0"}

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

# Authentication endpoints
@app.post("/api/v1/auth/login")
async def login(login_data: dict):
    try:
        username = login_data.get("username", "").strip()
        password = login_data.get("password", "").strip()
        
        logger.info(f"Login attempt: username={username}")
        
        if username == "admin" and password == "admin123":
            user = User(id=1, username="admin", email="admin@pharmacy.com", full_name="Admin User", role="super_admin")
            return {
                "access_token": "demo_token_12345", 
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role
                }
            }
        elif username == "manager" and password == "manager123":
            user = User(id=2, username="manager", email="manager@pharmacy.com", full_name="Manager User", role="admin")
            return {
                "access_token": "demo_token_manager_12345", 
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role
                }
            }
        elif username == "user" and password == "user123":
            user = User(id=3, username="user", email="user@pharmacy.com", full_name="Regular User", role="user")
            return {
                "access_token": "demo_token_user_12345", 
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role
                }
            }
        
        logger.warning(f"Failed login attempt: username={username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.get("/api/v1/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Initialize file processor
file_processor = FileProcessor()

# Upload endpoints
@app.post("/api/v1/upload/invoice-only")
async def upload_invoice(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file")
    
    try:
        # Clear existing invoice data before processing new file
        from app.database import get_db, Invoice
        db = next(get_db())
        try:
            db.query(Invoice).delete()
            db.commit()
        finally:
            db.close()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Process the invoice file
        result = file_processor.process_invoice_file(tmp_file_path)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Return processing summary (DB already updated inside processor)
        return {
            "message": "Invoice file processed successfully",
            "filename": file.filename,
            "processed_rows": result.get("processed_rows", 0),
            "status": "completed",
            "summary": result.get("summary", {}),
            "unmatched_pharmacies": result.get("unmatched_pharmacies", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/v1/upload/master-only")
async def upload_master(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file")
    
    try:
        # Clear existing master data before processing new file
        from app.database import get_db, MasterMapping
        db = next(get_db())
        try:
            db.query(MasterMapping).delete()
            db.commit()
        finally:
            db.close()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Process the master file
        result = file_processor.process_master_file(tmp_file_path)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Return processing summary (DB already updated inside processor)
        return {
            "message": "Master file processed successfully",
            "filename": file.filename,
            "processed_rows": result.get("processed_rows", 0),
            "status": "completed",
            "summary": result.get("summary", {}),
            "validation_errors": result.get("validation_errors", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/v1/upload/enhanced")
async def upload_enhanced(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="File must be an Excel file")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Process as invoice file for enhanced upload
        result = file_processor.process_invoice_file(tmp_file_path)
        
        # Clean up temporary file
        os.unlink(tmp_file_path)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Return processing summary
        return {
            "message": "Enhanced file processed successfully",
            "filename": file.filename,
            "processed_rows": result.get("processed_rows", 0),
            "status": "completed",
            "summary": result.get("summary", {}),
            "unmatched_pharmacies": result.get("unmatched_pharmacies", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Analytics endpoints
@app.post("/api/v1/analytics/analyze")
async def analyze_data(current_user: User = Depends(get_current_user)):
    """Analyze uploaded data and generate analytics"""
    try:
        from app.database import get_db
        # Ensure schema (defensive in case startup hook didn't run on reload worker)
        try:
            from app.database import ensure_unmatched_schema as _ensure_unmatched_schema
            _ensure_unmatched_schema()
        except Exception:
            pass
        from app.tasks_enhanced import merge_invoice_with_master
        import pandas as pd
        
        # Get database session
        db = next(get_db())
        
        # Import models
        from app.database import Invoice, MasterMapping
        
        # Get data from database with limits for performance
        invoice_records = db.query(Invoice).limit(10000).all()  # Limit to prevent memory issues
        master_records = db.query(MasterMapping).limit(10000).all()
        
        if not invoice_records or not master_records:
            return {
                "success": False,
                "message": "No data available for analysis. Please upload both invoice and master files first.",
                "requires_upload": True
            }
        
        # Convert to DataFrames for processing
        invoice_data = []
        for record in invoice_records:
            invoice_data.append({
                'Pharmacy_Name': record.pharmacy_name,
                'Product': record.product,
                'Quantity': record.quantity,
                'Amount': record.amount,
                'Generated_Pharmacy_ID': record.pharmacy_id
            })
        
        master_data = []
        for record in master_records:
            master_data.append({
                'Pharmacy_Names': record.pharmacy_names,
                'Product_Names': record.product_names,
                'Product_ID': record.product_id,
                'Product_Price': record.product_price,
                'Doctor_Names': record.doctor_names,
                'Doctor_ID': record.doctor_id,
                'REP_Names': record.rep_names,
                'HQ': record.hq,
                'AREA': record.area,
                'Generated_Pharmacy_ID': record.pharmacy_id
            })
        
        invoice_df = pd.DataFrame(invoice_data)
        master_df = pd.DataFrame(master_data)
        
        # Rename columns to lowercase for compatibility with merge function
        invoice_df = invoice_df.rename(columns={
            'Pharmacy_Name': 'pharmacy_name',
            'Product': 'product',
            'Quantity': 'quantity',
            'Amount': 'amount'
        })
        
        master_df = master_df.rename(columns={
            'Pharmacy_Names': 'pharmacy_names',
            'Product_Names': 'product_names',
            'Product_ID': 'product_id',
            'Product_Price': 'product_price',
            'Doctor_Names': 'doctor_names',
            'Doctor_ID': 'doctor_id',
            'REP_Names': 'rep_names',
            'HQ': 'hq',
            'AREA': 'area'
        })
        
        # Data already has IDs from file processing, no need to regenerate

        # IMPORTANT: clear previously stored invoices to prevent duplicate rows on re-analysis
        # We rebuild matched invoices from the current in-memory DataFrame below
        db.query(Invoice).delete()
        db.commit()

        # Clear old unmatched records before processing new data
        from app.database import Unmatched
        db.query(Unmatched).delete()
        db.commit()
        
        # Data is already in database from file uploads, just run the matching
        matched_count, unmatched_count = merge_invoice_with_master(invoice_df, current_user.id if hasattr(current_user, 'id') else 1, db)
        
        # Calculate analytics data for this specific analysis
        from app.tasks_enhanced import create_chart_ready_data
        try:
            chart_data = create_chart_ready_data(db, current_user)
            analysis_revenue = chart_data.get("total_revenue", 0)
            analysis_pharmacies = len(chart_data.get("pharmacy_revenue", []))
            analysis_doctors = len(chart_data.get("doctor_revenue", []))
            analysis_growth = chart_data.get("growth_rate", 0)
        except Exception as e:
            print(f"Error calculating analytics: {str(e)}")
            analysis_revenue = 0
            analysis_pharmacies = 0
            analysis_doctors = 0
            analysis_growth = 0
        
        # Create a recent upload record for this analysis
        from app.database import RecentUpload
        from datetime import datetime
        recent_upload = RecentUpload(
            user_id=current_user.id if hasattr(current_user, 'id') else 1,
            file_type='analysis',
            file_name=f'Analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            processed_rows=matched_count + unmatched_count,
            status='completed'
        )
        db.add(recent_upload)
        db.commit()
        
        # Store analysis-specific data in the upload record
        # We'll add these fields to the RecentUpload model
        recent_upload.total_revenue = analysis_revenue
        recent_upload.total_pharmacies = analysis_pharmacies
        recent_upload.total_doctors = analysis_doctors
        recent_upload.growth_rate = analysis_growth
        recent_upload.matched_count = matched_count
        recent_upload.unmatched_count = unmatched_count
        db.commit()
        
        return {
            "success": True,
            "message": "Analysis completed successfully",
            "summary": {
                "total_revenue": analysis_revenue,
                "total_pharmacies": analysis_pharmacies,
                "total_doctors": analysis_doctors,
                "total_reps": 0,  # Will be calculated by analytics endpoints
                "matched_records": matched_count,
                "unmatched_records": unmatched_count,
                "growth_rate": analysis_growth
            }
        }
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        return {
            "success": False,
            "message": f"Analysis failed: {str(e)}",
            "requires_upload": True
        }
    finally:
        db.close()

# Override endpoints
@app.post("/api/v1/analytics/override")
async def set_revenue_override(override_data: dict, current_user: User = Depends(get_current_user)):
    """Set revenue override for an analysis"""
    analysis_id = override_data.get("analysis_id")
    total_revenue = override_data.get("total_revenue")
    
    if not analysis_id or total_revenue is None:
        raise HTTPException(status_code=400, detail="analysis_id and total_revenue are required")
    
    # Store override in mock data
    if "overrides" not in mock_data:
        mock_data["overrides"] = {}
    
    mock_data["overrides"][str(analysis_id)] = {
        "total_revenue": float(total_revenue),
        "created_at": datetime.now().isoformat(),
        "created_by": current_user.username
    }
    
    return {"success": True, "message": "Revenue override set successfully"}

@app.delete("/api/v1/analytics/override")
async def clear_revenue_override(analysis_id: int, current_user: User = Depends(get_current_user)):
    """Clear revenue override for an analysis"""
    if "overrides" not in mock_data:
        mock_data["overrides"] = {}
    
    if str(analysis_id) in mock_data["overrides"]:
        del mock_data["overrides"][str(analysis_id)]
        return {"success": True, "message": "Revenue override cleared successfully"}
    else:
        return {"success": True, "message": "No override found for this analysis"}

# Recent Uploads endpoints
@app.get("/api/v1/uploads/recent")
async def get_recent_uploads(current_user: User = Depends(get_current_user)):
    """Get recent uploads/analyses from database"""
    try:
        from app.database import get_db, RecentUpload
        
        # Get database session
        db = next(get_db())
        
        # Get recent analysis uploads for the current user
        recent_uploads = db.query(RecentUpload).filter(
            RecentUpload.user_id == current_user.id,
            RecentUpload.file_type == 'analysis'
        ).order_by(RecentUpload.uploaded_at.desc()).limit(10).all()
        
        # Convert to response format - each upload has its own stored data
        result = []
        for upload in recent_uploads:
            result.append({
                "id": upload.id,
                "file_name": upload.file_name,
                "file_type": upload.file_type,
                "uploaded_at": upload.uploaded_at.isoformat() + "Z",
                "status": upload.status,
                "processed_rows": upload.processed_rows,
                "user": current_user.username,
                "total_revenue": float(upload.total_revenue or 0),
                "total_pharmacies": upload.total_pharmacies or 0,
                "total_doctors": upload.total_doctors or 0,
                "growth_rate": float(upload.growth_rate or 0),
                "matched_count": upload.matched_count or 0,
                "unmatched_count": upload.unmatched_count or 0
            })
        
        return result
        
    except Exception as e:
        print(f"Error getting recent uploads: {str(e)}")
        return []
    finally:
        db.close()

## Removed legacy mock upload-details endpoint (DB-backed version exists below)

@app.get("/api/v1/uploads/{upload_id}/export")
async def export_upload_data(upload_id: int, format: str = "csv", current_user: User = Depends(get_current_user)):
    """Export upload data in specified format"""
    try:
        from app.database import get_db
        from app.tasks_enhanced import get_matched_results_with_doctor_info
        
        # Get database session
        db = next(get_db())
        
        # Get matched results from database
        matched_results = get_matched_results_with_doctor_info(db, current_user.id)
        
        if not matched_results:
            raise HTTPException(status_code=404, detail="No analysis data available")
        
        # Generate export data
        export_data = []
        for result in matched_results:
            export_data.append({
                "Doctor_ID": result.get("Doctor_ID", ""),
                "Doctor_Name": result.get("Doctor_Name", ""),
                "REP_Name": result.get("REP_Name", ""),
                "Pharmacy_Name": result.get("Pharmacy_Name", ""),
                "Pharmacy_ID": result.get("Pharmacy_ID", ""),
                "Product": result.get("Product", ""),
                "Quantity": result.get("Quantity", 0),
                "Revenue": result.get("Revenue", 0.0)
            })
        
        db.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating export data: {str(e)}")
    
    if format.lower() == "csv":
        # Generate CSV
        import io
        import csv
        from fastapi.responses import Response
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
        writer.writeheader()
        writer.writerows(export_data)
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=analysis_{upload_id}.csv"}
        )
    elif format.lower() == "xlsx":
        # Generate Excel
        import io
        from fastapi.responses import Response
        
        df = pd.DataFrame(export_data)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=analysis_{upload_id}.xlsx"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'xlsx'")

## Removed legacy mock delete endpoint (DB-backed version exists below)

## Removed legacy mock unmatched endpoints (DB-backed versions exist below)

@app.get("/api/v1/analytics/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user)):
    try:
        from app.tasks_enhanced import create_chart_ready_data
        from app.database import get_db
        
        # Get database session
        db = next(get_db())
        
        # Get chart data from database
        chart_data = create_chart_ready_data(db, current_user)
        
        if not chart_data["pharmacy_revenue"]:
            return {
                "analysis_id": 1,
                "total_revenue": 0,
                "total_pharmacies": 0,
                "total_doctors": 0,
                "growth_rate": 0,
                "recent_activity": [],
                "requires_analysis": True,
                "message": "No data available. Please upload files and click 'Analyze' to generate analytics."
            }
        
        total_revenue = chart_data["total_revenue"]
        
        # Check for revenue override
        has_override = False
        if "overrides" in mock_data and "1" in mock_data["overrides"]:
            total_revenue = mock_data["overrides"]["1"]["total_revenue"]
            has_override = True
        
        # Count unique pharmacies from all invoices (including unmatched)
        total_pharmacies = chart_data.get("total_unique_pharmacies", len(chart_data["pharmacy_revenue"]))
        total_doctors = len(chart_data["doctor_revenue"])
        
        # Get growth rate from chart data
        growth_rate = chart_data.get("growth_rate", 0.0)
        
        return {
            "analysis_id": 1,
            "total_revenue": total_revenue,
            "total_pharmacies": total_pharmacies,
            "total_doctors": total_doctors,
            "growth_rate": round(growth_rate, 2),
            "has_override": has_override,
            "pharmacy_revenue": chart_data["pharmacy_revenue"],
            "doctor_revenue": chart_data["doctor_revenue"],
            "rep_revenue": chart_data["rep_revenue"],
            "hq_revenue": chart_data["hq_revenue"],
            "area_revenue": chart_data["area_revenue"],
            "monthly_revenue": chart_data["monthly_revenue"],
            "recent_activity": [
                {"description": "Data analysis completed", "timestamp": "2024-01-15T20:00:00Z"},
                {"description": "New invoice file uploaded", "timestamp": "2024-01-15T14:30:00Z"},
                {"description": "Master data updated", "timestamp": "2024-01-15T13:45:00Z"}
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        return {
            "analysis_id": 1,
            "total_revenue": 0,
            "total_pharmacies": 0,
            "total_doctors": 0,
            "growth_rate": 0,
            "recent_activity": [],
            "requires_analysis": True,
            "message": "Error loading data. Please try again."
        }

@app.get("/api/v1/analytics/pharmacy-revenue")
async def get_pharmacy_revenue(current_user: User = Depends(get_current_user)):
    try:
        from app.tasks_enhanced import create_chart_ready_data
        from app.database import get_db
        
        # Get database session
        db = next(get_db())
        
        # Get chart data from database
        chart_data = create_chart_ready_data(db, current_user)
        
        return chart_data["pharmacy_revenue"]
        
    except Exception as e:
        logger.error(f"Error getting pharmacy revenue: {str(e)}")
        return []

@app.get("/api/v1/analytics/doctor-revenue")
async def get_doctor_revenue(current_user: User = Depends(get_current_user)):
    try:
        from app.tasks_enhanced import create_chart_ready_data
        from app.database import get_db
        
        # Get database session
        db = next(get_db())
        
        # Get chart data from database
        chart_data = create_chart_ready_data(db, current_user)
        
        return chart_data["doctor_revenue"]
        
    except Exception as e:
        logger.error(f"Error getting doctor revenue: {str(e)}")
        return []

@app.get("/api/v1/analytics/rep-revenue")
async def get_rep_revenue(current_user: User = Depends(get_current_user)):
    try:
        from app.tasks_enhanced import create_chart_ready_data
        from app.database import get_db
        
        # Get database session
        db = next(get_db())
        
        # Get chart data from database
        chart_data = create_chart_ready_data(db, current_user)
        
        return chart_data["rep_revenue"]
        
    except Exception as e:
        logger.error(f"Error getting rep revenue: {str(e)}")
        return []

@app.get("/api/v1/analytics/hq-revenue")
async def get_hq_revenue(current_user: User = Depends(get_current_user)):
    try:
        from app.tasks_enhanced import create_chart_ready_data
        from app.database import get_db
        
        # Get database session
        db = next(get_db())
        
        # Get chart data from database
        chart_data = create_chart_ready_data(db, current_user)
        
        return chart_data["hq_revenue"]
        
    except Exception as e:
        logger.error(f"Error getting HQ revenue: {str(e)}")
        return []

@app.get("/api/v1/analytics/area-revenue")
async def get_area_revenue(current_user: User = Depends(get_current_user)):
    try:
        from app.tasks_enhanced import create_chart_ready_data
        from app.database import get_db
        
        # Get database session
        db = next(get_db())
        
        # Get chart data from database
        chart_data = create_chart_ready_data(db, current_user)
        
        return chart_data["area_revenue"]
        
    except Exception as e:
        logger.error(f"Error getting area revenue: {str(e)}")
        return []

@app.get("/api/v1/analytics/product-revenue")
async def get_product_revenue(current_user: User = Depends(get_current_user)):
    try:
        from app.tasks_enhanced import create_chart_ready_data
        from app.database import get_db
        
        # Get database session
        db = next(get_db())
        
        # Get chart data from database
        chart_data = create_chart_ready_data(db, current_user)
        
        return chart_data["product_revenue"]
        
    except Exception as e:
        logger.error(f"Error getting product revenue: {str(e)}")
        return []

@app.get("/api/v1/analytics/matched-results")
async def get_matched_results(current_user: User = Depends(get_current_user)):
    """Get matched results with proper doctor allocation and correct output format"""
    try:
        from app.tasks_enhanced import get_matched_results_with_doctor_info
        from app.database import get_db
        
        # Get database session
        db = next(get_db())
        
        # Get matched results with proper format
        results = get_matched_results_with_doctor_info(db, current_user.id if hasattr(current_user, 'id') else 1)
        
        return {
            "success": True,
            "data": results,
            "total_records": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error getting matched results: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": []
        }

@app.post("/api/v1/analytics/clear-cache")
async def clear_analytics_cache(current_user: User = Depends(get_current_user)):
    """Clear server-side cached analytics so the UI can fetch a fresh state."""
    mock_data["revenue_data"] = []
    mock_data.pop("analysis_timestamp", None)
    mock_data.pop("analysis_summary", None)
    return {"success": True, "message": "Analytics cache cleared"}

@app.post("/api/v1/analytics/clear-recent-uploads")
async def clear_recent_uploads(current_user: User = Depends(get_current_user)):
    """Clear recent uploads and reset all data to fresh state."""
    # Clear all mock data
    mock_data["revenue_data"] = []
    mock_data["invoice_uploads"] = {}
    mock_data["master_uploads"] = {}
    mock_data["enhanced_uploads"] = {}
    mock_data["transactions"] = []
    mock_data["overrides"] = {}
    mock_data.pop("analysis_timestamp", None)
    mock_data.pop("analysis_summary", None)
    return {"success": True, "message": "Recent uploads and all data cleared"}

@app.get("/api/v1/analytics/export-mapped-data")
async def export_mapped_data(format: str = "csv", current_user: User = Depends(get_current_user)):
    """Export mapped data after analysis"""
    try:
        from app.database import get_db
        from app.tasks_enhanced import get_matched_results_with_doctor_info
        
        # Get database session
        db = next(get_db())
        
        # Get matched results from database
        matched_results = get_matched_results_with_doctor_info(db, current_user.id)
        
        if not matched_results:
            raise HTTPException(status_code=404, detail="No mapped data available. Please run analysis first.")
        
        # Generate export data
        export_data = []
        for result in matched_results:
            export_data.append({
                "Doctor_ID": result.get("Doctor_ID", ""),
                "Doctor_Name": result.get("Doctor_Name", ""),
                "REP_Name": result.get("REP_Name", ""),
                "Pharmacy_Name": result.get("Pharmacy_Name", ""),
                "Pharmacy_ID": result.get("Pharmacy_ID", ""),
                "Product": result.get("Product", ""),
                "Quantity": result.get("Quantity", 0),
                "Revenue": result.get("Revenue", 0.0)
            })
        
        db.close()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating export data: {str(e)}")
    
    if format.lower() == "csv":
        # Generate CSV
        import io
        import csv
        from fastapi.responses import Response
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
        writer.writeheader()
        writer.writerows(export_data)
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=mapped_data.csv"}
        )
    elif format.lower() == "xlsx":
        # Generate Excel
        import io
        from fastapi.responses import Response
        
        df = pd.DataFrame(export_data)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=mapped_data.xlsx"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'xlsx'")

# Data Quality endpoints (Phase 12)
@app.get("/api/v1/analytics/data-quality")
async def get_data_quality_summary(current_user: User = Depends(get_current_user)):
    """Return summary of invalid/incomplete rows (NIL/INVALID) and basic quality metrics."""
    # Collect from latest uploads if present
    master_summaries = [u["result"].get("summary", {}) for u in mock_data.get("master_uploads", {}).values() if u.get("result", {}).get("success")]
    invoice_summaries = [u["result"].get("summary", {}) for u in mock_data.get("invoice_uploads", {}).values() if u.get("result", {}).get("success")]

    # Aggregate simple metrics if available from processor
    total_rows = 0
    valid_rows = 0
    error_rows = 0
    nil_count = 0
    invalid_count = 0

    for s in master_summaries + invoice_summaries:
        total_rows += int(s.get("processed_rows", 0))
        valid_rows += int(s.get("valid_rows", 0))
        error_rows += int(s.get("error_rows", 0))
        nil_count += int(s.get("nil_count", 0))
        invalid_count += int(s.get("invalid_count", 0))

    valid_pct = round((valid_rows / total_rows) * 100, 2) if total_rows > 0 else 0.0

    return {
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "error_rows": error_rows,
        "valid_percentage": valid_pct,
        "nil_count": nil_count,
        "invalid_count": invalid_count,
        "notes": {
            "nil": "NIL means no product mapped; keep flagged until resolved.",
            "invalid": "INVALID means failed validation; keep flagged until corrected."
        }
    }

@app.get("/api/v1/analytics/data-quality/export")
async def export_data_quality(format: str = "csv", current_user: User = Depends(get_current_user)):
    """Export data-quality summary in CSV/XLSX."""
    summary = await get_data_quality_summary(current_user)  # reuse logic

    if format.lower() == "csv":
        import io, csv
        from fastapi.responses import Response
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        for k in ["total_rows", "valid_rows", "error_rows", "valid_percentage", "nil_count", "invalid_count"]:
            writer.writerow([k, summary.get(k)])
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=data_quality.csv"})

    if format.lower() == "xlsx":
        import io
        from fastapi.responses import Response
        df = pd.DataFrame([
            {"Metric": "total_rows", "Value": summary.get("total_rows")},
            {"Metric": "valid_rows", "Value": summary.get("valid_rows")},
            {"Metric": "error_rows", "Value": summary.get("error_rows")},
            {"Metric": "valid_percentage", "Value": summary.get("valid_percentage")},
            {"Metric": "nil_count", "Value": summary.get("nil_count")},
            {"Metric": "invalid_count", "Value": summary.get("invalid_count")},
        ])
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=data_quality.xlsx"})

    raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'xlsx'")

# Transaction endpoints
@app.get("/api/v1/transactions")
async def get_transactions(current_user: User = Depends(get_current_user)):
    """Get all transactions"""
    return mock_data.get("transactions", [])

@app.post("/api/v1/transactions")
async def add_transaction(transaction_data: dict, current_user: User = Depends(get_current_user)):
    """Add a new transaction"""
    if "transactions" not in mock_data:
        mock_data["transactions"] = []
    
    new_transaction = {
        "id": len(mock_data["transactions"]) + 1,
        "created_at": datetime.now().isoformat(),
        "created_by": current_user.username,
        **transaction_data
    }
    mock_data["transactions"].append(new_transaction)
    return new_transaction

@app.put("/api/v1/transactions/{transaction_id}")
async def update_transaction(transaction_id: int, transaction_data: dict, current_user: User = Depends(get_current_user)):
    """Update an existing transaction"""
    if "transactions" not in mock_data:
        mock_data["transactions"] = []
    
    transaction_index = next((i for i, t in enumerate(mock_data["transactions"]) if t["id"] == transaction_id), None)
    if transaction_index is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    mock_data["transactions"][transaction_index].update({
        **transaction_data,
        "updated_at": datetime.now().isoformat(),
        "updated_by": current_user.username
    })
    return mock_data["transactions"][transaction_index]

@app.delete("/api/v1/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int, current_user: User = Depends(get_current_user)):
    """Delete a transaction"""
    if "transactions" not in mock_data:
        mock_data["transactions"] = []
    
    transaction_index = next((i for i, t in enumerate(mock_data["transactions"]) if t["id"] == transaction_id), None)
    if transaction_index is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    deleted_transaction = mock_data["transactions"].pop(transaction_index)
    return {"success": True, "message": "Transaction deleted", "deleted_transaction": deleted_transaction}

@app.get("/api/v1/analytics/trends")
async def get_monthly_trends(current_user: User = Depends(get_current_user)):
    """Generate monthly trends based on current analysis data."""
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Get current analysis data
    current_revenue = sum(float(item["revenue"]) for item in mock_data["revenue_data"]) if mock_data["revenue_data"] else 0.0
    
    # Generate trends for the last 6 months
    trends = []
    for i in range(6):
        month_offset = 5 - i  # Start from 6 months ago
        target_month = current_month - month_offset
        target_year = current_year
        
        # Handle year rollover
        if target_month <= 0:
            target_month += 12
            target_year -= 1
        
        month_name = datetime(target_year, target_month, 1).strftime("%b")
        
        # For current month, use actual data
        if i == 5:  # Current month
            revenue = current_revenue
        else:
            # For previous months, generate realistic variations
            # Base it on current revenue with some variation
            variation_factor = 0.7 + (i * 0.1)  # Gradual increase over time
            revenue = current_revenue * variation_factor * (0.8 + (i * 0.05))  # Add some randomness
        
        trends.append({
            "month": month_name,
            "revenue": round(revenue, 2)
        })
    
    return trends

@app.get("/api/v1/analytics/summary")
async def get_analytics_summary(current_user: User = Depends(get_current_user)):
    total_revenue = sum(float(item["revenue"]) for item in mock_data["revenue_data"]) if mock_data["revenue_data"] else 0.0
    total_transactions = len(mock_data["revenue_data"]) if mock_data["revenue_data"] else 0
    average_transaction = (total_revenue / total_transactions) if total_transactions > 0 else 0.0

    top_pharmacy = None
    if mock_data["revenue_data"]:
        # Aggregate by pharmacy to get true top pharmacy
        agg: Dict[str, float] = {}
        for item in mock_data["revenue_data"]:
            name = item["pharmacy_name"]
            agg[name] = agg.get(name, 0.0) + float(item["revenue"])
        top_pharmacy = max(agg.items(), key=lambda kv: kv[1])[0]

    return {
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "average_transaction": average_transaction,
        "top_pharmacy": top_pharmacy,
    }

# Admin endpoints
@app.get("/api/v1/admin/users")
async def get_users(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return mock_data["users"]

@app.post("/api/v1/admin/users")
async def create_user(user_data: dict, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    new_user = {
        "id": len(mock_data["users"]) + 1,
        "username": user_data["username"],
        "email": user_data["email"],
        "full_name": user_data["full_name"],
        "role": user_data["role"],
        "disabled": False
    }
    mock_data["users"].append(new_user)
    return new_user

@app.put("/api/v1/admin/users/{user_id}")
async def update_user(user_id: int, user_data: dict, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    for user in mock_data["users"]:
        if user["id"] == user_id:
            user.update(user_data)
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/api/v1/admin/users/{user_id}")
async def delete_user(user_id: int, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    mock_data["users"] = [user for user in mock_data["users"] if user["id"] != user_id]
    return {"message": "User deleted successfully"}

@app.get("/api/v1/admin/stats")
async def get_admin_stats(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return {
        "total_users": len(mock_data["users"]),
        "total_files": 15,
        "system_status": "healthy"
    }

@app.get("/api/v1/admin/audit-logs")
async def get_audit_logs(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return [
        {"action": "login", "user": "admin", "timestamp": "2024-01-15T14:30:00Z"},
        {"action": "file_upload", "user": "admin", "timestamp": "2024-01-15T14:25:00Z"},
        {"action": "data_export", "user": "admin", "timestamp": "2024-01-15T14:20:00Z"}
    ]

# Unmatched records endpoints
@app.get("/api/v1/unmatched")
async def get_unmatched_records(current_user: User = Depends(get_current_user)):
    """Get unmatched pharmacy records from database"""
    try:
        from app.database import get_db, Unmatched
        
        # Get database session
        db = next(get_db())
        
        # Get unmatched records from database
        unmatched_records = db.query(Unmatched).filter(
            Unmatched.status == "pending"
        ).all()
        
        result = [
            {
                "id": record.id,
                "pharmacy_name": record.pharmacy_name,
                "generated_id": record.generated_id,
                "product": getattr(record, "product", None),
                "quantity": int(getattr(record, "quantity", 0) or 0),
                "amount": float(getattr(record, "amount", 0.0) or 0.0),
                "status": record.status,
                "created_at": record.created_at.isoformat() if record.created_at else None
            }
            for record in unmatched_records
        ]
        
        return result
        
    except Exception as e:
        print(f"Error getting unmatched records: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting unmatched records: {str(e)}")
    finally:
        db.close()

@app.get("/api/v1/unmatched/export")
async def export_unmatched(format: str = "csv", current_user: User = Depends(get_current_user)):
    """Export unmatched records with quantity and amount for review."""
    try:
        from app.database import get_db, Unmatched
        db = next(get_db())
        # Export ALL unmatched records regardless of status so the file isn't empty unexpectedly
        records = db.query(Unmatched).all()
        export_data = [
            {
                "Pharmacy_Name": r.pharmacy_name,
                "Generated_ID": r.generated_id,
                "Product": getattr(r, "product", ""),
                "Quantity": int(getattr(r, "quantity", 0) or 0),
                "Amount": float(getattr(r, "amount", 0.0) or 0.0),
                "Status": r.status,
                "Created_At": r.created_at.isoformat() if r.created_at else ""
            }
            for r in records
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error preparing export: {str(e)}")
    finally:
        try:
            db.close()
        except Exception:
            pass

    # Ensure at least headers exist
    if not export_data:
        export_data = [{
            "Pharmacy_Name": "",
            "Generated_ID": "",
            "Product": "",
            "Quantity": 0,
            "Amount": 0.0,
            "Status": "",
            "Created_At": ""
        }]

    if format.lower() == "csv":
        import io, csv
        from fastapi.responses import Response
        output = io.StringIO()
        fieldnames = ["Pharmacy_Name","Generated_ID","Product","Quantity","Amount","Status","Created_At"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(export_data)
        return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=unmatched_records.csv"})
    elif format.lower() == "xlsx":
        import io
        from fastapi.responses import Response
        df = pd.DataFrame(export_data)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        return Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=unmatched_records.xlsx"})
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'xlsx'")

@app.post("/api/v1/unmatched/{record_id}/map")
async def map_record(record_id: int, mapping_data: Dict = Body(...), current_user: User = Depends(get_current_user)):
    """Map an unmatched record to a master pharmacy and create invoice for analytics"""
    try:
        from app.database import get_db, Unmatched, MasterMapping, Invoice
        
        master_pharmacy_id = mapping_data.get("master_pharmacy_id")
        if not master_pharmacy_id:
            raise HTTPException(status_code=400, detail="master_pharmacy_id is required")
        
        # Get database session
        db = next(get_db())
        
        # Find the unmatched record
        unmatched_record = db.query(Unmatched).filter(Unmatched.id == record_id).first()
        if not unmatched_record:
            raise HTTPException(status_code=404, detail="Unmatched record not found")
        
        # Import normalize_product_name for matching
        from app.tasks_enhanced import normalize_product_name
        
        # Normalize pharmacy_id and product for matching
        normalized_pharmacy_id = str(master_pharmacy_id).replace('-', '_')
        unmatched_product = unmatched_record.product or ''
        normalized_unmatched_product = normalize_product_name(unmatched_product)
        
        # Find master record that matches BOTH pharmacy_id AND product
        # This is critical for analytics to work properly
        master_pharmacy = None
        master_records = db.query(MasterMapping).filter(
            MasterMapping.pharmacy_id == master_pharmacy_id
        ).all()
        
        # Try to find exact match on pharmacy + product
        for record in master_records:
            normalized_master_product = normalize_product_name(record.product_names or '')
            if normalized_master_product == normalized_unmatched_product:
                master_pharmacy = record
                break
        
        # If no exact product match, use the first master record for this pharmacy
        # (This handles cases where product names don't match exactly)
        if not master_pharmacy and master_records:
            master_pharmacy = master_records[0]
            logger.warning(f"Product mismatch for {unmatched_record.pharmacy_name}: unmatched product '{unmatched_product}' vs master product '{master_pharmacy.product_names}'. Using first master record.")
        
        if not master_pharmacy:
            raise HTTPException(status_code=404, detail="Master pharmacy not found")
        
        # Update the record - mapped_to should be a string (pharmacy_id)
        unmatched_record.status = "mapped"
        unmatched_record.mapped_to = str(master_pharmacy_id)
        
        # Create or update Master Data record for this newly mapped pharmacy+product combination
        # This ensures the mapped pharmacy appears in Master Data Management
        invoice_product = master_pharmacy.product_names if master_pharmacy.product_names else unmatched_product
        
        # Create TWO master mappings for proper matching:
        # 1. One with the master pharmacy_id (for display and standard matching)
        # 2. One with the original generated_id (for future invoice uploads with same name variations)
        
        # First: Check/create mapping with the master pharmacy_id
        existing_master = db.query(MasterMapping).filter(
            MasterMapping.pharmacy_id == normalized_pharmacy_id,
            MasterMapping.pharmacy_names == unmatched_record.pharmacy_name,
            MasterMapping.product_names == invoice_product
        ).first()
        
        if not existing_master:
            # Create new master mapping record with the master pharmacy_id
            new_master_mapping = MasterMapping(
                pharmacy_id=normalized_pharmacy_id,
                pharmacy_names=unmatched_record.pharmacy_name,
                product_names=invoice_product,
                product_id=master_pharmacy.product_id,
                product_price=master_pharmacy.product_price,
                doctor_names=master_pharmacy.doctor_names,
                doctor_id=master_pharmacy.doctor_id,
                rep_names=master_pharmacy.rep_names,
                hq=master_pharmacy.hq,
                area=master_pharmacy.area,
                source="manual_mapping"
            )
            db.add(new_master_mapping)
            logger.info(f"Created master mapping (MANUAL) for: {unmatched_record.pharmacy_name} + {invoice_product}")
        
        # Second: Create mapping with the original generated_id to handle future uploads
        # This ensures re-uploaded invoices with same pharmacy name will auto-match
        original_generated_id = unmatched_record.generated_id
        if original_generated_id and original_generated_id != 'INVALID' and original_generated_id != normalized_pharmacy_id:
            # Normalize the original generated_id
            normalized_generated_id = original_generated_id.replace('-', '_')
            
            existing_variant = db.query(MasterMapping).filter(
                MasterMapping.pharmacy_id == normalized_generated_id,
                MasterMapping.pharmacy_names == unmatched_record.pharmacy_name,
                MasterMapping.product_names == invoice_product
            ).first()
            
            if not existing_variant:
                # Create a mapping variant for the original generated_id
                variant_mapping = MasterMapping(
                    pharmacy_id=normalized_generated_id,  # Use the original generated_id
                    pharmacy_names=unmatched_record.pharmacy_name,
                    product_names=invoice_product,
                    product_id=master_pharmacy.product_id,
                    product_price=master_pharmacy.product_price,
                    doctor_names=master_pharmacy.doctor_names,
                    doctor_id=master_pharmacy.doctor_id,
                    rep_names=master_pharmacy.rep_names,
                    hq=master_pharmacy.hq,
                    area=master_pharmacy.area,
                    source="manual_mapping"
                )
                db.add(variant_mapping)
                logger.info(f"Created variant mapping for future uploads: {normalized_generated_id} + {invoice_product}")
        
        # Create Invoice record for analytics
        # Use the master product name to ensure proper matching in analytics
        user_id = current_user.id if hasattr(current_user, 'id') else unmatched_record.user_id or 1
        
        # Use master product name for invoice to ensure analytics matching works
        invoice_product = master_pharmacy.product_names if master_pharmacy.product_names else unmatched_product
        
        # Create invoice for each mapped record (allow multiple invoices for same pharmacy+product)
        # Use the actual amount from unmatched record if available, otherwise calculate
        quantity = int(unmatched_record.quantity or 0)
        if unmatched_record.amount:
            # Use the actual invoice amount from the unmatched record
            invoice_amount = float(unmatched_record.amount)
        else:
            # Fall back to calculated amount: Quantity × Master.Product_Price
            product_price = float(master_pharmacy.product_price or 0.0)
            invoice_amount = quantity * product_price
        
        invoice = Invoice(
            pharmacy_id=normalized_pharmacy_id,
            pharmacy_name=unmatched_record.pharmacy_name,
            product=invoice_product,  # Use master product name for proper matching
            quantity=quantity,
            amount=invoice_amount,  # Use actual amount from unmatched record
            user_id=user_id,
            master_mapping_id=master_pharmacy.id  # Link to specific master record (doctor)
        )
        db.add(invoice)
        logger.info(f"Created invoice for mapped record: {unmatched_record.pharmacy_name} + {invoice_product} -> {master_pharmacy_id} (Revenue: {invoice_amount})")
        
        db.commit()
        
        return {"success": True, "message": f"Record {record_id} mapped to master pharmacy {master_pharmacy_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error mapping record: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to map record: {str(e)}")
    finally:
        db.close()

@app.get("/api/v1/newly-mapped")
async def get_newly_mapped_records(current_user: User = Depends(get_current_user)):
    """Get newly mapped records with their mapping details"""
    try:
        from app.database import get_db, Unmatched, MasterMapping
        
        db = next(get_db())
        
        # Get all mapped records
        mapped_records = db.query(Unmatched).filter(
            Unmatched.status == "mapped"
        ).order_by(Unmatched.created_at.desc()).all()
        
        result = []
        for record in mapped_records:
            # Get master pharmacy details if mapped_to exists
            master_pharmacy = None
            if record.mapped_to:
                master_pharmacy = db.query(MasterMapping).filter(
                    MasterMapping.pharmacy_id == record.mapped_to
                ).first()
            
            result.append({
                "id": record.id,
                "original_pharmacy_name": record.pharmacy_name,
                "generated_id": record.generated_id,
                "product": getattr(record, "product", None),
                "quantity": int(getattr(record, "quantity", 0) or 0),
                "amount": float(getattr(record, "amount", 0.0) or 0.0),
                "mapped_to_pharmacy_id": record.mapped_to,
                "mapped_to_pharmacy_name": master_pharmacy.pharmacy_names if master_pharmacy else None,
                "mapped_to_product_name": master_pharmacy.product_names if master_pharmacy else None,
                "mapped_to_doctor_name": master_pharmacy.doctor_names if master_pharmacy else None,
                "mapped_to_rep_name": master_pharmacy.rep_names if master_pharmacy else None,
                "mapped_to_hq": master_pharmacy.hq if master_pharmacy else None,
                "mapped_to_area": master_pharmacy.area if master_pharmacy else None,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "mapped_at": record.created_at.isoformat() if record.created_at else None,  # Using created_at as mapped_at for now
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting newly mapped records: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting newly mapped records: {str(e)}")
    finally:
        db.close()

@app.put("/api/v1/newly-mapped/{record_id}")
async def update_mapping(record_id: int, update_data: Dict = Body(...), current_user: User = Depends(get_current_user)):
    """Update a mapping for a newly mapped record and update invoice for analytics"""
    try:
        from app.database import get_db, Unmatched, MasterMapping, Invoice
        
        db = next(get_db())
        
        master_pharmacy_id = update_data.get("master_pharmacy_id")
        if not master_pharmacy_id:
            raise HTTPException(status_code=400, detail="master_pharmacy_id is required")
        
        # Find the unmatched record
        unmatched_record = db.query(Unmatched).filter(Unmatched.id == record_id).first()
        if not unmatched_record:
            raise HTTPException(status_code=404, detail="Record not found")
        
        if unmatched_record.status != "mapped":
            raise HTTPException(status_code=400, detail="Record is not mapped")
        
        # Import normalize_product_name for matching
        from app.tasks_enhanced import normalize_product_name
        
        # Normalize pharmacy_id and product for matching
        normalized_pharmacy_id = str(master_pharmacy_id).replace('-', '_')
        unmatched_product = unmatched_record.product or ''
        normalized_unmatched_product = normalize_product_name(unmatched_product)
        
        # Find master record that matches BOTH pharmacy_id AND product
        # This is critical for analytics to work properly
        master_pharmacy = None
        master_records = db.query(MasterMapping).filter(
            MasterMapping.pharmacy_id == master_pharmacy_id
        ).all()
        
        # Try to find exact match on pharmacy + product
        for record in master_records:
            normalized_master_product = normalize_product_name(record.product_names or '')
            if normalized_master_product == normalized_unmatched_product:
                master_pharmacy = record
                break
        
        # If no exact product match, use the first master record for this pharmacy
        # (This handles cases where product names don't match exactly)
        if not master_pharmacy and master_records:
            master_pharmacy = master_records[0]
            logger.warning(f"Product mismatch for {unmatched_record.pharmacy_name}: unmatched product '{unmatched_product}' vs master product '{master_pharmacy.product_names}'. Using first master record.")
        
        if not master_pharmacy:
            raise HTTPException(status_code=404, detail="Master pharmacy not found")
        
        old_pharmacy_id = unmatched_record.mapped_to
        
        # Update the mapping
        unmatched_record.mapped_to = str(master_pharmacy_id)
        
        # Create or update Master Data record for this newly mapped pharmacy+product combination
        # This ensures the mapped pharmacy appears in Master Data Management
        invoice_product = master_pharmacy.product_names if master_pharmacy.product_names else unmatched_product
        
        # Create TWO master mappings for proper matching (same as in map endpoint)
        # First: Check/create mapping with the master pharmacy_id
        existing_master = db.query(MasterMapping).filter(
            MasterMapping.pharmacy_id == normalized_pharmacy_id,
            MasterMapping.pharmacy_names == unmatched_record.pharmacy_name,
            MasterMapping.product_names == invoice_product
        ).first()
        
        if not existing_master:
            # Create new master mapping record with the master pharmacy_id
            new_master_mapping = MasterMapping(
                pharmacy_id=normalized_pharmacy_id,
                pharmacy_names=unmatched_record.pharmacy_name,
                product_names=invoice_product,
                product_id=master_pharmacy.product_id,
                product_price=master_pharmacy.product_price,
                doctor_names=master_pharmacy.doctor_names,
                doctor_id=master_pharmacy.doctor_id,
                rep_names=master_pharmacy.rep_names,
                hq=master_pharmacy.hq,
                area=master_pharmacy.area,
                source="manual_mapping"
            )
            db.add(new_master_mapping)
            logger.info(f"Created master mapping (MANUAL) for: {unmatched_record.pharmacy_name} + {invoice_product}")
        
        # Second: Create mapping with the original generated_id for future uploads
        original_generated_id = unmatched_record.generated_id
        if original_generated_id and original_generated_id != 'INVALID' and original_generated_id != normalized_pharmacy_id:
            normalized_generated_id = original_generated_id.replace('-', '_')
            
            existing_variant = db.query(MasterMapping).filter(
                MasterMapping.pharmacy_id == normalized_generated_id,
                MasterMapping.pharmacy_names == unmatched_record.pharmacy_name,
                MasterMapping.product_names == invoice_product
            ).first()
            
            if not existing_variant:
                variant_mapping = MasterMapping(
                    pharmacy_id=normalized_generated_id,
                    pharmacy_names=unmatched_record.pharmacy_name,
                    product_names=invoice_product,
                    product_id=master_pharmacy.product_id,
                    product_price=master_pharmacy.product_price,
                    doctor_names=master_pharmacy.doctor_names,
                    doctor_id=master_pharmacy.doctor_id,
                    rep_names=master_pharmacy.rep_names,
                    hq=master_pharmacy.hq,
                    area=master_pharmacy.area,
                    source="manual_mapping"
                )
                db.add(variant_mapping)
                logger.info(f"Created variant mapping for future uploads: {normalized_generated_id} + {invoice_product}")
        
        # Update or create Invoice record for analytics
        user_id = current_user.id if hasattr(current_user, 'id') else unmatched_record.user_id or 1
        
        # Use master product name for invoice to ensure analytics matching works
        invoice_product = master_pharmacy.product_names if master_pharmacy.product_names else unmatched_product
        
        # Find existing invoice created from this unmatched record
        old_normalized_id = str(old_pharmacy_id).replace('-', '_') if old_pharmacy_id else normalized_pharmacy_id
        existing_invoice = db.query(Invoice).filter(
            Invoice.pharmacy_id == old_normalized_id,
            Invoice.pharmacy_name == unmatched_record.pharmacy_name,
            Invoice.user_id == user_id
        ).first()
        
        if existing_invoice:
            # Update existing invoice with new pharmacy and product
            quantity = int(unmatched_record.quantity or 0)
            # Use the actual amount from unmatched record if available, otherwise calculate
            if unmatched_record.amount:
                invoice_amount = float(unmatched_record.amount)
            else:
                product_price = float(master_pharmacy.product_price or 0.0)
                invoice_amount = quantity * product_price
            
            existing_invoice.pharmacy_id = normalized_pharmacy_id
            existing_invoice.product = invoice_product  # Use master product name
            existing_invoice.amount = invoice_amount  # Use actual amount from unmatched record
            existing_invoice.quantity = quantity
            existing_invoice.master_mapping_id = master_pharmacy.id  # Link to specific master record (doctor)
            logger.info(f"Updated invoice for remapped record: {unmatched_record.pharmacy_name} + {invoice_product} -> {master_pharmacy_id} (Revenue: {invoice_amount})")
        else:
            # Create new invoice
            quantity = int(unmatched_record.quantity or 0)
            # Use the actual amount from unmatched record if available, otherwise calculate
            if unmatched_record.amount:
                invoice_amount = float(unmatched_record.amount)
            else:
                product_price = float(master_pharmacy.product_price or 0.0)
                invoice_amount = quantity * product_price
            
            invoice = Invoice(
                pharmacy_id=normalized_pharmacy_id,
                pharmacy_name=unmatched_record.pharmacy_name,
                product=invoice_product,  # Use master product name
                quantity=quantity,
                amount=invoice_amount,  # Use actual amount from unmatched record
                user_id=user_id,
                master_mapping_id=master_pharmacy.id  # Link to specific master record (doctor)
            )
            db.add(invoice)
            logger.info(f"Created invoice for remapped record: {unmatched_record.pharmacy_name} + {invoice_product} -> {master_pharmacy_id} (Revenue: {invoice_amount})")
        
        db.commit()
        
        return {"success": True, "message": f"Mapping updated successfully to {master_pharmacy_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating mapping: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating mapping: {str(e)}")
    finally:
        db.close()

@app.delete("/api/v1/newly-mapped/{record_id}")
async def delete_mapping(record_id: int, current_user: User = Depends(get_current_user)):
    """Delete a mapping and revert record to unmatched status, remove from analytics"""
    try:
        from app.database import get_db, Unmatched, Invoice
        
        db = next(get_db())
        
        # Find the unmatched record
        unmatched_record = db.query(Unmatched).filter(Unmatched.id == record_id).first()
        if not unmatched_record:
            raise HTTPException(status_code=404, detail="Record not found")
        
        if unmatched_record.status != "mapped":
            raise HTTPException(status_code=400, detail="Record is not mapped")
        
        # Remove invoice created from this mapping (if exists)
        user_id = current_user.id if hasattr(current_user, 'id') else unmatched_record.user_id or 1
        mapped_pharmacy_id = unmatched_record.mapped_to
        
        if mapped_pharmacy_id:
            normalized_pharmacy_id = str(mapped_pharmacy_id).replace('-', '_')
            # Find and delete invoice created from this mapping
            # Try to find by pharmacy_id, pharmacy_name, and user_id (product might vary)
            invoices_to_delete = db.query(Invoice).filter(
                Invoice.pharmacy_id == normalized_pharmacy_id,
                Invoice.pharmacy_name == unmatched_record.pharmacy_name,
                Invoice.user_id == user_id
            ).all()
            
            # If multiple invoices found, try to match by product as well
            if len(invoices_to_delete) > 1:
                unmatched_product = unmatched_record.product or ''
                for inv in invoices_to_delete:
                    if inv.product == unmatched_product:
                        db.delete(inv)
                        logger.info(f"Deleted invoice for unmapped record: {unmatched_record.pharmacy_name} + {unmatched_product}")
                        break
            elif len(invoices_to_delete) == 1:
                db.delete(invoices_to_delete[0])
                logger.info(f"Deleted invoice for unmapped record: {unmatched_record.pharmacy_name}")
        
        # Revert to pending status and clear mapped_to
        unmatched_record.status = "pending"
        unmatched_record.mapped_to = None
        db.commit()
        
        return {"success": True, "message": "Mapping deleted successfully. Record reverted to unmatched status."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting mapping: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting mapping: {str(e)}")
    finally:
        db.close()

@app.post("/api/v1/unmatched/{record_id}/ignore")
async def ignore_record(record_id: int, current_user: User = Depends(get_current_user)):
    """Ignore an unmatched record"""
    try:
        from app.database import get_db, Unmatched
        
        # Get database session
        db = next(get_db())
        
        # Find the unmatched record
        unmatched_record = db.query(Unmatched).filter(Unmatched.id == record_id).first()
        if not unmatched_record:
            raise HTTPException(status_code=404, detail="Unmatched record not found")
        
        # Update the record
        unmatched_record.status = "ignored"
        db.commit()
        
        return {"success": True, "message": f"Record {record_id} ignored"}
        
    except Exception as e:
        print(f"Error ignoring record: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to ignore record")

# Upload management endpoints
@app.get("/api/v1/uploads/history")
async def get_upload_history(current_user: User = Depends(get_current_user)):
    """Get upload history for all file types"""
    all_uploads = []
    
    # Add invoice uploads
    for upload_id, upload_data in mock_data["invoice_uploads"].items():
        all_uploads.append({
            "upload_id": upload_id,
            "type": "invoice",
            "filename": upload_data["filename"],
            "uploaded_at": upload_data["uploaded_at"],
            "processed_by": upload_data["processed_by"],
            "processed_rows": upload_data["result"]["processed_rows"],
            "status": "completed" if upload_data["result"]["success"] else "failed"
        })
    
    # Add master uploads
    for upload_id, upload_data in mock_data["master_uploads"].items():
        all_uploads.append({
            "upload_id": upload_id,
            "type": "master",
            "filename": upload_data["filename"],
            "uploaded_at": upload_data["uploaded_at"],
            "processed_by": upload_data["processed_by"],
            "processed_rows": upload_data["result"]["processed_rows"],
            "status": "completed" if upload_data["result"]["success"] else "failed"
        })
    
    # Add enhanced uploads
    for upload_id, upload_data in mock_data["enhanced_uploads"].items():
        all_uploads.append({
            "upload_id": upload_id,
            "type": "enhanced",
            "filename": upload_data["filename"],
            "uploaded_at": upload_data["uploaded_at"],
            "processed_by": upload_data["processed_by"],
            "processed_rows": upload_data["result"]["processed_rows"],
            "status": "completed" if upload_data["result"]["success"] else "failed"
        })
    
    # Sort by upload time (newest first)
    all_uploads.sort(key=lambda x: x["uploaded_at"], reverse=True)
    
    return all_uploads

## Removed mock upload details endpoint returning in-memory data

# Export endpoints
@app.get("/api/v1/export/analytics-excel")
async def export_analytics_excel(current_user: User = Depends(get_current_user)):
    return {"message": "Analytics Excel export would be generated here"}

@app.get("/api/v1/export/raw-data-excel")
async def export_raw_data_excel(current_user: User = Depends(get_current_user)):
    return {"message": "Raw data Excel export would be generated here"}

@app.get("/api/v1/export/raw-data-csv")
async def export_raw_data_csv(current_user: User = Depends(get_current_user)):
    return {"message": "Raw data CSV export would be generated here"}

@app.get("/api/v1/export/analytics-pdf")
async def export_analytics_pdf(current_user: User = Depends(get_current_user)):
    return {"message": "Analytics PDF export would be generated here"}

# ML Model endpoints
@app.post("/api/v1/ml/initialize")
async def initialize_ml_models(current_user: User = Depends(get_current_user)):
    """Initialize ML models for pharmacy matching and anomaly detection"""
    try:
        from app.ml_models import MLModelManager
        from app.database import get_db, MasterMapping, Invoice
        
        db = next(get_db())
        
        # Get master pharmacy names with limit for performance
        master_data = db.query(MasterMapping).limit(5000).all()
        master_pharmacy_names = [record.pharmacy_names for record in master_data if record.pharmacy_names]
        
        # Get revenue data with limit for performance
        invoice_data = db.query(Invoice).limit(5000).all()
        revenue_data = pd.DataFrame([{
            'amount': record.amount,
            'quantity': record.quantity,
            'pharmacy_count': 1,
            'daily_avg': record.amount / record.quantity if record.quantity > 0 else 0
        } for record in invoice_data])
        
        # Initialize ML models
        ml_manager = MLModelManager()
        success = ml_manager.initialize_models(master_pharmacy_names, revenue_data)
        
        if success:
            ml_manager.save_all_models()
            return {"success": True, "message": "ML models initialized successfully"}
        else:
            return {"success": False, "message": "Failed to initialize ML models"}
            
    except Exception as e:
        return {"success": False, "message": f"Error initializing ML models: {str(e)}"}

@app.get("/api/v1/ml/status")
async def get_ml_status(current_user: User = Depends(get_current_user)):
    """Get ML models status"""
    try:
        from app.ml_models import MLModelManager
        
        ml_manager = MLModelManager()
        
        return {
            "pharmacy_matcher_trained": ml_manager.pharmacy_matcher.is_trained,
            "anomaly_detector_trained": ml_manager.anomaly_detector.is_trained,
            "models_directory": ml_manager.models_dir
        }
        
    except Exception as e:
        return {"error": f"Error getting ML status: {str(e)}"}

@app.get("/api/v1/ml/match-pharmacy")
async def match_pharmacy_ml(
    pharmacy_name: str,
    threshold: float = 0.7,
    current_user: User = Depends(get_current_user)
):
    """Use ML to match pharmacy names"""
    try:
        from app.ml_models import MLModelManager
        
        ml_manager = MLModelManager()
        ml_manager.load_all_models()
        
        if not ml_manager.pharmacy_matcher.is_trained:
            return {"error": "Pharmacy matcher not trained"}
        
        match = ml_manager.pharmacy_matcher.find_best_match(pharmacy_name, threshold)
        
        if match:
            return {
                "success": True,
                "match": match
            }
        else:
            return {
                "success": False,
                "message": "No match found above threshold"
            }
            
    except Exception as e:
        return {"error": f"Error matching pharmacy: {str(e)}"}

# Admin endpoints
@app.post("/api/v1/admin/clear-recent-uploads")
async def clear_recent_uploads_admin(current_user: User = Depends(get_current_user)):
    """Clear all recent uploads"""
    if current_user.role not in ['super_admin', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        from app.database import get_db, RecentUpload
        db = next(get_db())
        
        # Clear recent uploads
        db.query(RecentUpload).delete()
        
        db.commit()
        
        return {"message": "Recent uploads cleared successfully", "success": True}
        
    except Exception as e:
        print(f"Error clearing recent uploads: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing recent uploads: {str(e)}")
    finally:
        db.close()

@app.post("/api/v1/admin/reset-system")
async def reset_system_admin(current_user: User = Depends(get_current_user)):
    """Reset system data - clear all data except master data management and split rules"""
    if current_user.role not in ['super_admin', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        from app.database import get_db, Invoice, Unmatched, RecentUpload, AuditLog, ProductReference, MasterSplitRule
        db = next(get_db())
        
        # Capture counts before reset (should remain unchanged)
        product_data_count_before = db.query(ProductReference).count()
        split_rules_count_before = db.query(MasterSplitRule).count()
        
        # Clear all data tables except MasterMapping, ProductReference, and MasterSplitRule
        db.query(Invoice).delete()
        db.query(Unmatched).delete()
        db.query(RecentUpload).delete()
        db.query(AuditLog).delete()
        
        # Clear mock data
        global mock_data
        mock_data = {
            "revenue_data": [],
            "analysis_timestamp": None,
            "overrides": {},
            "analysis_data": {}
        }
        
        db.commit()
        
        # Re-check counts to ensure they're preserved
        product_data_count_after = db.query(ProductReference).count()
        split_rules_count_after = db.query(MasterSplitRule).count()
        
        return {
            "message": "System data reset successfully (Master data, Product data, and Split rules preserved)",
            "success": True,
            "product_data_preserved": product_data_count_after == product_data_count_before,
            "product_data_count": product_data_count_after,
            "split_rules_preserved": split_rules_count_after == split_rules_count_before,
            "split_rules_count": split_rules_count_after
        }
        
    except Exception as e:
        logger.error(f"Error resetting system: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting system: {str(e)}")
    finally:
        db.close()

@app.post("/api/v1/admin/reset-master-data")
async def reset_master_data_admin(current_user: User = Depends(get_current_user)):
    """Reset master data management only"""
    if current_user.role not in ['super_admin', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        from app.database import get_db, MasterMapping
        db = next(get_db())
        
        # Clear only MasterMapping table
        db.query(MasterMapping).delete()
        
        db.commit()
        
        return {"message": "Master data reset successfully", "success": True}
        
    except Exception as e:
        logger.error(f"Error resetting master data: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting master data: {str(e)}")
    finally:
        db.close()

# Unmatched Records Management

@app.post("/api/v1/unmatched/{record_id}/ignore")
async def ignore_unmatched_record(record_id: int, current_user: User = Depends(get_current_user)):
    """Ignore an unmatched record"""
    try:
        from app.database import get_db
        db = next(get_db())
        
        # Find the unmatched record
        unmatched_record = db.query(Unmatched).filter(Unmatched.id == record_id).first()
        if not unmatched_record:
            raise HTTPException(status_code=404, detail="Unmatched record not found")
        
        # Update the unmatched record
        unmatched_record.status = "ignored"
        
        db.commit()
        
        return {"message": "Record ignored successfully", "success": True}
        
    except Exception as e:
        print(f"Error ignoring record: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ignoring record: {str(e)}")
    finally:
        db.close()

@app.get("/api/v1/unmatched/master-pharmacies")
async def get_master_pharmacies(current_user: User = Depends(get_current_user)):
    """Get list of master pharmacies for mapping"""
    try:
        from app.database import get_db, MasterMapping
        db = next(get_db())
        
        # Get unique pharmacies from master data
        master_pharmacies = db.query(MasterMapping.pharmacy_id, MasterMapping.pharmacy_names).distinct().all()
        
        result = []
        for pharmacy_id, pharmacy_name in master_pharmacies:
            result.append({
                "pharmacy_id": pharmacy_id,
                "pharmacy_name": pharmacy_name
            })
        
        return result
        
    except Exception as e:
        print(f"Error getting master pharmacies: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting master pharmacies: {str(e)}")
    finally:
        db.close()

@app.get("/api/v1/master-data")
async def get_master_data(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get all master data with pagination"""
    try:
        from app.database import get_db, MasterMapping
        db = next(get_db())
        
        # Get total count
        total = db.query(MasterMapping).count()
        
        # Get paginated data
        master_records = db.query(MasterMapping).offset(skip).limit(limit).all()
        
        result = []
        for record in master_records:
            result.append({
                "id": record.id,
                "pharmacy_id": record.pharmacy_id,
                "pharmacy_names": record.pharmacy_names,
                "product_names": record.product_names,
                "product_id": record.product_id,
                "product_price": float(record.product_price) if record.product_price else None,
                "doctor_names": record.doctor_names,
                "doctor_id": record.doctor_id,
                "rep_names": record.rep_names,
                "hq": record.hq,
                "area": record.area,
                "source": getattr(record, "source", "file_upload")  # Default to file_upload for old records
            })
        
        return {
            "data": result,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting master data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting master data: {str(e)}")
    finally:
        db.close()

@app.post("/api/v1/master-data")
async def create_master_data(
    record_data: Dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Create a new master data record"""
    try:
        from app.database import get_db, MasterMapping
        db = next(get_db())
        
        # Validate required fields
        if not record_data.get("pharmacy_id") or not record_data.get("pharmacy_names"):
            raise HTTPException(status_code=400, detail="pharmacy_id and pharmacy_names are required")
        
        # Create new master mapping record
        new_record = MasterMapping(
            pharmacy_id=record_data.get("pharmacy_id"),
            pharmacy_names=record_data.get("pharmacy_names"),
            product_names=record_data.get("product_names"),
            product_id=record_data.get("product_id"),
            product_price=record_data.get("product_price"),
            doctor_names=record_data.get("doctor_names"),
            doctor_id=record_data.get("doctor_id"),
            rep_names=record_data.get("rep_names"),
            hq=record_data.get("hq"),
            area=record_data.get("area")
        )
        
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        
        return {
            "id": new_record.id,
            "pharmacy_id": new_record.pharmacy_id,
            "pharmacy_names": new_record.pharmacy_names,
            "product_names": new_record.product_names,
            "product_id": new_record.product_id,
            "product_price": float(new_record.product_price) if new_record.product_price else None,
            "doctor_names": new_record.doctor_names,
            "doctor_id": new_record.doctor_id,
            "rep_names": new_record.rep_names,
            "hq": new_record.hq,
            "area": new_record.area,
            "source": getattr(new_record, "source", "file_upload")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating master data: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating master data: {str(e)}")
    finally:
        db.close()

@app.put("/api/v1/master-data/{record_id}")
async def update_master_data(
    record_id: int,
    update_data: Dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Update a master data record"""
    try:
        from app.database import get_db, MasterMapping
        db = next(get_db())
        
        # Get the record
        record = db.query(MasterMapping).filter(MasterMapping.id == record_id).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="Master data record not found")
        
        # Update fields
        if "pharmacy_id" in update_data:
            record.pharmacy_id = update_data["pharmacy_id"]
        if "pharmacy_names" in update_data:
            record.pharmacy_names = update_data["pharmacy_names"]
        if "product_names" in update_data:
            record.product_names = update_data["product_names"]
        if "product_id" in update_data:
            record.product_id = update_data["product_id"]
        if "product_price" in update_data:
            record.product_price = update_data["product_price"]
        if "doctor_names" in update_data:
            record.doctor_names = update_data["doctor_names"]
        if "doctor_id" in update_data:
            record.doctor_id = update_data["doctor_id"]
        if "rep_names" in update_data:
            record.rep_names = update_data["rep_names"]
        if "hq" in update_data:
            record.hq = update_data["hq"]
        if "area" in update_data:
            record.area = update_data["area"]
        
        db.commit()
        db.refresh(record)
        
        return {
            "id": record.id,
            "pharmacy_id": record.pharmacy_id,
            "pharmacy_names": record.pharmacy_names,
            "product_names": record.product_names,
            "product_id": record.product_id,
            "product_price": float(record.product_price) if record.product_price else None,
            "doctor_names": record.doctor_names,
            "doctor_id": record.doctor_id,
            "rep_names": record.rep_names,
            "hq": record.hq,
            "area": record.area,
            "source": getattr(record, "source", "file_upload")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating master data: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating master data: {str(e)}")
    finally:
        db.close()

@app.delete("/api/v1/master-data/{record_id}")
async def delete_master_data(
    record_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a master data record"""
    try:
        from app.database import get_db, MasterMapping
        db = next(get_db())
        
        # Get the record
        record = db.query(MasterMapping).filter(MasterMapping.id == record_id).first()
        
        if not record:
            raise HTTPException(status_code=404, detail="Master data record not found")
        
        db.delete(record)
        db.commit()
        
        return {"message": "Master data record deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting master data: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting master data: {str(e)}")
    finally:
        db.close()

# Split Rule Management Endpoints
@app.get("/api/v1/master-data/duplicates")
async def get_duplicate_master_combinations(current_user: User = Depends(get_current_user)):
    """Get all pharmacy+product combinations that have multiple master records"""
    try:
        from app.database import get_db, MasterMapping
        from sqlalchemy import func
        from app.tasks_enhanced import normalize_product_name
        
        db = next(get_db())
        
        # Get all master records
        all_records = db.query(MasterMapping).all()
        
        # Group by pharmacy_id + normalized_product
        combinations = {}
        for record in all_records:
            normalized_product = normalize_product_name(record.product_names)
            key = f"{record.pharmacy_id}|{normalized_product}"
            
            if key not in combinations:
                combinations[key] = {
                    "pharmacy_id": record.pharmacy_id,
                    "pharmacy_name": record.pharmacy_names,
                    "product_name": record.product_names,
                    "normalized_product": normalized_product,
                    "records": []
                }
            
            combinations[key]["records"].append({
                "id": record.id,
                "doctor_name": record.doctor_names,
                "doctor_id": record.doctor_id,
                "rep_name": record.rep_names,
                "hq": record.hq,
                "area": record.area,
                "price": float(record.product_price) if record.product_price else 0.0
            })
        
        # Filter to only duplicates
        duplicates = [combo for combo in combinations.values() if len(combo["records"]) > 1]
        
        logger.info(f"Found {len(duplicates)} duplicate pharmacy+product combinations")
        
        return {"duplicates": duplicates, "total": len(duplicates)}
        
    except Exception as e:
        logger.error(f"Error fetching duplicates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching duplicates: {str(e)}")
    finally:
        db.close()

@app.get("/api/v1/split-rules")
async def get_split_rules(current_user: User = Depends(get_current_user)):
    """Get all split rules"""
    try:
        from app.database import get_db, MasterSplitRule
        db = next(get_db())
        
        rules = db.query(MasterSplitRule).all()
        
        result = []
        for rule in rules:
            result.append({
                "id": rule.id,
                "pharmacy_id": rule.pharmacy_id,
                "product_key": rule.product_key,
                "rules": rule.rules,
                "updated_by": rule.updated_by,
                "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
                "created_at": rule.created_at.isoformat() if rule.created_at else None
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching split rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching split rules: {str(e)}")
    finally:
        db.close()

@app.post("/api/v1/split-rules")
async def create_split_rule(
    rule_data: Dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Create or update a split rule and retroactively apply to existing invoices"""
    try:
        from app.database import get_db, MasterSplitRule, MasterMapping, Invoice
        from app.tasks_enhanced import normalize_product_name
        db = next(get_db())
        
        pharmacy_id = rule_data.get("pharmacy_id")
        product_key = rule_data.get("product_key")
        rules = rule_data.get("rules", [])
        
        if not pharmacy_id or not product_key:
            raise HTTPException(status_code=400, detail="pharmacy_id and product_key are required")
        
        if not rules or not isinstance(rules, list):
            raise HTTPException(status_code=400, detail="rules must be a non-empty list")
        
        # Validate rules format and sum to 100
        total_ratio = 0
        for entry in rules:
            if "master_mapping_id" not in entry or "ratio" not in entry:
                raise HTTPException(status_code=400, detail="Each rule must have master_mapping_id and ratio")
            total_ratio += entry.get("ratio", 0)
        
        if abs(total_ratio - 100) > 0.1:
            raise HTTPException(status_code=400, detail=f"Ratios must sum to 100% (current: {total_ratio}%)")
        
        # Get master records for validation
        master_record_map = {}
        for entry in rules:
            master_rec = db.query(MasterMapping).filter_by(id=entry["master_mapping_id"]).first()
            if not master_rec:
                raise HTTPException(status_code=400, detail=f"Master mapping ID {entry['master_mapping_id']} not found")
            master_record_map[entry["master_mapping_id"]] = master_rec
        
        # Check if rule already exists
        existing_rule = db.query(MasterSplitRule).filter_by(
            pharmacy_id=pharmacy_id,
            product_key=product_key
        ).first()
        
        if existing_rule:
            # Update existing rule
            existing_rule.rules = rules
            existing_rule.updated_by = current_user.id
            existing_rule.updated_at = datetime.utcnow()
            message = "Split rule updated and applied to existing invoices"
        else:
            # Create new rule
            new_rule = MasterSplitRule(
                pharmacy_id=pharmacy_id,
                product_key=product_key,
                rules=rules,
                updated_by=current_user.id
            )
            db.add(new_rule)
            message = "Split rule created and applied to existing invoices"
        
        db.commit()
        
        # Retroactively apply to existing invoices
        # Extract normalized product from product_key (format: "pharmacy_id|EXACT|normalized_product")
        parts = product_key.split("|")
        if len(parts) >= 3:
            match_type = parts[1]  # EXACT or PID
            if match_type == "EXACT":
                normalized_product = parts[2]
            else:
                # For PID matches, we need to get the product from master records
                normalized_product = normalize_product_name(list(master_record_map.values())[0].product_names)
        else:
            normalized_product = ""
        
        # Find all invoices for this pharmacy that match the product
        from app.tasks_enhanced import normalize_product_name as norm_prod
        existing_invoices = db.query(Invoice).filter_by(pharmacy_id=pharmacy_id).all()
        
        invoices_to_split = []
        for inv in existing_invoices:
            inv_normalized = norm_prod(inv.product)
            if inv_normalized == normalized_product:
                invoices_to_split.append(inv)
        
        if invoices_to_split:
            logger.info(f"Retroactively applying split rule to {len(invoices_to_split)} existing invoices")
            
            # Delete old invoices and create split ones
            for old_invoice in invoices_to_split:
                quantity = old_invoice.quantity
                total_amount = old_invoice.amount
                pharmacy_name = old_invoice.pharmacy_name
                product = old_invoice.product
                user_id = old_invoice.user_id
                invoice_date = old_invoice.invoice_date
                
                # Delete old invoice
                db.delete(old_invoice)
                
                # Create split invoices
                for entry in rules:
                    master_record = master_record_map.get(entry["master_mapping_id"])
                    if not master_record:
                        continue
                    
                    ratio = entry.get("ratio", 0) / 100.0  # Convert to decimal
                    allocated_quantity = int(quantity * ratio)
                    allocated_amount = total_amount * ratio
                    
                    new_invoice = Invoice(
                        pharmacy_id=pharmacy_id,
                        pharmacy_name=pharmacy_name,
                        product=product,
                        quantity=allocated_quantity,
                        amount=allocated_amount,
                        user_id=user_id,
                        invoice_date=invoice_date,
                        created_at=old_invoice.created_at,
                        master_mapping_id=master_record.id  # Link to specific master record (doctor)
                    )
                    db.add(new_invoice)
            
            db.commit()
            logger.info(f"Split {len(invoices_to_split)} existing invoices into {len(invoices_to_split) * len(rules)} new invoices")
            message += f" ({len(invoices_to_split)} existing invoices reprocessed)"
        
        # Clear analytics cache to force refresh
        try:
            import redis
            redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
            # Clear all analytics cache keys for all users
            cache_keys = redis_client.keys("analytics_*")
            if cache_keys:
                redis_client.delete(*cache_keys)
                logger.info(f"Cleared {len(cache_keys)} analytics cache keys after split rule update")
        except Exception as cache_error:
            # Redis might not be available, log but don't fail
            logger.warning(f"Could not clear analytics cache: {str(cache_error)}")
        
        return {"message": message, "invoices_reprocessed": len(invoices_to_split)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/updating split rule: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating/updating split rule: {str(e)}")
    finally:
        db.close()

@app.delete("/api/v1/split-rules/{rule_id}")
async def delete_split_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a split rule"""
    try:
        from app.database import get_db, MasterSplitRule
        db = next(get_db())
        
        rule = db.query(MasterSplitRule).filter(MasterSplitRule.id == rule_id).first()
        
        if not rule:
            raise HTTPException(status_code=404, detail="Split rule not found")
        
        db.delete(rule)
        db.commit()
        
        # Clear analytics cache to force refresh
        try:
            import redis
            redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
            # Clear all analytics cache keys for all users
            cache_keys = redis_client.keys("analytics_*")
            if cache_keys:
                redis_client.delete(*cache_keys)
                logger.info(f"Cleared {len(cache_keys)} analytics cache keys after split rule deletion")
        except Exception as cache_error:
            # Redis might not be available, log but don't fail
            logger.warning(f"Could not clear analytics cache: {str(cache_error)}")
        
        return {"message": "Split rule deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting split rule: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting split rule: {str(e)}")
    finally:
        db.close()

@app.get("/api/v1/split-rules/export")
async def export_split_rules(format: str = "xlsx", current_user: User = Depends(get_current_user)):
    """Export all split rules to Excel or CSV for backup"""
    try:
        from app.database import get_db, MasterSplitRule, MasterMapping
        from fastapi.responses import Response
        import io
        import json
        
        db = next(get_db())
        
        # Get all split rules
        rules = db.query(MasterSplitRule).all()
        
        export_data = []
        for rule in rules:
            # Get master records to get doctor names
            master_records = {}
            if rule.rules:
                for rule_entry in rule.rules:
                    master_id = rule_entry.get("master_mapping_id")
                    if master_id:
                        master = db.query(MasterMapping).filter(MasterMapping.id == master_id).first()
                        if master:
                            master_records[master_id] = master
            
            # Build export rows - one per doctor in the rule
            for rule_entry in (rule.rules or []):
                master_id = rule_entry.get("master_mapping_id")
                ratio = rule_entry.get("ratio", 0)
                master = master_records.get(master_id)
                
                export_data.append({
                    "Pharmacy_ID": rule.pharmacy_id or "",
                    "Product_Key": rule.product_key or "",
                    "Master_Mapping_ID": master_id,
                    "Doctor_Name": master.doctor_names if master else "",
                    "Doctor_ID": master.doctor_id if master else "",
                    "Ratio_Percentage": ratio,
                    "Updated_By": rule.updated_by or "",
                    "Updated_At": rule.updated_at.isoformat() if rule.updated_at else "",
                    "Created_At": rule.created_at.isoformat() if rule.created_at else ""
                })
        
        db.close()
        
        if not export_data:
            raise HTTPException(status_code=404, detail="No split rules found to export")
        
        if format.lower() == "csv":
            import csv
            output = io.StringIO()
            fieldnames = ["Pharmacy_ID", "Product_Key", "Master_Mapping_ID", "Doctor_Name", "Doctor_ID", 
                         "Ratio_Percentage", "Updated_By", "Updated_At", "Created_At"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(export_data)
            return Response(
                content=output.getvalue(), 
                media_type="text/csv", 
                headers={"Content-Disposition": "attachment; filename=split_rules_backup.csv"}
            )
        elif format.lower() == "xlsx":
            df = pd.DataFrame(export_data)
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            return Response(
                content=output.getvalue(), 
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                headers={"Content-Disposition": "attachment; filename=split_rules_backup.xlsx"}
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'xlsx'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting split rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting split rules: {str(e)}")
    finally:
        try:
            db.close()
        except Exception:
            pass

@app.post("/api/v1/split-rules/import")
async def import_split_rules(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Import split rules from Excel file"""
    try:
        from app.database import get_db, MasterSplitRule, MasterMapping
        import io
        
        db = next(get_db())
        
        # Read Excel file
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')
        
        # Required columns
        required_columns = ["Pharmacy_ID", "Product_Key", "Master_Mapping_ID", "Ratio_Percentage"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Group by Pharmacy_ID + Product_Key to create split rules
        rules_by_key = {}
        errors = []
        imported_count = 0
        updated_count = 0
        
        for idx, row in df.iterrows():
            try:
                pharmacy_id = str(row["Pharmacy_ID"]).strip()
                product_key = str(row["Product_Key"]).strip()
                master_mapping_id = int(row["Master_Mapping_ID"])
                ratio = float(row["Ratio_Percentage"])
                
                # Validate master mapping exists
                master = db.query(MasterMapping).filter(MasterMapping.id == master_mapping_id).first()
                if not master:
                    errors.append(f"Row {idx + 2}: Master mapping ID {master_mapping_id} not found")
                    continue
                
                # Group by pharmacy_id + product_key
                key = f"{pharmacy_id}|{product_key}"
                if key not in rules_by_key:
                    rules_by_key[key] = {
                        "pharmacy_id": pharmacy_id,
                        "product_key": product_key,
                        "rules": []
                    }
                
                rules_by_key[key]["rules"].append({
                    "master_mapping_id": master_mapping_id,
                    "ratio": ratio
                })
                
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
                continue
        
        # Create or update split rules
        for key, rule_data in rules_by_key.items():
            # Validate ratios sum to 100
            total_ratio = sum(r["ratio"] for r in rule_data["rules"])
            if abs(total_ratio - 100) > 0.1:
                errors.append(f"Pharmacy {rule_data['pharmacy_id']} + Product {rule_data['product_key']}: Ratios sum to {total_ratio}% (must be 100%)")
                continue
            
            # Check if rule exists
            existing_rule = db.query(MasterSplitRule).filter_by(
                pharmacy_id=rule_data["pharmacy_id"],
                product_key=rule_data["product_key"]
            ).first()
            
            if existing_rule:
                # Update existing rule
                existing_rule.rules = rule_data["rules"]
                existing_rule.updated_by = current_user.id
                existing_rule.updated_at = datetime.utcnow()
                updated_count += 1
            else:
                # Create new rule
                new_rule = MasterSplitRule(
                    pharmacy_id=rule_data["pharmacy_id"],
                    product_key=rule_data["product_key"],
                    rules=rule_data["rules"],
                    updated_by=current_user.id
                )
                db.add(new_rule)
                imported_count += 1
        
        db.commit()
        
        message = f"Import completed: {imported_count} new rules, {updated_count} updated rules"
        if errors:
            message += f". {len(errors)} errors occurred."
        
        return {
            "message": message,
            "imported": imported_count,
            "updated": updated_count,
            "errors": errors[:10]  # Return first 10 errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing split rules: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error importing split rules: {str(e)}")
    finally:
        db.close()

@app.get("/api/v1/master-data/unique-values")
async def get_master_data_unique_values(current_user: User = Depends(get_current_user)):
    """Get unique values for all master data fields for dropdowns with mappings"""
    try:
        from app.database import get_db, MasterMapping
        from sqlalchemy import func
        
        db = next(get_db())
        
        # Get all records to build mappings
        all_records = db.query(MasterMapping).all()
        
        # Build mappings for auto-fill
        pharmacy_id_to_name = {}  # pharmacy_id -> pharmacy_name
        pharmacy_name_to_id = {}  # pharmacy_name -> pharmacy_id
        product_name_to_id = {}   # product_name -> product_id
        product_id_to_name = {}   # product_id -> product_name
        doctor_name_to_id = {}    # doctor_name -> doctor_id
        doctor_id_to_name = {}    # doctor_id -> doctor_name
        
        for record in all_records:
            # Pharmacy mappings
            if record.pharmacy_id and record.pharmacy_names:
                pharmacy_id_to_name[record.pharmacy_id] = record.pharmacy_names
                pharmacy_name_to_id[record.pharmacy_names] = record.pharmacy_id
            
            # Product mappings
            if record.product_names and record.product_id:
                product_name_to_id[record.product_names] = record.product_id
                product_id_to_name[record.product_id] = record.product_names
            
            # Doctor mappings
            if record.doctor_names and record.doctor_id:
                doctor_name_to_id[record.doctor_names] = record.doctor_id
                doctor_id_to_name[record.doctor_id] = record.doctor_names
        
        # Get unique values
        pharmacy_ids = db.query(MasterMapping.pharmacy_id).distinct().all()
        unique_pharmacy_ids = sorted([p[0] for p in pharmacy_ids if p[0]])
        
        pharmacy_names = db.query(MasterMapping.pharmacy_names).distinct().all()
        unique_pharmacy_names = sorted([p[0] for p in pharmacy_names if p[0]])
        
        product_names = db.query(MasterMapping.product_names).distinct().all()
        unique_product_names = sorted([p[0] for p in product_names if p[0]])
        
        product_ids = db.query(MasterMapping.product_id).distinct().all()
        unique_product_ids = sorted([p[0] for p in product_ids if p[0]])
        
        doctor_names = db.query(MasterMapping.doctor_names).distinct().all()
        unique_doctor_names = sorted([d[0] for d in doctor_names if d[0]])
        
        doctor_ids = db.query(MasterMapping.doctor_id).distinct().all()
        unique_doctor_ids = sorted([d[0] for d in doctor_ids if d[0]])
        
        rep_names = db.query(MasterMapping.rep_names).distinct().all()
        unique_rep_names = sorted([r[0] for r in rep_names if r[0]])
        
        hqs = db.query(MasterMapping.hq).distinct().all()
        unique_hqs = sorted([h[0] for h in hqs if h[0]])
        
        areas = db.query(MasterMapping.area).distinct().all()
        unique_areas = sorted([a[0] for a in areas if a[0]])
        
        db.close()
        
        return {
            "pharmacy_ids": unique_pharmacy_ids,
            "pharmacy_names": unique_pharmacy_names,
            "product_names": unique_product_names,
            "product_ids": unique_product_ids,
            "doctor_names": unique_doctor_names,
            "doctor_ids": unique_doctor_ids,
            "rep_names": unique_rep_names,
            "hqs": unique_hqs,
            "areas": unique_areas,
            "mappings": {
                "pharmacy_id_to_name": pharmacy_id_to_name,
                "pharmacy_name_to_id": pharmacy_name_to_id,
                "product_name_to_id": product_name_to_id,
                "product_id_to_name": product_id_to_name,
                "doctor_name_to_id": doctor_name_to_id,
                "doctor_id_to_name": doctor_id_to_name,
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting unique values: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting unique values: {str(e)}")
    finally:
        try:
            db.close()
        except Exception:
            pass

@app.get("/api/v1/master-data/export")
async def export_master_data(format: str = "xlsx", current_user: User = Depends(get_current_user)):
    """Export all master data to Excel or CSV for backup"""
    try:
        from app.database import get_db, MasterMapping
        from fastapi.responses import Response
        import io
        
        db = next(get_db())
        
        # Get ALL master data records
        records = db.query(MasterMapping).all()
        
        export_data = [
            {
                "Pharmacy_ID": r.pharmacy_id,
                "Pharmacy_Name": r.pharmacy_names,
                "Product_Name": r.product_names or "",
                "Product_ID": r.product_id or "",
                "Product_Price": float(r.product_price) if r.product_price else 0.0,
                "Doctor_Name": r.doctor_names or "",
                "Doctor_ID": r.doctor_id or "",
                "Rep_Name": r.rep_names or "",
                "HQ": r.hq or "",
                "Area": r.area or "",
                "Source": getattr(r, "source", "file_upload"),
                "Created_At": r.created_at.isoformat() if r.created_at else ""
            }
            for r in records
        ]
        
        db.close()
        
        # Ensure at least headers exist
        if not export_data:
            export_data = [{
                "Pharmacy_ID": "",
                "Pharmacy_Name": "",
                "Product_Name": "",
                "Product_ID": "",
                "Product_Price": 0.0,
                "Doctor_Name": "",
                "Doctor_ID": "",
                "Rep_Name": "",
                "HQ": "",
                "Area": "",
                "Source": "",
                "Created_At": ""
            }]
        
        if format.lower() == "csv":
            import csv
            output = io.StringIO()
            fieldnames = ["Pharmacy_ID", "Pharmacy_Name", "Product_Name", "Product_ID", "Product_Price", 
                         "Doctor_Name", "Doctor_ID", "Rep_Name", "HQ", "Area", "Source", "Created_At"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(export_data)
            return Response(
                content=output.getvalue(), 
                media_type="text/csv", 
                headers={"Content-Disposition": "attachment; filename=master_data_backup.csv"}
            )
        elif format.lower() == "xlsx":
            df = pd.DataFrame(export_data)
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            return Response(
                content=output.getvalue(), 
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                headers={"Content-Disposition": "attachment; filename=master_data_backup.xlsx"}
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'xlsx'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting master data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting master data: {str(e)}")
    finally:
        try:
            db.close()
        except Exception:
            pass

# Recent Uploads Management
@app.get("/api/v1/uploads/{upload_id}/details")
async def get_upload_details(upload_id: int, current_user: User = Depends(get_current_user)):
    """Get detailed information about a specific upload"""
    try:
        from app.database import get_db, RecentUpload, Unmatched
        db = next(get_db())
        
        # Get the upload record - for now, allow all users to access all uploads
        upload = db.query(RecentUpload).filter(RecentUpload.id == upload_id).first()
        
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        # Get unmatched records for this upload
        unmatched_records = db.query(Unmatched).filter(
            Unmatched.user_id == current_user.id
        ).limit(10).all()
        
        unmatched_preview = []
        for record in unmatched_records:
            unmatched_preview.append({
                "id": record.id,
                "pharmacy_name": record.pharmacy_name,
                "generated_id": record.generated_id,
                "status": record.status,
                "created_at": record.created_at.isoformat()
            })
        
        return {
            "id": upload.id,
            "file_name": upload.file_name,
            "file_type": upload.file_type,
            "uploaded_at": upload.uploaded_at.isoformat(),
            "status": upload.status,
            "processed_rows": upload.processed_rows,
            "total_revenue": float(upload.total_revenue or 0),
            "total_pharmacies": upload.total_pharmacies or 0,
            "total_doctors": upload.total_doctors or 0,
            "growth_rate": float(upload.growth_rate or 0),
            "matched_count": upload.matched_count or 0,
            "unmatched_count": upload.unmatched_count or 0,
            "unmatched_preview": unmatched_preview
        }
        
    except Exception as e:
        print(f"Error getting upload details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting upload details: {str(e)}")
    finally:
        db.close()

@app.delete("/api/v1/uploads/{upload_id}")
async def delete_upload(upload_id: int, current_user: User = Depends(get_current_user)):
    """Delete a specific upload"""
    try:
        from app.database import get_db, RecentUpload
        db = next(get_db())
        
        # Get the upload record (for admin users, allow access to all uploads)
        if current_user.role in ['super_admin', 'admin']:
            upload = db.query(RecentUpload).filter(RecentUpload.id == upload_id).first()
        else:
            upload = db.query(RecentUpload).filter(
                RecentUpload.id == upload_id,
                RecentUpload.user_id == current_user.id
            ).first()
        
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        # Delete the upload
        db.delete(upload)
        db.commit()
        
        return {"message": "Upload deleted successfully", "success": True}
        
    except Exception as e:
        print(f"Error deleting upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting upload: {str(e)}")
    finally:
        db.close()

@app.get("/api/v1/uploads/{upload_id}/export")
async def export_upload_data(upload_id: int, format: str = 'csv', current_user: User = Depends(get_current_user)):
    """Export data for a specific upload"""
    try:
        from app.database import get_db
        from app.tasks_enhanced import get_matched_results_with_doctor_info
        import io
        import csv
        
        db = next(get_db())
        
        # Get the upload record
        upload = db.query(RecentUpload).filter(
            RecentUpload.id == upload_id,
            RecentUpload.user_id == current_user.id
        ).first()
        
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        # Get matched results for this analysis
        matched_results = get_matched_results_with_doctor_info(db, current_user.id)
        
        if format.lower() == 'csv':
            # Create CSV
            output = io.StringIO()
            if matched_results:
                fieldnames = matched_results[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(matched_results)
            
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=analysis_{upload_id}.csv"}
            )
        else:
            # For Excel format, return CSV for now (Excel export can be added later)
            output = io.StringIO()
            if matched_results:
                fieldnames = matched_results[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(matched_results)
            
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=analysis_{upload_id}.xlsx"}
            )
        
    except Exception as e:
        print(f"Error exporting upload data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error exporting upload data: {str(e)}")
    finally:
        db.close()

# ID Generation API endpoints
@app.post("/api/v1/generator/generate", response_model=IdGenerationResponse)
async def generate_id_endpoint(request: IdGenerationRequest, current_user: User = Depends(get_current_user)):
    """Generate a standardized ID for pharmacy, product, or doctor"""
    db = None
    try:
        from app.database import get_db
        
        if request.type not in ['pharmacy', 'product', 'doctor']:
            raise HTTPException(status_code=400, detail="Invalid type. Must be 'pharmacy', 'product', or 'doctor'")
        
        if not request.name or not request.name.strip():
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        
        db = next(get_db())
        
        if request.type == 'product':
            # Product ID generation requires reference table matching
            from app.product_id_generator import generate_product_id
            product_id, price, matched_original = generate_product_id(request.name.strip(), db)
            
            if product_id:
                generated_id = str(product_id)
                # Include price and matched name in response
                return IdGenerationResponse(
                    original_name=request.name.strip(),
                    generated_id=generated_id,
                    type=request.type,
                    timestamp=datetime.now().isoformat(),
                    metadata={"price": price, "matched_original": matched_original} if matched_original else None
                )
            else:
                raise HTTPException(status_code=404, detail=f"Product '{request.name.strip()}' not found in reference table. Please upload product reference table first.")
        
        elif request.type == 'doctor':
            # Doctor ID generation with counter
            generated_id = generate_id(request.name.strip(), request.type, db)
        else:
            # Pharmacy ID generation
            generated_id = generate_id(request.name.strip(), request.type, db)
        
        return IdGenerationResponse(
            original_name=request.name.strip(),
            generated_id=generated_id,
            type=request.type,
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating ID: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating ID: {str(e)}")
    finally:
        if db:
            db.close()

@app.post("/api/v1/generator/batch", response_model=List[IdGenerationResponse])
async def generate_batch_ids(requests: List[IdGenerationRequest], current_user: User = Depends(get_current_user)):
    """Generate multiple IDs in batch"""
    db = None
    try:
        from app.database import get_db
        db = next(get_db())
        
        results = []
        for request in requests:
            if request.type not in ['pharmacy', 'product', 'doctor']:
                continue
            
            if not request.name or not request.name.strip():
                continue
            
            if request.type == 'product':
                from app.product_id_generator import generate_product_id
                product_id, price, matched_original = generate_product_id(request.name.strip(), db)
                if product_id:
                    results.append(IdGenerationResponse(
                        original_name=request.name.strip(),
                        generated_id=str(product_id),
                        type=request.type,
                        timestamp=datetime.now().isoformat(),
                        metadata={"price": price, "matched_original": matched_original} if matched_original else None
                    ))
            else:
                generated_id = generate_id(request.name.strip(), request.type, db)
            results.append(IdGenerationResponse(
                original_name=request.name.strip(),
                generated_id=generated_id,
                type=request.type,
                timestamp=datetime.now().isoformat()
            ))
        
        return results
    
    except Exception as e:
        logger.error(f"Error generating batch IDs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating batch IDs: {str(e)}")
    finally:
        if db:
            db.close()

@app.post("/api/v1/generator/upload-product-reference")
async def upload_product_reference(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload product reference table Excel file (Product Name, mprice columns)"""
    try:
        from app.database import get_db, ProductReference
        import tempfile
        import os
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="File must be an Excel file")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Read Excel file
            df = pd.read_excel(tmp_file_path, engine='openpyxl')
            
            # Find columns (flexible naming)
            product_col = None
            price_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'product' in col_lower and 'name' in col_lower:
                    product_col = col
                elif 'mprice' in col_lower or ('price' in col_lower and 'm' in col_lower):
                    price_col = col
            
            if not product_col or not price_col:
                raise HTTPException(status_code=400, detail="Excel file must contain 'Product Name' and 'mprice' columns")
            
            db = next(get_db())
            
            try:
                # Clear existing reference data (optional - you might want to keep it)
                # db.query(ProductReference).delete()
                
                # Process each row
                records_added = 0
                records_updated = 0
                
                for index, row in df.iterrows():
                    product_name = str(row[product_col]).strip()
                    try:
                        price = float(row[price_col])
                    except (ValueError, TypeError):
                        logger.warning(f"Row {index + 2}: Invalid price, skipping")
                        continue
                    
                    if pd.isna(product_name) or not product_name:
                        continue
                    
                    # Assign sequential ID starting from 1
                    product_id = index + 1
                    
                    # Check if product already exists
                    existing = db.query(ProductReference).filter(
                        ProductReference.product_name == product_name
                    ).first()
                    
                    if existing:
                        # Update existing record
                        existing.product_price = price
                        existing.product_id = product_id
                        records_updated += 1
                    else:
                        # Create new record
                        new_ref = ProductReference(
                            product_name=product_name,
                            product_id=product_id,
                            product_price=price
                        )
                        db.add(new_ref)
                        records_added += 1
                
                db.commit()
                
                return {
                    "success": True,
                    "message": f"Product reference table uploaded successfully",
                    "records_added": records_added,
                    "records_updated": records_updated,
                    "total_records": records_added + records_updated
                }
            except Exception as e:
                db.rollback()
                raise
            finally:
                db.close()
                
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading product reference: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading product reference: {str(e)}")

# Product Data Management API endpoints
@app.get("/api/v1/products")
async def get_products(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get all products with pagination"""
    try:
        from app.database import get_db, ProductReference
        db = next(get_db())
        
        # Get total count
        total = db.query(ProductReference).count()
        
        # Get paginated data
        products = db.query(ProductReference).offset(skip).limit(limit).all()
        
        result = []
        for product in products:
            result.append({
                "id": product.id,
                "product_name": product.product_name,
                "product_id": product.product_id,
                "product_price": float(product.product_price) if product.product_price else None,
                "created_at": product.created_at.isoformat() if product.created_at else None
            })
        
        return {
            "data": result,
            "total": total,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting products: {str(e)}")
    finally:
        db.close()

@app.get("/api/v1/products/all")
async def get_all_products(current_user: User = Depends(get_current_user)):
    """Get all products (for search/filtering)"""
    try:
        from app.database import get_db, ProductReference
        db = next(get_db())
        
        products = db.query(ProductReference).all()
        
        result = []
        for product in products:
            result.append({
                "id": product.id,
                "product_name": product.product_name,
                "product_id": product.product_id,
                "product_price": float(product.product_price) if product.product_price else None,
                "created_at": product.created_at.isoformat() if product.created_at else None
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting all products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting all products: {str(e)}")
    finally:
        db.close()

@app.post("/api/v1/products")
async def create_product(
    product_data: Dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Create a new product record"""
    try:
        from app.database import get_db, ProductReference
        from sqlalchemy import func
        db = next(get_db())
        
        # Validate required fields
        if not product_data.get("product_name"):
            raise HTTPException(status_code=400, detail="product_name is required")
        
        # Get next product_id if not provided
        product_id = product_data.get("product_id")
        if not product_id:
            max_id = db.query(func.max(ProductReference.product_id)).scalar()
            product_id = (max_id or 0) + 1
        
        # Check if product_name already exists
        existing = db.query(ProductReference).filter(
            ProductReference.product_name == product_data.get("product_name")
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Product name already exists")
        
        # Create new product record
        new_product = ProductReference(
            product_name=product_data.get("product_name"),
            product_id=product_id,
            product_price=product_data.get("product_price", 0.0)
        )
        
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        return {
            "id": new_product.id,
            "product_name": new_product.product_name,
            "product_id": new_product.product_id,
            "product_price": float(new_product.product_price) if new_product.product_price else None,
            "created_at": new_product.created_at.isoformat() if new_product.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")
    finally:
        db.close()

@app.put("/api/v1/products/{product_id}")
async def update_product(
    product_id: int,
    update_data: Dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Update a product record"""
    try:
        from app.database import get_db, ProductReference
        db = next(get_db())
        
        # Get the record
        product = db.query(ProductReference).filter(ProductReference.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update fields
        if "product_name" in update_data:
            # Check if new name already exists (excluding current record)
            existing = db.query(ProductReference).filter(
                ProductReference.product_name == update_data["product_name"],
                ProductReference.id != product_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Product name already exists")
            product.product_name = update_data["product_name"]
        if "product_id" in update_data:
            product.product_id = update_data["product_id"]
        if "product_price" in update_data:
            product.product_price = update_data["product_price"]
        
        db.commit()
        db.refresh(product)
        
        return {
            "id": product.id,
            "product_name": product.product_name,
            "product_id": product.product_id,
            "product_price": float(product.product_price) if product.product_price else None,
            "created_at": product.created_at.isoformat() if product.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")
    finally:
        db.close()

@app.delete("/api/v1/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a product record"""
    try:
        from app.database import get_db, ProductReference
        db = next(get_db())
        
        # Get the record
        product = db.query(ProductReference).filter(ProductReference.id == product_id).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        db.delete(product)
        db.commit()
        
        return {"message": "Product deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
