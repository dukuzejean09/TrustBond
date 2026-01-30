"""
Settings Service - System settings management
"""
from app import db
from app.models.system_settings import SystemSetting
from datetime import datetime
import json


class SettingsService:
    """Service for system settings management"""
    
    # Default settings
    DEFAULTS = {
        # Trust scoring settings
        'trust_score_min_threshold': {'value': 30, 'type': 'integer', 'category': 'trust_scoring'},
        'trust_score_suspicious_threshold': {'value': 50, 'type': 'integer', 'category': 'trust_scoring'},
        'trust_score_trusted_threshold': {'value': 70, 'type': 'integer', 'category': 'trust_scoring'},
        'auto_reject_threshold': {'value': 20, 'type': 'integer', 'category': 'trust_scoring'},
        
        # Hotspot detection settings
        'hotspot_dbscan_epsilon': {'value': 500, 'type': 'integer', 'category': 'hotspot_detection'},
        'hotspot_dbscan_min_samples': {'value': 3, 'type': 'integer', 'category': 'hotspot_detection'},
        'hotspot_min_reports': {'value': 3, 'type': 'integer', 'category': 'hotspot_detection'},
        'hotspot_auto_detect_enabled': {'value': True, 'type': 'boolean', 'category': 'hotspot_detection'},
        'hotspot_detect_interval_hours': {'value': 6, 'type': 'integer', 'category': 'hotspot_detection'},
        
        # Verification settings
        'verification_location_enabled': {'value': True, 'type': 'boolean', 'category': 'verification'},
        'verification_motion_enabled': {'value': True, 'type': 'boolean', 'category': 'verification'},
        'verification_duplicate_enabled': {'value': True, 'type': 'boolean', 'category': 'verification'},
        'verification_spam_enabled': {'value': True, 'type': 'boolean', 'category': 'verification'},
        'duplicate_distance_meters': {'value': 100, 'type': 'integer', 'category': 'verification'},
        'duplicate_time_minutes': {'value': 30, 'type': 'integer', 'category': 'verification'},
        'spam_check_hours': {'value': 24, 'type': 'integer', 'category': 'verification'},
        'spam_max_reports': {'value': 10, 'type': 'integer', 'category': 'verification'},
        
        # ML settings
        'ml_model_enabled': {'value': True, 'type': 'boolean', 'category': 'ml'},
        'ml_retrain_interval_days': {'value': 7, 'type': 'integer', 'category': 'ml'},
        'ml_min_training_samples': {'value': 100, 'type': 'integer', 'category': 'ml'},
        
        # Notification settings
        'notify_critical_hotspot': {'value': True, 'type': 'boolean', 'category': 'notifications'},
        'notify_high_priority_report': {'value': True, 'type': 'boolean', 'category': 'notifications'},
        'notification_cleanup_days': {'value': 90, 'type': 'integer', 'category': 'notifications'},
        
        # API settings
        'api_rate_limit_enabled': {'value': True, 'type': 'boolean', 'category': 'api'},
        'api_default_rate_limit_minute': {'value': 60, 'type': 'integer', 'category': 'api'},
        'api_default_rate_limit_day': {'value': 10000, 'type': 'integer', 'category': 'api'},
        'api_log_retention_days': {'value': 90, 'type': 'integer', 'category': 'api'},
        
        # System settings
        'system_maintenance_mode': {'value': False, 'type': 'boolean', 'category': 'system'},
        'audit_log_retention_days': {'value': 365, 'type': 'integer', 'category': 'system'},
        'session_timeout_hours': {'value': 24, 'type': 'integer', 'category': 'system'},
        'max_login_attempts': {'value': 5, 'type': 'integer', 'category': 'system'},
        'lockout_duration_minutes': {'value': 30, 'type': 'integer', 'category': 'system'},
        
        # Public map settings
        'public_map_enabled': {'value': True, 'type': 'boolean', 'category': 'public_map'},
        'public_map_min_reports': {'value': 3, 'type': 'integer', 'category': 'public_map'},
        'public_map_refresh_minutes': {'value': 30, 'type': 'integer', 'category': 'public_map'}
    }
    
    # ==================== SETTING RETRIEVAL ====================
    @staticmethod
    def get_setting(key, default=None):
        """Get a setting value by key"""
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        
        if setting:
            return SettingsService._convert_value(setting.setting_value, setting.value_type)
        
        # Check defaults
        if key in SettingsService.DEFAULTS:
            return SettingsService.DEFAULTS[key]['value']
        
        return default
    
    @staticmethod
    def get_all_settings(category=None):
        """Get all settings, optionally filtered by category"""
        query = SystemSetting.query
        
        if category:
            query = query.filter_by(category=category)
        
        settings = query.order_by(SystemSetting.category, SystemSetting.setting_key).all()
        
        # Build result with defaults
        result = {}
        
        # Start with defaults
        for key, config in SettingsService.DEFAULTS.items():
            if category is None or config['category'] == category:
                result[key] = {
                    'value': config['value'],
                    'type': config['type'],
                    'category': config['category'],
                    'is_default': True
                }
        
        # Override with stored values
        for setting in settings:
            result[setting.setting_key] = {
                'value': SettingsService._convert_value(setting.setting_value, setting.value_type),
                'type': setting.value_type,
                'category': setting.category,
                'description': setting.description,
                'is_encrypted': setting.is_encrypted,
                'is_default': False,
                'updated_at': setting.updated_at.isoformat() if setting.updated_at else None,
                'updated_by': setting.updated_by
            }
        
        return result
    
    @staticmethod
    def get_settings_by_category(category):
        """Get settings for a specific category"""
        return SettingsService.get_all_settings(category=category)
    
    @staticmethod
    def get_categories():
        """Get list of setting categories"""
        categories = db.session.query(SystemSetting.category.distinct()).all()
        db_categories = [c[0] for c in categories if c[0]]
        
        # Include default categories
        default_categories = set(c['category'] for c in SettingsService.DEFAULTS.values())
        
        return list(set(db_categories) | default_categories)
    
    # ==================== SETTING MANAGEMENT ====================
    @staticmethod
    def set_setting(key, value, description=None, updated_by_user_id=None):
        """Set a setting value"""
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        
        # Determine type and category from defaults
        default_config = SettingsService.DEFAULTS.get(key, {})
        value_type = default_config.get('type', SettingsService._detect_type(value))
        category = default_config.get('category', 'custom')
        
        # Convert value to string for storage
        str_value = SettingsService._value_to_string(value, value_type)
        
        if setting:
            setting.setting_value = str_value
            setting.value_type = value_type
            setting.description = description or setting.description
            setting.updated_at = datetime.utcnow()
            setting.updated_by = updated_by_user_id
        else:
            setting = SystemSetting(
                setting_key=key,
                setting_value=str_value,
                value_type=value_type,
                category=category,
                description=description,
                updated_by=updated_by_user_id
            )
            db.session.add(setting)
        
        db.session.commit()
        return setting
    
    @staticmethod
    def set_multiple_settings(settings_dict, updated_by_user_id=None):
        """Set multiple settings at once"""
        results = []
        for key, value in settings_dict.items():
            setting = SettingsService.set_setting(key, value, updated_by_user_id=updated_by_user_id)
            results.append(setting)
        return results
    
    @staticmethod
    def delete_setting(key):
        """Delete a setting (revert to default)"""
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        if setting:
            db.session.delete(setting)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def reset_to_defaults(category=None):
        """Reset settings to defaults"""
        query = SystemSetting.query
        
        if category:
            query = query.filter_by(category=category)
        
        count = query.delete()
        db.session.commit()
        return count
    
    # ==================== INITIALIZATION ====================
    @staticmethod
    def initialize_defaults():
        """Initialize default settings in database"""
        for key, config in SettingsService.DEFAULTS.items():
            existing = SystemSetting.query.filter_by(setting_key=key).first()
            if not existing:
                setting = SystemSetting(
                    setting_key=key,
                    setting_value=SettingsService._value_to_string(config['value'], config['type']),
                    value_type=config['type'],
                    category=config['category'],
                    description=f"Default setting for {key}"
                )
                db.session.add(setting)
        
        db.session.commit()
    
    # ==================== HELPER METHODS ====================
    @staticmethod
    def _convert_value(str_value, value_type):
        """Convert string value to appropriate type"""
        if str_value is None:
            return None
        
        try:
            if value_type == 'integer':
                return int(str_value)
            elif value_type == 'float':
                return float(str_value)
            elif value_type == 'boolean':
                return str_value.lower() in ('true', '1', 'yes')
            elif value_type == 'json':
                return json.loads(str_value)
            else:
                return str_value
        except (ValueError, json.JSONDecodeError):
            return str_value
    
    @staticmethod
    def _value_to_string(value, value_type):
        """Convert value to string for storage"""
        if value is None:
            return None
        
        if value_type == 'json':
            return json.dumps(value)
        elif value_type == 'boolean':
            return 'true' if value else 'false'
        else:
            return str(value)
    
    @staticmethod
    def _detect_type(value):
        """Detect the type of a value"""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, (dict, list)):
            return 'json'
        else:
            return 'string'
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def setting_to_dict(setting):
        """Convert setting to dictionary"""
        if not setting:
            return None
        return {
            'setting_key': setting.setting_key,
            'setting_value': SettingsService._convert_value(setting.setting_value, setting.value_type),
            'value_type': setting.value_type,
            'category': setting.category,
            'description': setting.description,
            'is_encrypted': setting.is_encrypted,
            'updated_at': setting.updated_at.isoformat() if setting.updated_at else None,
            'updated_by': setting.updated_by
        }
