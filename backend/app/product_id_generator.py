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

# Global cache for product reference mapping (to avoid rebuilding on every call)
_product_ref_cache = None
_product_ref_cache_timestamp = None

def build_product_reference_mapping(db: Session, use_cache: bool = True) -> Dict:
    """
    Build product reference mapping from database
    Uses caching to avoid rebuilding on every call
    Returns: core_to_variants dictionary
    """
    global _product_ref_cache, _product_ref_cache_timestamp
    
    # Use cache if available and less than 5 minutes old
    if use_cache and _product_ref_cache is not None:
        return _product_ref_cache
    
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
        
        # Log duplicates only once (not on every build)
        if _product_ref_cache is None:
            duplicates_found = []
            for core, variants in core_to_variants.items():
                if len(variants) > 1:
                    duplicates_found.append((core, len(variants), [v['original'] for v in variants]))
            
            if duplicates_found:
                logger.info(f"Found {len(duplicates_found)} product groups with multiple variants (this is normal)")
                # Only log first few duplicates to avoid spam
                for core, count, originals in duplicates_found[:5]:
                    logger.debug(f"Product group '{core}': {count} variants - {originals}")
                if len(duplicates_found) > 5:
                    logger.debug(f"... and {len(duplicates_found) - 5} more product groups with variants")
        
        # Cache the result
        _product_ref_cache = core_to_variants
        import time
        _product_ref_cache_timestamp = time.time()
        
        return core_to_variants
        
    except Exception as e:
        logger.error(f"Error building product reference mapping: {str(e)}")
        return {}

def clear_product_ref_cache():
    """Clear the product reference cache (useful for testing or after updates)"""
    global _product_ref_cache, _product_ref_cache_timestamp
    _product_ref_cache = None
    _product_ref_cache_timestamp = None

