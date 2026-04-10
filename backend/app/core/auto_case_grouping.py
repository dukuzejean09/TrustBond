from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import atan2, cos, radians, sin, sqrt
from typing import Iterable, Optional
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.case import Case, CaseReport
from app.models.incident_group import IncidentGroup
from app.models.location import Location
from app.models.ml_prediction import MLPrediction
from app.models.report import Report


AUTO_GROUP_RADIUS_METERS = 150.0
AUTO_GROUP_TIME_WINDOW_MINUTES = 20
AUTO_GROUP_MIN_REPORTS = 2
AUTO_GROUP_MIN_DEVICES = 2


@dataclass
class AutoGroupingResult:
    incident_group: Optional[IncidentGroup]
    case: Optional[Case]
    grouped_reports: list[Report]
    distinct_device_count: int


def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _report_lifecycle_state(report: Report) -> str:
    for field in ("verification_status", "status", "rule_status"):
        value = getattr(report, field, None)
        if value:
            normalized = str(value).strip().lower()
            if normalized:
                return normalized
    return "pending"


def _haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))


def _report_is_verified(report: Report) -> bool:
    return _report_lifecycle_state(report) == "verified"


def _latest_trust_score(report: Report) -> float:
    preds = list(getattr(report, "ml_predictions", None) or [])
    if preds:
        preds.sort(
            key=lambda p: p.evaluated_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        top = preds[0]
        if getattr(top, "trust_score", None) is not None:
            try:
                return float(top.trust_score)
            except Exception:
                pass
    device = getattr(report, "device", None)
    if device is not None and getattr(device, "device_trust_score", None) is not None:
        try:
            return float(device.device_trust_score)
        except Exception:
            pass
    return 50.0


def _generate_case_number(db: Session) -> str:
    year = datetime.now(timezone.utc).strftime("%Y")
    row = db.execute(
        text(
            """
            SELECT COALESCE(MAX(
                NULLIF(SUBSTRING(case_number FROM 'CASE-[0-9]{4}-([0-9]+)'), '')::INT
            ), 0) + 1 AS next_num
            FROM cases WHERE case_number LIKE :prefix
            """
        ),
        {"prefix": f"CASE-{year}-%"},
    ).fetchone()
    next_num = row[0] if row else 1
    return f"CASE-{year}-{next_num:04d}"


def _sector_location_id(db: Session, location_id: Optional[int]) -> Optional[int]:
    if location_id is None:
        return None
    loc = db.query(Location).filter(Location.location_id == location_id).first()
    while loc is not None and loc.location_type != "sector" and loc.parent_location_id:
        loc = db.query(Location).filter(Location.location_id == loc.parent_location_id).first()
    if loc is not None and loc.location_type == "sector":
        return loc.location_id
    return location_id


def _compute_group_confidence(reports: Iterable[Report], *, distinct_devices: int, radius_meters: float) -> float:
    report_list = list(reports)
    if not report_list:
        return 0.0
    avg_trust = sum(_latest_trust_score(r) for r in report_list) / len(report_list)
    device_bonus = min(20.0, distinct_devices * 8.0)
    count_bonus = min(15.0, len(report_list) * 4.0)
    radius_bonus = max(0.0, 10.0 - (radius_meters / 50.0))
    return round(max(0.0, min(100.0, avg_trust * 0.7 + device_bonus + count_bonus + radius_bonus)), 2)


def _load_verified_group_reports(
    db: Session,
    group: IncidentGroup,
    *,
    exclude_report_id: Optional[object] = None,
) -> list[Report]:
    q = (
        db.query(Report)
        .options(
            joinedload(Report.device),
            selectinload(Report.ml_predictions),
            selectinload(Report.case_reports),
        )
        .filter(Report.incident_group_id == group.group_id)
    )
    if exclude_report_id is not None:
        q = q.filter(Report.report_id != exclude_report_id)
    reports = q.all()
    return [r for r in reports if _report_lifecycle_state(r) == "verified"]


def find_groupable_reports(
    db: Session,
    report: Report,
    *,
    radius_meters: float = AUTO_GROUP_RADIUS_METERS,
    time_window_minutes: int = AUTO_GROUP_TIME_WINDOW_MINUTES,
) -> list[Report]:
    if not _report_is_verified(report):
        return []

    base_time = _to_utc(report.reported_at) or datetime.now(timezone.utc)
    try:
        base_lat = float(report.latitude)
        base_lon = float(report.longitude)
    except Exception:
        return []

    q = (
        db.query(Report)
        .options(
            joinedload(Report.device),
            selectinload(Report.ml_predictions),
            selectinload(Report.case_reports),
        )
        .filter(
            Report.incident_type_id == report.incident_type_id,
            Report.report_id != report.report_id,
            Report.reported_at >= base_time - timedelta(minutes=time_window_minutes),
            Report.reported_at <= base_time + timedelta(minutes=time_window_minutes),
        )
    )
    if report.village_location_id is not None:
        q = q.filter(Report.village_location_id == report.village_location_id)

    matches = [report]
    for candidate in q.all():
        if _report_lifecycle_state(candidate) != "verified":
            continue
        if str(candidate.device_id) == str(report.device_id):
            continue
        try:
            dist = _haversine_meters(base_lat, base_lon, float(candidate.latitude), float(candidate.longitude))
        except Exception:
            continue
        if dist <= radius_meters:
            matches.append(candidate)

    deduped: dict[str, Report] = {str(r.report_id): r for r in matches}
    return list(deduped.values())


def _find_existing_group(
    db: Session,
    report: Report,
    *,
    radius_meters: float,
    time_window_minutes: int,
) -> Optional[IncidentGroup]:
    base_time = _to_utc(report.reported_at) or datetime.now(timezone.utc)
    try:
        base_lat = float(report.latitude)
        base_lon = float(report.longitude)
    except Exception:
        return None

    candidates = (
        db.query(IncidentGroup)
        .filter(
            IncidentGroup.incident_type_id == report.incident_type_id,
            IncidentGroup.is_active == True,
            IncidentGroup.end_time >= base_time - timedelta(minutes=time_window_minutes),
            IncidentGroup.start_time <= base_time + timedelta(minutes=time_window_minutes),
        )
        .all()
    )
    for group in candidates:
        try:
            dist = _haversine_meters(base_lat, base_lon, float(group.center_lat), float(group.center_long))
        except Exception:
            continue
        if dist <= radius_meters:
            return group
    return None


def _upsert_group(
    db: Session,
    reports: list[Report],
    *,
    radius_meters: float,
) -> IncidentGroup:
    base_report = reports[0]
    group = _find_existing_group(
        db,
        base_report,
        radius_meters=radius_meters,
        time_window_minutes=AUTO_GROUP_TIME_WINDOW_MINUTES,
    )

    merged_reports = {str(r.report_id): r for r in reports}
    if group is not None:
        existing_group_reports = (
            db.query(Report)
            .options(joinedload(Report.device), selectinload(Report.ml_predictions))
            .filter(Report.incident_group_id == group.group_id)
            .all()
        )
        for existing in existing_group_reports:
            merged_reports[str(existing.report_id)] = existing

    report_list = list(merged_reports.values())
    start_time = min((_to_utc(r.reported_at) or datetime.now(timezone.utc)) for r in report_list)
    end_time = max((_to_utc(r.reported_at) or datetime.now(timezone.utc)) for r in report_list)
    center_lat = sum(float(r.latitude) for r in report_list) / len(report_list)
    center_long = sum(float(r.longitude) for r in report_list) / len(report_list)
    distinct_devices = len({str(r.device_id) for r in report_list})
    confidence_score = _compute_group_confidence(
        report_list,
        distinct_devices=distinct_devices,
        radius_meters=radius_meters,
    )

    if group is None:
        group = IncidentGroup(
            group_id=uuid4(),
            incident_type_id=base_report.incident_type_id,
            center_lat=center_lat,
            center_long=center_long,
            start_time=start_time,
            end_time=end_time,
            report_count=len(report_list),
            distinct_device_count=distinct_devices,
            radius_meters=radius_meters,
            confidence_score=confidence_score,
            grouping_method="ai_auto_grouped",
            metadata_json={
                "device_count": distinct_devices,
                "report_ids": [str(r.report_id) for r in report_list],
            },
            is_active=True,
        )
        db.add(group)
        db.flush()
    else:
        group.center_lat = center_lat
        group.center_long = center_long
        group.start_time = start_time
        group.end_time = end_time
        group.report_count = len(report_list)
        group.distinct_device_count = distinct_devices
        group.radius_meters = radius_meters
        group.confidence_score = confidence_score
        group.grouping_method = "ai_auto_grouped"
        group.metadata_json = {
            "device_count": distinct_devices,
            "report_ids": [str(r.report_id) for r in report_list],
        }
        group.is_active = True

    for matched in report_list:
        matched.incident_group_id = group.group_id

    return group


def _upsert_case_for_group(db: Session, group: IncidentGroup, reports: list[Report]) -> Case:
    case = (
        db.query(Case)
        .filter(Case.incident_group_id == group.group_id)
        .first()
    )
    merged_reports = {str(r.report_id): r for r in reports}
    if case is not None:
        existing_case_reports = (
            db.query(Report)
            .join(CaseReport, CaseReport.report_id == Report.report_id)
            .options(joinedload(Report.incident_type))
            .filter(CaseReport.case_id == case.case_id)
            .all()
        )
        for existing in existing_case_reports:
            merged_reports[str(existing.report_id)] = existing

    report_list = list(merged_reports.values())
    first_report = min(report_list, key=lambda r: _to_utc(r.reported_at) or datetime.now(timezone.utc))
    sector_location_id = _sector_location_id(db, first_report.village_location_id or first_report.location_id)
    confidence = _compute_group_confidence(
        report_list,
        distinct_devices=len({str(r.device_id) for r in report_list}),
        radius_meters=float(group.radius_meters or AUTO_GROUP_RADIUS_METERS),
    )
    if case is None:
        case = Case(
            case_id=uuid4(),
            case_number=_generate_case_number(db),
            status="open",
            priority="high" if confidence >= 80 else "medium",
            title=f"Auto-grouped {getattr(first_report.incident_type, 'type_name', 'incident')} incident",
            description=(
                f"Automatically created from {len(report_list)} corroborating reports "
                f"across {len({str(r.device_id) for r in report_list})} devices."
            ),
            location_id=sector_location_id,
            incident_type_id=group.incident_type_id,
            incident_group_id=group.group_id,
            created_by=None,
            report_count=len(report_list),
            device_count=len({str(r.device_id) for r in report_list}),
            auto_created=True,
            source="ai_auto_grouped",
            auto_group_confidence=confidence,
        )
        db.add(case)
        db.flush()
    else:
        case.location_id = sector_location_id
        case.incident_type_id = group.incident_type_id
        case.report_count = len(report_list)
        case.device_count = len({str(r.device_id) for r in report_list})
        case.auto_created = True
        case.source = "ai_auto_grouped"
        case.auto_group_confidence = confidence

    existing_links = {
        str(report_id)
        for (report_id,) in db.query(CaseReport.report_id).filter(CaseReport.case_id == case.case_id).all()
    }
    for report in report_list:
        if str(report.report_id) not in existing_links:
            db.add(CaseReport(case_id=case.case_id, report_id=report.report_id))
    return case


def _degroup_report_from_group(
    db: Session,
    report: Report,
    *,
    radius_meters: float,
) -> AutoGroupingResult:
    group_id = getattr(report, "incident_group_id", None)
    if group_id is None:
        return AutoGroupingResult(
            incident_group=None,
            case=None,
            grouped_reports=[],
            distinct_device_count=0,
        )

    group = db.query(IncidentGroup).filter(IncidentGroup.group_id == group_id).first()
    if group is None:
        report.incident_group_id = None
        return AutoGroupingResult(
            incident_group=None,
            case=None,
            grouped_reports=[],
            distinct_device_count=0,
        )

    case = group.case
    report.incident_group_id = None
    db.flush()

    if case is not None:
        db.query(CaseReport).filter(
            CaseReport.case_id == case.case_id,
            CaseReport.report_id == report.report_id,
        ).delete(synchronize_session=False)

    remaining_reports = _load_verified_group_reports(db, group, exclude_report_id=report.report_id)
    distinct_devices = len({str(r.device_id) for r in remaining_reports})

    if len(remaining_reports) < AUTO_GROUP_MIN_REPORTS or distinct_devices < AUTO_GROUP_MIN_DEVICES:
        for remaining in remaining_reports:
            remaining.incident_group_id = None

        if case is not None:
            db.query(CaseReport).filter(CaseReport.case_id == case.case_id).delete(synchronize_session=False)
            case.report_count = 0
            case.device_count = 0
            case.auto_created = True
            case.source = "ai_auto_grouped"
            case.auto_group_confidence = 0.0

        group.report_count = 0
        group.distinct_device_count = 0
        group.confidence_score = 0.0
        group.is_active = False
        group.metadata_json = {
            "device_count": 0,
            "report_ids": [],
            "degrouped_report_id": str(report.report_id),
            "degrouped_at": datetime.now(timezone.utc).isoformat(),
        }
        return AutoGroupingResult(
            incident_group=group,
            case=case,
            grouped_reports=[],
            distinct_device_count=0,
        )

    group = _upsert_group(db, remaining_reports, radius_meters=radius_meters)
    case = _upsert_case_for_group(db, group, remaining_reports)
    return AutoGroupingResult(
        incident_group=group,
        case=case,
        grouped_reports=remaining_reports,
        distinct_device_count=distinct_devices,
    )


def auto_group_verified_report(
    db: Session,
    report: Report,
    *,
    radius_meters: float = AUTO_GROUP_RADIUS_METERS,
    time_window_minutes: int = AUTO_GROUP_TIME_WINDOW_MINUTES,
    min_reports: int = AUTO_GROUP_MIN_REPORTS,
    min_devices: int = AUTO_GROUP_MIN_DEVICES,
) -> AutoGroupingResult:
    current_state = _report_lifecycle_state(report)
    if current_state != "verified":
        return _degroup_report_from_group(db, report, radius_meters=radius_meters)

    grouped_reports = find_groupable_reports(
        db,
        report,
        radius_meters=radius_meters,
        time_window_minutes=time_window_minutes,
    )
    distinct_device_count = len({str(r.device_id) for r in grouped_reports})
    if len(grouped_reports) < min_reports or distinct_device_count < min_devices:
        return AutoGroupingResult(
            incident_group=None,
            case=None,
            grouped_reports=grouped_reports,
            distinct_device_count=distinct_device_count,
        )

    group = _upsert_group(db, grouped_reports, radius_meters=radius_meters)
    case = _upsert_case_for_group(db, group, grouped_reports)
    return AutoGroupingResult(
        incident_group=group,
        case=case,
        grouped_reports=grouped_reports,
        distinct_device_count=distinct_device_count,
    )
