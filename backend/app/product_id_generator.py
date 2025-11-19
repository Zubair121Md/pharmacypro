"""
Product ID Generator with fuzzy matching against reference table
"""
import pandas as pd
import logging
import re
from collections import defaultdict
from typing import Optional, Tuple, Dict
from sqlalchemy.orm import Session
from app.database import ProductReference

logger = logging.getLogger(__name__)

# Common suffixes to remove for normalization
COMMON_SUFFIXES = ['SYP', 'SYRUP', 'EXP', 'EXPT', 'PLUS', 'DSR', 'TAB', 'TABLET', 'GEL', 'DROPS', 'DROP', 'SUSP', 'KID', 'DT', 'LB', 'CV', 'MG', 'O']

def normalize_name(name: str, aggressive: bool = True) -> Optional[str]:
    """
    Normalize product names by removing special characters and parentheses.
    Standardize by gluing numbers to previous words (remove spaces around digits).
    If aggressive=True, also remove numbers and common suffixes for core matching.
    If aggressive=False, keep numbers and suffixes for variant distinction.
    """
    if not name or pd.isna(name):
        return None
    # Remove parentheses content like (6001)
    name = re.sub(r'\([^)]*\)', '', str(name))
    # Remove other special characters (e.g., '-', becomes space or removed)
    name = re.sub(r'[^\w\s]', '', name).strip()
    # Standardize: remove spaces around digits (glue numbers to words, e.g., 'FLOK 20' -> 'FLOK20')
    name = re.sub(r'\s*(\d+)\s*', r'\1', name).strip()
    
    if aggressive:
        # Remove numbers and common suffixes for core
        name = re.sub(r'\d+', '', name).strip()
        name_parts = name.split()
        cleaned_parts = [part for part in name_parts if part.upper() not in COMMON_SUFFIXES]
        name = ' '.join(cleaned_parts).strip()
    
    return name.lower() if name else None

def parse_product_input(raw_input: str) -> Tuple[Optional[str], Optional[int], Optional[float]]:
    """
    Parse raw input like 'ENDOL 250 SUSP 15 26.92' to extract product name, qty, price.
    Looks for trailing ' <positive_int> <float>' pattern; otherwise, full as product.
    Handles cases like 'FLOK -40 37.23' (treats -40 as part of name).
    """
    if not raw_input or pd.isna(raw_input):
        return None, None, None
    s = str(raw_input).strip()
    # Regex to match trailing qty price: space + digits (no leading -) + space + digits.digits
    match = re.search(r'(\s+(\d+)\s+([\d.]+)\s*)$', s)
    if match and match.group(2):  # Valid positive qty and price
        qty = int(match.group(2))
        price = float(match.group(3))
        product = s[:match.start(1)].strip()
        return product, qty, price
    return s, None, None

def build_product_reference_mapping(db: Session) -> Dict:
    """
    Build product reference mapping from database
    Returns: core_to_variants dictionary
    """
    try:
        products = db.query(ProductReference).all()
        
        if not products:
            logger.warning("No product reference data found in database")
            return {}
        
        # Core normalized name to list of (variant, ID, price, original)
        core_to_variants = defaultdict(list)
        
        for product in products:
            core_name = normalize_name(product.product_name, aggressive=True)  # Core for grouping
            variant_name = normalize_name(product.product_name, aggressive=False)  # Full for distinction
            
            if core_name:
                core_to_variants[core_name].append({
                    'variant': variant_name,
                    'ID': product.product_id,
                    'price': float(product.product_price),
                    'original': product.product_name
                })
        
        # Check for duplicates
        for core, variants in core_to_variants.items():
            if len(variants) > 1:
                logger.warning(f"Duplicate core name '{core}': {len(variants)} variants - {[v['original'] for v in variants]}")
        
        return core_to_variants
        
    except Exception as e:
        logger.error(f"Error building product reference mapping: {str(e)}")
        return {}

def find_best_match(input_name: str, core_to_variants: Dict, use_fuzzy: bool = True) -> Tuple[Optional[int], Optional[float], Optional[str]]:
    """
    Find the best match: first try exact on variant, then fuzzy on variants within core group.
    Fallback to global fuzzy if no core group.
    """
    fuzzy_available = False
    if use_fuzzy:
        try:
            from fuzzywuzzy import process
            fuzzy_available = True
        except ImportError:
            logger.warning("fuzzywuzzy not installed, using exact matching only")
            use_fuzzy = False
    
    input_core = normalize_name(input_name, aggressive=True)
    input_variant = normalize_name(input_name, aggressive=False)
    
    if not input_core:
        return None, None, None
    
    # Get candidate variants for this core
    candidates = core_to_variants.get(input_core, [])
    
    if not candidates:
        # No core match, try fuzzy on all variant names (fallback)
        if use_fuzzy and fuzzy_available:
            try:
                from fuzzywuzzy import process
                all_variants = [v['variant'] for vars in core_to_variants.values() for v in vars]
                fuzzy_match = process.extractOne(input_variant, all_variants, score_cutoff=75)
                if fuzzy_match:
                    matched_variant, score = fuzzy_match
                    # Find the exact variant entry
                    for core, vars in core_to_variants.items():
                        for v in vars:
                            if v['variant'] == matched_variant:
                                return v['ID'], v['price'], v['original']
            except Exception as e:
                logger.warning(f"Fuzzy matching error: {str(e)}")
        return None, None, None
    
    # Exact match on variant
    for cand in candidates:
        if cand['variant'] == input_variant:
            return cand['ID'], cand['price'], cand['original']
    
    # Fuzzy match within core variants (higher cutoff for precision)
    if use_fuzzy and fuzzy_available and len(candidates) > 1:
        try:
            from fuzzywuzzy import process
            fuzzy_matches = process.extractBests(input_variant, [c['variant'] for c in candidates], score_cutoff=80, limit=len(candidates))
            if fuzzy_matches:
                # Pick the highest score
                best_match = max(fuzzy_matches, key=lambda x: x[1])
                matched_variant, score = best_match
                for cand in candidates:
                    if cand['variant'] == matched_variant:
                        return cand['ID'], cand['price'], cand['original']
        except Exception as e:
            logger.warning(f"Fuzzy matching error: {str(e)}")
    
    # If no fuzzy within group, pick the first (or log choice)
    if candidates:
        first = candidates[0]
        logger.warning(f"Input '{input_name}': No exact/fuzzy match in core '{input_core}', defaulting to '{first['original']}'")
        return first['ID'], first['price'], first['original']
    
    return None, None, None

def generate_product_id(product_name: str, db: Session) -> Tuple[Optional[int], Optional[float], Optional[str]]:
    """
    Generate product ID by matching against reference table
    Returns: (product_id, product_price, matched_original_name) or (None, None, None) if not found
    """
    try:
        core_to_variants = build_product_reference_mapping(db)
        
        if not core_to_variants:
            logger.warning("Product reference table is empty")
            return None, None, None
        
        product_id, price, matched_original = find_best_match(product_name, core_to_variants)
        
        if product_id:
            logger.info(f"Matched '{product_name}' to '{matched_original}' (ID: {product_id}, Price: {price})")
        else:
            logger.warning(f"Unmatched product name: {product_name}")
        
        return product_id, price, matched_original
        
    except Exception as e:
        logger.error(f"Error generating product ID: {str(e)}")
        return None, None, None

