"""
Database configuration and models for Pharmacy Revenue Management System
Version: 2.0
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index, Numeric, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy import JSON
from sqlalchemy.pool import QueuePool
import os
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
# Get the backend directory (where this file is located: app/ -> backend/)
BACKEND_DIR = Path(__file__).parent.parent  # Goes up from app/ to backend/
DATABASE_FILE = BACKEND_DIR / "pharmacy_revenue.db"

# Use absolute path for database file to ensure persistence regardless of working directory
DEFAULT_DATABASE_URL = f"sqlite:///{DATABASE_FILE.absolute()}"

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    DEFAULT_DATABASE_URL
)

logger.info(f"Database file location: {DATABASE_FILE.absolute()}")

# Create engine with connection pooling
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},  # SQLite specific
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600  # Recycle connections every hour
    )
else:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

# Database Models
class User(Base):
    """User model for authentication and role-based access"""
    __tablename__ = "prms_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # super_admin, admin, user
    area = Column(String(50))  # For region-specific access
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class MasterMapping(Base):
    """Master data mapping table"""
    __tablename__ = "prms_master_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    rep_names = Column(String(100), nullable=False)
    doctor_names = Column(String(100), nullable=False)
    doctor_id = Column(String(50), nullable=False, index=True)
    pharmacy_names = Column(String(200), nullable=False, index=True)
    pharmacy_id = Column(String(50), nullable=False, index=True)
    product_names = Column(String(200), nullable=False)
    product_id = Column(String(50), nullable=True, index=True)
    product_price = Column(Numeric(10, 2), nullable=False)
    hq = Column(String(50), nullable=False)
    area = Column(String(50), nullable=False, index=True)
    source = Column(String(50), default="file_upload")  # file_upload or manual_mapping
    created_at = Column(DateTime, default=datetime.utcnow)

class Invoice(Base):
    """Invoice data table (partitioned by year)"""
    __tablename__ = "prms_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(String(50), nullable=False, index=True)
    pharmacy_name = Column(String(200), nullable=False)
    product = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    invoice_date = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, ForeignKey("prms_users.id"), nullable=False, index=True)
    master_mapping_id = Column(Integer, ForeignKey("prms_master_mapping.id"), nullable=True, index=True)  # Link to specific master record (doctor)
    created_at = Column(DateTime, default=datetime.utcnow)

class Allocation(Base):
    """Revenue allocation records"""
    __tablename__ = "prms_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_names = Column(String(100), nullable=False)
    allocated_revenue = Column(Numeric(10, 2), nullable=False)
    pharmacy_id = Column(String(50), nullable=False, index=True)
    allocation_date = Column(DateTime, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("prms_users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RecentUpload(Base):
    """Recent uploads tracking"""
    __tablename__ = "prms_recent_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("prms_users.id"), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'invoice' or 'master'
    file_name = Column(String(255), nullable=False)
    processed_rows = Column(Integer, default=0)
    status = Column(String(50), default='completed')  # 'completed', 'failed', 'processing'
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Analysis-specific fields
    total_revenue = Column(Numeric(15, 2), default=0)
    total_pharmacies = Column(Integer, default=0)
    total_doctors = Column(Integer, default=0)
    growth_rate = Column(Numeric(5, 2), default=0)
    matched_count = Column(Integer, default=0)
    unmatched_count = Column(Integer, default=0)

class AuditLog(Base):
    """Audit logs for compliance"""
    __tablename__ = "prms_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("prms_users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    table_name = Column(String(50))
    record_id = Column(Integer)
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))  # IPv6 max length
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class Unmatched(Base):
    """Unmatched records for manual review"""
    __tablename__ = "prms_unmatched"
    
    id = Column(Integer, primary_key=True, index=True)
    pharmacy_name = Column(String(200), nullable=False)
    generated_id = Column(String(50), nullable=False)
    # Optional raw invoice details to aid review/export
    product = Column(String(200))
    quantity = Column(Integer)
    amount = Column(Numeric(10, 2))
    invoice_id = Column(Integer)
    confidence_score = Column(Numeric(3, 2))
    status = Column(String(20), default="pending")  # pending, mapped, ignored
    mapped_to = Column(String(50))
    user_id = Column(Integer, ForeignKey("prms_users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MasterSplitRule(Base):
    """Split rules for multiple masters with same pharmacy+product combination"""
    __tablename__ = "prms_master_split_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(String(50), nullable=False, index=True)
    product_key = Column(String(300), nullable=False, index=True)  # The lookup key (EXACT|... or PID|...)
    rules = Column(JSON, nullable=False)  # [{"master_mapping_id": 1, "ratio": 60}, {"master_mapping_id": 2, "ratio": 40}]
    updated_by = Column(Integer, ForeignKey("prms_users.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductReference(Base):
    """Product reference table for ID generation"""
    __tablename__ = "prms_product_reference"
    
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String(200), nullable=False, unique=True, index=True)
    product_id = Column(Integer, nullable=False, unique=True, index=True)
    product_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DoctorIdCounter(Base):
    """Doctor ID counter for maintaining unique IDs"""
    __tablename__ = "prms_doctor_id_counter"
    
    id = Column(Integer, primary_key=True, index=True)
    normalized_name = Column(String(200), nullable=False, unique=True, index=True)
    doctor_id = Column(String(50), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create indexes for performance
Index('idx_pharmacy_id', Invoice.pharmacy_id)
Index('idx_invoice_date', Invoice.invoice_date)
Index('idx_user_id', Invoice.user_id)
Index('idx_audit_user', AuditLog.user_id)
Index('idx_audit_date', AuditLog.created_at)
Index('idx_unmatched_status', Unmatched.status)
Index('idx_split_rule_lookup', MasterSplitRule.pharmacy_id, MasterSplitRule.product_key, unique=True)

# Full-text search index for pharmacy names
Index('idx_pharmacy_name_fts', MasterMapping.pharmacy_names, postgresql_using='gin')

# Database dependency
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Lightweight SQLite schema migration for backward compatibility
def ensure_unmatched_schema():
    try:
        with engine.connect() as conn:
            # SQLite pragma to inspect table columns
            cols = conn.execute(text("PRAGMA table_info(prms_unmatched)")).fetchall()
            existing = {row[1] for row in cols}  # row[1] is column name
            # Add missing columns without dropping data
            if 'product' not in existing:
                conn.execute(text("ALTER TABLE prms_unmatched ADD COLUMN product VARCHAR(200)"))
            if 'quantity' not in existing:
                conn.execute(text("ALTER TABLE prms_unmatched ADD COLUMN quantity INTEGER"))
            if 'amount' not in existing:
                conn.execute(text("ALTER TABLE prms_unmatched ADD COLUMN amount NUMERIC(10,2)"))
            conn.commit()
    except Exception as e:
        logger.warning(f"Schema check/migration for prms_unmatched skipped: {e}")

def ensure_invoice_schema():
    """Ensure invoices table has master_mapping_id column"""
    try:
        with engine.connect() as conn:
            # SQLite pragma to inspect table columns
            cols = conn.execute(text("PRAGMA table_info(prms_invoices)")).fetchall()
            existing = {row[1] for row in cols}  # row[1] is column name
            # Add missing master_mapping_id column if it doesn't exist
            if 'master_mapping_id' not in existing:
                conn.execute(text("ALTER TABLE prms_invoices ADD COLUMN master_mapping_id INTEGER"))
                conn.commit()
                logger.info("Added master_mapping_id column to prms_invoices table")
    except Exception as e:
        logger.warning(f"Schema check/migration for prms_invoices skipped: {e}")

# Ensure tables and columns exist on import
try:
    Base.metadata.create_all(bind=engine)
    ensure_unmatched_schema()
    ensure_invoice_schema()
except Exception as _e:
    logger.warning(f"Initial metadata creation/schema ensure failed: {_e}")

# Initialize database
async def init_db():
    """Initialize database tables"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        # Run schema migrations
        ensure_unmatched_schema()
        ensure_invoice_schema()
        logger.info("Database tables created successfully")
        
        # Create default users if they don't exist
        db = SessionLocal()
        try:
            from app.auth import get_password_hash
            
            # Check if users exist
            if not db.query(User).filter(User.username == "admin").first():
                # Create Super Admin
                admin_user = User(
                    username="admin",
                    email="admin@pharmacy.com",
                    password_hash=get_password_hash("admin123"),
                    role="super_admin",
                    area=None
                )
                db.add(admin_user)
                
                # Create Admin
                manager_user = User(
                    username="manager",
                    email="manager@pharmacy.com",
                    password_hash=get_password_hash("manager123"),
                    role="admin",
                    area="CALICUT"
                )
                db.add(manager_user)
                
                # Create User
                user_user = User(
                    username="user",
                    email="user@pharmacy.com",
                    password_hash=get_password_hash("user123"),
                    role="user",
                    area="CALICUT"
                )
                db.add(user_user)
                
                db.commit()
                logger.info("Default users created successfully")
            
            # Load sample master data
            if not db.query(MasterMapping).first():
                sample_data = [
                    {
                        "rep_names": "VIKRAM",
                        "doctor_names": "DR SHAJIKUMAR",
                        "doctor_id": "DR_SHA_733",
                        "pharmacy_names": "Gayathri Medicals",
                        "pharmacy_id": "GM_CAL_001",
                        "product_names": "ENDOL 650",
                        "product_id": "PRD_6824",
                        "product_price": 13.46,
                        "hq": "CL",
                        "area": "CALICUT"
                    },
                    {
                        "rep_names": "VIKRAM",
                        "doctor_names": "DR SHAJIKUMAR",
                        "doctor_id": "DR_SHA_733",
                        "pharmacy_names": "Gayathri Medicals",
                        "pharmacy_id": "GM_CAL_001",
                        "product_names": "CLONAPET 0.25",
                        "product_id": "PRD_6825",
                        "product_price": 12.5,
                        "hq": "CL",
                        "area": "CALICUT"
                    },
                    {
                        "rep_names": "ANITA",
                        "doctor_names": "DR RADHAKRISHNAN",
                        "doctor_id": "DR_RAD_744",
                        "pharmacy_names": "City Care Pharmacy",
                        "pharmacy_id": "CCP_CAL_002",
                        "product_names": "BRETHNOL SYRUP",
                        "product_id": "PRD_6826",
                        "product_price": 14.5,
                        "hq": "CL",
                        "area": "CALICUT"
                    },
                    {
                        "rep_names": "ANITA",
                        "doctor_names": "DR RADHAKRISHNAN",
                        "doctor_id": "DR_RAD_744",
                        "pharmacy_names": "City Care Pharmacy",
                        "pharmacy_id": "CCP_CAL_002",
                        "product_names": "ENCIFER SYRUP",
                        "product_id": "PRD_6827",
                        "product_price": 26.5,
                        "hq": "CL",
                        "area": "CALICUT"
                    },
                    {
                        "rep_names": "RAHUL",
                        "doctor_names": "DR AJITH KUMAR",
                        "doctor_id": "DR_AJI_755",
                        "pharmacy_names": "MedPlus Calicut",
                        "pharmacy_id": "MP_CAL_003",
                        "product_names": "CLOZACT-100 TAB",
                        "product_id": "PRD_6828",
                        "product_price": 57.0,
                        "hq": "CL",
                        "area": "CALICUT"
                    },
                    {
                        "rep_names": "RAHUL",
                        "doctor_names": "DR AJITH KUMAR",
                        "doctor_id": "DR_AJI_755",
                        "pharmacy_names": "MedPlus Calicut",
                        "pharmacy_id": "MP_CAL_003",
                        "product_names": "ACEDOL",
                        "product_id": "PRD_6829",
                        "product_price": 26.95,
                        "hq": "CL",
                        "area": "CALICUT"
                    }
                ]
                
                for data in sample_data:
                    master_record = MasterMapping(**data)
                    db.add(master_record)
                
                db.commit()
                logger.info("Sample master data loaded successfully")
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

# Health check
def check_db_health():
    """Check database health"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False
