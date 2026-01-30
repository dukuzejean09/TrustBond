"""
Device Service - Manages anonymous device profiles and trust history
"""
from app import db
from app.models.device import Device, DeviceTrustHistory
from datetime import datetime
import uuid
import hashlib


class DeviceService:
    """Service for managing anonymous reporter devices"""
    
    @staticmethod
    def get_or_create_device(device_fingerprint, platform, app_version=None, os_version=None, device_language='en'):
        """Get existing device or create new one"""
        device = Device.query.filter_by(device_fingerprint=device_fingerprint).first()
        
        if not device:
            device = Device(
                device_id=str(uuid.uuid4()),
                device_fingerprint=device_fingerprint,
                platform=platform,
                app_version=app_version,
                os_version=os_version,
                device_language=device_language,
                current_trust_score=50.00,
                registered_at=datetime.utcnow()
            )
            db.session.add(device)
            db.session.commit()
        else:
            # Update last active
            device.last_active_at = datetime.utcnow()
            if app_version:
                device.app_version = app_version
            if os_version:
                device.os_version = os_version
            db.session.commit()
        
        return device
    
    @staticmethod
    def generate_fingerprint(hardware_data):
        """Generate SHA-256 hash from hardware characteristics"""
        fingerprint_string = '|'.join([
            str(hardware_data.get('device_id', '')),
            str(hardware_data.get('model', '')),
            str(hardware_data.get('manufacturer', '')),
            str(hardware_data.get('brand', '')),
            str(hardware_data.get('android_id', '')),
        ])
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    @staticmethod
    def get_device_by_id(device_id):
        """Get device by ID"""
        return Device.query.get(device_id)
    
    @staticmethod
    def get_device_by_fingerprint(fingerprint):
        """Get device by fingerprint hash"""
        return Device.query.filter_by(device_fingerprint=fingerprint).first()
    
    @staticmethod
    def update_trust_score(device_id, score_change, reason):
        """Update device trust score and log history"""
        device = Device.query.get(device_id)
        if not device:
            return None
        
        old_score = float(device.current_trust_score or 50)
        new_score = max(0, min(100, old_score + score_change))
        
        # Update device
        device.current_trust_score = new_score
        device.last_active_at = datetime.utcnow()
        
        # Log history
        history = DeviceTrustHistory(
            device_id=device_id,
            trust_score=new_score,
            total_reports=device.total_reports,
            trusted_reports=device.trusted_reports,
            suspicious_reports=device.suspicious_reports,
            false_reports=device.false_reports,
            score_change=score_change,
            change_reason=reason
        )
        db.session.add(history)
        db.session.commit()
        
        return device
    
    @staticmethod
    def increment_report_count(device_id, classification=None):
        """Increment report count and update classification counts"""
        device = Device.query.get(device_id)
        if not device:
            return None
        
        device.total_reports = (device.total_reports or 0) + 1
        device.last_report_at = datetime.utcnow()
        
        if classification == 'Trusted':
            device.trusted_reports = (device.trusted_reports or 0) + 1
        elif classification == 'Suspicious':
            device.suspicious_reports = (device.suspicious_reports or 0) + 1
        elif classification == 'False':
            device.false_reports = (device.false_reports or 0) + 1
        
        db.session.commit()
        return device
    
    @staticmethod
    def block_device(device_id, reason, blocked_by_user_id):
        """Block a device from reporting"""
        device = Device.query.get(device_id)
        if not device:
            return None
        
        device.is_blocked = True
        device.block_reason = reason
        device.blocked_at = datetime.utcnow()
        device.blocked_by = blocked_by_user_id
        
        db.session.commit()
        return device
    
    @staticmethod
    def unblock_device(device_id):
        """Unblock a device"""
        device = Device.query.get(device_id)
        if not device:
            return None
        
        device.is_blocked = False
        device.block_reason = None
        device.blocked_at = None
        device.blocked_by = None
        
        db.session.commit()
        return device
    
    @staticmethod
    def get_device_trust_history(device_id, limit=50):
        """Get trust score history for a device"""
        return DeviceTrustHistory.query.filter_by(device_id=device_id)\
            .order_by(DeviceTrustHistory.calculated_at.desc())\
            .limit(limit).all()
    
    @staticmethod
    def get_blocked_devices(page=1, per_page=20):
        """Get list of blocked devices"""
        return Device.query.filter_by(is_blocked=True)\
            .order_by(Device.blocked_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_device_statistics():
        """Get overall device statistics"""
        total = Device.query.count()
        blocked = Device.query.filter_by(is_blocked=True).count()
        active_7_days = Device.query.filter(
            Device.last_active_at >= datetime.utcnow() - timedelta(days=7)
        ).count() if 'timedelta' in dir() else 0
        
        avg_trust = db.session.query(db.func.avg(Device.current_trust_score)).scalar() or 50
        
        return {
            'total_devices': total,
            'blocked_devices': blocked,
            'active_7_days': active_7_days,
            'average_trust_score': float(avg_trust)
        }
    
    @staticmethod
    def update_push_token(device_id, push_token_encrypted):
        """Update encrypted push notification token"""
        device = Device.query.get(device_id)
        if device:
            device.push_token_encrypted = push_token_encrypted
            db.session.commit()
        return device
    
    @staticmethod
    def to_dict(device):
        """Convert device to dictionary"""
        if not device:
            return None
        return {
            'device_id': device.device_id,
            'platform': device.platform,
            'app_version': device.app_version,
            'os_version': device.os_version,
            'device_language': device.device_language,
            'current_trust_score': float(device.current_trust_score) if device.current_trust_score else 50,
            'total_reports': device.total_reports or 0,
            'trusted_reports': device.trusted_reports or 0,
            'suspicious_reports': device.suspicious_reports or 0,
            'false_reports': device.false_reports or 0,
            'is_blocked': device.is_blocked or False,
            'registered_at': device.registered_at.isoformat() if device.registered_at else None,
            'last_active_at': device.last_active_at.isoformat() if device.last_active_at else None,
            'last_report_at': device.last_report_at.isoformat() if device.last_report_at else None
        }
