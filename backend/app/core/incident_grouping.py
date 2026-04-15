from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import func, text
from sqlalchemy.orm import Session, joinedload

from app.models.case import Case, CaseReport
from app.models.incident_group import IncidentGroup
from app.models.incident_type import IncidentType
from app.models.location import Location
from app.models.ml_prediction import MLPrediction
from app.models.police_user import PoliceUser
from app.models.report import Report
from app.models.station import Station


DEFAULT_TIME_WINDOW_HOURS = 24
DEFAULT_RADIUS_METERS = 500.0
DEFAULT_MIN_REPORTS = 3
DEFAULT_MIN_DISTINCT_DEVICES = 2
DEFAULT_LOOKBACK_HOURS = 72
DEFAULT_GROUP_MATCH_RADIUS_KM = 0.35
DEFAULT_GROUP_MATCH_TIME_HOURS = 6


@dataclass(slots=True)
class IncidentGroupCluster:
    incident_type_id: int
    reports: List[Report]
    center_lat: float
    center_long: float
    start_time: datetime
    end_time: datetime
    report_count: int
    device_count: int
    average_trust_score: Optional[float]
    location_name: Optional[str]


def _to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1 = radians(lat1)
    p2 = radians(lat2)
    dp = radians(lat2 - lat1)
    dl = radians(lon2 - lon1)
    a = sin(dp / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * r * asin(sqrt(a))


def _latest_ml_prediction(report: Report) -> Optional[MLPrediction]:
    preds = list(getattr(report, "ml_predictions", None) or [])
    if not preds:
        return None
    finals = [p for p in preds if getattr(p, "is_final", False)]
    source = finals or preds
    source.sort(
        key=lambda p: _to_utc(getattr(p, "evaluated_at", None))
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return source[0]


def _report_trust_score(report: Report) -> float:
    latest = _latest_ml_prediction(report)
    if latest is not None and latest.trust_score is not None:
        try:
            return float(latest.trust_score)
        except Exception:
            pass

    if (report.verification_status or "").lower() == "verified":
        return 90.0
    if (report.rule_status or "").lower() == "passed":
        return 65.0
    return 35.0


def _report_is_verified_for_auto_case(report: Report) -> bool:
    return (
        (report.verification_status or "").lower() == "verified"
        and (report.status or "").lower() == "verified"
    )


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


def _dominant_location_name(reports: Iterable[Report]) -> Optional[str]:
    names = [
        getattr(getattr(report, "village_location", None), "location_name", None)
        for report in reports
        if getattr(getattr(report, "village_location", None), "location_name", None)
    ]
    if names:
        return Counter(names).most_common(1)[0][0]
    return None


def _case_priority_from_reports(reports: Iterable[Report]) -> str:
    prioritized = [(getattr(report, "priority", None) or "").lower() for report in reports]
    if any(priority == "urgent" for priority in prioritized):
        return "urgent"
    if sum(1 for priority in prioritized if priority == "high") >= 2:
        return "high"
    if any(priority == "high" for priority in prioritized):
        return "medium"
    return "medium"


def _case_title_from_group(group: IncidentGroup, reports: Iterable[Report]) -> str:
    report_list = list(reports)
    first_report = report_list[0] if report_list else None
    incident_label = None
    if first_report is not None:
        incident_label = getattr(getattr(first_report, "incident_type", None), "type_name", None)
    if incident_label is None:
        incident_type = getattr(group, "incident_type", None)
        incident_label = getattr(incident_type, "type_name", None) or f"Incident Type {group.incident_type_id}"
    location_name = _dominant_location_name(report_list) or "reported area"
    report_count = len(report_list)
    return f"{incident_label} cluster in {location_name} ({report_count} reports)"


def _assign_officer_to_case(db: Session, case_lat: float, case_lon: float) -> Optional[int]:
    def calculate_distance(lat1: Optional[float], lon1: Optional[float], lat2: Optional[float], lon2: Optional[float]) -> float:
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return float("inf")
        return _haversine_km(float(lat1), float(lon1), float(lat2), float(lon2))

    stations = db.query(Station).filter(Station.is_active == True).all()
    if not stations:
        return None

    ranked_stations = sorted(
        stations,
        key=lambda station: calculate_distance(
            case_lat,
            case_lon,
            getattr(station, "latitude", None),
            getattr(station, "longitude", None),
        ),
    )

    for station in ranked_stations:
        officers = (
            db.query(PoliceUser)
            .filter(
                PoliceUser.is_active == True,
                PoliceUser.role == "officer",
                PoliceUser.station_id == station.station_id,
            )
            .all()
        )
        if not officers:
            continue

        officer_ids = [officer.police_user_id for officer in officers]
        case_count_rows = (
            db.query(Case.assigned_to_id, func.count(Case.case_id))
            .filter(
                Case.assigned_to_id.in_(officer_ids),
                Case.status != "closed",
            )
            .group_by(Case.assigned_to_id)
            .all()
        )
        open_case_counts = {row[0]: row[1] for row in case_count_rows}
        selected_officer = min(
            officers,
            key=lambda officer: open_case_counts.get(officer.police_user_id, 0),
        )
        return selected_officer.police_user_id

    return None


def _verified_reports_query(
    db: Session,
    *,
    incident_type_id: Optional[int] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
):
    query = (
        db.query(Report)
        .options(
            joinedload(Report.incident_type),
            joinedload(Report.village_location).joinedload(Location.parent),
            joinedload(Report.location),
            joinedload(Report.ml_predictions),
        )
        .filter(
            Report.verification_status == "verified",
            Report.status == "verified",
        )
    )
    if incident_type_id is not None:
        query = query.filter(Report.incident_type_id == incident_type_id)
    if since is not None:
        query = query.filter(Report.reported_at >= since)
    if until is not None:
        query = query.filter(Report.reported_at <= until)
    return query


def _report_time(report: Report) -> datetime:
    return _to_utc(report.reported_at) or datetime.min.replace(tzinfo=timezone.utc)


def _report_point(report: Report) -> Tuple[float, float]:
    return float(report.latitude), float(report.longitude)


def _cluster_reports(
    reports: Iterable[Report],
    *,
    radius_meters: float = DEFAULT_RADIUS_METERS,
    time_window_hours: int = DEFAULT_TIME_WINDOW_HOURS,
) -> List[IncidentGroupCluster]:
    sorted_reports = sorted(reports, key=_report_time)
    if not sorted_reports:
        return []

    radius_km = max(0.05, float(radius_meters) / 1000.0)
    time_window = timedelta(hours=max(1, int(time_window_hours)))
    seen: set[str] = set()
    clusters: List[IncidentGroupCluster] = []

    for seed in sorted_reports:
        seed_id = str(seed.report_id)
        if seed_id in seen:
            continue

        queue = [seed]
        cluster_reports = [seed]
        seen.add(seed_id)

        while queue:
            current = queue.pop(0)
            current_time = _report_time(current)
            current_lat, current_lon = _report_point(current)

            for candidate in sorted_reports:
                candidate_id = str(candidate.report_id)
                if candidate_id in seen:
                    continue
                if int(candidate.incident_type_id) != int(seed.incident_type_id):
                    continue

                candidate_time = _report_time(candidate)
                if abs(candidate_time - current_time) > time_window:
                    continue

                candidate_lat, candidate_lon = _report_point(candidate)
                if _haversine_km(current_lat, current_lon, candidate_lat, candidate_lon) > radius_km:
                    continue

                seen.add(candidate_id)
                cluster_reports.append(candidate)
                queue.append(candidate)

        if len(cluster_reports) < max(DEFAULT_MIN_REPORTS, 2):
            continue

        device_ids = {str(r.device_id) for r in cluster_reports if getattr(r, "device_id", None)}
        if len(device_ids) < DEFAULT_MIN_DISTINCT_DEVICES:
            continue

        lats = [float(r.latitude) for r in cluster_reports]
        lons = [float(r.longitude) for r in cluster_reports]
        times = sorted(_report_time(r) for r in cluster_reports)
        trust_scores = [_report_trust_score(r) for r in cluster_reports]
        village_names = [
            getattr(getattr(r, "village_location", None), "location_name", None)
            for r in cluster_reports
            if getattr(getattr(r, "village_location", None), "location_name", None)
        ]
        location_name = Counter(village_names).most_common(1)[0][0] if village_names else None

        clusters.append(
            IncidentGroupCluster(
                incident_type_id=int(seed.incident_type_id),
                reports=cluster_reports,
                center_lat=sum(lats) / len(lats),
                center_long=sum(lons) / len(lons),
                start_time=times[0],
                end_time=times[-1],
                report_count=len(cluster_reports),
                device_count=len(device_ids),
                average_trust_score=round(sum(trust_scores) / len(trust_scores), 2),
                location_name=location_name,
            )
        )

    return clusters


def cluster_verified_reports(
    db: Session,
    *,
    incident_type_id: Optional[int] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    radius_meters: float = DEFAULT_RADIUS_METERS,
    time_window_hours: int = DEFAULT_TIME_WINDOW_HOURS,
) -> List[IncidentGroupCluster]:
    reports = _verified_reports_query(
        db,
        incident_type_id=incident_type_id,
        since=since,
        until=until,
    ).all()
    return _cluster_reports(
        reports,
        radius_meters=radius_meters,
        time_window_hours=time_window_hours,
    )


def _group_distance_km(group: IncidentGroup, cluster: IncidentGroupCluster) -> float:
    return _haversine_km(
        float(group.center_lat),
        float(group.center_long),
        float(cluster.center_lat),
        float(cluster.center_long),
    )


def find_matching_group(
    db: Session,
    cluster: IncidentGroupCluster,
    *,
    match_radius_km: float = DEFAULT_GROUP_MATCH_RADIUS_KM,
    match_time_hours: int = DEFAULT_GROUP_MATCH_TIME_HOURS,
) -> Optional[IncidentGroup]:
    candidates = (
        db.query(IncidentGroup)
        .filter(IncidentGroup.incident_type_id == cluster.incident_type_id)
        .all()
    )
    if not candidates:
        return None

    time_window = timedelta(hours=max(1, int(match_time_hours)))
    best_group: Optional[IncidentGroup] = None
    best_score: Optional[Tuple[float, float]] = None

    for group in candidates:
        group_start = _to_utc(group.start_time)
        group_end = _to_utc(group.end_time)
        if group_start is None or group_end is None:
            continue

        if cluster.end_time < group_start - time_window or cluster.start_time > group_end + time_window:
            continue

        distance_km = _group_distance_km(group, cluster)
        if distance_km > match_radius_km:
            continue

        score = (
            abs((_to_utc(group_start) - cluster.start_time).total_seconds()) if group_start else 0.0,
            distance_km,
        )
        if best_score is None or score < best_score:
            best_score = score
            best_group = group

    return best_group


def upsert_group_from_cluster(
    db: Session,
    cluster: IncidentGroupCluster,
    *,
    match_radius_km: float = DEFAULT_GROUP_MATCH_RADIUS_KM,
    match_time_hours: int = DEFAULT_GROUP_MATCH_TIME_HOURS,
) -> tuple[IncidentGroup, str]:
    group = find_matching_group(
        db,
        cluster,
        match_radius_km=match_radius_km,
        match_time_hours=match_time_hours,
    )
    action = "updated" if group is not None else "created"

    if group is None:
        group = IncidentGroup(group_id=uuid4(), incident_type_id=cluster.incident_type_id)
        db.add(group)

    group.center_lat = cluster.center_lat
    group.center_long = cluster.center_long
    group.start_time = cluster.start_time
    group.end_time = cluster.end_time
    group.report_count = cluster.report_count

    return group, action


def _refresh_group_from_linked_reports(db: Session, group: IncidentGroup) -> bool:
    reports = (
        db.query(Report)
        .options(
            joinedload(Report.incident_type),
            joinedload(Report.village_location),
            joinedload(Report.ml_predictions),
        )
        .filter(
            Report.incident_group_id == group.group_id,
            Report.verification_status == "verified",
            Report.status == "verified",
        )
        .all()
    )

    if not reports:
        db.delete(group)
        return False

    lats = [float(report.latitude) for report in reports]
    lons = [float(report.longitude) for report in reports]
    times = sorted(_report_time(report) for report in reports)
    group.center_lat = sum(lats) / len(lats)
    group.center_long = sum(lons) / len(lons)
    group.start_time = times[0]
    group.end_time = times[-1]
    group.report_count = len(reports)
    return True


def detach_report_from_incident_group(db: Session, report: Report) -> bool:
    group_id = getattr(report, "incident_group_id", None)
    if group_id is None:
        return False

    report.incident_group_id = None
    db.flush()

    group = db.query(IncidentGroup).filter(IncidentGroup.group_id == group_id).first()
    if group is not None:
        _refresh_group_from_linked_reports(db, group)
    sync_case_for_group_id(db, group_id)
    db.commit()
    return True


def sync_incident_groups(
    db: Session,
    *,
    incident_type_id: Optional[int] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    radius_meters: float = DEFAULT_RADIUS_METERS,
    time_window_hours: int = DEFAULT_TIME_WINDOW_HOURS,
) -> Dict[str, Any]:
    verified_reports = _verified_reports_query(
        db,
        incident_type_id=incident_type_id,
        since=since,
        until=until,
    ).all()
    clusters = _cluster_reports(
        verified_reports,
        radius_meters=radius_meters,
        time_window_hours=time_window_hours,
    )

    created = 0
    updated = 0
    deleted = 0
    case_created = 0
    case_updated = 0
    case_deleted = 0
    groups: List[IncidentGroup] = []
    touched_group_ids: set[Any] = set()

    for report in verified_reports:
        if getattr(report, "incident_group_id", None) is not None:
            touched_group_ids.add(report.incident_group_id)
        report.incident_group_id = None

    db.flush()

    for cluster in clusters:
        group, action = upsert_group_from_cluster(db, cluster)
        db.flush()
        for report in cluster.reports:
            report.incident_group_id = group.group_id
        touched_group_ids.add(group.group_id)
        groups.append(group)
        if action == "created":
            created += 1
        else:
            updated += 1

    refreshed_groups: List[IncidentGroup] = []
    for group_id in touched_group_ids:
        group = db.query(IncidentGroup).filter(IncidentGroup.group_id == group_id).first()
        if group is None:
            continue
        if _refresh_group_from_linked_reports(db, group):
            refreshed_groups.append(group)
        else:
            deleted += 1

    for group_id in touched_group_ids:
        case_stats = sync_case_for_group_id(db, group_id)
        action = case_stats.get("action")
        if action == "created":
            case_created += 1
        elif action == "updated":
            case_updated += 1
        elif action == "deleted":
            case_deleted += 1

    db.commit()

    return {
        "clusters": clusters,
        "groups": refreshed_groups or groups,
        "created": created,
        "updated": updated,
        "deleted": deleted,
        "case_created": case_created,
        "case_updated": case_updated,
        "case_deleted": case_deleted,
        "matched": created + updated,
        "cluster_count": len(clusters),
    }


def sync_incident_groups_for_report(
    db: Session,
    report: Report,
    *,
    lookback_hours: int = DEFAULT_LOOKBACK_HOURS,
    radius_meters: float = DEFAULT_RADIUS_METERS,
    time_window_hours: int = DEFAULT_TIME_WINDOW_HOURS,
) -> Dict[str, Any]:
    if not _report_is_verified_for_auto_case(report):
        detach_report_from_incident_group(db, report)
        return {"created": 0, "updated": 0, "deleted": 0, "matched": 0, "cluster_count": 0, "groups": []}

    report_time = _report_time(report)
    lookback = timedelta(hours=max(int(lookback_hours), int(time_window_hours)))
    return sync_incident_groups(
        db,
        incident_type_id=int(report.incident_type_id),
        since=report_time - lookback,
        until=report_time + lookback,
        radius_meters=radius_meters,
        time_window_hours=time_window_hours,
    )


def _case_linked_report_ids(db: Session, case: Case) -> set[str]:
    rows = (
        db.query(CaseReport.report_id)
        .filter(CaseReport.case_id == case.case_id)
        .all()
    )
    return {str(row[0]) for row in rows}


def _case_reports_linked_to_case(db: Session, case: Case) -> List[Report]:
    return (
        db.query(Report)
        .options(
            joinedload(Report.incident_type),
            joinedload(Report.village_location).joinedload(Location.parent),
            joinedload(Report.location),
            joinedload(Report.ml_predictions),
        )
        .join(CaseReport, CaseReport.report_id == Report.report_id)
        .filter(CaseReport.case_id == case.case_id)
        .order_by(Report.reported_at.asc(), Report.report_id.asc())
        .all()
    )


def _case_location_id_from_reports(reports: Iterable[Report]) -> Optional[int]:
    location_ids = [
        getattr(report, "location_id", None)
        for report in reports
        if getattr(report, "location_id", None) is not None
    ]
    if location_ids:
        return int(Counter(location_ids).most_common(1)[0][0])

    village_location_ids = [
        getattr(report, "village_location_id", None)
        for report in reports
        if getattr(report, "village_location_id", None) is not None
    ]
    if village_location_ids:
        return int(Counter(village_location_ids).most_common(1)[0][0])
    return None


def _case_lat_lon_from_reports(reports: Iterable[Report]) -> tuple[Optional[float], Optional[float]]:
    report_list = list(reports)
    if not report_list:
        return None, None
    lats = [float(report.latitude) for report in report_list]
    lons = [float(report.longitude) for report in report_list]
    return sum(lats) / len(lats), sum(lons) / len(lons)


def _case_description_from_reports(reports: Iterable[Report]) -> str:
    report_list = list(reports)
    device_count = len({str(report.device_id) for report in report_list if getattr(report, "device_id", None)})
    return (
        f"Auto-generated case from {len(report_list)} verified reports "
        f"across {device_count} devices."
    )


def _case_title_looks_auto_generated(title: Optional[str]) -> bool:
    if not title:
        return True
    lowered = title.lower()
    return lowered.startswith("incident type") or lowered.startswith("auto-generated") or "cluster" in lowered


def find_matching_case_for_group(db: Session, group: IncidentGroup) -> Optional[Case]:
    linked_case = db.query(Case).filter(Case.incident_group_id == group.group_id).first()
    if linked_case is not None:
        return linked_case

    report_ids = [str(report.report_id) for report in fetch_group_reports(db, group, limit=None)]
    if not report_ids:
        return None

    from sqlalchemy import func

    matches = (
        db.query(Case, func.count(CaseReport.report_id).label("overlap_count"))
        .join(CaseReport, CaseReport.case_id == Case.case_id)
        .filter(CaseReport.report_id.in_(report_ids))
        .group_by(Case.case_id)
        .order_by(
            func.count(CaseReport.report_id).desc(),
            Case.opened_at.asc().nullslast(),
            Case.case_id.asc(),
        )
        .all()
    )
    if not matches:
        return None

    case, overlap_count = matches[0]
    if int(overlap_count or 0) <= 0:
        return None
    return case


def _sync_case_reports(
    db: Session,
    case: Case,
    reports: List[Report],
) -> None:
    case_reports_table = CaseReport.__table__
    existing_report_ids = _case_linked_report_ids(db, case)
    for report in reports:
        if str(report.report_id) in existing_report_ids:
            continue
        db.execute(
            case_reports_table.insert().values(
                case_id=case.case_id,
                report_id=report.report_id,
                added_at=datetime.now(timezone.utc),
            )
        )


def sync_case_for_group(
    db: Session,
    group: IncidentGroup,
) -> Dict[str, Any]:
    reports = fetch_group_reports(db, group, limit=None)
    existing_case = (
        db.query(Case)
        .filter(Case.incident_group_id == group.group_id)
        .first()
    )

    if not reports:
        if existing_case is not None:
            db.delete(existing_case)
            return {"action": "deleted", "case": None, "report_count": 0}
        return {"action": "skipped", "case": None, "report_count": 0}

    report_count = len(reports)
    case_lat = sum(float(report.latitude) for report in reports) / report_count
    case_lon = sum(float(report.longitude) for report in reports) / report_count
    officer_id = _assign_officer_to_case(db, case_lat, case_lon)
    location_id = next(
        (
            getattr(report, "location_id", None) or getattr(report, "village_location_id", None)
            for report in reports
            if getattr(report, "location_id", None) or getattr(report, "village_location_id", None)
        ),
        None,
    )
    priority = _case_priority_from_reports(reports)
    title = _case_title_from_group(group, reports)
    description = (
        f"Auto-generated case from {report_count} verified reports "
        f"across {len({str(report.device_id) for report in reports if getattr(report, 'device_id', None)})} devices."
    )

    if existing_case is None:
        existing_case = Case(
            case_id=uuid4(),
            case_number=_generate_case_number(db),
            status="open",
            priority=priority,
            title=title,
            description=description,
            location_id=location_id,
            incident_type_id=group.incident_type_id,
            incident_group_id=group.group_id,
            assigned_to_id=officer_id,
            report_count=report_count,
            latitude=case_lat,
            longitude=case_lon,
            opened_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(existing_case)
        action = "created"
    else:
        existing_case.priority = priority
        if _case_title_looks_auto_generated(existing_case.title):
            existing_case.title = title
        if not (existing_case.description or "").strip():
            existing_case.description = description
        existing_case.location_id = location_id
        existing_case.incident_type_id = group.incident_type_id
        existing_case.incident_group_id = group.group_id
        if existing_case.assigned_to_id is None and officer_id is not None:
            existing_case.assigned_to_id = officer_id
        existing_case.latitude = case_lat
        existing_case.longitude = case_lon
        existing_case.updated_at = datetime.now(timezone.utc)
        action = "updated"

    db.flush()
    _sync_case_reports(db, existing_case, reports)
    all_case_reports = _case_reports_linked_to_case(db, existing_case)
    if all_case_reports:
        existing_case.report_count = len(all_case_reports)
        existing_case.latitude, existing_case.longitude = _case_lat_lon_from_reports(all_case_reports)
        if existing_case.location_id is None:
            existing_case.location_id = _case_location_id_from_reports(all_case_reports)
        if _case_title_looks_auto_generated(existing_case.title):
            existing_case.title = _case_title_from_group(group, all_case_reports)
        if not (existing_case.description or "").strip():
            existing_case.description = _case_description_from_reports(all_case_reports)
    return {"action": action, "case": existing_case, "report_count": report_count}


def sync_cases_for_groups(
    db: Session,
    groups: Iterable[IncidentGroup],
) -> Dict[str, Any]:
    created = 0
    updated = 0
    deleted = 0
    cases: List[Case] = []

    for group in groups:
        result = sync_case_for_group(db, group)
        case = result.get("case")
        if case is not None:
            cases.append(case)
        action = result.get("action")
        if action == "created":
            created += 1
        elif action == "updated":
            updated += 1
        elif action == "deleted":
            deleted += 1

    return {
        "created": created,
        "updated": updated,
        "deleted": deleted,
        "matched": created + updated,
        "cases": cases,
    }


def sync_cases_from_incident_groups(
    db: Session,
    *,
    incident_type_id: Optional[int] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    query = db.query(IncidentGroup)
    if incident_type_id is not None:
        query = query.filter(IncidentGroup.incident_type_id == incident_type_id)
    if since is not None:
        query = query.filter(IncidentGroup.end_time >= since)
    if until is not None:
        query = query.filter(IncidentGroup.start_time <= until)

    query = query.order_by(IncidentGroup.created_at.desc(), IncidentGroup.start_time.desc())
    if limit is not None:
        query = query.limit(limit)

    return sync_cases_for_groups(db, query.all())


def sync_case_for_group_id(
    db: Session,
    group_id: UUID,
) -> Dict[str, Any]:
    group = db.query(IncidentGroup).filter(IncidentGroup.group_id == group_id).first()
    if group is None:
        existing_case = db.query(Case).filter(Case.incident_group_id == group_id).first()
        if existing_case is not None:
            db.delete(existing_case)
            return {"action": "deleted", "case": None, "report_count": 0}
        return {"action": "skipped", "case": None, "report_count": 0}
    return sync_case_for_group(db, group)


def find_related_reports_for_report(
    db: Session,
    report: Report,
    *,
    limit: int = 5,
    radius_meters: float = DEFAULT_RADIUS_METERS,
    time_window_hours: int = DEFAULT_TIME_WINDOW_HOURS,
) -> List[Report]:
    if getattr(report, "incident_group_id", None) is not None:
        group = db.query(IncidentGroup).filter(IncidentGroup.group_id == report.incident_group_id).first()
        if group is not None:
            reports = fetch_group_reports(
                db,
                group,
                radius_meters=radius_meters,
                time_margin_hours=max(1, int(time_window_hours)),
                limit=None,
            )
            related = [item for item in reports if item.report_id != report.report_id]
            related.sort(key=_report_time, reverse=True)
            return related[:limit]

    report_time = _report_time(report)
    window = timedelta(hours=max(1, int(time_window_hours)))
    query = (
        _verified_reports_query(
            db,
            incident_type_id=int(report.incident_type_id),
            since=report_time - window,
            until=report_time + window,
        )
        .options(
            joinedload(Report.incident_type),
            joinedload(Report.village_location),
            joinedload(Report.device),
            joinedload(Report.ml_predictions),
        )
        .filter(Report.report_id != report.report_id)
    )

    if getattr(report, "device_id", None) is not None:
        query = query.filter(Report.device_id != report.device_id)

    candidates = query.all()
    if not candidates:
        return []

    clusters = _cluster_reports(
        [report, *candidates],
        radius_meters=radius_meters,
        time_window_hours=time_window_hours,
    )
    for cluster in clusters:
        if any(item.report_id == report.report_id for item in cluster.reports):
            related = [item for item in cluster.reports if item.report_id != report.report_id]
            related.sort(key=lambda item: (_report_time(item), str(item.report_id)), reverse=True)
            return related[:limit]

    return []


def _report_is_inside_group(
    report: Report,
    group: IncidentGroup,
    *,
    radius_meters: float = DEFAULT_RADIUS_METERS,
    time_margin_hours: int = DEFAULT_GROUP_MATCH_TIME_HOURS,
) -> bool:
    if int(report.incident_type_id) != int(group.incident_type_id):
        return False

    group_start = _to_utc(group.start_time)
    group_end = _to_utc(group.end_time)
    report_time = _report_time(report)
    if group_start is None or group_end is None:
        return False

    margin = timedelta(hours=max(1, int(time_margin_hours)))
    if report_time < group_start - margin or report_time > group_end + margin:
        return False

    return _haversine_km(
        float(group.center_lat),
        float(group.center_long),
        float(report.latitude),
        float(report.longitude),
    ) <= max(0.05, float(radius_meters) / 1000.0)


def fetch_group_reports(
    db: Session,
    group: IncidentGroup,
    *,
    radius_meters: float = DEFAULT_RADIUS_METERS,
    time_margin_hours: int = DEFAULT_GROUP_MATCH_TIME_HOURS,
    limit: Optional[int] = None,
) -> List[Report]:
    linked_reports = (
        db.query(Report)
        .options(
            joinedload(Report.incident_type),
            joinedload(Report.village_location),
            joinedload(Report.ml_predictions),
        )
        .filter(
            Report.incident_group_id == group.group_id,
            Report.verification_status == "verified",
            Report.status == "verified",
        )
        .order_by(Report.reported_at.desc())
        .all()
    )
    if linked_reports:
        if limit is None:
            return linked_reports
        return linked_reports[:limit]

    reports = _verified_reports_query(
        db,
        incident_type_id=group.incident_type_id,
        since=_to_utc(group.start_time) - timedelta(hours=max(1, int(time_margin_hours))),
        until=_to_utc(group.end_time) + timedelta(hours=max(1, int(time_margin_hours))),
    ).all()

    matches = [
        report
        for report in reports
        if _report_is_inside_group(
            report,
            group,
            radius_meters=radius_meters,
            time_margin_hours=time_margin_hours,
        )
    ]
    matches.sort(key=_report_time, reverse=True)
    if limit is None:
        return matches
    return matches[:limit]


def serialize_report_preview(report: Report) -> Dict[str, Any]:
    latest = _latest_ml_prediction(report)
    trust_score = None
    if latest is not None and latest.trust_score is not None:
        try:
            trust_score = round(float(latest.trust_score), 2)
        except Exception:
            trust_score = None

    return {
        "report_id": str(report.report_id),
        "report_number": getattr(report, "report_number", None),
        "device_id": str(report.device_id) if getattr(report, "device_id", None) else None,
        "incident_type_id": int(report.incident_type_id),
        "incident_type_name": getattr(getattr(report, "incident_type", None), "type_name", None),
        "reported_at": _to_utc(report.reported_at),
        "latitude": float(report.latitude),
        "longitude": float(report.longitude),
        "verification_status": getattr(report, "verification_status", None),
        "rule_status": getattr(report, "rule_status", None),
        "village_name": getattr(getattr(report, "village_location", None), "location_name", None),
        "trust_score": trust_score,
    }


def summarize_group(
    db: Session,
    group: IncidentGroup,
    *,
    preview_limit: int = 5,
    radius_meters: float = DEFAULT_RADIUS_METERS,
    time_margin_hours: int = DEFAULT_GROUP_MATCH_TIME_HOURS,
) -> Dict[str, Any]:
    reports = fetch_group_reports(
        db,
        group,
        radius_meters=radius_meters,
        time_margin_hours=time_margin_hours,
        limit=None,
    )
    preview_reports = reports[:preview_limit]

    average_trust_score = None
    if reports:
        scores = [item["trust_score"] for item in map(serialize_report_preview, reports) if item["trust_score"] is not None]
        if scores:
            average_trust_score = round(sum(scores) / len(scores), 2)

    incident_type_name = None
    if reports:
        incident_type_name = reports[0].incident_type.type_name if getattr(reports[0], "incident_type", None) else None
    if incident_type_name is None:
        incident_type = db.query(IncidentType).filter(IncidentType.incident_type_id == group.incident_type_id).first()
        incident_type_name = incident_type.type_name if incident_type else None

    dominant_village_name = None
    if reports:
        village_names = [
            getattr(getattr(report, "village_location", None), "location_name", None)
            for report in reports
            if getattr(getattr(report, "village_location", None), "location_name", None)
        ]
        if village_names:
            dominant_village_name = Counter(village_names).most_common(1)[0][0]

    return {
        "group_id": str(group.group_id),
        "incident_type_id": int(group.incident_type_id),
        "incident_type_name": incident_type_name,
        "center_lat": float(group.center_lat),
        "center_long": float(group.center_long),
        "start_time": _to_utc(group.start_time),
        "end_time": _to_utc(group.end_time),
        "report_count": int(group.report_count or 0),
        "created_at": _to_utc(group.created_at),
        "location_name": dominant_village_name,
        "device_count": len(
            {
                preview["device_id"]
                for preview in map(serialize_report_preview, reports)
                if preview["device_id"]
            }
        ),
        "average_trust_score": average_trust_score,
        "time_span_hours": round(
            max(
                0.0,
                (
                    (_to_utc(group.end_time) or _to_utc(group.start_time))
                    - (_to_utc(group.start_time) or _to_utc(group.end_time))
                ).total_seconds()
                / 3600.0,
            ),
            2,
        ),
        "report_ids": [str(report.report_id) for report in reports],
        "sample_reports": [serialize_report_preview(report) for report in preview_reports],
    }
