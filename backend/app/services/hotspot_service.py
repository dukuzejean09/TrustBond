"""
Hotspot Service - Crime hotspot detection and management
"""
from app import db
from app.models.hotspots import Hotspot, HotspotReport, HotspotHistory, ClusteringRun
from app.models.incident_report import IncidentReport
from datetime import datetime, timedelta
from geopy.distance import geodesic
import uuid
import numpy as np
from collections import defaultdict


class HotspotService:
    """Service for hotspot detection and management"""
    
    # ==================== HOTSPOT RETRIEVAL ====================
    @staticmethod
    def get_all_hotspots(filters=None, page=1, per_page=20):
        """Get all hotspots with optional filters"""
        query = Hotspot.query
        
        if filters:
            if filters.get('district_id'):
                query = query.filter_by(district_id=filters['district_id'])
            if filters.get('sector_id'):
                query = query.filter_by(sector_id=filters['sector_id'])
            if filters.get('status'):
                query = query.filter_by(status=filters['status'])
            if filters.get('risk_level'):
                query = query.filter_by(risk_level=filters['risk_level'])
            if filters.get('is_active') is not None:
                query = query.filter_by(is_active=filters['is_active'])
        
        return query.order_by(Hotspot.priority_score.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_hotspot_by_id(hotspot_id):
        """Get hotspot by ID"""
        return Hotspot.query.get(hotspot_id)
    
    @staticmethod
    def get_active_hotspots(district_id=None):
        """Get all active hotspots"""
        query = Hotspot.query.filter_by(is_active=True)
        if district_id:
            query = query.filter_by(district_id=district_id)
        return query.order_by(Hotspot.priority_score.desc()).all()
    
    # ==================== CLUSTERING (DBSCAN) ====================
    @staticmethod
    def run_clustering(
        district_id=None,
        epsilon_meters=500,
        min_samples=3,
        trust_weight_enabled=True,
        min_trust_score=30,
        days_back=30,
        triggered_by_user_id=None
    ):
        """Run DBSCAN clustering to detect hotspots"""
        run_id = str(uuid.uuid4())
        
        # Create clustering run record
        clustering_run = ClusteringRun(
            run_id=run_id,
            district_id=district_id,
            epsilon_meters=epsilon_meters,
            min_samples=min_samples,
            trust_weight_enabled=trust_weight_enabled,
            min_trust_score_threshold=min_trust_score,
            date_range_start=datetime.utcnow() - timedelta(days=days_back),
            date_range_end=datetime.utcnow(),
            status='running',
            triggered_by=triggered_by_user_id
        )
        db.session.add(clustering_run)
        db.session.commit()
        
        try:
            # Get reports for clustering
            query = IncidentReport.query.filter(
                IncidentReport.reported_at >= datetime.utcnow() - timedelta(days=days_back),
                IncidentReport.is_auto_rejected == False
            )
            
            if district_id:
                query = query.filter_by(district_id=district_id)
            
            if trust_weight_enabled and min_trust_score:
                query = query.filter(IncidentReport.ml_trust_score >= min_trust_score)
            
            reports = query.all()
            clustering_run.total_reports_processed = len(reports)
            
            if len(reports) < min_samples:
                clustering_run.status = 'completed'
                clustering_run.clusters_found = 0
                clustering_run.noise_points = len(reports)
                clustering_run.completed_at = datetime.utcnow()
                db.session.commit()
                return {'run_id': run_id, 'clusters_found': 0, 'message': 'Not enough reports for clustering'}
            
            # Extract coordinates and trust scores
            points = []
            report_data = []
            for report in reports:
                points.append([float(report.latitude), float(report.longitude)])
                report_data.append({
                    'report': report,
                    'trust_score': float(report.ml_trust_score or 50)
                })
            
            # Run simplified DBSCAN
            labels = HotspotService._simple_dbscan(
                points, 
                epsilon_meters=epsilon_meters,
                min_samples=min_samples
            )
            
            # Group reports by cluster
            clusters = defaultdict(list)
            noise_count = 0
            
            for i, label in enumerate(labels):
                if label == -1:
                    noise_count += 1
                else:
                    clusters[label].append(report_data[i])
            
            clustering_run.reports_after_filtering = len(reports)
            clustering_run.clusters_found = len(clusters)
            clustering_run.noise_points = noise_count
            
            # Create hotspots from clusters
            created_hotspots = []
            for cluster_label, cluster_reports in clusters.items():
                hotspot = HotspotService._create_hotspot_from_cluster(
                    cluster_label=cluster_label,
                    cluster_reports=cluster_reports,
                    run_id=run_id,
                    epsilon_meters=epsilon_meters,
                    min_samples=min_samples,
                    trust_weight_enabled=trust_weight_enabled
                )
                created_hotspots.append(hotspot)
            
            # Calculate average cluster size
            if clusters:
                avg_size = sum(len(c) for c in clusters.values()) / len(clusters)
                clustering_run.avg_cluster_size = avg_size
            
            clustering_run.status = 'completed'
            clustering_run.completed_at = datetime.utcnow()
            clustering_run.execution_time_seconds = (
                clustering_run.completed_at - clustering_run.started_at
            ).total_seconds()
            
            db.session.commit()
            
            return {
                'run_id': run_id,
                'clusters_found': len(clusters),
                'noise_points': noise_count,
                'total_reports': len(reports),
                'hotspots': [HotspotService.hotspot_to_dict(h) for h in created_hotspots]
            }
            
        except Exception as e:
            clustering_run.status = 'failed'
            clustering_run.error_message = str(e)
            clustering_run.completed_at = datetime.utcnow()
            db.session.commit()
            raise
    
    @staticmethod
    def _simple_dbscan(points, epsilon_meters, min_samples):
        """Simplified DBSCAN implementation"""
        n_points = len(points)
        labels = [-1] * n_points  # -1 = noise
        cluster_id = 0
        visited = [False] * n_points
        
        def get_neighbors(point_idx):
            neighbors = []
            for i in range(n_points):
                if i != point_idx:
                    dist = geodesic(points[point_idx], points[i]).meters
                    if dist <= epsilon_meters:
                        neighbors.append(i)
            return neighbors
        
        for i in range(n_points):
            if visited[i]:
                continue
            
            visited[i] = True
            neighbors = get_neighbors(i)
            
            if len(neighbors) < min_samples - 1:
                continue  # Noise point
            
            # Start new cluster
            labels[i] = cluster_id
            
            # Expand cluster
            seed_set = list(neighbors)
            j = 0
            while j < len(seed_set):
                q = seed_set[j]
                
                if not visited[q]:
                    visited[q] = True
                    q_neighbors = get_neighbors(q)
                    
                    if len(q_neighbors) >= min_samples - 1:
                        seed_set.extend(q_neighbors)
                
                if labels[q] == -1:
                    labels[q] = cluster_id
                
                j += 1
            
            cluster_id += 1
        
        return labels
    
    @staticmethod
    def _create_hotspot_from_cluster(cluster_label, cluster_reports, run_id, 
                                      epsilon_meters, min_samples, trust_weight_enabled):
        """Create a hotspot from a cluster of reports"""
        # Calculate centroid
        lats = [float(r['report'].latitude) for r in cluster_reports]
        lons = [float(r['report'].longitude) for r in cluster_reports]
        centroid_lat = sum(lats) / len(lats)
        centroid_lon = sum(lons) / len(lons)
        
        # Calculate statistics
        trust_scores = [r['trust_score'] for r in cluster_reports]
        unique_devices = len(set(r['report'].device_id for r in cluster_reports))
        
        # Count by classification
        trusted_count = sum(1 for r in cluster_reports if r['report'].trust_classification == 'Trusted')
        suspicious_count = sum(1 for r in cluster_reports if r['report'].trust_classification == 'Suspicious')
        false_count = sum(1 for r in cluster_reports if r['report'].trust_classification == 'False')
        verified_count = sum(1 for r in cluster_reports if r['report'].police_verified)
        
        # Calculate radius
        distances = [
            geodesic((centroid_lat, centroid_lon), (float(r['report'].latitude), float(r['report'].longitude))).meters
            for r in cluster_reports
        ]
        radius = max(distances) if distances else 0
        
        # Calculate temporal data
        timestamps = [r['report'].incident_occurred_at or r['report'].reported_at for r in cluster_reports]
        timestamps = [t for t in timestamps if t]
        
        # Incident type distribution
        type_counts = defaultdict(int)
        for r in cluster_reports:
            type_counts[r['report'].incident_type_id] += 1
        
        dominant_type_id = max(type_counts, key=type_counts.get) if type_counts else None
        dominant_pct = (type_counts[dominant_type_id] / len(cluster_reports) * 100) if dominant_type_id else 0
        
        # Calculate risk level
        avg_trust = sum(trust_scores) / len(trust_scores)
        risk_level = HotspotService._calculate_risk_level(
            len(cluster_reports), avg_trust, trusted_count, verified_count
        )
        
        # Calculate priority score
        priority_score = HotspotService._calculate_priority_score(
            len(cluster_reports), avg_trust, unique_devices, radius, timestamps
        )
        
        # Get location from first report
        first_report = cluster_reports[0]['report']
        
        hotspot = Hotspot(
            cluster_label=cluster_label,
            cluster_run_id=run_id,
            centroid_latitude=centroid_lat,
            centroid_longitude=centroid_lon,
            radius_meters=radius,
            district_id=first_report.district_id,
            sector_id=first_report.sector_id,
            cell_id=first_report.cell_id,
            village_id=first_report.village_id,
            report_count=len(cluster_reports),
            unique_devices=unique_devices,
            avg_trust_score=avg_trust,
            min_trust_score=min(trust_scores),
            max_trust_score=max(trust_scores),
            std_trust_score=float(np.std(trust_scores)) if len(trust_scores) > 1 else 0,
            trusted_report_count=trusted_count,
            suspicious_report_count=suspicious_count,
            false_report_count=false_count,
            police_verified_count=verified_count,
            earliest_incident_at=min(timestamps) if timestamps else None,
            latest_incident_at=max(timestamps) if timestamps else None,
            time_span_hours=int((max(timestamps) - min(timestamps)).total_seconds() / 3600) if len(timestamps) > 1 else 0,
            incident_type_distribution=dict(type_counts),
            dominant_incident_type_id=dominant_type_id,
            dominant_incident_pct=dominant_pct,
            risk_level=risk_level,
            priority_score=priority_score,
            dbscan_epsilon_meters=epsilon_meters,
            dbscan_min_samples=min_samples,
            trust_weight_enabled=trust_weight_enabled,
            is_active=True,
            status='new'
        )
        db.session.add(hotspot)
        db.session.flush()  # Get hotspot_id
        
        # Link reports to hotspot
        for r in cluster_reports:
            report = r['report']
            dist = geodesic(
                (centroid_lat, centroid_lon),
                (float(report.latitude), float(report.longitude))
            ).meters
            
            link = HotspotReport(
                hotspot_id=hotspot.hotspot_id,
                report_id=report.report_id,
                trust_weight=r['trust_score'] / 100,
                distance_to_centroid_meters=dist,
                is_core_point=dist <= epsilon_meters / 2
            )
            db.session.add(link)
            
            # Update report
            report.hotspot_id = hotspot.hotspot_id
            report.added_to_hotspot_at = datetime.utcnow()
        
        return hotspot
    
    @staticmethod
    def _calculate_risk_level(report_count, avg_trust, trusted_count, verified_count):
        """Calculate risk level based on cluster characteristics"""
        score = 0
        
        # More reports = higher risk
        if report_count >= 10:
            score += 3
        elif report_count >= 5:
            score += 2
        else:
            score += 1
        
        # Higher trust = higher risk (more credible)
        if avg_trust >= 70:
            score += 3
        elif avg_trust >= 50:
            score += 2
        else:
            score += 1
        
        # Verified reports = higher risk
        if verified_count >= 3:
            score += 2
        elif verified_count >= 1:
            score += 1
        
        if score >= 7:
            return 'critical'
        elif score >= 5:
            return 'high'
        elif score >= 3:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def _calculate_priority_score(report_count, avg_trust, unique_devices, radius, timestamps):
        """Calculate priority score (0-100)"""
        score = 0
        
        # Report count (max 30 points)
        score += min(30, report_count * 3)
        
        # Trust score (max 30 points)
        score += avg_trust * 0.3
        
        # Device diversity (max 20 points)
        score += min(20, unique_devices * 4)
        
        # Compactness (smaller = higher priority) (max 10 points)
        if radius > 0:
            score += max(0, 10 - radius / 100)
        
        # Recency (max 10 points)
        if timestamps:
            hours_ago = (datetime.utcnow() - max(timestamps)).total_seconds() / 3600
            score += max(0, 10 - hours_ago / 24)
        
        return min(100, score)
    
    # ==================== HOTSPOT MANAGEMENT ====================
    @staticmethod
    def assign_hotspot(hotspot_id, officer_id, unit=None):
        """Assign hotspot to an officer"""
        hotspot = Hotspot.query.get(hotspot_id)
        if not hotspot:
            return None
        
        hotspot.is_assigned = True
        hotspot.assigned_to_officer_id = officer_id
        hotspot.assigned_to_unit = unit
        hotspot.assigned_at = datetime.utcnow()
        hotspot.status = 'responding'
        
        db.session.commit()
        return hotspot
    
    @staticmethod
    def update_hotspot_status(hotspot_id, status):
        """Update hotspot status"""
        hotspot = Hotspot.query.get(hotspot_id)
        if not hotspot:
            return None
        
        hotspot.status = status
        hotspot.updated_at = datetime.utcnow()
        
        db.session.commit()
        return hotspot
    
    @staticmethod
    def address_hotspot(hotspot_id, resolution_notes, addressed_by_user_id):
        """Mark hotspot as addressed"""
        hotspot = Hotspot.query.get(hotspot_id)
        if not hotspot:
            return None
        
        hotspot.is_addressed = True
        hotspot.addressed_at = datetime.utcnow()
        hotspot.addressed_by = addressed_by_user_id
        hotspot.resolution_notes = resolution_notes
        hotspot.status = 'addressed'
        hotspot.is_active = False
        
        db.session.commit()
        return hotspot
    
    @staticmethod
    def deactivate_hotspot(hotspot_id):
        """Deactivate a hotspot"""
        hotspot = Hotspot.query.get(hotspot_id)
        if hotspot:
            hotspot.is_active = False
            hotspot.updated_at = datetime.utcnow()
            db.session.commit()
        return hotspot
    
    # ==================== HOTSPOT HISTORY ====================
    @staticmethod
    def create_history_snapshot(hotspot_id):
        """Create a historical snapshot of hotspot"""
        hotspot = Hotspot.query.get(hotspot_id)
        if not hotspot:
            return None
        
        # Get previous snapshot
        prev = HotspotHistory.query.filter_by(hotspot_id=hotspot_id)\
            .order_by(HotspotHistory.snapshot_date.desc()).first()
        
        history = HotspotHistory(
            hotspot_id=hotspot_id,
            snapshot_date=datetime.utcnow().date(),
            report_count=hotspot.report_count,
            avg_trust_score=hotspot.avg_trust_score,
            risk_level=hotspot.risk_level,
            priority_score=hotspot.priority_score,
            report_count_change=hotspot.report_count - prev.report_count if prev else 0,
            trust_score_change=float(hotspot.avg_trust_score or 0) - float(prev.avg_trust_score or 0) if prev else 0,
            risk_level_changed=hotspot.risk_level != prev.risk_level if prev else False,
            trend_direction=HotspotService._determine_trend(hotspot, prev)
        )
        
        db.session.add(history)
        db.session.commit()
        return history
    
    @staticmethod
    def _determine_trend(hotspot, prev):
        """Determine trend direction"""
        if not prev:
            return 'stable'
        
        report_change = hotspot.report_count - prev.report_count
        
        if report_change > 2:
            return 'worsening'
        elif report_change < -2:
            return 'improving'
        else:
            return 'stable'
    
    @staticmethod
    def get_hotspot_history(hotspot_id, limit=30):
        """Get hotspot history"""
        return HotspotHistory.query.filter_by(hotspot_id=hotspot_id)\
            .order_by(HotspotHistory.snapshot_date.desc()).limit(limit).all()
    
    # ==================== CLUSTERING RUNS ====================
    @staticmethod
    def get_clustering_runs(limit=20):
        """Get recent clustering runs"""
        return ClusteringRun.query.order_by(ClusteringRun.started_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_clustering_run(run_id):
        """Get clustering run by ID"""
        return ClusteringRun.query.get(run_id)
    
    # ==================== PUBLIC SAFETY MAP ====================
    @staticmethod
    def get_public_hotspots(district_id=None, min_reports=3):
        """Get anonymized hotspots for public safety map"""
        query = Hotspot.query.filter(
            Hotspot.is_active == True,
            Hotspot.report_count >= min_reports
        )
        
        if district_id:
            query = query.filter_by(district_id=district_id)
        
        hotspots = query.all()
        
        # Return anonymized data
        return [{
            'latitude': float(h.centroid_latitude),
            'longitude': float(h.centroid_longitude),
            'radius_meters': float(h.radius_meters or 500),
            'risk_level': h.risk_level,
            'incident_count': h.report_count,
            'top_incident_type': h.dominant_incident_type_id,
            'safety_advice': HotspotService._get_safety_advice(h.risk_level)
        } for h in hotspots]
    
    @staticmethod
    def _get_safety_advice(risk_level):
        """Get safety advice based on risk level"""
        advice = {
            'critical': 'High incident area. Exercise extreme caution and avoid if possible.',
            'high': 'Elevated risk area. Stay alert and avoid traveling alone.',
            'medium': 'Moderate activity area. Be aware of your surroundings.',
            'low': 'Generally safe area. Standard precautions recommended.'
        }
        return advice.get(risk_level, advice['low'])
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def hotspot_to_dict(hotspot, include_reports=False):
        """Convert hotspot to dictionary"""
        if not hotspot:
            return None
        
        result = {
            'hotspot_id': hotspot.hotspot_id,
            'cluster_label': hotspot.cluster_label,
            'centroid_latitude': float(hotspot.centroid_latitude) if hotspot.centroid_latitude else None,
            'centroid_longitude': float(hotspot.centroid_longitude) if hotspot.centroid_longitude else None,
            'radius_meters': float(hotspot.radius_meters) if hotspot.radius_meters else None,
            'district_id': hotspot.district_id,
            'sector_id': hotspot.sector_id,
            'cell_id': hotspot.cell_id,
            'report_count': hotspot.report_count,
            'unique_devices': hotspot.unique_devices,
            'avg_trust_score': float(hotspot.avg_trust_score) if hotspot.avg_trust_score else None,
            'trusted_report_count': hotspot.trusted_report_count,
            'suspicious_report_count': hotspot.suspicious_report_count,
            'false_report_count': hotspot.false_report_count,
            'police_verified_count': hotspot.police_verified_count,
            'earliest_incident_at': hotspot.earliest_incident_at.isoformat() if hotspot.earliest_incident_at else None,
            'latest_incident_at': hotspot.latest_incident_at.isoformat() if hotspot.latest_incident_at else None,
            'time_span_hours': hotspot.time_span_hours,
            'dominant_incident_type_id': hotspot.dominant_incident_type_id,
            'dominant_incident_pct': float(hotspot.dominant_incident_pct) if hotspot.dominant_incident_pct else None,
            'risk_level': hotspot.risk_level,
            'priority_score': float(hotspot.priority_score) if hotspot.priority_score else None,
            'is_active': hotspot.is_active,
            'status': hotspot.status,
            'is_assigned': hotspot.is_assigned,
            'assigned_to_officer_id': hotspot.assigned_to_officer_id,
            'assigned_to_unit': hotspot.assigned_to_unit,
            'assigned_at': hotspot.assigned_at.isoformat() if hotspot.assigned_at else None,
            'is_addressed': hotspot.is_addressed,
            'addressed_at': hotspot.addressed_at.isoformat() if hotspot.addressed_at else None,
            'resolution_notes': hotspot.resolution_notes,
            'detected_at': hotspot.detected_at.isoformat() if hotspot.detected_at else None,
            'updated_at': hotspot.updated_at.isoformat() if hotspot.updated_at else None
        }
        
        if include_reports:
            result['reports'] = [
                {
                    'report_id': hr.report_id,
                    'trust_weight': float(hr.trust_weight) if hr.trust_weight else None,
                    'distance_to_centroid_meters': float(hr.distance_to_centroid_meters) if hr.distance_to_centroid_meters else None,
                    'is_core_point': hr.is_core_point
                }
                for hr in hotspot.reports
            ]
        
        return result
    
    @staticmethod
    def clustering_run_to_dict(run):
        """Convert clustering run to dictionary"""
        if not run:
            return None
        return {
            'run_id': run.run_id,
            'district_id': run.district_id,
            'epsilon_meters': float(run.epsilon_meters) if run.epsilon_meters else None,
            'min_samples': run.min_samples,
            'trust_weight_enabled': run.trust_weight_enabled,
            'min_trust_score_threshold': float(run.min_trust_score_threshold) if run.min_trust_score_threshold else None,
            'total_reports_processed': run.total_reports_processed,
            'reports_after_filtering': run.reports_after_filtering,
            'clusters_found': run.clusters_found,
            'noise_points': run.noise_points,
            'avg_cluster_size': float(run.avg_cluster_size) if run.avg_cluster_size else None,
            'execution_time_seconds': float(run.execution_time_seconds) if run.execution_time_seconds else None,
            'status': run.status,
            'error_message': run.error_message,
            'started_at': run.started_at.isoformat() if run.started_at else None,
            'completed_at': run.completed_at.isoformat() if run.completed_at else None
        }
