"""
Enhanced file processing with ID generation for Pharmacy Revenue Management System
Version: 2.0
"""

import pandas as pd
import logging
import re
import os
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import redis
import json

from app.database import get_db, MasterMapping, Invoice, Unmatched, AuditLog

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Redis connection for caching
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

def _calculate_growth_rate(db: Session, current_revenue: float) -> float:
    """
    Calculate growth rate by comparing current revenue with previous analysis
    
    Args:
        db: Database session
        current_revenue: Current analysis revenue
        
    Returns:
        Growth rate percentage
    """
    try:
        from app.database import RecentUpload
        
        # Get the most recent analysis before the current one
        recent_analyses = db.query(RecentUpload).filter(
            RecentUpload.file_type == 'analysis',
            RecentUpload.total_revenue > 0
        ).order_by(RecentUpload.uploaded_at.desc()).limit(2).all()
        
        if len(recent_analyses) < 2:
            # Not enough data for comparison, return 0
            return 0.0
        
        # Get the previous analysis (second most recent)
        previous_revenue = float(recent_analyses[1].total_revenue or 0)
        
        if previous_revenue == 0:
            return 0.0
        
        # Calculate growth rate: ((current - previous) / previous) * 100
        growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100
        
        # Cap extreme growth rates to prevent unrealistic values
        if growth_rate > 500:
            growth_rate = 500
        elif growth_rate < -100:
            growth_rate = -100
            
        return round(growth_rate, 2)
        
    except Exception as e:
        logger.error(f"Error calculating growth rate: {str(e)}")
        return 0.0

def normalize_text(text, length, from_end=False):
    """
    Normalize text by:
    - Removing special characters except spaces and periods
    - Lowercasing
    - Taking first/last `length` characters
    - Padding with dashes if shorter
    """
    if not text or pd.isna(text):
        return "-" * length
    cleaned = re.sub(r'[^\w\s.]', '', str(text)).strip().lower()
    if not cleaned:
        return "-" * length
    if from_end:
        slice_txt = cleaned.replace(" ", "")[-length:]
    else:
        slice_txt = cleaned.replace(" ", "")[:length]
    return slice_txt.upper().ljust(length, "-")

def generate_id(facility_name: str, location: str, row_index: int, id_counter: Dict[str, str]) -> str:
    """
    Generate ID exactly as specified: FACILITY(10)-LOCATION(10)
    """
    try:
        if facility_name is None or (isinstance(facility_name, float) and pd.isna(facility_name)) or not str(facility_name).strip():
            logger.warning(f"Row {row_index + 2}: Invalid facility name: {facility_name}")
            return "INVALID"
        
        # Normalize facility and location
        facility_code = normalize_text(facility_name, 10, from_end=False)
        location_code = normalize_text(location, 10, from_end=True)
        
        # Just return without numbering
        return f"{facility_code}-{location_code}"
    except Exception as e:
        logger.warning(f"Row {row_index + 2}: ID generation error: {e}")
        return "INVALID"

def normalize_column_name(column_name: str) -> str:
    """
    Normalize column names for flexible mapping
    
    Args:
        column_name: Original column name
    
    Returns:
        Normalized column name
    """
    if not column_name:
        return ""
    
    # Convert to lowercase and remove extra spaces
    normalized = str(column_name).strip().lower()
    
    # Remove special characters except spaces and underscores
    normalized = re.sub(r'[^\w\s]', '', normalized)
    
    # Replace multiple spaces with single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    return normalized

