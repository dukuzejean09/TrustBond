from app import db
from datetime import datetime
import enum


class VerificationRule(db.Model):
    """Configurable Verification Rules"""
    __tablename__ = 'verification_rules'
    
    rule_id = db.Column(db.Integer, primary_key=True)
    rule_name = db.Column(db.String(100), nullable=False, unique=True)
    rule_code = db.Column(db.String(50), nullable=False, unique=True)
    rule_description = db.Column(db.Text)
    rule_category = db.Column(db.Enum('spatial', 'temporal', 'motion', 'evidence', 'device', 'content'), nullable=False)
    rule_parameters = db.Column(db.JSON)
    severity = db.Column(db.Enum('info', 'low', 'medium', 'high', 'critical'), default='low')
    is_blocking = db.Column(db.Boolean, default=False)
    failure_score_penalty = db.Column(db.Numeric(5, 2), default=0)
    execution_order = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    applies_to_categories = db.Column(db.JSON)
    applies_to_districts = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('police_users.user_id'))
    
    # Relationships
    executions = db.relationship('RuleExecutionLog', backref='rule', lazy=True, cascade='all, delete-orphan')


class RuleExecutionLog(db.Model):
    """Rule Execution Results for every report"""
    __tablename__ = 'rule_execution_logs'
    
    execution_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    report_id = db.Column(db.String(36), db.ForeignKey('incident_reports.report_id'), nullable=False)
    rule_id = db.Column(db.Integer, db.ForeignKey('verification_rules.rule_id'), nullable=False)
    passed = db.Column(db.Boolean, nullable=False)
    input_values = db.Column(db.JSON)
    threshold_values = db.Column(db.JSON)
    failure_reason = db.Column(db.Text)
    execution_time_ms = db.Column(db.Numeric(8, 2))
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_rule_execution_report_id', 'report_id'),
        db.Index('idx_rule_execution_rule_id', 'rule_id'),
    )
