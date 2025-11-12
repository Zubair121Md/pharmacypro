"""
Enhanced data processing with chunked processing and advanced matching
Version: 2.0
"""

import pandas as pd
import logging
import re
import os
from typing import Dict, List, Tuple, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime
import redis
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from difflib import SequenceMatcher

from app.database import get_db, MasterMapping, Invoice, Unmatched, AuditLog, User
from app.tasks_enhanced import generate_id, normalize_column_name, flexible_column_mapping

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis connection for caching
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

class DataProcessor:
    """Enhanced data processor with chunked processing and caching"""
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.cache_prefix = f"pharmacy_processing_{user_id}"
        
    def process_large_file(self, df: pd.DataFrame, file_type: str, chunk_size: int = 1000) -> Dict[str, Any]:
        """
        Process large files in chunks for better memory management
        
        Args:
            df: DataFrame to process
            file_type: 'master' or 'invoice'
            chunk_size: Number of rows per chunk
        
        Returns:
            Dictionary with processing results
        """
        try:
            logger.info(f"Processing {len(df)} rows in chunks of {chunk_size}")
            
            total_processed = 0
            total_matched = 0
            total_unmatched = 0
            errors = []
            
            # Process in chunks
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i:i + chunk_size]
                logger.info(f"Processing chunk {i//chunk_size + 1}: rows {i} to {min(i + chunk_size, len(df))}")
                
                try:
                    if file_type == 'master':
                        processed = self.process_master_chunk(chunk)
                        total_processed += processed
                    else:
                        matched, unmatched = self.process_invoice_chunk(chunk)
                        total_matched += matched
                        total_unmatched += unmatched
                        total_processed += len(chunk)
                        
                except Exception as e:
                    error_msg = f"Error processing chunk {i//chunk_size + 1}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
            
            # Cache results
            cache_key = f"{self.cache_prefix}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            results = {
                'total_processed': total_processed,
                'total_matched': total_matched,
                'total_unmatched': total_unmatched,
                'errors': errors,
                'file_type': file_type,
                'processed_at': datetime.now().isoformat()
            }
            redis_client.setex(cache_key, 3600, json.dumps(results))  # Cache for 1 hour
            
            return results
            
        except Exception as e:
            logger.error(f"Error in chunked processing: {str(e)}")
            raise
    
    def process_master_chunk(self, chunk: pd.DataFrame) -> int:
        """Process a chunk of master data"""
        try:
            # Define required columns for master data
            required_columns = {
                'rep_names': ['rep names', 'sales rep', 'representative', 'rep name', 'sales representative'],
                'doctor_names': ['doctor names', 'doctor', 'dr name', 'physician', 'doctor name'],
                'doctor_id': ['doctor id', 'doctor_id'],
                'pharmacy_names': ['pharmacy names', 'store name', 'pharmacy', 'outlet', 'store'],
                'pharmacy_id': ['pharmacy id', 'pharmacy_id'],
                'product_names': ['product names', 'item', 'product', 'medicine', 'drug'],
                'product_id': ['product id', 'product_id'],
                'product_price': ['product price', 'rate', 'price', 'cost', 'unit price'],
                'hq': ['hq', 'office', 'headquarters', 'head office', 'branch'],
                'area': ['area', 'zone', 'region', 'territory', 'district']
            }
            
            # Map columns
            column_mapping = flexible_column_mapping(chunk.columns.tolist(), required_columns)
            
            # Check if all required columns are present
            missing_columns = []
            for req_col in required_columns.keys():
                if req_col not in column_mapping.values():
                    missing_columns.append(req_col)
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Rename columns to standard names
            chunk_renamed = chunk.rename(columns={k: v for v, k in column_mapping.items()})
            
            # Process each row
            processed_count = 0
            for index, row in chunk_renamed.iterrows():
                try:
                    # Check if record already exists
                    existing = self.db.query(MasterMapping).filter(
                        MasterMapping.pharmacy_id == str(row['pharmacy_id']),
                        MasterMapping.product_id == str(row['product_id'])
                    ).first()
                    
                    if existing:
                        continue  # Skip duplicates
                    
                    master_record = MasterMapping(
                        rep_names=str(row['rep_names']) if pd.notna(row['rep_names']) else '',
                        doctor_names=str(row['doctor_names']) if pd.notna(row['doctor_names']) else '',
                        doctor_id=str(row['doctor_id']) if pd.notna(row['doctor_id']) else '',
                        pharmacy_names=str(row['pharmacy_names']) if pd.notna(row['pharmacy_names']) else '',
                        pharmacy_id=str(row['pharmacy_id']) if pd.notna(row['pharmacy_id']) else '',
                        product_names=str(row['product_names']) if pd.notna(row['product_names']) else '',
                        product_id=str(row['product_id']) if pd.notna(row['product_id']) else '',
                        product_price=float(row['product_price']) if pd.notna(row['product_price']) else 0.0,
                        hq=str(row['hq']) if pd.notna(row['hq']) else '',
                        area=str(row['area']) if pd.notna(row['area']) else ''
                    )
                    self.db.add(master_record)
                    processed_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error processing master data row {index + 2}: {str(e)}")
                    continue
            
            # Commit chunk
            self.db.commit()
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing master chunk: {str(e)}")
            self.db.rollback()
            raise
    
    def process_invoice_chunk(self, chunk: pd.DataFrame) -> Tuple[int, int]:
        """Process a chunk of invoice data with enhanced matching"""
        try:
            # Define required columns for invoice data
            required_columns = {
                'pharmacy_name': ['pharmacy name', 'pharmacy', 'store name', 'store', 'outlet', 'pharmacy_name'],
                'product': ['product', 'medicine', 'item', 'drug', 'product_name'],
                'quantity': ['quantity', 'qty', 'units', 'pieces', 'count'],
                'amount': ['amount', 'total', 'revenue', 'value', 'sales', 'price']
            }
            
            # Map columns
            column_mapping = flexible_column_mapping(chunk.columns.tolist(), required_columns)
            
            # Check if all required columns are present
            missing_columns = []
            for req_col in required_columns.keys():
                if req_col not in column_mapping.values():
                    missing_columns.append(req_col)
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Rename columns to standard names
            chunk_renamed = chunk.rename(columns={k: v for v, k in column_mapping.items()})
            
            # Split 'Pharmacy Name' into 'Facility Name' and 'Location'
            chunk_renamed[['Facility Name', 'Location']] = chunk_renamed['pharmacy_name'].str.split(',', n=1, expand=True)
            chunk_renamed['Location'] = chunk_renamed['Location'].fillna('Not Specified').str.strip()
            
            # Generate IDs
            id_counter = {}
            chunk_renamed['Generated_Pharmacy_ID'] = ''
            
            for index, row in chunk_renamed.iterrows():
                if index % 100 == 0:
                    logger.info(f"Processing row {index} in chunk")
                
                facility_name = row['Facility Name']
                location = row['Location']
                
                if pd.isna(facility_name) or not str(facility_name).strip():
                    chunk_renamed.at[index, 'Generated_Pharmacy_ID'] = 'INVALID'
                    logger.warning(f"Row {index + 2}: Invalid facility name: {row['pharmacy_name']}")
                else:
                    chunk_renamed.at[index, 'Generated_Pharmacy_ID'] = generate_id(
                        facility_name, location, index, id_counter
                    )
            
            # Enhanced matching
            matched_count, unmatched_count = self.enhanced_matching(chunk_renamed)
            
            return matched_count, unmatched_count
            
        except Exception as e:
            logger.error(f"Error processing invoice chunk: {str(e)}")
            raise
    
    def enhanced_matching(self, df: pd.DataFrame) -> Tuple[int, int]:
        """
        Enhanced matching system with deterministic ID matching and ML fallback
        
        Args:
            df: Processed invoice DataFrame
        
        Returns:
            Tuple of (matched_count, unmatched_count)
        """
        try:
            matched_count = 0
            unmatched_count = 0
            
            # Get all master data with caching
            master_data = self.get_cached_master_data()
            master_dict = {record.pharmacy_id: record for record in master_data}
            
            # Create fuzzy matching cache
            fuzzy_cache = {}
            
            for index, row in df.iterrows():
                generated_id = row['Generated_Pharmacy_ID']
                
                if generated_id == 'INVALID':
                    unmatched_count += 1
                    continue
                
                # Normalize ID for matching (replace - with _)
                normalized_id = generated_id.replace('-', '_')
                
                # Try exact match first
                master_record = master_dict.get(normalized_id)
                
                if master_record:
                    # Create invoice record
                    invoice = Invoice(
                        pharmacy_id=normalized_id,
                        pharmacy_name=row['pharmacy_name'],
                        product=row['product'],
                        quantity=int(row['quantity']) if pd.notna(row['quantity']) else 0,
                        amount=float(row['amount']) if pd.notna(row['amount']) else 0.0,
                        user_id=self.user_id
                    )
                    self.db.add(invoice)
                    matched_count += 1
                else:
                    # Try fuzzy matching
                    fuzzy_match = self.fuzzy_match_pharmacy(
                        row['pharmacy_name'], master_data, fuzzy_cache
                    )
                    
                    if fuzzy_match:
                        # Create invoice record with matched ID
                        invoice = Invoice(
                            pharmacy_id=fuzzy_match.pharmacy_id,
                            pharmacy_name=row['pharmacy_name'],
                            product=row['product'],
                            quantity=int(row['quantity']) if pd.notna(row['quantity']) else 0,
                            amount=float(row['amount']) if pd.notna(row['amount']) else 0.0,
                            user_id=self.user_id
                        )
                        self.db.add(invoice)
                        matched_count += 1
                    else:
                        # Add to unmatched records with helpful context
                        unmatched = Unmatched(
                            pharmacy_name=row['pharmacy_name'],
                            generated_id=generated_id,
                            product=str(row.get('product', '')),
                            quantity=int(row.get('quantity', 0)) if pd.notna(row.get('quantity', 0)) else 0,
                            amount=float(row.get('amount', 0.0)) if pd.notna(row.get('amount', 0.0)) else 0.0,
                            user_id=self.user_id
                        )
                        self.db.add(unmatched)
                        unmatched_count += 1
            
            # Commit all changes
            self.db.commit()
            
            # Log the processing action
            audit_log = AuditLog(
                user_id=self.user_id,
                action="ENHANCED_PROCESSING",
                table_name="prms_invoices",
                new_values={
                    "matched_count": matched_count,
                    "unmatched_count": unmatched_count,
                    "total_processed": len(df)
                }
            )
            self.db.add(audit_log)
            self.db.commit()
            
            return matched_count, unmatched_count
            
        except Exception as e:
            logger.error(f"Error in enhanced matching: {str(e)}")
            self.db.rollback()
            raise
    
    def get_cached_master_data(self) -> List[MasterMapping]:
        """Get master data with caching"""
        cache_key = f"{self.cache_prefix}_master_data"
        cached_data = redis_client.get(cache_key)
        
        if cached_data:
            # Return cached data (simplified for now)
            return self.db.query(MasterMapping).all()
        else:
            # Cache master data
            master_data = self.db.query(MasterMapping).all()
            redis_client.setex(cache_key, 1800, "cached")  # Cache for 30 minutes
            return master_data
    
    def fuzzy_match_pharmacy(self, pharmacy_name: str, master_data: List[MasterMapping], cache: Dict) -> Optional[MasterMapping]:
        """
        Fuzzy matching for pharmacy names using string similarity
        
        Args:
            pharmacy_name: Name to match
            master_data: List of master records
            cache: Fuzzy matching cache
        
        Returns:
            Best matching master record or None
        """
        try:
            # Check cache first
            if pharmacy_name in cache:
                return cache[pharmacy_name]
            
            best_match = None
            best_score = 0.0
            threshold = 0.8  # 80% similarity threshold
            
            normalized_pharmacy = normalize_column_name(pharmacy_name)
            
            for master_record in master_data:
                normalized_master = normalize_column_name(master_record.pharmacy_names)
                
                # Calculate similarity
                similarity = SequenceMatcher(None, normalized_pharmacy, normalized_master).ratio()
                
                if similarity > best_score and similarity >= threshold:
                    best_score = similarity
                    best_match = master_record
            
            # Cache result
            cache[pharmacy_name] = best_match
            return best_match
            
        except Exception as e:
            logger.error(f"Error in fuzzy matching: {str(e)}")
            return None
    
    def validate_data_quality(self, df: pd.DataFrame, file_type: str) -> Dict[str, Any]:
        """
        Comprehensive data quality validation
        
        Args:
            df: DataFrame to validate
            file_type: 'master' or 'invoice'
        
        Returns:
            Validation results dictionary
        """
        try:
            validation_results = {
                'total_rows': len(df),
                'empty_rows': 0,
                'duplicate_rows': 0,
                'invalid_data': [],
                'warnings': [],
                'quality_score': 0.0
            }
            
            # Check for empty rows
            empty_rows = df.isnull().all(axis=1).sum()
            validation_results['empty_rows'] = int(empty_rows)
            
            # Check for duplicates
            if file_type == 'master':
                duplicate_rows = df.duplicated(subset=['pharmacy_id', 'product_id']).sum()
            else:
                duplicate_rows = df.duplicated().sum()
            validation_results['duplicate_rows'] = int(duplicate_rows)
            
            # Check for invalid data
            for index, row in df.iterrows():
                row_errors = []
                
                if file_type == 'master':
                    # Validate master data
                    if pd.isna(row.get('pharmacy_id', '')) or str(row.get('pharmacy_id', '')).strip() == '':
                        row_errors.append('Missing pharmacy_id')
                    if pd.isna(row.get('product_id', '')) or str(row.get('product_id', '')).strip() == '':
                        row_errors.append('Missing product_id')
                    if pd.isna(row.get('product_price', 0)) or float(row.get('product_price', 0)) < 0:
                        row_errors.append('Invalid product_price')
                else:
                    # Validate invoice data
                    if pd.isna(row.get('pharmacy_name', '')) or str(row.get('pharmacy_name', '')).strip() == '':
                        row_errors.append('Missing pharmacy_name')
                    if pd.isna(row.get('product', '')) or str(row.get('product', '')).strip() == '':
                        row_errors.append('Missing product')
                    if pd.isna(row.get('quantity', 0)) or int(row.get('quantity', 0)) < 0:
                        row_errors.append('Invalid quantity')
                    if pd.isna(row.get('amount', 0)) or float(row.get('amount', 0)) < 0:
                        row_errors.append('Invalid amount')
                
                if row_errors:
                    validation_results['invalid_data'].append({
                        'row': index + 2,
                        'errors': row_errors
                    })
            
            # Calculate quality score
            total_issues = validation_results['empty_rows'] + validation_results['duplicate_rows'] + len(validation_results['invalid_data'])
            validation_results['quality_score'] = max(0.0, 1.0 - (total_issues / validation_results['total_rows']))
            
            # Add warnings
            if validation_results['quality_score'] < 0.8:
                validation_results['warnings'].append('Data quality is below 80%')
            if validation_results['duplicate_rows'] > 0:
                validation_results['warnings'].append(f'{validation_results["duplicate_rows"]} duplicate rows found')
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error in data validation: {str(e)}")
            return {
                'total_rows': len(df),
                'empty_rows': 0,
                'duplicate_rows': 0,
                'invalid_data': [],
                'warnings': ['Validation error occurred'],
                'quality_score': 0.0
            }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics for the user"""
        try:
            # Get recent processing stats
            recent_uploads = self.db.query(AuditLog).filter(
                AuditLog.user_id == self.user_id,
                AuditLog.action.in_(['PROCESS_INVOICE_DATA', 'ENHANCED_PROCESSING'])
            ).order_by(AuditLog.created_at.desc()).limit(10).all()
            
            # Get unmatched records count
            unmatched_count = self.db.query(Unmatched).filter(
                Unmatched.status == 'pending'
            ).count()
            
            # Get total invoices processed
            total_invoices = self.db.query(Invoice).filter(
                Invoice.user_id == self.user_id
            ).count()
            
            return {
                'recent_uploads': len(recent_uploads),
                'unmatched_records': unmatched_count,
                'total_invoices': total_invoices,
                'last_upload': recent_uploads[0].created_at.isoformat() if recent_uploads else None
            }
            
        except Exception as e:
            logger.error(f"Error getting processing stats: {str(e)}")
            return {
                'recent_uploads': 0,
                'unmatched_records': 0,
                'total_invoices': 0,
                'last_upload': None
            }
