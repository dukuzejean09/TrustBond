# Core Device Management
from app.models.device import Device, DeviceTrustHistory

# Rwanda Administrative Geography
from app.models.geography import Province, District, Sector, Cell, Village

# Incident Taxonomy
from app.models.incident_taxonomy import IncidentCategory, IncidentType

# Incident Reports
from app.models.incident_report import IncidentReport

# Evidence Management
from app.models.evidence import ReportEvidence

# Verification Rules Engine
from app.models.verification_rules import VerificationRule, RuleExecutionLog

# Machine Learning System
from app.models.ml_models import MLModel, MLPrediction, MLTrainingData

# Hotspot Detection & Clustering
from app.models.hotspots import Hotspot, HotspotReport, HotspotHistory, ClusteringRun

# Police User Management
from app.models.police_users import PoliceUser, PoliceSession

# Notifications
from app.models.notifications import Notification

# Analytics & Statistics
from app.models.analytics import DailyStatistic, IncidentTypeTrend

# Public Community Safety Map
from app.models.public_map import PublicSafetyZone

# System Configuration
from app.models.system_settings import SystemSetting

# Audit & Activity Logging
from app.models.audit import ActivityLog, DataChangeAudit

# User Feedback
from app.models.feedback import AppFeedback, FeedbackAttachment

# API Management
from app.models.api_management import APIKey, APIRequestLog

__all__ = [
    # Device
    'Device', 'DeviceTrustHistory',
    # Geography
    'Province', 'District', 'Sector', 'Cell', 'Village',
    # Taxonomy
    'IncidentCategory', 'IncidentType',
    # Reports
    'IncidentReport',
    # Evidence
    'ReportEvidence',
    # Rules
    'VerificationRule', 'RuleExecutionLog',
    # ML
    'MLModel', 'MLPrediction', 'MLTrainingData',
    # Hotspots
    'Hotspot', 'HotspotReport', 'HotspotHistory', 'ClusteringRun',
    # Police
    'PoliceUser', 'PoliceSession',
    # Notifications
    'Notification',
    # Analytics
    'DailyStatistic', 'IncidentTypeTrend',
    # Public Map
    'PublicSafetyZone',
    # System
    'SystemSetting',
    # Audit
    'ActivityLog', 'DataChangeAudit',
    # Feedback
    'AppFeedback', 'FeedbackAttachment',
    # API
    'APIKey', 'APIRequestLog'
]
