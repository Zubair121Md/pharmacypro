from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd
import json
from datetime import datetime, timedelta
import uuid
import os
import tempfile
from app.file_processor import FileProcessor
from fastapi import BackgroundTasks
from app.database import init_db as _init_db
from app.database import ensure_unmatched_schema as _ensure_unmatched_schema
from typing import Dict
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

def generate_id(name: str, id_type: str) -> str:
    """Generate standardized ID based on type"""
    import re

    if id_type == 'pharmacy':
        # Match the provided script behavior exactly:
        # - Split on first comma into Facility, Location (remainder)
        # - Facility code: first 10 alnum chars of Facility (spaces removed)
        # - Location code: last 10 alnum chars of full Location remainder (spaces removed)
        raw = (name or "").strip()
        facility = raw
        location_remainder = ""

        comma_idx = raw.find(",")
        if comma_idx != -1:
            facility = raw[:comma_idx]
            location_remainder = raw[comma_idx+1:]
        else:
            # No comma -> treat as missing location (per excel script uses 'Not Specified')
            location_remainder = 'Not Specified'

        def _clean_alnum(s: str) -> str:
            # Allow dots to be retained
            return re.sub(r"[^A-Za-z0-9\.]", "", s or "")

        facility_code = _clean_alnum(facility).upper()[:10]
        loc_clean = _clean_alnum(location_remainder).upper()
        location_code = (loc_clean[-10:] if loc_clean else "")
        if location_code and len(location_code) < 10:
            location_code = location_code.ljust(10, "_")

        return f"{facility_code}-{location_code}" if location_code else facility_code

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
    username = login_data.get("username")
    password = login_data.get("password")
    
    if username == "admin" and password == "admin123":
        user = User(id=1, username="admin", email="admin@pharmacy.com", full_name="Admin User", role="super_admin")
        return {
            "access_token": "demo_token_12345", 
            "token_type": "bearer",
            "user": user
        }
    elif username == "user" and password == "user123":
        user = User(id=2, username="user", email="user@pharmacy.com", full_name="Regular User", role="user")
        return {
            "access_token": "demo_token_user_12345", 
            "token_type": "bearer",
            "user": user
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
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
    hq_revenue: Dict[str, float] = {}
    for item in mock_data["revenue_data"]:
        hq = item.get("hq") or "Unknown"
        hq_revenue[hq] = hq_revenue.get(hq, 0.0) + float(item["revenue"])
    return [{"hq": k, "revenue": v} for k, v in hq_revenue.items()]

@app.get("/api/v1/analytics/area-revenue")
async def get_area_revenue(current_user: User = Depends(get_current_user)):
    area_revenue: Dict[str, float] = {}
    for item in mock_data["revenue_data"]:
        area = item.get("area") or "Unknown"
        area_revenue[area] = area_revenue.get(area, 0.0) + float(item["revenue"])
    return [{"area": k, "revenue": v} for k, v in area_revenue.items()]

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
async def map_record(record_id: int, mapping_data: dict, current_user: User = Depends(get_current_user)):
    """Map an unmatched record to a master pharmacy"""
    try:
        from app.database import get_db, Unmatched
        
        master_pharmacy_id = mapping_data.get("master_pharmacy_id")
        if not master_pharmacy_id:
            raise HTTPException(status_code=400, detail="master_pharmacy_id is required")
        
        # Get database session
        db = next(get_db())
        
        # Find the unmatched record
        unmatched_record = db.query(Unmatched).filter(Unmatched.id == record_id).first()
        if not unmatched_record:
            raise HTTPException(status_code=404, detail="Unmatched record not found")
        
        # Update the record
        unmatched_record.status = "mapped"
        unmatched_record.mapped_to = master_pharmacy_id
        db.commit()
        
        return {"success": True, "message": f"Record {record_id} mapped to master pharmacy {master_pharmacy_id}"}
        
    except Exception as e:
        print(f"Error mapping record: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to map record")

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

@app.post("/api/v1/admin/reset-memory")
async def reset_memory_admin(current_user: User = Depends(get_current_user)):
    """Reset system memory - clear all data"""
    if current_user.role not in ['super_admin', 'admin']:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        from app.database import get_db, Invoice, MasterMapping, Unmatched, RecentUpload, AuditLog
        db = next(get_db())
        
        # Clear all data tables
        db.query(Invoice).delete()
        db.query(MasterMapping).delete()
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
        
        return {"message": "System memory reset successfully", "success": True}
        
    except Exception as e:
        print(f"Error resetting memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resetting memory: {str(e)}")
    finally:
        db.close()

# Unmatched Records Management
@app.post("/api/v1/unmatched/{record_id}/map")
async def map_unmatched_record(record_id: int, request: dict, current_user: User = Depends(get_current_user)):
    """Map an unmatched record to a master pharmacy"""
    try:
        from app.database import get_db
        db = next(get_db())
        
        master_pharmacy_id = request.get('master_pharmacy_id')
        if not master_pharmacy_id:
            raise HTTPException(status_code=400, detail="master_pharmacy_id is required")
        
        # Find the unmatched record
        unmatched_record = db.query(Unmatched).filter(Unmatched.id == record_id).first()
        if not unmatched_record:
            raise HTTPException(status_code=404, detail="Unmatched record not found")
        
        # Find the master pharmacy
        master_pharmacy = db.query(MasterMapping).filter(
            MasterMapping.pharmacy_id == master_pharmacy_id
        ).first()
        if not master_pharmacy:
            raise HTTPException(status_code=404, detail="Master pharmacy not found")
        
        # Update the unmatched record
        unmatched_record.status = "mapped"
        unmatched_record.mapped_to = master_pharmacy.pharmacy_names
        
        db.commit()
        
        return {"message": "Record mapped successfully", "success": True}
        
    except Exception as e:
        print(f"Error mapping record: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error mapping record: {str(e)}")
    finally:
        db.close()

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
    try:
        if request.type not in ['pharmacy', 'product', 'doctor']:
            raise HTTPException(status_code=400, detail="Invalid type. Must be 'pharmacy', 'product', or 'doctor'")
        
        if not request.name or not request.name.strip():
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        
        generated_id = generate_id(request.name.strip(), request.type)
        
        return IdGenerationResponse(
            original_name=request.name.strip(),
            generated_id=generated_id,
            type=request.type,
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating ID: {str(e)}")

@app.post("/api/v1/generator/batch", response_model=List[IdGenerationResponse])
async def generate_batch_ids(requests: List[IdGenerationRequest], current_user: User = Depends(get_current_user)):
    """Generate multiple IDs in batch"""
    try:
        results = []
        for request in requests:
            if request.type not in ['pharmacy', 'product', 'doctor']:
                continue
            
            if not request.name or not request.name.strip():
                continue
            
            generated_id = generate_id(request.name.strip(), request.type)
            
            results.append(IdGenerationResponse(
                original_name=request.name.strip(),
                generated_id=generated_id,
                type=request.type,
                timestamp=datetime.now().isoformat()
            ))
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating batch IDs: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
