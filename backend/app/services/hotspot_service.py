"""Hotspot service — DBSCAN clustering and management."""

from sqlalchemy.orm import Session


class HotspotService:
    """Business logic for hotspots + hotspot_reports tables."""

    @staticmethod
    def recalculate(db: Session, eps: float = 200, min_samples: int = 3, time_window_hours: int = 720):
        """
        Run trust-weighted DBSCAN:
        - Input: reports where rule_status='passed' and ai_ready=true
        - Weight by ml_predictions.trust_score (is_final=true)
        - Write results to hotspots + hotspot_reports
        """
        # TODO: implement
        pass

    @staticmethod
    def get_map_geojson(db: Session) -> dict:
        """Generate GeoJSON from hotspots + locations.geometry."""
        # TODO: implement
        pass
