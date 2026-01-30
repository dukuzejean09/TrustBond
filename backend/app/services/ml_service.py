"""
ML Service - Machine Learning model management and predictions
"""
from app import db
from app.models.ml_models import MLModel, MLPrediction, MLTrainingData
from app.models.incident_report import IncidentReport
from datetime import datetime
import uuid
import numpy as np
import json


class MLService:
    """Service for ML model management and predictions"""
    
    # ==================== MODEL MANAGEMENT ====================
    @staticmethod
    def get_all_models(active_only=False):
        """Get all ML models"""
        query = MLModel.query
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(MLModel.created_at.desc()).all()
    
    @staticmethod
    def get_model_by_id(model_id):
        """Get model by ID"""
        return MLModel.query.get(model_id)
    
    @staticmethod
    def get_champion_model():
        """Get the current champion (best) model"""
        return MLModel.query.filter_by(is_champion=True, is_active=True).first()
    
    @staticmethod
    def create_model(data, created_by_user_id):
        """Create a new ML model record"""
        model = MLModel(
            model_name=data['model_name'],
            model_version=data['model_version'],
            model_type=data['model_type'],
            model_file_path=data.get('model_file_path'),
            model_file_hash=data.get('model_file_hash'),
            model_size_kb=data.get('model_size_kb'),
            trained_at=data.get('trained_at'),
            training_dataset_size=data.get('training_dataset_size'),
            training_duration_seconds=data.get('training_duration_seconds'),
            accuracy=data.get('accuracy'),
            precision_score=data.get('precision_score'),
            recall_score=data.get('recall_score'),
            f1_score=data.get('f1_score'),
            auc_roc=data.get('auc_roc'),
            metrics_by_class=data.get('metrics_by_class'),
            confusion_matrix=data.get('confusion_matrix'),
            feature_names=data.get('feature_names'),
            feature_importance=data.get('feature_importance'),
            threshold_trusted=data.get('threshold_trusted', 70),
            threshold_suspicious=data.get('threshold_suspicious', 40),
            is_active=True,
            is_champion=False,
            training_notes=data.get('training_notes'),
            created_by=created_by_user_id
        )
        db.session.add(model)
        db.session.commit()
        return model
    
    @staticmethod
    def set_champion_model(model_id):
        """Set model as champion"""
        # Unset current champion
        current_champion = MLModel.query.filter_by(is_champion=True).first()
        if current_champion:
            current_champion.is_champion = False
        
        # Set new champion
        model = MLModel.query.get(model_id)
        if model:
            model.is_champion = True
            model.deployed_at = datetime.utcnow()
            db.session.commit()
        return model
    
    @staticmethod
    def deprecate_model(model_id, reason):
        """Deprecate a model"""
        model = MLModel.query.get(model_id)
        if model:
            model.is_active = False
            model.deprecated_at = datetime.utcnow()
            model.deprecation_reason = reason
            db.session.commit()
        return model
    
    # ==================== FEATURE EXTRACTION ====================
    @staticmethod
    def extract_features(report):
        """Extract feature vector from report"""
        features = {}
        
        # Device features
        device = report.device
        if device:
            features['device_trust_score'] = float(device.current_trust_score or 50)
            features['device_total_reports'] = device.total_reports or 0
            features['device_trusted_reports'] = device.trusted_reports or 0
            features['device_false_reports'] = device.false_reports or 0
            features['device_trust_ratio'] = (
                features['device_trusted_reports'] / features['device_total_reports']
                if features['device_total_reports'] > 0 else 0.5
            )
        else:
            features['device_trust_score'] = 50
            features['device_total_reports'] = 0
            features['device_trusted_reports'] = 0
            features['device_false_reports'] = 0
            features['device_trust_ratio'] = 0.5
        
        # Location features
        features['location_accuracy'] = float(report.location_accuracy_meters or 50)
        features['has_precise_location'] = 1 if features['location_accuracy'] < 30 else 0
        
        # Evidence features
        features['photo_count'] = report.photo_count or 0
        features['video_count'] = report.video_count or 0
        features['audio_count'] = report.audio_count or 0
        features['total_evidence'] = features['photo_count'] + features['video_count'] + features['audio_count']
        features['has_evidence'] = 1 if features['total_evidence'] > 0 else 0
        features['evidence_size_kb'] = report.total_evidence_size_kb or 0
        
        # Motion features
        features['motion_score'] = float(report.device_motion_score or 50)
        features['has_motion_data'] = 1 if report.accelerometer_data else 0
        
        # Content features
        features['description_length'] = len(report.description or '')
        features['has_title'] = 1 if report.title else 0
        
        # Time features
        if report.incident_occurred_at and report.reported_at:
            time_diff = (report.reported_at - report.incident_occurred_at).total_seconds() / 3600
            features['report_delay_hours'] = min(time_diff, 168)  # Cap at 1 week
        else:
            features['report_delay_hours'] = 0
        
        features['incident_time_approximate'] = 1 if report.incident_time_approximate else 0
        
        # Rule check features
        features['rules_passed'] = report.rules_passed or 0
        features['rules_failed'] = report.rules_failed or 0
        features['rules_pass_ratio'] = (
            features['rules_passed'] / (features['rules_passed'] + features['rules_failed'])
            if (features['rules_passed'] + features['rules_failed']) > 0 else 0.5
        )
        
        # Network/battery features
        features['battery_level'] = report.battery_level or 50
        network_scores = {'wifi': 1.0, '4g': 0.9, '3g': 0.7, '2g': 0.5}
        features['network_quality'] = network_scores.get(report.network_type, 0.5)
        
        return features
    
    # ==================== PREDICTION ====================
    @staticmethod
    def score_report(report_id, model_id=None):
        """Score a report using ML model"""
        report = IncidentReport.query.get(report_id)
        if not report:
            return None
        
        # Get model
        if model_id:
            model = MLModel.query.get(model_id)
        else:
            model = MLService.get_champion_model()
        
        if not model:
            # No model available - use rule-based fallback
            return MLService._fallback_scoring(report)
        
        # Extract features
        start_time = datetime.utcnow()
        features = MLService.extract_features(report)
        
        # Calculate score using weighted features (simplified model)
        score = MLService._calculate_trust_score(features, model)
        
        # Determine classification
        if score >= float(model.threshold_trusted):
            predicted_class = 'Trusted'
        elif score >= float(model.threshold_suspicious):
            predicted_class = 'Suspicious'
        else:
            predicted_class = 'False'
        
        # Calculate confidence (simplified)
        confidence = min(0.95, 0.5 + abs(score - 50) / 100)
        
        # Calculate class probabilities
        class_probs = MLService._calculate_class_probabilities(score, model)
        
        inference_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create prediction record
        prediction = MLPrediction(
            prediction_id=str(uuid.uuid4()),
            report_id=report_id,
            model_id=model.model_id,
            feature_vector=features,
            predicted_score=score,
            predicted_class=predicted_class,
            confidence=confidence,
            class_probabilities=class_probs,
            inference_time_ms=inference_time
        )
        db.session.add(prediction)
        
        # Update report
        report.ml_model_id = model.model_id
        report.ml_trust_score = score
        report.ml_confidence = confidence
        report.ml_feature_vector = features
        report.ml_scored_at = datetime.utcnow()
        report.trust_classification = predicted_class
        report.classification_reason = f'ML score: {score:.1f}, Class: {predicted_class}'
        
        if not report.is_auto_rejected:
            report.report_status = 'pending_review'
            report.processing_stage = 'ready_for_review'
        
        # Update model statistics
        model.total_predictions = (model.total_predictions or 0) + 1
        
        db.session.commit()
        
        return {
            'report_id': report_id,
            'model_id': model.model_id,
            'model_version': model.model_version,
            'trust_score': score,
            'predicted_class': predicted_class,
            'confidence': confidence,
            'class_probabilities': class_probs,
            'features': features,
            'inference_time_ms': inference_time
        }
    
    @staticmethod
    def _calculate_trust_score(features, model):
        """Calculate trust score from features"""
        # Weighted scoring (configurable via model)
        weights = model.feature_importance or {
            'device_trust_score': 0.20,
            'device_trust_ratio': 0.15,
            'has_evidence': 0.15,
            'motion_score': 0.10,
            'description_length': 0.10,
            'rules_pass_ratio': 0.15,
            'has_precise_location': 0.10,
            'network_quality': 0.05
        }
        
        # Normalize features to 0-100 scale
        normalized = {
            'device_trust_score': features.get('device_trust_score', 50),
            'device_trust_ratio': features.get('device_trust_ratio', 0.5) * 100,
            'has_evidence': features.get('has_evidence', 0) * 100,
            'motion_score': features.get('motion_score', 50),
            'description_length': min(features.get('description_length', 0) / 5, 100),
            'rules_pass_ratio': features.get('rules_pass_ratio', 0.5) * 100,
            'has_precise_location': features.get('has_precise_location', 0) * 100,
            'network_quality': features.get('network_quality', 0.5) * 100
        }
        
        # Calculate weighted score
        score = sum(
            normalized.get(key, 50) * weight
            for key, weight in weights.items()
        )
        
        # Ensure in 0-100 range
        return max(0, min(100, score))
    
    @staticmethod
    def _calculate_class_probabilities(score, model):
        """Calculate probability distribution across classes"""
        # Simplified probability calculation
        trusted_threshold = float(model.threshold_trusted)
        suspicious_threshold = float(model.threshold_suspicious)
        
        if score >= trusted_threshold:
            p_trusted = 0.5 + (score - trusted_threshold) / (200 - 2 * trusted_threshold)
            p_suspicious = (1 - p_trusted) * 0.7
            p_false = 1 - p_trusted - p_suspicious
        elif score >= suspicious_threshold:
            p_suspicious = 0.5 + (score - suspicious_threshold) / (2 * (trusted_threshold - suspicious_threshold))
            p_trusted = (1 - p_suspicious) * 0.4
            p_false = 1 - p_trusted - p_suspicious
        else:
            p_false = 0.5 + (suspicious_threshold - score) / (2 * suspicious_threshold)
            p_suspicious = (1 - p_false) * 0.6
            p_trusted = 1 - p_false - p_suspicious
        
        return {
            'Trusted': round(max(0, min(1, p_trusted)), 4),
            'Suspicious': round(max(0, min(1, p_suspicious)), 4),
            'False': round(max(0, min(1, p_false)), 4)
        }
    
    @staticmethod
    def _fallback_scoring(report):
        """Fallback scoring when no ML model is available"""
        features = MLService.extract_features(report)
        
        # Simple rule-based score
        score = 50  # Start at neutral
        
        # Device trust
        score += (features.get('device_trust_score', 50) - 50) * 0.3
        
        # Evidence bonus
        if features.get('has_evidence'):
            score += 10
        
        # Motion bonus
        if features.get('has_motion_data'):
            score += 5
        
        # Rules pass ratio
        if features.get('rules_pass_ratio', 0.5) > 0.8:
            score += 10
        elif features.get('rules_pass_ratio', 0.5) < 0.3:
            score -= 15
        
        score = max(0, min(100, score))
        
        # Classify
        if score >= 70:
            predicted_class = 'Trusted'
        elif score >= 40:
            predicted_class = 'Suspicious'
        else:
            predicted_class = 'False'
        
        # Update report
        report.ml_trust_score = score
        report.trust_classification = predicted_class
        report.classification_reason = 'Fallback rule-based scoring (no ML model)'
        report.report_status = 'pending_review'
        report.processing_stage = 'ready_for_review'
        db.session.commit()
        
        return {
            'report_id': report.report_id,
            'model_id': None,
            'model_version': 'fallback',
            'trust_score': score,
            'predicted_class': predicted_class,
            'confidence': 0.5,
            'features': features
        }
    
    # ==================== TRAINING DATA ====================
    @staticmethod
    def add_training_data(report_id, label, label_source, labeled_by_user_id=None):
        """Add report to training dataset"""
        report = IncidentReport.query.get(report_id)
        if not report:
            return None
        
        # Extract features
        features = MLService.extract_features(report)
        
        training_data = MLTrainingData(
            report_id=report_id,
            feature_vector=features,
            label=label,
            label_confidence=100 if label_source == 'police_verification' else 80,
            labeled_by=labeled_by_user_id,
            label_source=label_source,
            is_high_quality=True
        )
        
        db.session.add(training_data)
        db.session.commit()
        return training_data
    
    @staticmethod
    def get_training_data(dataset_split=None, limit=None):
        """Get training data"""
        query = MLTrainingData.query.filter_by(is_high_quality=True)
        
        if dataset_split:
            query = query.filter_by(dataset_split=dataset_split)
        
        query = query.order_by(MLTrainingData.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def assign_dataset_splits(train_ratio=0.7, validation_ratio=0.15, test_ratio=0.15):
        """Assign training data to dataset splits"""
        unassigned = MLTrainingData.query.filter_by(dataset_split=None).all()
        
        import random
        random.shuffle(unassigned)
        
        n = len(unassigned)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * validation_ratio)
        
        for i, data in enumerate(unassigned):
            if i < train_end:
                data.dataset_split = 'train'
            elif i < val_end:
                data.dataset_split = 'validation'
            else:
                data.dataset_split = 'test'
            data.assigned_to_split_at = datetime.utcnow()
        
        db.session.commit()
        
        return {
            'total': n,
            'train': train_end,
            'validation': val_end - train_end,
            'test': n - val_end
        }
    
    # ==================== PREDICTION FEEDBACK ====================
    @staticmethod
    def record_ground_truth(report_id, actual_class):
        """Record ground truth for a prediction"""
        prediction = MLPrediction.query.filter_by(report_id=report_id).first()
        if prediction:
            prediction.actual_class = actual_class
            prediction.is_correct = (prediction.predicted_class == actual_class)
            prediction.verified_at = datetime.utcnow()
            
            # Update model statistics
            if prediction.model:
                if prediction.is_correct:
                    prediction.model.correct_predictions = \
                        (prediction.model.correct_predictions or 0) + 1
            
            db.session.commit()
        return prediction
    
    @staticmethod
    def get_model_performance(model_id):
        """Get model performance metrics"""
        model = MLModel.query.get(model_id)
        if not model:
            return None
        
        predictions = MLPrediction.query.filter_by(model_id=model_id).all()
        verified = [p for p in predictions if p.actual_class]
        
        if not verified:
            return {
                'model_id': model_id,
                'total_predictions': len(predictions),
                'verified_predictions': 0,
                'accuracy': None
            }
        
        correct = sum(1 for p in verified if p.is_correct)
        
        # Calculate per-class metrics
        classes = ['Trusted', 'Suspicious', 'False']
        class_metrics = {}
        
        for cls in classes:
            tp = sum(1 for p in verified if p.predicted_class == cls and p.actual_class == cls)
            fp = sum(1 for p in verified if p.predicted_class == cls and p.actual_class != cls)
            fn = sum(1 for p in verified if p.predicted_class != cls and p.actual_class == cls)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            class_metrics[cls] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'support': sum(1 for p in verified if p.actual_class == cls)
            }
        
        return {
            'model_id': model_id,
            'model_version': model.model_version,
            'total_predictions': len(predictions),
            'verified_predictions': len(verified),
            'correct_predictions': correct,
            'accuracy': correct / len(verified),
            'class_metrics': class_metrics
        }
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def model_to_dict(model):
        """Convert model to dictionary"""
        if not model:
            return None
        return {
            'model_id': model.model_id,
            'model_name': model.model_name,
            'model_version': model.model_version,
            'model_type': model.model_type,
            'trained_at': model.trained_at.isoformat() if model.trained_at else None,
            'training_dataset_size': model.training_dataset_size,
            'accuracy': float(model.accuracy) if model.accuracy else None,
            'precision_score': float(model.precision_score) if model.precision_score else None,
            'recall_score': float(model.recall_score) if model.recall_score else None,
            'f1_score': float(model.f1_score) if model.f1_score else None,
            'auc_roc': float(model.auc_roc) if model.auc_roc else None,
            'threshold_trusted': float(model.threshold_trusted) if model.threshold_trusted else 70,
            'threshold_suspicious': float(model.threshold_suspicious) if model.threshold_suspicious else 40,
            'is_active': model.is_active,
            'is_champion': model.is_champion,
            'deployed_at': model.deployed_at.isoformat() if model.deployed_at else None,
            'total_predictions': model.total_predictions or 0,
            'correct_predictions': model.correct_predictions or 0,
            'created_at': model.created_at.isoformat() if model.created_at else None
        }
    
    @staticmethod
    def prediction_to_dict(prediction):
        """Convert prediction to dictionary"""
        if not prediction:
            return None
        return {
            'prediction_id': prediction.prediction_id,
            'report_id': prediction.report_id,
            'model_id': prediction.model_id,
            'predicted_score': float(prediction.predicted_score) if prediction.predicted_score else None,
            'predicted_class': prediction.predicted_class,
            'confidence': float(prediction.confidence) if prediction.confidence else None,
            'class_probabilities': prediction.class_probabilities,
            'actual_class': prediction.actual_class,
            'is_correct': prediction.is_correct,
            'inference_time_ms': float(prediction.inference_time_ms) if prediction.inference_time_ms else None,
            'predicted_at': prediction.predicted_at.isoformat() if prediction.predicted_at else None,
            'verified_at': prediction.verified_at.isoformat() if prediction.verified_at else None
        }
