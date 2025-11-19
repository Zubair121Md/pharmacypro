import pandas as pd
import logging
import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileProcessor:
    def __init__(self):
        self.id_counter = {}
        
    def generate_id(self, pharmacy_name: str, row_index: int) -> str:
        """
        Generate ID using the same logic as tasks_enhanced.py
        Uses full pharmacy name for both facility and location parts
        """
        from app.tasks_enhanced import generate_id
        return generate_id(pharmacy_name, pharmacy_name, row_index, {})
    
    def validate_invoice_columns(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that invoice file has required columns
        Expected: Pharmacy_Name | Product | Quantity | Amount
        """
        required_columns = ['Pharmacy_Name', 'Product', 'Quantity', 'Amount']
        missing_columns = []
        
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        return len(missing_columns) == 0, missing_columns
    
    def validate_master_columns(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that master file has required columns
        Expected: REP_Names | Doctor_Names | Doctor_ID | Pharmacy_Names | Pharmacy_ID | 
                 Product_Names | Product_ID | Product_Price | HQ | AREA
        """
        required_columns = [
            'REP_Names', 'Doctor_Names', 'Doctor_ID', 'Pharmacy_Names', 'Pharmacy_ID',
            'Product_Names', 'Product_ID', 'Product_Price', 'HQ', 'AREA'
        ]
        missing_columns = []
        
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        return len(missing_columns) == 0, missing_columns
    
    def process_invoice_file(self, file_path: str) -> Dict:
        """
        Process invoice file and generate pharmacy IDs, storing directly in database
        """
        try:
            from app.database import get_db, Invoice
            
            # Read Excel file
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Validate columns
            is_valid, missing_cols = self.validate_invoice_columns(df)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Missing required columns: {', '.join(missing_cols)}",
                    "processed_rows": 0
                }
            
            # Get database session
            db = next(get_db())
            
            try:
                # Process each row and generate IDs
                processed_data = []
                unmatched_pharmacies = []
                
                for index, row in df.iterrows():
                    pharmacy_name = str(row['Pharmacy_Name']).strip()
                    product = str(row['Product']).strip()
                    quantity = float(row['Quantity']) if pd.notna(row['Quantity']) else 0
                    amount = float(row['Amount']) if pd.notna(row['Amount']) else 0
                    
                    # Use full pharmacy name for both facility and location (no splitting)
                    # Generate ID using the same logic as tasks_enhanced.py
                    from app.tasks_enhanced import generate_id
                    generated_id = generate_id(pharmacy_name, pharmacy_name, index, {})
                    
                    # Store in database
                    if generated_id != 'INVALID':
                        invoice_record = Invoice(
                            pharmacy_id=generated_id.replace('-', '_'),
                            pharmacy_name=pharmacy_name,
                            product=product,
                            quantity=int(quantity),
                            amount=amount,
                            user_id=1  # Default user ID
                        )
                        db.add(invoice_record)
                    
                    processed_row = {
                        "original_pharmacy_name": pharmacy_name,
                        "generated_id": generated_id,
                        "product": product,
                        "quantity": quantity,
                        "amount": amount,
                        "row_index": index + 2  # +2 because Excel is 1-indexed and has header
                    }
                    
                    processed_data.append(processed_row)
                    
                    # Track unmatched pharmacies (those with INVALID IDs)
                    if generated_id == "INVALID":
                        unmatched_pharmacies.append({
                            "pharmacy_name": pharmacy_name,
                            "generated_id": generated_id,
                            "row_index": index + 2,
                            "reason": "Invalid pharmacy name"
                        })
                
                # Commit to database
                db.commit()
                
                # Do not create a RecentUpload here; analysis endpoint will create one
                
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
            
            return {
                "success": True,
                "processed_rows": len(processed_data),
                "data": processed_data,
                "unmatched_pharmacies": unmatched_pharmacies,
                "summary": {
                    "total_rows": len(df),
                    "valid_rows": len([d for d in processed_data if d["generated_id"] != "INVALID"]),
                    "invalid_rows": len(unmatched_pharmacies),
                    "unique_pharmacies": len(set(d["generated_id"] for d in processed_data if d["generated_id"] != "INVALID"))
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing invoice file: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processed_rows": 0
            }
    
    def process_master_file(self, file_path: str) -> Dict:
        """
        Process master file and validate data, storing directly in database
        """
        try:
            from app.database import get_db, MasterMapping
            
            # Read Excel file
            df = pd.read_excel(file_path, engine='openpyxl')
            
            # Validate columns
            is_valid, missing_cols = self.validate_master_columns(df)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Missing required columns: {', '.join(missing_cols)}",
                    "processed_rows": 0
                }
            
            # Get database session
            db = next(get_db())
            
            try:
                # Process and validate data
                processed_data = []
                validation_errors = []
                
                for index, row in df.iterrows():
                    processed_row = {
                        "rep_name": str(row['REP_Names']).strip() if pd.notna(row['REP_Names']) else "",
                        "doctor_name": str(row['Doctor_Names']).strip() if pd.notna(row['Doctor_Names']) else "",
                        "doctor_id": str(row['Doctor_ID']).strip() if pd.notna(row['Doctor_ID']) else "",
                        "pharmacy_name": str(row['Pharmacy_Names']).strip() if pd.notna(row['Pharmacy_Names']) else "",
                        "pharmacy_id": str(row['Pharmacy_ID']).strip() if pd.notna(row['Pharmacy_ID']) else "",
                        "product_name": str(row['Product_Names']).strip() if pd.notna(row['Product_Names']) else "",
                        "product_id": str(row['Product_ID']).strip() if pd.notna(row['Product_ID']) else "",
                        "product_price": float(row['Product_Price']) if pd.notna(row['Product_Price']) else 0.0,
                        "hq": str(row['HQ']).strip() if pd.notna(row['HQ']) else "",
                        "area": str(row['AREA']).strip() if pd.notna(row['AREA']) else "",
                        "row_index": index + 2
                    }
                    
                    # Validate required fields
                    if not processed_row["pharmacy_name"]:
                        validation_errors.append({
                            "row": index + 2,
                            "field": "Pharmacy_Names",
                            "error": "Pharmacy name is required"
                        })
                    
                    if not processed_row["pharmacy_id"]:
                        validation_errors.append({
                            "row": index + 2,
                            "field": "Pharmacy_ID",
                            "error": "Pharmacy ID is required"
                        })
                    
                    if processed_row["product_price"] <= 0:
                        validation_errors.append({
                            "row": index + 2,
                            "field": "Product_Price",
                            "error": "Product price must be greater than 0"
                        })
                    
                    # Store in database if valid
                    if not validation_errors or all(error["row"] != index + 2 for error in validation_errors):
                        master_record = MasterMapping(
                            pharmacy_id=processed_row["pharmacy_id"].replace('-', '_'),
                            pharmacy_names=processed_row["pharmacy_name"],
                            product_names=processed_row["product_name"],
                            product_id=processed_row["product_id"] if processed_row["product_id"] else None,
                            product_price=processed_row["product_price"],
                            doctor_names=processed_row["doctor_name"],
                            doctor_id=processed_row["doctor_id"],
                            rep_names=processed_row["rep_name"],
                            hq=processed_row["hq"],
                            area=processed_row["area"]
                        )
                        db.add(master_record)
                    
                    processed_data.append(processed_row)
                
                # Commit to database
                db.commit()
                
                # Do not create a RecentUpload here; analysis endpoint will create one
                
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
            
            return {
                "success": True,
                "processed_rows": len(processed_data),
                "data": processed_data,
                "validation_errors": validation_errors,
                "summary": {
                    "total_rows": len(df),
                    "valid_rows": len(processed_data) - len(validation_errors),
                    "error_rows": len(validation_errors),
                    "unique_pharmacies": len(set(d["pharmacy_id"] for d in processed_data if d["pharmacy_id"])),
                    "unique_products": len(set(d["product_id"] for d in processed_data if d["product_id"]))
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing master file: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processed_rows": 0
            }
    
    def match_invoice_with_master(self, invoice_data: List[Dict], master_data: List[Dict]) -> Dict:
        """
        Match invoice data with master data using STRICT Pharmacy + Product matching
        """
        # Create master lookup by pharmacy_id + product
        master_lookup = {}
        
        for master_row in master_data:
            # Normalize product name for matching
            normalized_product = self._normalize_product_name(master_row["product_name"])
            key = f"{master_row['pharmacy_id']}|{normalized_product}"
            master_lookup[key] = master_row
        
        matched_data = []
        unmatched_invoices = []
        
        for invoice_row in invoice_data:
            generated_id = invoice_row["generated_id"]
            
            # Normalize ID for matching (replace - with _)
            normalized_id = generated_id.replace("-", "_")
            
            # Normalize product name for matching
            normalized_product = self._normalize_product_name(invoice_row["product"])
            
            # Create composite key for lookup
            lookup_key = f"{normalized_id}|{normalized_product}"
            
            # Try to find exact match for BOTH pharmacy and product
            matched_master = master_lookup.get(lookup_key)
            
            if matched_master:
                # Calculate revenue: Quantity × Master.Product_Price
                quantity = invoice_row["quantity"]
                product_price = matched_master["product_price"]
                calculated_amount = quantity * product_price
                
                matched_row = {
                    **invoice_row,
                    "master_pharmacy_id": matched_master["pharmacy_id"],
                    "master_pharmacy_name": matched_master["pharmacy_name"],
                    "doctor_name": matched_master["doctor_name"],
                    "doctor_id": matched_master["doctor_id"],
                    "rep_name": matched_master["rep_name"],
                    "product_name": matched_master["product_name"],
                    "product_id": matched_master["product_id"],
                    "product_price": product_price,
                    "hq": matched_master["hq"],
                    "area": matched_master["area"],
                    "calculated_amount": calculated_amount,
                    "match_status": "matched"
                }
                matched_data.append(matched_row)
            else:
                # No match for this pharmacy+product combination
                unmatched_invoices.append({
                    **invoice_row,
                    "match_status": "unmatched",
                    "reason": "No matching pharmacy+product combination found in master data"
                })
        
        return {
            "matched_data": matched_data,
            "unmatched_invoices": unmatched_invoices,
            "summary": {
                "total_invoices": len(invoice_data),
                "matched_count": len(matched_data),
                "unmatched_count": len(unmatched_invoices),
                "match_rate": len(matched_data) / len(invoice_data) * 100 if invoice_data else 0
            }
        }
    
    def _normalize_product_name(self, product_name: str) -> str:
        """
        Normalize product name for matching: uppercase, remove punctuation, trim spaces
        """
        if not product_name or pd.isna(product_name):
            return ""
        return re.sub(r'[^\w\s]', '', str(product_name)).strip().upper().replace(' ', '')
