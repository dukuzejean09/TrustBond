"""
Machine Learning Module.

Contains ML models for:
- Trust scoring (Gradient Boosting)
- Hotspot detection (DBSCAN clustering)
- Anomaly detection (Isolation Forest)
- Trend prediction (Random Forest)
"""

from app.ml.trust_scorer import MLTrustScorer
from app.ml.hotspot_detector import HotspotDetector

__all__ = [
    'MLTrustScorer',
    'HotspotDetector',
]
