"""
ML Models for Pharmacy Revenue Management System
Version: 2.0
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PharmacyMatcher:
    """ML-based pharmacy name matching for unmatched records"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            max_features=1000,
            stop_words='english',
            lowercase=True
        )
        self.master_pharmacy_names = []
        self.master_vectors = None
        self.is_trained = False
        
    def train(self, master_pharmacy_names: List[str]):
        """Train the matcher with master pharmacy names"""
        try:
            logger.info(f"Training pharmacy matcher with {len(master_pharmacy_names)} names")
            
            # Clean and normalize names
            cleaned_names = [self._clean_pharmacy_name(name) for name in master_pharmacy_names]
            
            # Remove duplicates and empty names
            unique_names = list(set([name for name in cleaned_names if name.strip()]))
            
            if len(unique_names) < 2:
                logger.warning("Not enough unique pharmacy names for training")
                return False
            
            # Fit vectorizer
            self.master_vectors = self.vectorizer.fit_transform(unique_names)
            self.master_pharmacy_names = unique_names
            self.is_trained = True
            
            logger.info(f"Pharmacy matcher trained successfully with {len(unique_names)} unique names")
            return True
            
        except Exception as e:
            logger.error(f"Error training pharmacy matcher: {str(e)}")
            return False
    
    def find_best_match(self, query_name: str, threshold: float = 0.7) -> Optional[Dict]:
        """Find the best match for a pharmacy name"""
        if not self.is_trained:
            logger.warning("Pharmacy matcher not trained")
            return None
        
        try:
            # Clean query name
            cleaned_query = self._clean_pharmacy_name(query_name)
            
            if not cleaned_query.strip():
                return None
            
            # Vectorize query
            query_vector = self.vectorizer.transform([cleaned_query])
            
            # Calculate similarities
            similarities = cosine_similarity(query_vector, self.master_vectors)[0]
            
            # Find best match
            best_idx = np.argmax(similarities)
            best_similarity = similarities[best_idx]
            
            if best_similarity >= threshold:
                return {
                    'matched_name': self.master_pharmacy_names[best_idx],
                    'similarity': float(best_similarity),
                    'confidence': self._calculate_confidence(best_similarity),
                    'original_query': query_name
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding match for '{query_name}': {str(e)}")
            return None
    
    def find_multiple_matches(self, query_name: str, top_k: int = 5, threshold: float = 0.5) -> List[Dict]:
        """Find multiple potential matches"""
        if not self.is_trained:
            return []
        
        try:
            cleaned_query = self._clean_pharmacy_name(query_name)
            if not cleaned_query.strip():
                return []
            
            query_vector = self.vectorizer.transform([cleaned_query])
            similarities = cosine_similarity(query_vector, self.master_vectors)[0]
            
            # Get top k matches
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            matches = []
            for idx in top_indices:
                similarity = similarities[idx]
                if similarity >= threshold:
                    matches.append({
                        'matched_name': self.master_pharmacy_names[idx],
                        'similarity': float(similarity),
                        'confidence': self._calculate_confidence(similarity),
                        'original_query': query_name
                    })
            
            return matches
            
        except Exception as e:
            logger.error(f"Error finding multiple matches for '{query_name}': {str(e)}")
            return []
    
    def _clean_pharmacy_name(self, name: str) -> str:
        """Clean and normalize pharmacy name"""
        if not name:
            return ""
        
        # Convert to lowercase
        cleaned = name.lower().strip()
        
        # Remove common pharmacy suffixes
        suffixes = ['pharmacy', 'medical', 'medicals', 'store', 'shop', 'center', 'centre']
        for suffix in suffixes:
            if cleaned.endswith(f' {suffix}'):
                cleaned = cleaned[:-len(f' {suffix}')].strip()
        
        # Remove special characters except spaces and hyphens
        cleaned = re.sub(r'[^\w\s-]', '', cleaned)
        
        # Normalize spaces
        cleaned = ' '.join(cleaned.split())
        
        return cleaned
    
    def _calculate_confidence(self, similarity: float) -> str:
        """Calculate confidence level based on similarity score"""
        if similarity >= 0.9:
            return "Very High"
        elif similarity >= 0.8:
            return "High"
        elif similarity >= 0.7:
            return "Medium"
        elif similarity >= 0.6:
            return "Low"
        else:
            return "Very Low"
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        try:
            model_data = {
                'vectorizer': self.vectorizer,
                'master_pharmacy_names': self.master_pharmacy_names,
                'master_vectors': self.master_vectors,
                'is_trained': self.is_trained
            }
            joblib.dump(model_data, filepath)
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
    
    def load_model(self, filepath: str):
        """Load a trained model"""
        try:
            if os.path.exists(filepath):
                model_data = joblib.load(filepath)
                self.vectorizer = model_data['vectorizer']
                self.master_pharmacy_names = model_data['master_pharmacy_names']
                self.master_vectors = model_data['master_vectors']
                self.is_trained = model_data['is_trained']
                logger.info(f"Model loaded from {filepath}")
                return True
            else:
                logger.warning(f"Model file not found: {filepath}")
                return False
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False

class AnomalyDetector:
    """ML-based anomaly detection for revenue patterns"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_columns = ['amount', 'quantity', 'pharmacy_count', 'daily_avg']
    
    def train(self, revenue_data: pd.DataFrame):
        """Train the anomaly detector"""
        try:
            logger.info(f"Training anomaly detector with {len(revenue_data)} records")
            
            # Prepare features
            features = self._prepare_features(revenue_data)
            
            if len(features) < 10:
                logger.warning("Not enough data for anomaly detection training")
                return False
            
            # Scale features
            scaled_features = self.scaler.fit_transform(features)
            
            # Train model
            self.isolation_forest.fit(scaled_features)
            self.is_trained = True
            
            logger.info("Anomaly detector trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training anomaly detector: {str(e)}")
            return False
    
    def detect_anomalies(self, revenue_data: pd.DataFrame) -> pd.DataFrame:
        """Detect anomalies in revenue data"""
        if not self.is_trained:
            logger.warning("Anomaly detector not trained")
            return pd.DataFrame()
        
        try:
            features = self._prepare_features(revenue_data)
            scaled_features = self.scaler.transform(features)
            
            # Predict anomalies
            anomaly_scores = self.isolation_forest.decision_function(scaled_features)
            is_anomaly = self.isolation_forest.predict(scaled_features) == -1
            
            # Add results to dataframe
            result_df = revenue_data.copy()
            result_df['anomaly_score'] = anomaly_scores
            result_df['is_anomaly'] = is_anomaly
            result_df['anomaly_severity'] = self._calculate_severity(anomaly_scores)
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return pd.DataFrame()
    
    def _prepare_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features for anomaly detection"""
        features = []
        
        for _, row in data.iterrows():
            feature_vector = [
                float(row.get('amount', 0)),
                float(row.get('quantity', 0)),
                float(row.get('pharmacy_count', 1)),
                float(row.get('daily_avg', 0))
            ]
            features.append(feature_vector)
        
        return np.array(features)
    
    def _calculate_severity(self, scores: np.ndarray) -> List[str]:
        """Calculate anomaly severity levels"""
        severities = []
        for score in scores:
            if score < -0.5:
                severities.append("High")
            elif score < -0.2:
                severities.append("Medium")
            elif score < 0:
                severities.append("Low")
            else:
                severities.append("Normal")
        return severities
    
    def save_model(self, filepath: str):
        """Save the trained model"""
        try:
            model_data = {
                'isolation_forest': self.isolation_forest,
                'scaler': self.scaler,
                'is_trained': self.is_trained,
                'feature_columns': self.feature_columns
            }
            joblib.dump(model_data, filepath)
            logger.info(f"Anomaly detector saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving anomaly detector: {str(e)}")
    
    def load_model(self, filepath: str):
        """Load a trained model"""
        try:
            if os.path.exists(filepath):
                model_data = joblib.load(filepath)
                self.isolation_forest = model_data['isolation_forest']
                self.scaler = model_data['scaler']
                self.is_trained = model_data['is_trained']
                self.feature_columns = model_data['feature_columns']
                logger.info(f"Anomaly detector loaded from {filepath}")
                return True
            else:
                logger.warning(f"Model file not found: {filepath}")
                return False
        except Exception as e:
            logger.error(f"Error loading anomaly detector: {str(e)}")
            return False

class MLModelManager:
    """Manager for all ML models"""
    
    def __init__(self):
        self.pharmacy_matcher = PharmacyMatcher()
        self.anomaly_detector = AnomalyDetector()
        self.models_dir = "models"
        
        # Create models directory if it doesn't exist
        os.makedirs(self.models_dir, exist_ok=True)
    
    def initialize_models(self, master_pharmacy_names: List[str], revenue_data: pd.DataFrame):
        """Initialize and train all models"""
        try:
            logger.info("Initializing ML models...")
            
            # Train pharmacy matcher
            pharmacy_success = self.pharmacy_matcher.train(master_pharmacy_names)
            
            # Train anomaly detector
            anomaly_success = self.anomaly_detector.train(revenue_data)
            
            if pharmacy_success and anomaly_success:
                logger.info("All ML models initialized successfully")
                return True
            else:
                logger.warning("Some models failed to initialize")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
            return False
    
    def save_all_models(self):
        """Save all trained models"""
        try:
            self.pharmacy_matcher.save_model(f"{self.models_dir}/pharmacy_matcher.joblib")
            self.anomaly_detector.save_model(f"{self.models_dir}/anomaly_detector.joblib")
            logger.info("All models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {str(e)}")
    
    def load_all_models(self):
        """Load all trained models"""
        try:
            pharmacy_loaded = self.pharmacy_matcher.load_model(f"{self.models_dir}/pharmacy_matcher.joblib")
            anomaly_loaded = self.anomaly_detector.load_model(f"{self.models_dir}/anomaly_detector.joblib")
            
            if pharmacy_loaded and anomaly_loaded:
                logger.info("All models loaded successfully")
                return True
            else:
                logger.warning("Some models failed to load")
                return False
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            return False
    
    def get_model_status(self) -> Dict:
        """Get status of all models"""
        return {
            'pharmacy_matcher': {
                'trained': self.pharmacy_matcher.is_trained,
                'master_count': len(self.pharmacy_matcher.master_pharmacy_names)
            },
            'anomaly_detector': {
                'trained': self.anomaly_detector.is_trained,
                'feature_count': len(self.anomaly_detector.feature_columns)
            }
        }
