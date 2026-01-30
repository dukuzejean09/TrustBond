"""
Verification Engine Module.

This module contains the rule-based verification engine that assesses
report credibility based on spatial-temporal consistency, evidence
quality, and device trust.
"""

from app.verification.rule_engine import RuleBasedVerifier, TrustClassification
from app.verification.spatial_temporal import SpatialTemporalChecker
from app.verification.evidence_validator import EvidenceValidator

__all__ = [
    'RuleBasedVerifier',
    'TrustClassification',
    'SpatialTemporalChecker', 
    'EvidenceValidator'
]
