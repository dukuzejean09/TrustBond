"""
Trust Score Model for Report Verification Results.

Stores the verification results and trust scores for each report,
including breakdown of individual verification checks.
"""

from app import db
from datetime import datetime
import enum


class TrustClassification(enum.Enum):
    """Report trust classification levels."""
    TRUSTED = 'trusted'
    DELAYED = 'delayed'
    SUSPICIOUS = 'suspicious'


class VerificationStatus(enum.Enum):
    """Verification process status."""
    PENDING = 'pending'
    VERIFIED = 'verified'
    POLICE_VALIDATED = 'police_validated'
    POLICE_REJECTED = 'police_rejected'


class TrustScore(db.Model):
    """
    Stores trust verification results for each report.
    
    This model captures both rule-based and ML-based verification
    scores, enabling the incremental learning system.
    """
    __tablename__ = 'trust_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Link to report
    report_id = db.Column(db.Integer, db.ForeignKey('reports.id'), nullable=False, unique=True)
    
    # Link to device
    device_id = db.Column(db.Integer, db.ForeignKey('device_profiles.id'))
    
    # Overall scores
    final_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    classification = db.Column(db.Enum(TrustClassification), nullable=False)
    
    # Rule-based verification scores (0.0 to 1.0 each)
    gps_score = db.Column(db.Float, default=0.5)
    timestamp_score = db.Column(db.Float, default=0.5)
    evidence_score = db.Column(db.Float, default=0.5)
    description_score = db.Column(db.Float, default=0.5)
    device_trust_score = db.Column(db.Float, default=0.5)
    spatial_temporal_score = db.Column(db.Float, default=0.5)
    
    # ML-based scores (populated after ML model runs)
    ml_score = db.Column(db.Float)
    ml_confidence = db.Column(db.Float)
    is_anomaly = db.Column(db.Boolean, default=False)
    anomaly_score = db.Column(db.Float)
    
    # Verification details
    verification_status = db.Column(db.Enum(VerificationStatus), default=VerificationStatus.PENDING)
    verification_notes = db.Column(db.Text)
    verified_at = db.Column(db.DateTime)
    
    # Police validation (for ML training)
    police_validated = db.Column(db.Boolean, default=False)
    police_classification = db.Column(db.String(20))  # 'genuine', 'fake', 'unclear'
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    validated_at = db.Column(db.DateTime)
    validation_notes = db.Column(db.Text)
    
    # Used for ML training
    used_for_training = db.Column(db.Boolean, default=False)
    training_batch_id = db.Column(db.Integer)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    report = db.relationship('Report', backref=db.backref('trust_score', uselist=False))
    device = db.relationship('DeviceProfile', backref='trust_scores')
    validator = db.relationship('User', foreign_keys=[validated_by])
    
    def calculate_final_score(self):
        """
        Calculate final trust score from component scores.
        
        Weights:
        - GPS verification: 15%
        - Timestamp consistency: 10%
        - Evidence quality: 20%
        - Description quality: 15%
        - Device reputation: 20%
        - Spatial-temporal consistency: 20%
        """
        weights = {
            'gps': 0.15,
            'timestamp': 0.10,
            'evidence': 0.20,
            'description': 0.15,
            'device': 0.20,
            'spatial_temporal': 0.20,
        }
        
        score = (
            self.gps_score * weights['gps'] +
            self.timestamp_score * weights['timestamp'] +
            self.evidence_score * weights['evidence'] +
            self.description_score * weights['description'] +
            self.device_trust_score * weights['device'] +
            self.spatial_temporal_score * weights['spatial_temporal']
        )
        
        # If ML score is available, blend it (60% rule-based, 40% ML)
        if self.ml_score is not None:
            score = score * 0.6 + self.ml_score * 0.4
        
        self.final_score = round(score, 3)
        return self.final_score
    
    def classify(self):
        """
        Classify report based on final score.
        
        Thresholds:
        - >= 0.7: Trusted (auto-approve)
        - >= 0.4: Delayed (needs manual review)
        - < 0.4: Suspicious (flag for investigation)
        """
        if self.final_score >= 0.7:
            self.classification = TrustClassification.TRUSTED
        elif self.final_score >= 0.4:
            self.classification = TrustClassification.DELAYED
        else:
            self.classification = TrustClassification.SUSPICIOUS
        
        return self.classification
    
    def police_validate(self, user_id, classification, notes=None):
        """
        Record police validation for ML training.
        
        Args:
            user_id: ID of the validating officer
            classification: 'genuine', 'fake', or 'unclear'
            notes: Optional validation notes
        """
        self.police_validated = True
        self.police_classification = classification
        self.validated_by = user_id
        self.validated_at = datetime.utcnow()
        self.validation_notes = notes
        self.verification_status = (
            VerificationStatus.POLICE_VALIDATED 
            if classification == 'genuine' 
            else VerificationStatus.POLICE_REJECTED
        )
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'reportId': self.report_id,
            'finalScore': self.final_score,
            'classification': self.classification.value if self.classification else None,
            'breakdown': {
                'gpsScore': self.gps_score,
                'timestampScore': self.timestamp_score,
                'evidenceScore': self.evidence_score,
                'descriptionScore': self.description_score,
                'deviceTrustScore': self.device_trust_score,
                'spatialTemporalScore': self.spatial_temporal_score,
            },
            'mlScore': self.ml_score,
            'mlConfidence': self.ml_confidence,
            'isAnomaly': self.is_anomaly,
            'verificationStatus': self.verification_status.value if self.verification_status else None,
            'verificationNotes': self.verification_notes,
            'policeValidated': self.police_validated,
            'policeClassification': self.police_classification,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<TrustScore report={self.report_id} score={self.final_score:.2f} class={self.classification}>'
