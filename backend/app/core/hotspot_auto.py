"""
Automatic hotspot creation: when many reports of the same place AND the same
incident type are submitted, a hotspot is created. No manual creation.
Links each hotspot to its contributing reports via hotspot_reports table.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Tuple, Any

import numpy as np
from sklearn.cluster import DBSCAN

from sqlalchemy import insert
from sqlalchemy.orm import Session, selectinload

from app.models.hotspot import Hotspot, hotspot_reports_table
from app.models.report import Report


# Same place + same type: 2+ reports in last 24h in one area (village or lat/long bucket), same incident_type_id
DEFAULT_TIME_WINDOW_HOURS = 24
DEFAULT_MIN_INCIDENTS = 2
DEFAULT_RADIUS_METERS = 500
LAT_LONG_PRECISION = 6
EARTH_RADIUS_METERS = 6_371_000.0


def _normalize_rule_status(status: Any) -> str:
    value = str(status or "").strip().lower()
    aliases = {
        "passed": "classified",
        "confirmed": "classified",
        "verified": "classified",
    }
    return aliases.get(value, value)


def _is_map_eligible_status(status: Any) -> bool:
    return _normalize_rule_status(status) == "classified"


def _weight_for_report(report: Report) -> Tuple[float, bool]:
    """
    Compute a numeric weight and whether this report has a confirmed police review.

    - rule_status passed     -> 1.0
    - rule_status pending    -> 0.6
    - rule_status flagged    -> 0.3
    - rule_status rejected   -> 0.0
    - bonus for confirmed review: +0.7
    """
    status = _normalize_rule_status(report.rule_status)
    if status == "classified":
        base = 1.0
    elif status == "pending":
        base = 0.6
    elif status == "flagged":
        base = 0.3
    elif status == "rejected":
        base = 0.0
    else:
        base = 0.5

    has_confirmed = any((rv.decision or "").lower() == "confirmed" for rv in (report.police_reviews or []))
    if has_confirmed:
        base += 0.7
    return base, has_confirmed


def _risk_level_from_score(score: float, confirmed_reports: int) -> str:
    """
    Derive hotspot risk:
    - high:   strong score OR multiple confirmed reports
    - medium: some confirmations OR moderate score
    - low:    weak, mostly provisional
    """
    if confirmed_reports >= 2 or score >= 6.0:
        return "high"
    if confirmed_reports >= 1 or score >= 3.0:
        return "medium"
    return "low"


def create_hotspots_from_reports(
    db: Session,
    time_window_hours: int = DEFAULT_TIME_WINDOW_HOURS,
    min_incidents: int = DEFAULT_MIN_INCIDENTS,
    radius_meters: float = DEFAULT_RADIUS_METERS,
) -> int:
    """
    Create hotspots using DBSCAN spatial clustering per incident type.

    Only reports with map-eligible status (classified/passed aliases)
    participate in clustering.

    For each DBSCAN cluster with at least min_incidents, compute a weighted
    score using normalized rule_status and police reviews, then create a
    hotspot if none exists.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)

    reports = (
        db.query(Report)
        .options(selectinload(Report.police_reviews))
        .filter(Report.reported_at >= since)
        .all()
    )

    eligible_reports = []
    for r in reports:
        if not _is_map_eligible_status(r.rule_status):
            continue
        try:
            float(r.latitude)
            float(r.longitude)
        except (TypeError, ValueError):
            continue
        eligible_reports.append(r)

    reports_by_incident_type: Dict[int, list[Report]] = {}
    for r in eligible_reports:
        incident_type_id = int(r.incident_type_id)
        reports_by_incident_type.setdefault(incident_type_id, []).append(r)

    created = 0
    eps_radians = float(radius_meters) / EARTH_RADIUS_METERS
    for incident_type_id, type_reports in reports_by_incident_type.items():
        if len(type_reports) < min_incidents:
            continue

        coords_degrees = np.array(
            [[float(r.latitude), float(r.longitude)] for r in type_reports],
            dtype=float,
        )
        coords_radians = np.radians(coords_degrees)

        model = DBSCAN(
            eps=eps_radians,
            min_samples=min_incidents,
            metric="haversine",
            algorithm="ball_tree",
        )
        labels = model.fit_predict(coords_radians)

        unique_labels = {int(label) for label in labels.tolist() if int(label) >= 0}
        for label in unique_labels:
            cluster_reports = [r for i, r in enumerate(type_reports) if int(labels[i]) == label]
            incident_count = len(cluster_reports)
            if incident_count < min_incidents:
                continue

            lats = [float(r.latitude) for r in cluster_reports]
            lons = [float(r.longitude) for r in cluster_reports]
            avg_lat = sum(lats) / incident_count
            avg_lon = sum(lons) / incident_count

            score = 0.0
            confirmed_reports = 0
            for r in cluster_reports:
                w, has_confirmed = _weight_for_report(r)
                score += w
                if has_confirmed:
                    confirmed_reports += 1

            center_lat = Decimal(str(round(avg_lat, LAT_LONG_PRECISION)))
            center_long = Decimal(str(round(avg_lon, LAT_LONG_PRECISION)))

            existing = (
                db.query(Hotspot)
                .filter(
                    Hotspot.center_lat == center_lat,
                    Hotspot.center_long == center_long,
                    Hotspot.incident_type_id == incident_type_id,
                    Hotspot.time_window_hours == time_window_hours,
                )
                .first()
            )
            if existing:
                continue

            hotspot = Hotspot(
                center_lat=center_lat,
                center_long=center_long,
                radius_meters=Decimal(str(radius_meters)),
                incident_count=incident_count,
                risk_level=_risk_level_from_score(score, confirmed_reports),
                time_window_hours=time_window_hours,
                incident_type_id=incident_type_id,
            )
            db.add(hotspot)
            db.flush()  # get hotspot_id

            db.execute(
                insert(hotspot_reports_table),
                [{"hotspot_id": hotspot.hotspot_id, "report_id": r.report_id} for r in cluster_reports],
            )
            created += 1

    if created > 0:
        db.commit()
    return created
