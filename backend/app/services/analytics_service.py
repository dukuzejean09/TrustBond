"""
Analytics Service - Dashboard analytics and reporting
"""
from app import db
from app.models.analytics import DailyStatistic, IncidentTypeTrend
from app.models.incident_report import IncidentReport
from app.models.incident_taxonomy import IncidentType, IncidentCategory
from app.models.hotspots import Hotspot
from app.models.device import Device
from app.models.police_users import PoliceUser
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, or_, extract
import uuid


class AnalyticsService:
    """Service for analytics and statistics"""
    
    # ==================== DASHBOARD STATISTICS ====================
    @staticmethod
    def get_dashboard_stats(district_id=None, days=30):
        """Get comprehensive dashboard statistics"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        # Base report query
        report_query = IncidentReport.query.filter(
            IncidentReport.reported_at >= from_date
        )
        
        if district_id:
            report_query = report_query.filter_by(district_id=district_id)
        
        # Total reports
        total_reports = report_query.count()
        
        # Verified reports
        verified_reports = report_query.filter_by(police_verified=True).count()
        
        # Trust classification breakdown
        trusted = report_query.filter_by(trust_classification='Trusted').count()
        suspicious = report_query.filter_by(trust_classification='Suspicious').count()
        false_reports = report_query.filter_by(trust_classification='False').count()
        
        # Average trust score
        avg_trust = db.session.query(func.avg(IncidentReport.ml_trust_score))\
            .filter(IncidentReport.reported_at >= from_date)
        if district_id:
            avg_trust = avg_trust.filter(IncidentReport.district_id == district_id)
        avg_trust = avg_trust.scalar() or 0
        
        # Active hotspots
        hotspot_query = Hotspot.query.filter_by(is_active=True)
        if district_id:
            hotspot_query = hotspot_query.filter_by(district_id=district_id)
        active_hotspots = hotspot_query.count()
        
        # Critical hotspots
        critical_hotspots = hotspot_query.filter_by(risk_level='critical').count()
        
        # Unique devices
        unique_devices = db.session.query(func.count(func.distinct(IncidentReport.device_id)))\
            .filter(IncidentReport.reported_at >= from_date)
        if district_id:
            unique_devices = unique_devices.filter(IncidentReport.district_id == district_id)
        unique_devices = unique_devices.scalar() or 0
        
        # Response rate (verified / total)
        response_rate = (verified_reports / total_reports * 100) if total_reports > 0 else 0
        
        # Compare with previous period
        prev_from = from_date - timedelta(days=days)
        prev_reports = IncidentReport.query.filter(
            IncidentReport.reported_at >= prev_from,
            IncidentReport.reported_at < from_date
        )
        if district_id:
            prev_reports = prev_reports.filter_by(district_id=district_id)
        prev_total = prev_reports.count()
        
        change_pct = ((total_reports - prev_total) / prev_total * 100) if prev_total > 0 else 0
        
        return {
            'total_reports': total_reports,
            'verified_reports': verified_reports,
            'trusted_reports': trusted,
            'suspicious_reports': suspicious,
            'false_reports': false_reports,
            'avg_trust_score': round(float(avg_trust), 2),
            'active_hotspots': active_hotspots,
            'critical_hotspots': critical_hotspots,
            'unique_devices': unique_devices,
            'response_rate': round(response_rate, 2),
            'change_pct': round(change_pct, 2),
            'period_days': days
        }
    
    # ==================== TIME SERIES DATA ====================
    @staticmethod
    def get_reports_over_time(district_id=None, days=30, group_by='day'):
        """Get report counts over time"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        if group_by == 'hour':
            date_trunc = func.date_trunc('hour', IncidentReport.reported_at)
        elif group_by == 'week':
            date_trunc = func.date_trunc('week', IncidentReport.reported_at)
        else:  # day
            date_trunc = func.date_trunc('day', IncidentReport.reported_at)
        
        query = db.session.query(
            date_trunc.label('period'),
            func.count(IncidentReport.report_id).label('total'),
            func.count(func.nullif(IncidentReport.police_verified, False)).label('verified'),
            func.avg(IncidentReport.ml_trust_score).label('avg_trust')
        ).filter(IncidentReport.reported_at >= from_date)
        
        if district_id:
            query = query.filter(IncidentReport.district_id == district_id)
        
        results = query.group_by(date_trunc).order_by(date_trunc).all()
        
        return [{
            'period': r.period.isoformat() if r.period else None,
            'total': r.total,
            'verified': r.verified,
            'avg_trust': round(float(r.avg_trust or 0), 2)
        } for r in results]
    
    @staticmethod
    def get_hourly_distribution(district_id=None, days=30):
        """Get report distribution by hour of day"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.session.query(
            extract('hour', IncidentReport.reported_at).label('hour'),
            func.count(IncidentReport.report_id).label('count')
        ).filter(IncidentReport.reported_at >= from_date)
        
        if district_id:
            query = query.filter(IncidentReport.district_id == district_id)
        
        results = query.group_by(extract('hour', IncidentReport.reported_at))\
            .order_by('hour').all()
        
        # Fill in missing hours
        hourly = {i: 0 for i in range(24)}
        for r in results:
            hourly[int(r.hour)] = r.count
        
        return [{'hour': h, 'count': c} for h, c in hourly.items()]
    
    @staticmethod
    def get_daily_distribution(district_id=None, days=30):
        """Get report distribution by day of week"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.session.query(
            extract('dow', IncidentReport.reported_at).label('day'),
            func.count(IncidentReport.report_id).label('count')
        ).filter(IncidentReport.reported_at >= from_date)
        
        if district_id:
            query = query.filter(IncidentReport.district_id == district_id)
        
        results = query.group_by(extract('dow', IncidentReport.reported_at)).all()
        
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        daily = {i: 0 for i in range(7)}
        for r in results:
            daily[int(r.day)] = r.count
        
        return [{'day': day_names[d], 'day_num': d, 'count': c} for d, c in daily.items()]
    
    # ==================== INCIDENT TYPE ANALYSIS ====================
    @staticmethod
    def get_incident_type_breakdown(district_id=None, days=30, limit=10):
        """Get breakdown by incident type"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.session.query(
            IncidentReport.incident_type_id,
            IncidentType.type_name,
            IncidentCategory.category_name,
            func.count(IncidentReport.report_id).label('count'),
            func.avg(IncidentReport.ml_trust_score).label('avg_trust'),
            func.count(func.nullif(IncidentReport.police_verified, False)).label('verified')
        ).join(IncidentType, IncidentReport.incident_type_id == IncidentType.type_id)\
         .join(IncidentCategory, IncidentType.category_id == IncidentCategory.category_id)\
         .filter(IncidentReport.reported_at >= from_date)
        
        if district_id:
            query = query.filter(IncidentReport.district_id == district_id)
        
        results = query.group_by(
            IncidentReport.incident_type_id,
            IncidentType.type_name,
            IncidentCategory.category_name
        ).order_by(func.count(IncidentReport.report_id).desc())\
         .limit(limit).all()
        
        return [{
            'type_id': r.incident_type_id,
            'type_name': r.type_name,
            'category_name': r.category_name,
            'count': r.count,
            'avg_trust': round(float(r.avg_trust or 0), 2),
            'verified': r.verified
        } for r in results]
    
    @staticmethod
    def get_category_breakdown(district_id=None, days=30):
        """Get breakdown by incident category"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.session.query(
            IncidentCategory.category_id,
            IncidentCategory.category_name,
            func.count(IncidentReport.report_id).label('count')
        ).join(IncidentType, IncidentReport.incident_type_id == IncidentType.type_id)\
         .join(IncidentCategory, IncidentType.category_id == IncidentCategory.category_id)\
         .filter(IncidentReport.reported_at >= from_date)
        
        if district_id:
            query = query.filter(IncidentReport.district_id == district_id)
        
        results = query.group_by(
            IncidentCategory.category_id,
            IncidentCategory.category_name
        ).order_by(func.count(IncidentReport.report_id).desc()).all()
        
        return [{
            'category_id': r.category_id,
            'category_name': r.category_name,
            'count': r.count
        } for r in results]
    
    # ==================== GEOGRAPHIC ANALYSIS ====================
    @staticmethod
    def get_geographic_breakdown(level='district', parent_id=None, days=30):
        """Get breakdown by geographic level"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        if level == 'district':
            from app.models.geography import District
            query = db.session.query(
                IncidentReport.district_id,
                District.district_name,
                func.count(IncidentReport.report_id).label('count'),
                func.avg(IncidentReport.ml_trust_score).label('avg_trust')
            ).join(District, IncidentReport.district_id == District.district_id)\
             .filter(IncidentReport.reported_at >= from_date)\
             .group_by(IncidentReport.district_id, District.district_name)
             
        elif level == 'sector':
            from app.models.geography import Sector
            query = db.session.query(
                IncidentReport.sector_id,
                Sector.sector_name,
                func.count(IncidentReport.report_id).label('count'),
                func.avg(IncidentReport.ml_trust_score).label('avg_trust')
            ).join(Sector, IncidentReport.sector_id == Sector.sector_id)\
             .filter(IncidentReport.reported_at >= from_date)
            
            if parent_id:
                query = query.filter(IncidentReport.district_id == parent_id)
            
            query = query.group_by(IncidentReport.sector_id, Sector.sector_name)
        
        else:
            return []
        
        results = query.order_by(func.count(IncidentReport.report_id).desc()).all()
        
        return [{
            'id': r[0],
            'name': r[1],
            'count': r.count,
            'avg_trust': round(float(r.avg_trust or 0), 2)
        } for r in results]
    
    @staticmethod
    def get_heatmap_data(district_id=None, days=30):
        """Get data for heatmap visualization"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.session.query(
            IncidentReport.latitude,
            IncidentReport.longitude,
            IncidentReport.ml_trust_score
        ).filter(
            IncidentReport.reported_at >= from_date,
            IncidentReport.latitude.isnot(None),
            IncidentReport.longitude.isnot(None)
        )
        
        if district_id:
            query = query.filter(IncidentReport.district_id == district_id)
        
        results = query.all()
        
        return [{
            'lat': float(r.latitude),
            'lng': float(r.longitude),
            'weight': float(r.ml_trust_score or 50) / 100
        } for r in results]
    
    # ==================== TRUST SCORE ANALYSIS ====================
    @staticmethod
    def get_trust_score_distribution(district_id=None, days=30):
        """Get distribution of trust scores"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        # Define buckets
        buckets = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
        result = []
        
        for low, high in buckets:
            query = IncidentReport.query.filter(
                IncidentReport.reported_at >= from_date,
                IncidentReport.ml_trust_score >= low,
                IncidentReport.ml_trust_score < high if high < 100 else IncidentReport.ml_trust_score <= high
            )
            
            if district_id:
                query = query.filter_by(district_id=district_id)
            
            count = query.count()
            result.append({
                'range': f'{low}-{high}',
                'low': low,
                'high': high,
                'count': count
            })
        
        return result
    
    @staticmethod
    def get_verification_stats(district_id=None, days=30):
        """Get verification statistics"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        query = IncidentReport.query.filter(
            IncidentReport.reported_at >= from_date
        )
        
        if district_id:
            query = query.filter_by(district_id=district_id)
        
        total = query.count()
        verified = query.filter_by(police_verified=True).count()
        auto_rejected = query.filter_by(is_auto_rejected=True).count()
        pending = total - verified - auto_rejected
        
        # Verification outcomes for verified reports
        true_positive = query.filter(
            IncidentReport.police_verified == True,
            IncidentReport.trust_classification == 'Trusted'
        ).count()
        
        false_positive = query.filter(
            IncidentReport.police_verified == True,
            IncidentReport.verification_result == 'false'
        ).count()
        
        return {
            'total': total,
            'verified': verified,
            'auto_rejected': auto_rejected,
            'pending': pending,
            'verification_rate': round(verified / total * 100, 2) if total > 0 else 0,
            'true_positive': true_positive,
            'false_positive': false_positive,
            'accuracy': round(true_positive / verified * 100, 2) if verified > 0 else 0
        }
    
    # ==================== DAILY STATISTICS ====================
    @staticmethod
    def generate_daily_stats(stat_date=None, district_id=None):
        """Generate daily statistics record"""
        if stat_date is None:
            stat_date = date.today() - timedelta(days=1)
        
        start = datetime.combine(stat_date, datetime.min.time())
        end = datetime.combine(stat_date, datetime.max.time())
        
        query = IncidentReport.query.filter(
            IncidentReport.reported_at >= start,
            IncidentReport.reported_at <= end
        )
        
        if district_id:
            query = query.filter_by(district_id=district_id)
        
        reports = query.all()
        
        if not reports:
            return None
        
        # Calculate statistics
        total = len(reports)
        verified = sum(1 for r in reports if r.police_verified)
        trusted = sum(1 for r in reports if r.trust_classification == 'Trusted')
        suspicious = sum(1 for r in reports if r.trust_classification == 'Suspicious')
        false = sum(1 for r in reports if r.trust_classification == 'False')
        auto_rejected = sum(1 for r in reports if r.is_auto_rejected)
        
        trust_scores = [r.ml_trust_score for r in reports if r.ml_trust_score]
        avg_trust = sum(trust_scores) / len(trust_scores) if trust_scores else 0
        
        unique_devices = len(set(r.device_id for r in reports))
        
        # Hotspot count
        hotspot_count = Hotspot.query.filter(
            Hotspot.detected_at >= start,
            Hotspot.detected_at <= end
        )
        if district_id:
            hotspot_count = hotspot_count.filter_by(district_id=district_id)
        hotspot_count = hotspot_count.count()
        
        stat = DailyStatistic(
            stat_id=str(uuid.uuid4()),
            stat_date=stat_date,
            district_id=district_id,
            total_reports=total,
            verified_reports=verified,
            trusted_reports=trusted,
            suspicious_reports=suspicious,
            false_reports=false,
            auto_rejected_reports=auto_rejected,
            avg_trust_score=avg_trust,
            unique_devices=unique_devices,
            new_hotspots=hotspot_count
        )
        
        db.session.add(stat)
        db.session.commit()
        return stat
    
    @staticmethod
    def get_daily_stats(start_date, end_date, district_id=None):
        """Get daily statistics for a date range"""
        query = DailyStatistic.query.filter(
            DailyStatistic.stat_date >= start_date,
            DailyStatistic.stat_date <= end_date
        )
        
        if district_id:
            query = query.filter_by(district_id=district_id)
        
        return query.order_by(DailyStatistic.stat_date).all()
    
    # ==================== TREND ANALYSIS ====================
    @staticmethod
    def calculate_incident_trends(days=30):
        """Calculate incident type trends"""
        from_date = datetime.utcnow() - timedelta(days=days)
        prev_from = from_date - timedelta(days=days)
        
        # Current period
        current = db.session.query(
            IncidentReport.incident_type_id,
            func.count(IncidentReport.report_id).label('count')
        ).filter(IncidentReport.reported_at >= from_date)\
         .group_by(IncidentReport.incident_type_id).all()
        
        # Previous period
        previous = db.session.query(
            IncidentReport.incident_type_id,
            func.count(IncidentReport.report_id).label('count')
        ).filter(
            IncidentReport.reported_at >= prev_from,
            IncidentReport.reported_at < from_date
        ).group_by(IncidentReport.incident_type_id).all()
        
        prev_dict = {r.incident_type_id: r.count for r in previous}
        
        trends = []
        for r in current:
            prev_count = prev_dict.get(r.incident_type_id, 0)
            change = r.count - prev_count
            change_pct = (change / prev_count * 100) if prev_count > 0 else 100 if r.count > 0 else 0
            
            if change > 0:
                direction = 'increasing'
            elif change < 0:
                direction = 'decreasing'
            else:
                direction = 'stable'
            
            trend = IncidentTypeTrend(
                trend_id=str(uuid.uuid4()),
                incident_type_id=r.incident_type_id,
                period_start=from_date.date(),
                period_end=datetime.utcnow().date(),
                report_count=r.count,
                previous_count=prev_count,
                change_count=change,
                change_pct=change_pct,
                trend_direction=direction
            )
            trends.append(trend)
        
        # Save trends
        for trend in trends:
            db.session.add(trend)
        db.session.commit()
        
        return trends
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def daily_stat_to_dict(stat):
        """Convert daily statistic to dictionary"""
        if not stat:
            return None
        return {
            'stat_id': stat.stat_id,
            'stat_date': stat.stat_date.isoformat() if stat.stat_date else None,
            'district_id': stat.district_id,
            'total_reports': stat.total_reports,
            'verified_reports': stat.verified_reports,
            'trusted_reports': stat.trusted_reports,
            'suspicious_reports': stat.suspicious_reports,
            'false_reports': stat.false_reports,
            'auto_rejected_reports': stat.auto_rejected_reports,
            'avg_trust_score': float(stat.avg_trust_score) if stat.avg_trust_score else None,
            'unique_devices': stat.unique_devices,
            'new_hotspots': stat.new_hotspots
        }
    
    @staticmethod
    def trend_to_dict(trend):
        """Convert trend to dictionary"""
        if not trend:
            return None
        return {
            'trend_id': trend.trend_id,
            'incident_type_id': trend.incident_type_id,
            'period_start': trend.period_start.isoformat() if trend.period_start else None,
            'period_end': trend.period_end.isoformat() if trend.period_end else None,
            'report_count': trend.report_count,
            'previous_count': trend.previous_count,
            'change_count': trend.change_count,
            'change_pct': float(trend.change_pct) if trend.change_pct else None,
            'trend_direction': trend.trend_direction
        }