def find_best_match(input_name: str, core_to_variants: Dict, use_fuzzy: bool = True) -> Tuple[Optional[int], Optional[float], Optional[str]]:
    """
    Find the best match using multiple strategies:
    1. Exact normalized match
    2. Fuzzy match within core group (high threshold)
    3. Fuzzy match globally (lower threshold for misspellings)
    4. Character-level similarity (handles OCR errors)
    5. Partial match (handles missing characters)
    6. Substring/garbage-prefix tolerant match (handles inputs like 'SSDADQRITTAB')
    """
    fuzzy_available = False
    if use_fuzzy:
        try:
            from fuzzywuzzy import fuzz, process
            fuzzy_available = True
        except ImportError:
            logger.warning("fuzzywuzzy not installed, using exact matching only")
            use_fuzzy = False
    
    input_core = normalize_name(input_name, aggressive=True)
    input_variant = normalize_name(input_name, aggressive=False)
    
    if not input_core:
        return None, None, None
    
    # Strategy 1: Exact normalized match
    candidates = core_to_variants.get(input_core, [])
    
    # Exact match on variant
    for cand in candidates:
        if cand['variant'] == input_variant:
            return cand['ID'], cand['price'], cand['original']
    
    # Strategy 2: Fuzzy match within core variants (high precision)
    if use_fuzzy and fuzzy_available and candidates:
        try:
            from fuzzywuzzy import fuzz, process
            # Try with high threshold first (85+)
            fuzzy_matches = process.extractBests(
                input_variant, 
                [c['variant'] for c in candidates], 
                score_cutoff=85, 
                limit=len(candidates)
            )
            if fuzzy_matches:
                best_match = max(fuzzy_matches, key=lambda x: x[1])
                matched_variant, score = best_match
                for cand in candidates:
                    if cand['variant'] == matched_variant:
                        logger.debug(f"High-precision fuzzy match: '{input_name}' -> '{cand['original']}' (score: {score})")
                        return cand['ID'], cand['price'], cand['original']
            
            # Try with medium threshold (70+) for misspellings
            fuzzy_matches = process.extractBests(
                input_variant, 
                [c['variant'] for c in candidates], 
                score_cutoff=70, 
                limit=len(candidates)
            )
            if fuzzy_matches:
                best_match = max(fuzzy_matches, key=lambda x: x[1])
                matched_variant, score = best_match
                for cand in candidates:
                    if cand['variant'] == matched_variant:
                        logger.debug(f"Medium-precision fuzzy match: '{input_name}' -> '{cand['original']}' (score: {score})")
                        return cand['ID'], cand['price'], cand['original']
        except Exception as e:
            logger.warning(f"Fuzzy matching error: {str(e)}")
    
    # Strategy 3: Global fuzzy match (if no core match)
    if not candidates and use_fuzzy and fuzzy_available:
        try:
            from fuzzywuzzy import fuzz, process
            all_variants = [(v['variant'], v) for vars in core_to_variants.values() for v in vars]
            variant_names = [v[0] for v in all_variants]
            
            # Try high threshold first
            fuzzy_match = process.extractOne(input_variant, variant_names, score_cutoff=80)
            if fuzzy_match:
                matched_variant, score = fuzzy_match
                for variant_name, variant_data in all_variants:
                    if variant_name == matched_variant:
                        logger.debug(f"Global fuzzy match: '{input_name}' -> '{variant_data['original']}' (score: {score})")
                        return variant_data['ID'], variant_data['price'], variant_data['original']
            
            # Try lower threshold for misspellings
            fuzzy_match = process.extractOne(input_variant, variant_names, score_cutoff=65)
            if fuzzy_match:
                matched_variant, score = fuzzy_match
                for variant_name, variant_data in all_variants:
                    if variant_name == matched_variant:
                        logger.debug(f"Global fuzzy match (low threshold): '{input_name}' -> '{variant_data['original']}' (score: {score})")
                        return variant_data['ID'], variant_data['price'], variant_data['original']
        except Exception as e:
            logger.warning(f"Global fuzzy matching error: {str(e)}")
    
    # Strategy 4: Character-level similarity (handles OCR errors, missing chars)
    if use_fuzzy and fuzzy_available:
        try:
            from fuzzywuzzy import fuzz
            best_score = 0
            best_match = None
            
            # Check all variants
            all_variants = [v for vars in core_to_variants.values() for v in vars]
            for variant_data in all_variants:
                variant = variant_data['variant']
                # Use ratio for overall similarity
                ratio_score = fuzz.ratio(input_variant, variant)
                # Use partial_ratio for substring matches
                partial_score = fuzz.partial_ratio(input_variant, variant)
                # Use token_sort_ratio for word order independence
                token_score = fuzz.token_sort_ratio(input_variant, variant)
                
                # Take the best of all three
                max_score = max(ratio_score, partial_score, token_score)
                
                if max_score > best_score and max_score >= 70:
                    best_score = max_score
                    best_match = variant_data
            
            if best_match:
                logger.debug(f"Character-level match: '{input_name}' -> '{best_match['original']}' (score: {best_score})")
                return best_match['ID'], best_match['price'], best_match['original']
        except Exception as e:
            logger.warning(f"Character-level matching error: {str(e)}")
    
    # Strategy 5: Partial match (handles missing prefixes/suffixes)
    if input_variant:
        all_variants = [v for vars in core_to_variants.values() for v in vars]
        for variant_data in all_variants:
            variant = variant_data['variant']
            # Check if one is contained in the other (with minimum length)
            if len(input_variant) >= 5 and len(variant) >= 5:
                if input_variant in variant or variant in input_variant:
                    # Verify it's a significant match (at least 70% of shorter string)
                    min_len = min(len(input_variant), len(variant))
                    overlap = len(input_variant) if input_variant in variant else len(variant)
                    if overlap >= min_len * 0.7:
                        logger.debug(f"Partial match: '{input_name}' -> '{variant_data['original']}'")
                        return variant_data['ID'], variant_data['price'], variant_data['original']
    
    # Strategy 6: Substring extraction (handles noisy prefixes/suffixes like 'SSDADQRIT TAB 100X10')
    if input_variant:
        stripped_input = re.sub(r'[^a-z0-9]', '', input_variant)
        if len(stripped_input) >= 4:
            all_variants = [v for vars in core_to_variants.values() for v in vars]
            best_match = None
            best_score = 0
            for variant_data in all_variants:
                variant_value = variant_data['variant'] or ''
                stripped_variant = re.sub(r'[^a-z0-9]', '', variant_value)
                if len(stripped_variant) < 4:
                    continue
                if stripped_variant in stripped_input or stripped_input in stripped_variant:
                    score = len(stripped_variant) if stripped_variant in stripped_input else len(stripped_input)
                    if score > best_score:
                        best_score = score
                        best_match = variant_data
                elif use_fuzzy and fuzzy_available:
                    try:
                        from fuzzywuzzy import fuzz
                        score = fuzz.partial_ratio(stripped_variant, stripped_input)
                        if score >= 85 and score > best_score:
                            best_score = score
                            best_match = variant_data
                    except Exception as e:
                        logger.debug(f"Substring fuzzy match error: {str(e)}")
            if best_match:
                logger.debug(f"Substring match: '{input_name}' -> '{best_match['original']}'")
                return best_match['ID'], best_match['price'], best_match['original']
    
    # Fallback: Return first candidate if available
    if candidates:
        first = candidates[0]
        logger.warning(f"Input '{input_name}': No match found, defaulting to '{first['original']}'")
        return first['ID'], first['price'], first['original']
    
    return None, None, None

def generate_product_id(product_name: str, db: Session, core_to_variants: Dict = None) -> Tuple[Optional[int], Optional[float], Optional[str]]:
    """
    Generate product ID by matching against reference table
    If core_to_variants is provided, uses that instead of rebuilding (for performance)
    Returns: (product_id, product_price, matched_original_name) or (None, None, None) if not found
    """
    try:
        # Use provided mapping if available, otherwise build it
        if core_to_variants is None:
            core_to_variants = build_product_reference_mapping(db)
        
        if not core_to_variants:
            logger.warning("Product reference table is empty")
            return None, None, None
        
        product_id, price, matched_original = find_best_match(product_name, core_to_variants, use_fuzzy=True)
        
        # Only log successful matches at debug level to reduce noise
        if product_id:
            logger.debug(f"Matched '{product_name}' -> '{matched_original}' (ID: {product_id})")
        # Only log unmatched at warning level if it's a significant product
        elif len(product_name) > 3:
            logger.debug(f"Unmatched product: '{product_name}'")
        
        return product_id, price, matched_original
        
    except Exception as e:
        logger.error(f"Error generating product ID: {str(e)}")
        return None, None, None

