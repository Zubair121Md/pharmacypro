"""
Pydantic models for Pharmacy Revenue Management System
Version: 2.0
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# User Models
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: str = Field(..., pattern="^(super_admin|admin|user)$")
    area: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = Field(None, pattern="^(super_admin|admin|user)$")
    area: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

# Authentication Models
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None

# Master Mapping Models
class MasterMappingBase(BaseModel):
    rep_names: str
    doctor_names: str
    doctor_id: str
    pharmacy_names: str
    pharmacy_id: str
    product_names: str
    product_id: str
    product_price: Decimal
    hq: str
    area: str

class MasterMappingCreate(MasterMappingBase):
    pass

class MasterMappingResponse(MasterMappingBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Invoice Models
class InvoiceBase(BaseModel):
    pharmacy_id: str
    pharmacy_name: str
    product: str
    quantity: int
    amount: Decimal
    invoice_date: Optional[datetime] = None

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceResponse(InvoiceBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Allocation Models
class AllocationBase(BaseModel):
    doctor_names: str
    allocated_revenue: Decimal
    pharmacy_id: str
    allocation_date: datetime

class AllocationCreate(AllocationBase):
    pass

class AllocationResponse(AllocationBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# File Upload Models
class FileUploadResponse(BaseModel):
    message: str
    file_id: str
    rows_processed: int
    matched_count: int
    unmatched_count: int

class ColumnMapping(BaseModel):
    pharmacy_name: str
    product: str
    quantity: str
    amount: str

# Analytics Models
class RevenueAnalytics(BaseModel):
    total_revenue: Decimal
    pharmacy_revenue: List[dict]
    doctor_revenue: List[dict]
    rep_revenue: List[dict]
    hq_revenue: List[dict]
    area_revenue: List[dict]
    monthly_revenue: List[dict]

class ChartData(BaseModel):
    labels: List[str]
    data: List[float]
    backgroundColor: Optional[str] = None
    borderColor: Optional[str] = None

# Unmatched Records Models
class UnmatchedBase(BaseModel):
    pharmacy_name: str
    generated_id: str
    invoice_id: Optional[int] = None
    confidence_score: Optional[Decimal] = None

class UnmatchedCreate(UnmatchedBase):
    pass

class UnmatchedResponse(UnmatchedBase):
    id: int
    status: str
    mapped_to: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UnmatchedUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|mapped|ignored)$")
    mapped_to: Optional[str] = None

# Audit Log Models
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    table_name: Optional[str]
    record_id: Optional[int]
    old_values: Optional[dict]
    new_values: Optional[dict]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Health Check Models
class HealthCheck(BaseModel):
    status: str
    service: str
    version: str
    database: bool
    redis: bool
    timestamp: datetime

# Error Models
class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime

# Export Models
class ExportRequest(BaseModel):
    format: str = Field(..., pattern="^(excel|csv|pdf)$")
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    area: Optional[str] = None
    include_unmatched: bool = False

class ExportResponse(BaseModel):
    file_url: str
    filename: str
    expires_at: datetime
