"""
Incident Service - Manages incident reports and evidence
"""
from app import db
from app.models.incident_report import IncidentReport
from app.models.evidence import ReportEvidence
from app.models.incident_taxonomy import IncidentCategory, IncidentType
from app.services.device_service import DeviceService
from app.services.geography_service import GeographyService
from datetime import datetime
import uuid
import hashlib
import random
import string


class IncidentService:
    """Service for managing incident reports"""
    
    @staticmethod
    def generate_tracking_code():
        """Generate unique tracking code for anonymous reports"""
        timestamp = datetime.utcnow().strftime('%y%m%d')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"TB-{timestamp}-{random_part}"
    
    @staticmethod
    def create_report(data, device_fingerprint):
        """Create a new incident report"""
        # Get or create device
        device = DeviceService.get_or_create_device(
            device_fingerprint=device_fingerprint,
            platform=data.get('platform', 'android'),
            app_version=data.get('app_version'),
            os_version=data.get('os_version')
        )
        
        if device.is_blocked:
            raise ValueError('Device is blocked from reporting')
        
        # Resolve location to administrative units
        location = GeographyService.resolve_location(
            float(data['latitude']),
            float(data['longitude'])
        )
        
        report_id = str(uuid.uuid4())
        
        report = IncidentReport(
            report_id=report_id,
            device_id=device.device_id,
            incident_type_id=data['incident_type_id'],
            title=data.get('title'),
            description=data['description'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            location_accuracy_meters=data.get('location_accuracy_meters'),
            altitude_meters=data.get('altitude_meters'),
            location_source=data.get('location_source', 'gps'),
            district_id=location.get('district_id'),
            sector_id=location.get('sector_id'),
            cell_id=location.get('cell_id'),
            village_id=location.get('village_id'),
            address_description=data.get('address_description'),
            incident_occurred_at=data.get('incident_occurred_at', datetime.utcnow()),
            incident_time_approximate=data.get('incident_time_approximate', False),
            
            # Motion sensor data
            accelerometer_data=data.get('accelerometer_data'),
            gyroscope_data=data.get('gyroscope_data'),
            magnetometer_data=data.get('magnetometer_data'),
            device_motion_score=data.get('device_motion_score'),
            device_orientation=data.get('device_orientation'),
            battery_level=data.get('battery_level'),
            network_type=data.get('network_type'),
            
            # Metadata
            app_version=data.get('app_version'),
            submission_ip_hash=data.get('submission_ip_hash'),
            
            # Initial status
            report_status='submitted',
            processing_stage='received',
            trust_classification='Pending'
        )
        
        db.session.add(report)
        DeviceService.increment_report_count(device.device_id)
        db.session.commit()
        
        return report
    
    @staticmethod
    def get_report_by_id(report_id):
        """Get report by ID"""
        return IncidentReport.query.get(report_id)
    
    @staticmethod
    def get_reports(filters=None, page=1, per_page=20):
        """Get reports with optional filters"""
        query = IncidentReport.query
        
        if filters:
            if filters.get('district_id'):
                query = query.filter_by(district_id=filters['district_id'])
            if filters.get('sector_id'):
                query = query.filter_by(sector_id=filters['sector_id'])
            if filters.get('incident_type_id'):
                query = query.filter_by(incident_type_id=filters['incident_type_id'])
            if filters.get('trust_classification'):
                query = query.filter_by(trust_classification=filters['trust_classification'])
            if filters.get('report_status'):
                query = query.filter_by(report_status=filters['report_status'])
            if filters.get('police_verification_status'):
                query = query.filter_by(police_verification_status=filters['police_verification_status'])
            if filters.get('start_date'):
                query = query.filter(IncidentReport.reported_at >= filters['start_date'])
            if filters.get('end_date'):
                query = query.filter(IncidentReport.reported_at <= filters['end_date'])
            if filters.get('min_trust_score'):
                query = query.filter(IncidentReport.ml_trust_score >= filters['min_trust_score'])
        
        return query.order_by(IncidentReport.reported_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def update_report_status(report_id, status, user_id=None):
        """Update report workflow status"""
        report = IncidentReport.query.get(report_id)
        if not report:
            return None
        
        report.report_status = status
        report.updated_at = datetime.utcnow()
        
        if status == 'resolved':
            report.resolved_at = datetime.utcnow()
        
        db.session.commit()
        return report
    
    @staticmethod
    def verify_report(report_id, verification_status, notes, verified_by_user_id, priority=None):
        """Police verification of report"""
        report = IncidentReport.query.get(report_id)
        if not report:
            return None
        
        report.police_verified = True
        report.police_verified_at = datetime.utcnow()
        report.police_verified_by = verified_by_user_id
        report.police_verification_status = verification_status
        report.police_verification_notes = notes
        
        if priority:
            report.police_priority = priority
        
        # Update device trust score based on verification
        if verification_status == 'confirmed':
            DeviceService.update_trust_score(report.device_id, 10, 'report_confirmed')
            DeviceService.increment_report_count(report.device_id, 'Trusted')
        elif verification_status == 'false':
            DeviceService.update_trust_score(report.device_id, -15, 'report_rejected')
            DeviceService.increment_report_count(report.device_id, 'False')
        
        db.session.commit()
        return report
    
    @staticmethod
    def assign_report(report_id, officer_id, unit=None):
        """Assign report to an officer"""
        report = IncidentReport.query.get(report_id)
        if not report:
            return None
        
        report.assigned_officer_id = officer_id
        report.assigned_unit = unit
        report.assigned_at = datetime.utcnow()
        report.report_status = 'investigating'
        
        db.session.commit()
        return report
    
    @staticmethod
    def resolve_report(report_id, resolution_type, notes, resolved_by_user_id):
        """Resolve a report"""
        report = IncidentReport.query.get(report_id)
        if not report:
            return None
        
        report.resolved_at = datetime.utcnow()
        report.resolution_type = resolution_type
        report.resolution_notes = notes
        report.report_status = 'resolved'
        report.processing_stage = 'completed'
        
        db.session.commit()
        return report
    
    @staticmethod
    def mark_duplicate(report_id, original_report_id, confidence):
        """Mark report as duplicate"""
        report = IncidentReport.query.get(report_id)
        if not report:
            return None
        
        report.is_duplicate = True
        report.duplicate_of_report_id = original_report_id
        report.duplicate_confidence = confidence
        report.report_status = 'rejected'
        report.resolution_type = 'duplicate'
        
        db.session.commit()
        return report
    
    # ==================== EVIDENCE ====================
    @staticmethod
    def add_evidence(report_id, evidence_data):
        """Add evidence file to report"""
        report = IncidentReport.query.get(report_id)
        if not report:
            return None
        
        evidence = ReportEvidence(
            evidence_id=str(uuid.uuid4()),
            report_id=report_id,
            evidence_type=evidence_data['evidence_type'],
            file_name=evidence_data['file_name'],
            file_path=evidence_data['file_path'],
            file_size_bytes=evidence_data.get('file_size_bytes'),
            mime_type=evidence_data.get('mime_type'),
            duration_seconds=evidence_data.get('duration_seconds'),
            width_pixels=evidence_data.get('width_pixels'),
            height_pixels=evidence_data.get('height_pixels'),
            file_hash_sha256=evidence_data.get('file_hash_sha256'),
            file_hash_perceptual=evidence_data.get('file_hash_perceptual'),
            captured_at=evidence_data.get('captured_at'),
            capture_latitude=evidence_data.get('capture_latitude'),
            capture_longitude=evidence_data.get('capture_longitude'),
            camera_metadata=evidence_data.get('camera_metadata'),
            blur_score=evidence_data.get('blur_score'),
            brightness_score=evidence_data.get('brightness_score')
        )
        
        db.session.add(evidence)
        
        # Update evidence counts
        if evidence_data['evidence_type'] == 'photo':
            report.photo_count = (report.photo_count or 0) + 1
        elif evidence_data['evidence_type'] == 'video':
            report.video_count = (report.video_count or 0) + 1
        elif evidence_data['evidence_type'] == 'audio':
            report.audio_count = (report.audio_count or 0) + 1
        
        report.total_evidence_size_kb = (report.total_evidence_size_kb or 0) + \
            (evidence_data.get('file_size_bytes', 0) // 1024)
        
        db.session.commit()
        return evidence
    
    @staticmethod
    def get_report_evidence(report_id):
        """Get all evidence for a report"""
        return ReportEvidence.query.filter_by(report_id=report_id, is_deleted=False).all()
    
    @staticmethod
    def moderate_evidence(evidence_id, status, has_inappropriate, flags, moderated_by):
        """Moderate evidence content"""
        evidence = ReportEvidence.query.get(evidence_id)
        if not evidence:
            return None
        
        evidence.content_moderation_status = status
        evidence.has_inappropriate_content = has_inappropriate
        evidence.moderation_flags = flags
        evidence.moderated_at = datetime.utcnow()
        evidence.moderated_by = moderated_by
        
        db.session.commit()
        return evidence
    
    # ==================== CATEGORIES & TYPES ====================
    @staticmethod
    def get_all_categories():
        """Get all incident categories"""
        return IncidentCategory.query.filter_by(is_active=True)\
            .order_by(IncidentCategory.display_order).all()
    
    @staticmethod
    def get_category_by_id(category_id):
        """Get category by ID"""
        return IncidentCategory.query.get(category_id)
    
    @staticmethod
    def create_category(data):
        """Create incident category"""
        category = IncidentCategory(
            category_id=data.get('category_id'),
            category_name=data['category_name'],
            description=data.get('description'),
            icon_name=data.get('icon_name'),
            color_hex=data.get('color_hex'),
            display_order=data.get('display_order'),
            is_active=True,
            requires_evidence=data.get('requires_evidence', False)
        )
        db.session.add(category)
        db.session.commit()
        return category
    
    @staticmethod
    def get_types_by_category(category_id):
        """Get incident types for a category"""
        return IncidentType.query.filter_by(category_id=category_id, is_active=True)\
            .order_by(IncidentType.display_order).all()
    
    @staticmethod
    def get_all_types():
        """Get all incident types"""
        return IncidentType.query.filter_by(is_active=True)\
            .order_by(IncidentType.category_id, IncidentType.display_order).all()
    
    @staticmethod
    def get_type_by_id(type_id):
        """Get incident type by ID"""
        return IncidentType.query.get(type_id)
    
    @staticmethod
    def create_type(data):
        """Create incident type"""
        inc_type = IncidentType(
            type_id=data.get('type_id'),
            category_id=data['category_id'],
            type_name=data['type_name'],
            description=data.get('description'),
            severity_level=data.get('severity_level'),
            response_priority=data.get('response_priority', 'normal'),
            requires_photo=data.get('requires_photo', False),
            requires_video=data.get('requires_video', False),
            min_description_length=data.get('min_description_length', 20),
            icon_name=data.get('icon_name'),
            display_order=data.get('display_order'),
            is_active=True
        )
        db.session.add(inc_type)
        db.session.commit()
        return inc_type
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def report_to_dict(report, include_evidence=False, include_device=False):
        """Convert report to dictionary"""
        if not report:
            return None
        
        result = {
            'report_id': report.report_id,
            'device_id': report.device_id,
            'incident_type_id': report.incident_type_id,
            'title': report.title,
            'description': report.description,
            'latitude': float(report.latitude) if report.latitude else None,
            'longitude': float(report.longitude) if report.longitude else None,
            'location_accuracy_meters': float(report.location_accuracy_meters) if report.location_accuracy_meters else None,
            'location_source': report.location_source,
            'district_id': report.district_id,
            'sector_id': report.sector_id,
            'cell_id': report.cell_id,
            'village_id': report.village_id,
            'address_description': report.address_description,
            'reported_at': report.reported_at.isoformat() if report.reported_at else None,
            'incident_occurred_at': report.incident_occurred_at.isoformat() if report.incident_occurred_at else None,
            'incident_time_approximate': report.incident_time_approximate,
            'photo_count': report.photo_count or 0,
            'video_count': report.video_count or 0,
            'audio_count': report.audio_count or 0,
            'total_evidence_size_kb': report.total_evidence_size_kb or 0,
            'device_motion_score': float(report.device_motion_score) if report.device_motion_score else None,
            'rule_check_status': report.rule_check_status,
            'rules_passed': report.rules_passed,
            'rules_failed': report.rules_failed,
            'ml_trust_score': float(report.ml_trust_score) if report.ml_trust_score else None,
            'ml_confidence': float(report.ml_confidence) if report.ml_confidence else None,
            'trust_classification': report.trust_classification,
            'classification_reason': report.classification_reason,
            'police_verified': report.police_verified,
            'police_verified_at': report.police_verified_at.isoformat() if report.police_verified_at else None,
            'police_verification_status': report.police_verification_status,
            'police_verification_notes': report.police_verification_notes,
            'police_priority': report.police_priority,
            'report_status': report.report_status,
            'processing_stage': report.processing_stage,
            'is_duplicate': report.is_duplicate,
            'assigned_officer_id': report.assigned_officer_id,
            'assigned_unit': report.assigned_unit,
            'assigned_at': report.assigned_at.isoformat() if report.assigned_at else None,
            'resolved_at': report.resolved_at.isoformat() if report.resolved_at else None,
            'resolution_type': report.resolution_type,
            'resolution_notes': report.resolution_notes,
            'hotspot_id': report.hotspot_id,
            'app_version': report.app_version,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'updated_at': report.updated_at.isoformat() if report.updated_at else None
        }
        
        if include_evidence:
            result['evidence'] = [IncidentService.evidence_to_dict(e) for e in report.evidence_files]
        
        if include_device:
            result['device'] = DeviceService.to_dict(report.device)
        
        return result
    
    @staticmethod
    def evidence_to_dict(evidence):
        """Convert evidence to dictionary"""
        if not evidence:
            return None
        return {
            'evidence_id': evidence.evidence_id,
            'report_id': evidence.report_id,
            'evidence_type': evidence.evidence_type,
            'file_name': evidence.file_name,
            'file_path': evidence.file_path,
            'file_size_bytes': evidence.file_size_bytes,
            'mime_type': evidence.mime_type,
            'duration_seconds': evidence.duration_seconds,
            'width_pixels': evidence.width_pixels,
            'height_pixels': evidence.height_pixels,
            'captured_at': evidence.captured_at.isoformat() if evidence.captured_at else None,
            'blur_score': float(evidence.blur_score) if evidence.blur_score else None,
            'brightness_score': float(evidence.brightness_score) if evidence.brightness_score else None,
            'is_low_quality': evidence.is_low_quality,
            'content_moderation_status': evidence.content_moderation_status,
            'uploaded_at': evidence.uploaded_at.isoformat() if evidence.uploaded_at else None
        }
    
    @staticmethod
    def category_to_dict(category, include_types=False):
        """Convert category to dictionary"""
        if not category:
            return None
        result = {
            'category_id': category.category_id,
            'category_name': category.category_name,
            'description': category.description,
            'icon_name': category.icon_name,
            'color_hex': category.color_hex,
            'display_order': category.display_order,
            'requires_evidence': category.requires_evidence,
            'is_active': category.is_active
        }
        if include_types:
            result['types'] = [IncidentService.type_to_dict(t) for t in category.types]
        return result
    
    @staticmethod
    def type_to_dict(inc_type):
        """Convert incident type to dictionary"""
        if not inc_type:
            return None
        return {
            'type_id': inc_type.type_id,
            'category_id': inc_type.category_id,
            'type_name': inc_type.type_name,
            'description': inc_type.description,
            'severity_level': inc_type.severity_level,
            'response_priority': inc_type.response_priority,
            'requires_photo': inc_type.requires_photo,
            'requires_video': inc_type.requires_video,
            'min_description_length': inc_type.min_description_length,
            'icon_name': inc_type.icon_name,
            'display_order': inc_type.display_order,
            'is_active': inc_type.is_active
        }
