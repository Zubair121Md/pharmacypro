"""
Authentication routes for Pharmacy Revenue Management System
Version: 2.0
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.database import get_db, User
from app.auth import authenticate_user, create_access_token, get_current_user, get_password_hash
from app.models import LoginRequest, Token, UserCreate, UserResponse, UserUpdate
from app.database import AuditLog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    try:
        # Authenticate user
        user = authenticate_user(db, login_data.username, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Log login action
        audit_log = AuditLog(
            user_id=user.id,
            action="LOGIN",
            ip_address=None,  # Will be set by middleware
            user_agent=None   # Will be set by middleware
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"User {user.username} logged in successfully")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800  # 30 minutes
        }
        
    except Exception as e:
        logger.error(f"Login failed for user {login_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout user (invalidate token on client side)"""
    try:
        # Log logout action
        audit_log = AuditLog(
            user_id=current_user.id,
            action="LOGOUT",
            ip_address=None,
            user_agent=None
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"User {current_user.username} logged out")
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout failed for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register new user (Admin/Super Admin only)"""
    try:
        # Check if user has permission to create users
        if current_user.role not in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to create users"
            )
        
        # Check if username already exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            role=user_data.role,
            area=user_data.area
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Log user creation
        audit_log = AuditLog(
            user_id=current_user.id,
            action="CREATE_USER",
            table_name="prms_users",
            record_id=new_user.id,
            new_values={"username": new_user.username, "role": new_user.role}
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"User {new_user.username} created by {current_user.username}")
        
        return new_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed"
        )

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    try:
        # Update user fields
        if user_update.username is not None:
            # Check if new username is available
            if db.query(User).filter(User.username == user_update.username, User.id != current_user.id).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            current_user.username = user_update.username
        
        if user_update.email is not None:
            # Check if new email is available
            if db.query(User).filter(User.email == user_update.email, User.id != current_user.id).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
            current_user.email = user_update.email
        
        if user_update.password is not None:
            current_user.password_hash = get_password_hash(user_update.password)
        
        if user_update.area is not None:
            current_user.area = user_update.area
        
        db.commit()
        
        # Log profile update
        audit_log = AuditLog(
            user_id=current_user.id,
            action="UPDATE_PROFILE",
            table_name="prms_users",
            record_id=current_user.id,
            new_values={"username": current_user.username, "email": current_user.email}
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"User {current_user.username} updated their profile")
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update failed for user {current_user.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )
