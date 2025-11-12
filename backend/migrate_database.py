#!/usr/bin/env python3
"""
Database migration script to add new columns to RecentUpload table
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, RecentUpload
from sqlalchemy import text

def migrate_database():
    """Add new columns to RecentUpload table"""
    try:
        # Check if columns already exist
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(prms_recent_uploads)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'total_revenue' in columns:
                print("Migration already applied - columns exist")
                return True
                
        # Add new columns
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE prms_recent_uploads 
                ADD COLUMN total_revenue DECIMAL(15,2) DEFAULT 0
            """))
            
            conn.execute(text("""
                ALTER TABLE prms_recent_uploads 
                ADD COLUMN total_pharmacies INTEGER DEFAULT 0
            """))
            
            conn.execute(text("""
                ALTER TABLE prms_recent_uploads 
                ADD COLUMN total_doctors INTEGER DEFAULT 0
            """))
            
            conn.execute(text("""
                ALTER TABLE prms_recent_uploads 
                ADD COLUMN growth_rate DECIMAL(5,2) DEFAULT 0
            """))
            
            conn.execute(text("""
                ALTER TABLE prms_recent_uploads 
                ADD COLUMN matched_count INTEGER DEFAULT 0
            """))
            
            conn.execute(text("""
                ALTER TABLE prms_recent_uploads 
                ADD COLUMN unmatched_count INTEGER DEFAULT 0
            """))
            
            conn.commit()
            
        print("Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    migrate_database()