def flexible_column_mapping(df_columns: List[str], required_columns: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Map flexible column names to required columns using fuzzy matching
    
    Args:
        df_columns: List of actual column names from the file
        required_columns: Dictionary mapping required columns to possible variations
    
    Returns:
        Dictionary mapping actual column names to required column names
    """
    mapping = {}
    normalized_df_columns = [normalize_column_name(col) for col in df_columns]
    
    for required_col, variations in required_columns.items():
        found = False
        for variation in variations:
            normalized_variation = normalize_column_name(variation)
            for i, normalized_df_col in enumerate(normalized_df_columns):
                if normalized_variation in normalized_df_col or normalized_df_col in normalized_variation:
                    mapping[df_columns[i]] = required_col
                    found = True
                    break
            if found:
                break
    
    return mapping

def process_pharmacies(df: pd.DataFrame, user_id: int, db: Session) -> Tuple[pd.DataFrame, int, int]:
    """
    Process pharmacy data and generate IDs
    
    Args:
        df: DataFrame with pharmacy data
        user_id: ID of the user processing the data
        db: Database session
    
    Returns:
        Tuple of (processed_df, matched_count, unmatched_count)
    """
    try:
        logger.info(f"Processing {len(df)} pharmacy records...")
        
        # Define required columns for invoice data
        required_columns = {
            'pharmacy_name': ['pharmacy name', 'pharmacy', 'store name', 'store', 'outlet', 'pharmacy_name'],
            'product': ['product', 'medicine', 'item', 'drug', 'product_name'],
            'quantity': ['quantity', 'qty', 'units', 'pieces', 'count'],
            'amount': ['amount', 'total', 'revenue', 'value', 'sales', 'price']
        }
        
        # Map columns
        column_mapping = flexible_column_mapping(df.columns.tolist(), required_columns)
        
        # Check if all required columns are present
        missing_columns = []
        for req_col in required_columns.keys():
            if req_col not in column_mapping.values():
                missing_columns.append(req_col)
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Rename columns to standard names
        df_renamed = df.rename(columns={k: v for v, k in column_mapping.items()})
        
        # Split 'Pharmacy Name' into 'Facility Name' and 'Location'
        df_renamed[['Facility Name', 'Location']] = df_renamed['pharmacy_name'].str.split(',', n=1, expand=True)
        df_renamed['Location'] = df_renamed['Location'].fillna('Not Specified').str.strip()
        
        # Generate IDs
        id_counter = {}
        df_renamed['Generated_Pharmacy_ID'] = ''
        
        for index, row in df_renamed.iterrows():
            if index % 500 == 0:
                logger.info(f"Processed {index} rows...")
            
            facility_name = row['Facility Name']
            location = row['Location']
            
            if pd.isna(facility_name) or not str(facility_name).strip():
                df_renamed.at[index, 'Generated_Pharmacy_ID'] = 'INVALID'
                logger.warning(f"Row {index + 2}: Invalid facility name: {row['pharmacy_name']}")
            else:
                df_renamed.at[index, 'Generated_Pharmacy_ID'] = generate_id(
                    facility_name, location, index, id_counter
                )
        
        # Match with master data
        matched_count, unmatched_count = merge_invoice_with_master(df_renamed, user_id, db)
        
        logger.info(f"Processing complete: {matched_count} matched, {unmatched_count} unmatched")
        
        return df_renamed, matched_count, unmatched_count
        
    except Exception as e:
        logger.error(f"Error processing pharmacies: {str(e)}")
        raise

def normalize_product_name(product_name: str) -> str:
    """
    Normalize product name for matching: uppercase, remove punctuation, trim spaces
    """
    if not product_name or pd.isna(product_name):
        return ""
    return re.sub(r'[^\w\s]', '', str(product_name)).strip().upper().replace(' ', '')

def merge_invoice_with_master(df: pd.DataFrame, user_id: int, db: Session) -> Tuple[int, int]:
    """
    Merge invoice data with master data using STRICT Pharmacy + Product matching
    
    Args:
        df: Processed invoice DataFrame
        user_id: ID of the user processing the data
        db: Database session
    
    Returns:
        Tuple of (matched_count, unmatched_count)
    """
    try:
        matched_count = 0
        unmatched_count = 0
        
        # Get all master data and create lookup by pharmacy_id + product
        master_data = db.query(MasterMapping).all()
        master_lookup = {}
        
        for record in master_data:
            # Create composite key: pharmacy_id + normalized_product
            normalized_product = normalize_product_name(record.product_names)
            key = f"{record.pharmacy_id}|{normalized_product}"
            master_lookup[key] = record
        
        logger.info(f"Created master lookup with {len(master_lookup)} pharmacy+product combinations")
        
        for index, row in df.iterrows():
            generated_id = row['Generated_Pharmacy_ID']
            
            if generated_id == 'INVALID':
                unmatched_count += 1
                continue
            
            # Normalize ID for matching (replace - with _)
            normalized_id = generated_id.replace('-', '_')
            
            # Normalize product name for matching
            normalized_product = normalize_product_name(row['product'])
            
            # Create composite key for lookup
            lookup_key = f"{normalized_id}|{normalized_product}"
            
            # Try to find exact match for BOTH pharmacy and product
            master_record = master_lookup.get(lookup_key)
            
            if master_record:
                # Calculate revenue: Quantity × Master.Product_Price
                quantity = int(row['quantity']) if pd.notna(row['quantity']) else 0
                product_price = float(master_record.product_price) if master_record.product_price else 0.0
                calculated_revenue = quantity * product_price
                
                # Get pharmacy name from the row (try different column names)
                pharmacy_name = row.get('pharmacy_name', row.get('facility_name', row.get('original_pharmacy_name', 'Unknown')))
                
                # Create invoice record with doctor allocation
                invoice = Invoice(
                    pharmacy_id=normalized_id,
                    pharmacy_name=pharmacy_name,
                    product=row['product'],
                    quantity=quantity,
                    amount=calculated_revenue,  # Use calculated revenue, not invoice amount
                    user_id=user_id
                )
                db.add(invoice)
                matched_count += 1
                
                logger.info(f"Matched: {pharmacy_name} + {row['product']} -> {master_record.doctor_names} (Revenue: {calculated_revenue})")
            else:
                # Get pharmacy name from the row (try different column names)
                pharmacy_name = row.get('pharmacy_name', row.get('facility_name', row.get('original_pharmacy_name', 'Unknown')))
                
                # No match for this pharmacy+product combination
                # Store helpful context: product, quantity and invoice amount
                unmatched = Unmatched(
                    pharmacy_name=pharmacy_name,
                    generated_id=generated_id,
                    product=str(row.get('product', '')),
                    quantity=int(row.get('quantity', 0)) if pd.notna(row.get('quantity', 0)) else 0,
                    amount=float(row.get('amount', 0.0)) if pd.notna(row.get('amount', 0.0)) else 0.0,
                    user_id=user_id
                )
                db.add(unmatched)
                unmatched_count += 1
                
                logger.info(f"Unmatched: {pharmacy_name} + {row['product']} (No matching pharmacy+product in master)")
        
        # Commit all changes
        db.commit()
        
        # Log the processing action
        audit_log = AuditLog(
            user_id=user_id,
            action="PROCESS_INVOICE_DATA",
            table_name="prms_invoices",
            new_values={
                "matched_count": matched_count,
                "unmatched_count": unmatched_count,
                "total_processed": len(df)
            }
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Processing complete: {matched_count} matched, {unmatched_count} unmatched")
        return matched_count, unmatched_count
        
    except Exception as e:
        logger.error(f"Error merging with master data: {str(e)}")
        db.rollback()
        raise

def get_matched_results_with_doctor_info(db: Session, user_id: int) -> List[Dict]:
    """
    Get matched results with proper doctor allocation and correct output format
    
    Returns:
        List of dictionaries with columns: Doctor_ID | Doctor_Name | REP_Name | Pharmacy_Name | Pharmacy_ID | Product | Quantity | Revenue
    """
    try:
        # Get all invoices
        invoices = db.query(Invoice).filter(Invoice.user_id == user_id).all()
        
        # Get all master data
        master_data = db.query(MasterMapping).all()
        
        # Create lookup by pharmacy_id + normalized_product
        master_lookup = {}
        for record in master_data:
            normalized_product = normalize_product_name(record.product_names)
            key = f"{record.pharmacy_id}|{normalized_product}"
            master_lookup[key] = record
        
        results = []
        for invoice in invoices:
            # Normalize product name for matching
            normalized_product = normalize_product_name(invoice.product)
            
            # Create composite key for lookup
            lookup_key = f"{invoice.pharmacy_id}|{normalized_product}"
            
            # Find matching master record
            master_record = master_lookup.get(lookup_key)
            
            if master_record:
                result = {
                    "Doctor_ID": master_record.doctor_id,
                    "Doctor_Name": master_record.doctor_names,
                    "REP_Name": master_record.rep_names,
                    "Pharmacy_Name": invoice.pharmacy_name,
                    "Pharmacy_ID": invoice.pharmacy_id,
                    "Product": invoice.product,
                    "Quantity": invoice.quantity,
                    "Revenue": float(invoice.amount)
                }
                results.append(result)
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting matched results: {str(e)}")
        return []

def create_chart_ready_data(db: Session, user) -> Dict:
    """
    Create chart-ready data for analytics with proper doctor allocation
    
    Args:
        db: Database session
        user: Current user object
    
    Returns:
        Dictionary with chart data
    """
    try:
        # Get all invoices
        invoices = db.query(Invoice).all()
        
        # Get all master data
        master_data = db.query(MasterMapping).all()
        
        # Apply area filter for non-super-admin users
        if user.role != 'super_admin' and user.area:
            master_data = [record for record in master_data if record.area == user.area]
        
        # Create lookup by pharmacy_id + normalized_product
        master_lookup = {}
        for record in master_data:
            normalized_product = normalize_product_name(record.product_names)
            key = f"{record.pharmacy_id}|{normalized_product}"
            master_lookup[key] = record
        
        # Find matched records using strict pharmacy+product matching
        matched_records = []
        for invoice in invoices:
            # Normalize product name for matching
            normalized_product = normalize_product_name(invoice.product)
            
            # Create composite key for lookup
            lookup_key = f"{invoice.pharmacy_id}|{normalized_product}"
            
            # Find matching master record
            master_record = master_lookup.get(lookup_key)
            
            if master_record:
                matched_records.append({
                    'invoice': invoice,
                    'master': master_record
                })
        
        if not matched_records:
            return {
                "total_revenue": 0.0,
                "pharmacy_revenue": [],
                "doctor_revenue": [],
                "rep_revenue": [],
                "hq_revenue": [],
                "area_revenue": [],
                "monthly_revenue": []
            }
        
        # Calculate total revenue
        # Revenue = Quantity × Master.Product_Price
        def _calc_revenue(rec):
            quantity = 0
            try:
                quantity = int(rec['invoice'].quantity or 0)
            except Exception:
                quantity = 0
            price = 0.0
            try:
                price = float(rec['master'].product_price or 0.0)
            except Exception:
                price = 0.0
            return float(quantity) * float(price)

        total_revenue = sum(_calc_revenue(rec) for rec in matched_records)
        
        # Group by pharmacy with extra fields (top product and total quantity)
        pharmacy_stats: Dict[str, Dict] = {}
        for record in matched_records:
            inv = record['invoice']
            mas = record['master']
            pharmacy_name = inv.pharmacy_name
            product = mas.product_names or inv.product
            qty = int(inv.quantity or 0)
            rev = _calc_revenue(record)
            stat = pharmacy_stats.setdefault(pharmacy_name, {"revenue": 0.0, "quantity": 0, "product_map": {}})
            stat["revenue"] += rev
            stat["quantity"] += qty
            stat["product_map"][product] = stat["product_map"].get(product, 0.0) + rev
        
        # Group by doctor with extra fields
        doctor_stats: Dict[str, Dict] = {}
        for record in matched_records:
            inv = record['invoice']
            mas = record['master']
            doctor_name = mas.doctor_names
            pharmacy_name = inv.pharmacy_name
            product = mas.product_names or inv.product
            qty = int(inv.quantity or 0)
            rev = _calc_revenue(record)
            stat = doctor_stats.setdefault(doctor_name, {"revenue": 0.0, "quantity": 0, "product_map": {}, "pharmacy_map": {}})
            stat["revenue"] += rev
            stat["quantity"] += qty
            stat["product_map"][product] = stat["product_map"].get(product, 0.0) + rev
            stat["pharmacy_map"][pharmacy_name] = stat["pharmacy_map"].get(pharmacy_name, 0.0) + rev
        
        # Group by rep with extra fields
        rep_stats: Dict[str, Dict] = {}
        for record in matched_records:
            inv = record['invoice']
            mas = record['master']
            rep_name = mas.rep_names
            pharmacy_name = inv.pharmacy_name
            doctor_name = mas.doctor_names
            product = mas.product_names or inv.product
            qty = int(inv.quantity or 0)
            rev = _calc_revenue(record)
            stat = rep_stats.setdefault(rep_name, {"revenue": 0.0, "quantity": 0, "product_map": {}, "pharmacy_map": {}, "doctor_map": {}})
            stat["revenue"] += rev
            stat["quantity"] += qty
            stat["product_map"][product] = stat["product_map"].get(product, 0.0) + rev
            stat["pharmacy_map"][pharmacy_name] = stat["pharmacy_map"].get(pharmacy_name, 0.0) + rev
            stat["doctor_map"][doctor_name] = stat["doctor_map"].get(doctor_name, 0.0) + rev
        
        # Group by HQ
        hq_revenue = {}
        for record in matched_records:
            hq = record['master'].hq or "Unknown"
            if hq not in hq_revenue:
                hq_revenue[hq] = 0.0
            hq_revenue[hq] += _calc_revenue(record)
        
        # Group by Area
        area_revenue = {}
        for record in matched_records:
            area = record['master'].area or "Unknown"
            if area not in area_revenue:
                area_revenue[area] = 0.0
            area_revenue[area] += _calc_revenue(record)
        
        # Group by Product
        product_revenue = {}
        for record in matched_records:
            product_name = record['master'].product_names or "Unknown"
            if product_name not in product_revenue:
                product_revenue[product_name] = 0.0
            product_revenue[product_name] += _calc_revenue(record)
        
        # Convert to chart/list-friendly format including extra columns
        def _top_key(d: Dict[str, float]) -> str:
            return max(d.items(), key=lambda x: x[1])[0] if d else "-"

        pharmacy_chart_data = []
        for name, stat in sorted(pharmacy_stats.items(), key=lambda x: x[1]["revenue"], reverse=True):
            pharmacy_chart_data.append({
                "name": name,
                "revenue": float(stat["revenue"]),
                "product_name": _top_key(stat["product_map"]),
                "quantity": int(stat["quantity"]),
            })

        doctor_chart_data = []
        for name, stat in sorted(doctor_stats.items(), key=lambda x: x[1]["revenue"], reverse=True):
            doctor_chart_data.append({
                "doctor_name": name,
                "revenue": float(stat["revenue"]),
                "product_name": _top_key(stat["product_map"]),
                "quantity": int(stat["quantity"]),
                "pharmacy_name": _top_key(stat["pharmacy_map"]),
            })

        rep_chart_data = []
        for name, stat in sorted(rep_stats.items(), key=lambda x: x[1]["revenue"], reverse=True):
            rep_chart_data.append({
                "rep_name": name,
                "revenue": float(stat["revenue"]),
                "product_name": _top_key(stat["product_map"]),
                "quantity": int(stat["quantity"]),
                "pharmacy_name": _top_key(stat["pharmacy_map"]),
                "doctor_name": _top_key(stat["doctor_map"]),
            })
        
        hq_chart_data = [
            {"hq": name, "revenue": float(revenue)}
            for name, revenue in sorted(hq_revenue.items(), key=lambda x: x[1], reverse=True)
        ]
        
        area_chart_data = [
            {"area": name, "revenue": float(revenue)}
            for name, revenue in sorted(area_revenue.items(), key=lambda x: x[1], reverse=True)
        ]
        
        product_chart_data = [
            {"product_name": name, "revenue": float(revenue)}
            for name, revenue in sorted(product_revenue.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # Also compute total unique pharmacies from all uploaded invoices
        total_unique_pharmacies = len({inv.pharmacy_name for inv in invoices})
        
        # Calculate growth rate by comparing with previous analysis
        growth_rate = _calculate_growth_rate(db, total_revenue)

        return {
            "total_revenue": float(total_revenue),
            "pharmacy_revenue": pharmacy_chart_data,
            "doctor_revenue": doctor_chart_data,
            "rep_revenue": rep_chart_data,
            "hq_revenue": hq_chart_data,
            "area_revenue": area_chart_data,
            "product_revenue": product_chart_data,
            "monthly_revenue": [],  # Will be implemented later
            "total_unique_pharmacies": total_unique_pharmacies,
            "growth_rate": growth_rate,
        }
        
    except Exception as e:
        logger.error(f"Error creating chart data: {str(e)}")
        return {
            "total_revenue": 0.0,
            "pharmacy_revenue": [],
            "doctor_revenue": [],
            "rep_revenue": [],
            "hq_revenue": [],
            "area_revenue": [],
            "product_revenue": [],
            "monthly_revenue": [],
            "growth_rate": 0.0
        }

def process_master_data(df: pd.DataFrame, user_id: int, db: Session) -> int:
    """
    Process and store master data
    
    Args:
        df: DataFrame with master data
        user_id: ID of the user processing the data
        db: Database session
    
    Returns:
        Number of records processed
    """
    try:
        logger.info(f"Processing {len(df)} master data records...")
        
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
        column_mapping = flexible_column_mapping(df.columns.tolist(), required_columns)
        
        # Check if all required columns are present
        missing_columns = []
        for req_col in required_columns.keys():
            if req_col not in column_mapping.values():
                missing_columns.append(req_col)
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Rename columns to standard names
        df_renamed = df.rename(columns={k: v for v, k in column_mapping.items()})
        
        # Process each row
        processed_count = 0
        for index, row in df_renamed.iterrows():
            try:
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
                db.add(master_record)
                processed_count += 1
                
            except Exception as e:
                logger.warning(f"Error processing master data row {index + 2}: {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        # Log the processing action
        audit_log = AuditLog(
            user_id=user_id,
            action="PROCESS_MASTER_DATA",
            table_name="prms_master_mapping",
            new_values={"processed_count": processed_count}
        )
        db.add(audit_log)
        db.commit()
        
        logger.info(f"Master data processing complete: {processed_count} records processed")
        return processed_count
        
    except Exception as e:
        logger.error(f"Error processing master data: {str(e)}")
        db.rollback()
        raise
