"""
ML Trust Scorer using Gradient Boosting.

This module implements a machine learning model that enhances the rule-based
verification system by learning patterns from police-validated reports.

Training Data:
- Features extracted from reports (temporal, spatial, evidence)
- Labels from police verification (correct/false reports)

The model starts with rule-based scores and progressively improves
as more validated data becomes available.
"""

import os
import pickle
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np

# Graceful import handling
try:
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class MLTrustScorer:
    """
    Machine Learning Trust Scorer using Gradient Boosting.
    
    This model predicts the likelihood that a report is credible
    based on features extracted from the report and reporter behavior.
    
    Features used:
    - Hour of day (cyclic encoding)
    - Day of week (cyclic encoding)
    - Has evidence (binary)
    - Evidence count (numeric)
    - Has GPS (binary)
    - GPS within bounds (binary)
    - Rule-based score (numeric)
    - Device report count (numeric)
    - Device historical accuracy (numeric)
    - Incident type (categorical encoded)
    
    The model is trained on police-validated reports and predicts
    a trust probability between 0 and 1.
    """
    
    # Feature names in order
    FEATURE_NAMES = [
        'hour_sin', 'hour_cos',         # Cyclic hour encoding
        'dow_sin', 'dow_cos',           # Cyclic day of week encoding  
        'has_evidence',                  # Binary
        'evidence_count',                # Numeric
        'has_gps',                       # Binary
        'gps_valid',                     # Binary
        'rule_based_score',              # Numeric 0-1
        'device_report_count',           # Numeric
        'device_accuracy',               # Numeric 0-1
        'incident_type_encoded',         # Numeric (categorical)
    ]
    
    # Incident type encoding
    INCIDENT_TYPES = {
        'theft': 0,
        'burglary': 1,
        'assault': 2,
        'vandalism': 3,
        'robbery': 4,
        'fraud': 5,
        'drugs': 6,
        'violence': 7,
        'suspicious_activity': 8,
        'traffic': 9,
        'other': 10,
    }
    
    # Minimum samples needed before training
    MIN_TRAINING_SAMPLES = 50
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the ML Trust Scorer.
        
        Args:
            model_path: Path to save/load the trained model
        """
        self.model_path = model_path or 'ml_models/trust_scorer.pkl'
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.training_samples = 0
        self.last_trained = None
        
        if SKLEARN_AVAILABLE:
            self._initialize_model()
            self._load_model()
        else:
            logger.warning("scikit-learn not available. ML scoring disabled.")
    
    def _initialize_model(self):
        """Initialize a new Gradient Boosting model."""
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            validation_fraction=0.1,
            n_iter_no_change=10,
        )
        self.scaler = StandardScaler()
    
    def _load_model(self):
        """Load a previously trained model if available."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.scaler = data['scaler']
                    self.is_trained = data.get('is_trained', True)
                    self.training_samples = data.get('training_samples', 0)
                    self.last_trained = data.get('last_trained')
                logger.info(f"Loaded ML model with {self.training_samples} training samples")
            except Exception as e:
                logger.error(f"Failed to load ML model: {e}")
                self._initialize_model()
    
    def _save_model(self):
        """Save the trained model to disk."""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'is_trained': self.is_trained,
                    'training_samples': self.training_samples,
                    'last_trained': self.last_trained,
                }, f)
            logger.info(f"Saved ML model to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save ML model: {e}")
    
    def extract_features(
        self,
        report_data: Dict,
        rule_based_result: Dict,
        device_history: Optional[Dict] = None
    ) -> np.ndarray:
        """
        Extract features from a report for ML scoring.
        
        Args:
            report_data: The report data
            rule_based_result: Results from rule-based verification
            device_history: Device's historical data
        
        Returns:
            Feature vector as numpy array
        """
        features = []
        
        # 1. Hour of day (cyclic encoding)
        timestamp = report_data.get('timestamp') or report_data.get('created_at')
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    dt = datetime.utcnow()
            else:
                dt = timestamp
        else:
            dt = datetime.utcnow()
        
        hour = dt.hour
        features.append(np.sin(2 * np.pi * hour / 24))  # hour_sin
        features.append(np.cos(2 * np.pi * hour / 24))  # hour_cos
        
        # 2. Day of week (cyclic encoding)
        dow = dt.weekday()
        features.append(np.sin(2 * np.pi * dow / 7))    # dow_sin
        features.append(np.cos(2 * np.pi * dow / 7))    # dow_cos
        
        # 3. Evidence features
        evidence = report_data.get('attachments') or report_data.get('evidence') or []
        features.append(1.0 if len(evidence) > 0 else 0.0)  # has_evidence
        features.append(min(len(evidence), 5) / 5.0)         # evidence_count (normalized)
        
        # 4. GPS features
        lat = report_data.get('latitude')
        lng = report_data.get('longitude')
        features.append(1.0 if lat and lng else 0.0)  # has_gps
        
        gps_result = rule_based_result.get('rule_results', {}).get('gps_valid', {})
        features.append(1.0 if gps_result.get('passed') else 0.0)  # gps_valid
        
        # 5. Rule-based score
        features.append(rule_based_result.get('overall_score', 0.5))  # rule_based_score
        
        # 6. Device history features
        if device_history:
            total = device_history.get('total_reports', 0)
            verified = device_history.get('verified_reports', 0)
            features.append(min(total, 20) / 20.0)  # device_report_count (normalized)
            features.append(verified / total if total > 0 else 0.5)  # device_accuracy
        else:
            features.append(0.0)  # device_report_count
            features.append(0.5)  # device_accuracy (neutral)
        
        # 7. Incident type
        incident_type = report_data.get('incident_type', 'other').lower()
        type_encoded = self.INCIDENT_TYPES.get(incident_type, 10)
        features.append(type_encoded / 10.0)  # incident_type_encoded (normalized)
        
        return np.array(features).reshape(1, -1)
    
    def predict_trust(
        self,
        report_data: Dict,
        rule_based_result: Dict,
        device_history: Optional[Dict] = None
    ) -> Dict:
        """
        Predict trust score using ML model.
        
        If model is not trained, returns rule-based score with ML adjustment.
        
        Args:
            report_data: The report data
            rule_based_result: Results from rule-based verification
            device_history: Device's historical data
        
        Returns:
            Dictionary with ML-enhanced trust score and explanation
        """
        result = {
            'ml_score': None,
            'confidence': 0.0,
            'method': 'rule_based',
            'rule_based_score': rule_based_result.get('overall_score', 0.5),
            'features_used': self.FEATURE_NAMES,
        }
        
        if not SKLEARN_AVAILABLE:
            result['ml_score'] = result['rule_based_score']
            result['explanation'] = 'ML libraries not available'
            return result
        
        features = self.extract_features(report_data, rule_based_result, device_history)
        
        if not self.is_trained:
            # Use rule-based score when model isn't trained yet
            result['ml_score'] = result['rule_based_score']
            result['method'] = 'rule_based'
            result['explanation'] = f'ML model not yet trained (need {self.MIN_TRAINING_SAMPLES} samples, have {self.training_samples})'
            return result
        
        try:
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Get probability of being credible (class 1)
            proba = self.model.predict_proba(features_scaled)[0]
            
            result['ml_score'] = float(proba[1])  # Probability of being credible
            result['confidence'] = float(abs(proba[1] - 0.5) * 2)  # How confident
            result['method'] = 'gradient_boosting'
            result['explanation'] = f'ML prediction based on {self.training_samples} training samples'
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            result['ml_score'] = result['rule_based_score']
            result['explanation'] = f'ML prediction error: {str(e)}'
        
        return result
    
    def get_combined_score(
        self,
        report_data: Dict,
        rule_based_result: Dict,
        device_history: Optional[Dict] = None
    ) -> Tuple[float, str]:
        """
        Get combined trust score from rule-based and ML systems.
        
        Combines scores with adaptive weighting based on ML confidence.
        
        Returns:
            Tuple of (combined_score, classification)
        """
        ml_result = self.predict_trust(report_data, rule_based_result, device_history)
        
        rule_score = ml_result['rule_based_score']
        ml_score = ml_result['ml_score']
        confidence = ml_result['confidence']
        
        if ml_result['method'] == 'rule_based':
            # Not using ML, just return rule-based
            combined = rule_score
        else:
            # Adaptive weighting: more weight to ML when confident
            ml_weight = 0.3 + (confidence * 0.4)  # 0.3 to 0.7
            rule_weight = 1.0 - ml_weight
            combined = (rule_score * rule_weight) + (ml_score * ml_weight)
        
        # Classify
        if combined >= 0.75:
            classification = 'trusted'
        elif combined >= 0.45:
            classification = 'delayed'
        else:
            classification = 'suspicious'
        
        return combined, classification
    
    def train(self, training_data: List[Dict]) -> Dict:
        """
        Train the ML model on validated report data.
        
        Args:
            training_data: List of dicts with 'features' and 'label' keys
                          label: 1 = credible, 0 = false report
        
        Returns:
            Training results including accuracy
        """
        if not SKLEARN_AVAILABLE:
            return {'success': False, 'error': 'scikit-learn not available'}
        
        if len(training_data) < self.MIN_TRAINING_SAMPLES:
            return {
                'success': False,
                'error': f'Need at least {self.MIN_TRAINING_SAMPLES} samples, got {len(training_data)}'
            }
        
        try:
            # Extract features and labels
            X = np.array([d['features'] for d in training_data])
            y = np.array([d['label'] for d in training_data])
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Fit scaler and transform
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            
            # Update state
            self.is_trained = True
            self.training_samples = len(training_data)
            self.last_trained = datetime.utcnow().isoformat()
            
            # Save model
            self._save_model()
            
            return {
                'success': True,
                'training_samples': len(training_data),
                'train_accuracy': train_score,
                'test_accuracy': test_score,
                'last_trained': self.last_trained,
            }
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def add_training_sample(
        self,
        report_data: Dict,
        rule_based_result: Dict,
        device_history: Optional[Dict],
        is_credible: bool
    ):
        """
        Add a single validated sample to training queue.
        
        Samples are stored until MIN_TRAINING_SAMPLES is reached,
        then model is automatically retrained.
        """
        # This would typically store to database for batch training
        # For now, just log it
        features = self.extract_features(report_data, rule_based_result, device_history)
        logger.info(f"Training sample added: credible={is_credible}, features_shape={features.shape}")
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model."""
        if not self.is_trained or not hasattr(self.model, 'feature_importances_'):
            return {}
        
        importances = self.model.feature_importances_
        return dict(zip(self.FEATURE_NAMES, importances))
    
    def get_model_info(self) -> Dict:
        """Get information about the current model state."""
        return {
            'ml_available': SKLEARN_AVAILABLE,
            'is_trained': self.is_trained,
            'training_samples': self.training_samples,
            'last_trained': self.last_trained,
            'min_samples_required': self.MIN_TRAINING_SAMPLES,
            'feature_count': len(self.FEATURE_NAMES),
            'feature_names': self.FEATURE_NAMES,
        }
