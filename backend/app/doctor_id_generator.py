"""
Doctor ID Generator with counter-based unique ID generation
"""
import re
import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.database import DoctorIdCounter

logger = logging.getLogger(__name__)

def normalize_doctor_name(doctor_name: str) -> str:
    """Normalize input, removing special characters except periods"""
    if not doctor_name:
        return ""
    normalized = re.sub(r'[^\w\s.]', '', str(doctor_name)).strip().lower()
    return normalized

def generate_doctor_id(doctor_name: str, db: Session, row_index: int = 0) -> str:
    """
    Generate doctor ID with format: XXX-YYY-NNN
    - XXX: Name code (first letters or DR_)
    - YYY: Secondary code (more of the name for uniqueness)
    - NNN: Counter (001, 002, etc.)
    """
    try:
        # Normalize input
        normalized_name = normalize_doctor_name(doctor_name)
        
        # Handle invalid or empty names
        if not normalized_name:
            logger.warning(f"Row {row_index + 2}: Invalid doctor name: {doctor_name}")
            return "INVALID"
        
        # Check database for existing ID
        existing = db.query(DoctorIdCounter).filter(
            DoctorIdCounter.normalized_name == normalized_name
        ).first()
        
        if existing:
            return existing.doctor_id
        
        # Generate name code (XXX)
        name_parts = normalized_name.replace(".", " ").split()
        if normalized_name.startswith("dr "):
            name_code = "DR_"
        else:
            # Use first letters of up to two name parts, or first three letters if one part
            if len(name_parts) > 1:
                name_code = "".join(part[:1] for part in name_parts[:2]).upper()
            else:
                name_code = normalized_name[:3].upper()
        
        # Generate secondary code (YYY) using more of the name for uniqueness
        if normalized_name.startswith("dr ") and len(name_parts) > 1:
            # Use first three letters of the word after "DR"
            yyy_code = name_parts[1][:3].upper()
        elif len(name_parts) > 1:
            # Use first three letters of the last name part for more uniqueness
            yyy_code = name_parts[-1][:3].upper()
        else:
            # Fallback to first three letters of the name
            yyy_code = name_parts[0][:3].upper()
        
        # Generate unique counter (NNN) based on XXX-YYY- prefix
        prefix = f"{name_code}-{yyy_code}-"
        existing_count = db.query(DoctorIdCounter).filter(
            DoctorIdCounter.doctor_id.like(f"{prefix}%")
        ).count()
        
        counter = existing_count + 1
        new_id = f"{prefix}{counter:03d}"
        
        # Store the new ID in database
        new_counter = DoctorIdCounter(
            normalized_name=normalized_name,
            doctor_id=new_id
        )
        db.add(new_counter)
        db.commit()
        
        logger.info(f"Generated doctor ID: {new_id} for '{doctor_name}' (normalized: '{normalized_name}')")
        
        return new_id
        
    except Exception as e:
        logger.error(f"Error generating doctor ID: {str(e)}")
        db.rollback()
        return "INVALID"

