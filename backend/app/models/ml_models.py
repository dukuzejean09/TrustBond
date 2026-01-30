from app import db
from datetime import datetime
import json


class MLModel(db.Model):
    """ML Model Registry - Tracks model versions and performance"""
    __tablename__ = 'ml_models'
    
    model_id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    model_version = db.Column(db.String(20), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)
    model_file_path = db.Column(db.String(500))
    model_file_hash = db.Column(db.String(64))
    model_size_kb = db.Column(db.Integer)
    trained_at = db.Column(db.DateTime)
    training_dataset_size = db.Column(db.Integer)
    training_duration_seconds = db.Column(db.Integer)
    
    # Performance Metrics
    accuracy = db.Column(db.Numeric(5, 4))
    precision_score = db.Column(db.Numeric(5, 4))
    recall_score = db.Column(db.Numeric(5, 4))
    f1_score = db.Column(db.Numeric(5, 4))
    auc_roc = db.Column(db.Numeric(5, 4))
    metrics_by_class = db.Column(db.JSON)
    confusion_matrix = db.Column(db.JSON)
    
    # Features
    feature_names = db.Column(db.JSON)
    feature_importance = db.Column(db.JSON)
    
    # Thresholds
    threshold_trusted = db.Column(db.Numeric(5, 2), default=70)
    threshold_suspicious = db.Column(db.Numeric(5, 2), default=40)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_champion = db.Column(db.Boolean, default=False)
    deployed_at = db.Column(db.DateTime)
    deprecated_at = db.Column(db.DateTime)
    deprecation_reason = db.Column(db.String(255))
    
    # Statistics
    total_predictions = db.Column(db.Integer, default=0)
    correct_predictions = db.Column(db.Integer, default=0)
    avg_inference_time_ms = db.Column(db.Numeric(8, 2))
    
    training_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    
    # Relationships
    predictions = db.relationship('MLPrediction', backref='model', lazy=True, cascade='all, delete-orphan')
    training_data = db.relationship('MLTrainingData', backref='model', lazy=True)


class MLPrediction(db.Model):
    """Prediction Logs - All ML predictions for monitoring"""
    __tablename__ = 'ml_predictions'
    
    prediction_id = db.Column(db.String(36), primary_key=True, default=lambda: __import__('uuid').uuid4().__str__)
    report_id = db.Column(db.String(36), db.ForeignKey('incident_reports.report_id'), nullable=False, unique=True)
    model_id = db.Column(db.Integer, db.ForeignKey('ml_models.model_id'), nullable=False)
    feature_vector = db.Column(db.JSON)
    predicted_score = db.Column(db.Numeric(5, 2), nullable=False)
    predicted_class = db.Column(db.Enum('Trusted', 'Suspicious', 'False'), nullable=False)
    confidence = db.Column(db.Numeric(5, 4))
    class_probabilities = db.Column(db.JSON)
    actual_class = db.Column(db.Enum('Trusted', 'Suspicious', 'False'))
    is_correct = db.Column(db.Boolean)
    inference_time_ms = db.Column(db.Numeric(8, 2))
    predicted_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    
    __table_args__ = (
        db.Index('idx_prediction_report_id', 'report_id'),
        db.Index('idx_prediction_model_id', 'model_id'),
    )


class MLTrainingData(db.Model):
    """Training Dataset - High-quality labeled data"""
    __tablename__ = 'ml_training_data'
    
    training_id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(36), db.ForeignKey('incident_reports.report_id'), nullable=False)
    feature_vector = db.Column(db.JSON)
    label = db.Column(db.Enum('Trusted', 'Suspicious', 'False'), nullable=False)
    label_confidence = db.Column(db.Numeric(5, 2))
    labeled_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    labeled_at = db.Column(db.DateTime, default=datetime.utcnow)
    label_source = db.Column(db.Enum('police_verification', 'expert_review', 'consensus', 'auto'), default='police_verification')
    dataset_split = db.Column(db.Enum('train', 'validation', 'test', 'holdout'))
    assigned_to_split_at = db.Column(db.DateTime)
    used_in_model_version = db.Column(db.String(20))
    used_at = db.Column(db.DateTime)
    is_high_quality = db.Column(db.Boolean, default=True)
    quality_issues = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_training_data_report_id', 'report_id'),
        db.Index('idx_training_data_dataset_split', 'dataset_split'),
    )
