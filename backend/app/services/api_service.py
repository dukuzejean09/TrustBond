"""
API Management Service - API key and request logging management
"""
from app import db
from app.models.api_management import APIKey, APIRequestLog
from datetime import datetime, timedelta
import uuid
import secrets
import hashlib


class APIService:
    """Service for API key and request management"""
    
    # Scope definitions
    SCOPES = {
        'reports:read': 'Read incident reports',
        'reports:write': 'Submit incident reports',
        'hotspots:read': 'Read hotspot data',
        'devices:read': 'Read device information',
        'devices:write': 'Register/update devices',
        'public:read': 'Access public safety map data',
        'analytics:read': 'Access analytics data',
        'admin:full': 'Full administrative access'
    }
    
    # Rate limit tiers
    RATE_LIMITS = {
        'basic': {'requests_per_minute': 60, 'requests_per_day': 10000},
        'standard': {'requests_per_minute': 120, 'requests_per_day': 50000},
        'premium': {'requests_per_minute': 300, 'requests_per_day': 100000},
        'unlimited': {'requests_per_minute': None, 'requests_per_day': None}
    }
    
    # ==================== API KEY MANAGEMENT ====================
    @staticmethod
    def create_api_key(key_data, created_by_user_id=None):
        """Create a new API key"""
        # Generate secure key
        raw_key = secrets.token_hex(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]  # Store prefix for identification
        
        # Get rate limits
        tier = key_data.get('rate_limit_tier', 'basic')
        rate_limits = APIService.RATE_LIMITS.get(tier, APIService.RATE_LIMITS['basic'])
        
        api_key = APIKey(
            key_id=str(uuid.uuid4()),
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=key_data.get('name'),
            description=key_data.get('description'),
            client_name=key_data.get('client_name'),
            client_email=key_data.get('client_email'),
            scopes=key_data.get('scopes', ['public:read']),
            rate_limit_per_minute=rate_limits['requests_per_minute'],
            rate_limit_per_day=rate_limits['requests_per_day'],
            allowed_ips=key_data.get('allowed_ips', []),
            allowed_origins=key_data.get('allowed_origins', []),
            expires_at=key_data.get('expires_at'),
            is_active=True,
            created_by=created_by_user_id
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        # Return the raw key only on creation
        return {
            'api_key': api_key,
            'raw_key': raw_key,  # Only shown once!
            'message': 'Store this key securely. It cannot be retrieved again.'
        }
    
    @staticmethod
    def get_api_key_by_id(key_id):
        """Get API key by ID"""
        return APIKey.query.get(key_id)
    
    @staticmethod
    def get_api_key_by_prefix(prefix):
        """Get API key by prefix"""
        return APIKey.query.filter_by(key_prefix=prefix, is_active=True).first()
    
    @staticmethod
    def validate_api_key(raw_key):
        """Validate an API key and return the key record if valid"""
        if not raw_key or len(raw_key) < 8:
            return None, "Invalid API key format"
        
        prefix = raw_key[:8]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        api_key = APIKey.query.filter_by(key_prefix=prefix, key_hash=key_hash).first()
        
        if not api_key:
            return None, "Invalid API key"
        
        if not api_key.is_active:
            return None, "API key is inactive"
        
        if api_key.is_revoked:
            return None, "API key has been revoked"
        
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None, "API key has expired"
        
        # Update last used
        api_key.last_used_at = datetime.utcnow()
        api_key.total_requests = (api_key.total_requests or 0) + 1
        db.session.commit()
        
        return api_key, "Valid"
    
    @staticmethod
    def check_rate_limit(api_key, ip_address=None):
        """Check if request is within rate limits"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        day_ago = now - timedelta(days=1)
        
        # Check per-minute limit
        if api_key.rate_limit_per_minute:
            minute_count = APIRequestLog.query.filter(
                APIRequestLog.api_key_id == api_key.key_id,
                APIRequestLog.requested_at >= minute_ago
            ).count()
            
            if minute_count >= api_key.rate_limit_per_minute:
                return False, "Rate limit exceeded (per minute)"
        
        # Check per-day limit
        if api_key.rate_limit_per_day:
            day_count = APIRequestLog.query.filter(
                APIRequestLog.api_key_id == api_key.key_id,
                APIRequestLog.requested_at >= day_ago
            ).count()
            
            if day_count >= api_key.rate_limit_per_day:
                return False, "Rate limit exceeded (per day)"
        
        return True, "OK"
    
    @staticmethod
    def check_ip_allowed(api_key, ip_address):
        """Check if IP address is allowed"""
        if not api_key.allowed_ips:
            return True  # No restrictions
        
        return ip_address in api_key.allowed_ips
    
    @staticmethod
    def check_scope(api_key, required_scope):
        """Check if API key has required scope"""
        if 'admin:full' in api_key.scopes:
            return True
        return required_scope in api_key.scopes
    
    @staticmethod
    def get_all_api_keys(filters=None, page=1, per_page=20):
        """Get all API keys with optional filters"""
        query = APIKey.query
        
        if filters:
            if filters.get('is_active') is not None:
                query = query.filter_by(is_active=filters['is_active'])
            if filters.get('client_name'):
                query = query.filter(APIKey.client_name.ilike(f"%{filters['client_name']}%"))
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query = query.filter(
                    db.or_(
                        APIKey.name.ilike(search),
                        APIKey.client_name.ilike(search),
                        APIKey.client_email.ilike(search)
                    )
                )
        
        return query.order_by(APIKey.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def update_api_key(key_id, update_data, updated_by_user_id=None):
        """Update API key settings"""
        api_key = APIKey.query.get(key_id)
        if not api_key:
            return None
        
        allowed_fields = [
            'name', 'description', 'client_name', 'client_email',
            'scopes', 'rate_limit_per_minute', 'rate_limit_per_day',
            'allowed_ips', 'allowed_origins', 'expires_at', 'is_active'
        ]
        
        for field in allowed_fields:
            if field in update_data:
                setattr(api_key, field, update_data[field])
        
        api_key.updated_at = datetime.utcnow()
        db.session.commit()
        return api_key
    
    @staticmethod
    def revoke_api_key(key_id, reason=None, revoked_by_user_id=None):
        """Revoke an API key"""
        api_key = APIKey.query.get(key_id)
        if not api_key:
            return None
        
        api_key.is_revoked = True
        api_key.revoked_at = datetime.utcnow()
        api_key.revoked_by = revoked_by_user_id
        api_key.revoke_reason = reason
        api_key.is_active = False
        
        db.session.commit()
        return api_key
    
    @staticmethod
    def regenerate_api_key(key_id, regenerated_by_user_id=None):
        """Regenerate API key (creates new key, keeps settings)"""
        api_key = APIKey.query.get(key_id)
        if not api_key:
            return None
        
        # Generate new key
        raw_key = secrets.token_hex(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]
        
        api_key.key_hash = key_hash
        api_key.key_prefix = key_prefix
        api_key.updated_at = datetime.utcnow()
        api_key.total_requests = 0
        
        db.session.commit()
        
        return {
            'api_key': api_key,
            'raw_key': raw_key,
            'message': 'Store this key securely. It cannot be retrieved again.'
        }
    
    # ==================== REQUEST LOGGING ====================
    @staticmethod
    def log_request(
        api_key_id,
        endpoint,
        method,
        ip_address=None,
        user_agent=None,
        request_body_size=None,
        response_status=None,
        response_time_ms=None,
        error_message=None
    ):
        """Log an API request"""
        log = APIRequestLog(
            log_id=str(uuid.uuid4()),
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            request_body_size=request_body_size,
            response_status=response_status,
            response_time_ms=response_time_ms,
            error_message=error_message
        )
        
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def get_request_logs(api_key_id=None, filters=None, page=1, per_page=50):
        """Get API request logs"""
        query = APIRequestLog.query
        
        if api_key_id:
            query = query.filter_by(api_key_id=api_key_id)
        
        if filters:
            if filters.get('endpoint'):
                query = query.filter(APIRequestLog.endpoint.ilike(f"%{filters['endpoint']}%"))
            if filters.get('method'):
                query = query.filter_by(method=filters['method'])
            if filters.get('status'):
                query = query.filter_by(response_status=filters['status'])
            if filters.get('from_date'):
                query = query.filter(APIRequestLog.requested_at >= filters['from_date'])
            if filters.get('to_date'):
                query = query.filter(APIRequestLog.requested_at <= filters['to_date'])
            if filters.get('has_error'):
                query = query.filter(APIRequestLog.error_message.isnot(None))
        
        return query.order_by(APIRequestLog.requested_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    # ==================== STATISTICS ====================
    @staticmethod
    def get_api_key_stats(key_id, days=30):
        """Get usage statistics for an API key"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        api_key = APIKey.query.get(key_id)
        if not api_key:
            return None
        
        # Total requests in period
        total_requests = APIRequestLog.query.filter(
            APIRequestLog.api_key_id == key_id,
            APIRequestLog.requested_at >= from_date
        ).count()
        
        # Requests by status
        by_status = db.session.query(
            APIRequestLog.response_status,
            db.func.count(APIRequestLog.log_id)
        ).filter(
            APIRequestLog.api_key_id == key_id,
            APIRequestLog.requested_at >= from_date
        ).group_by(APIRequestLog.response_status).all()
        
        # Requests by endpoint
        by_endpoint = db.session.query(
            APIRequestLog.endpoint,
            db.func.count(APIRequestLog.log_id)
        ).filter(
            APIRequestLog.api_key_id == key_id,
            APIRequestLog.requested_at >= from_date
        ).group_by(APIRequestLog.endpoint)\
         .order_by(db.func.count(APIRequestLog.log_id).desc())\
         .limit(10).all()
        
        # Average response time
        avg_response_time = db.session.query(
            db.func.avg(APIRequestLog.response_time_ms)
        ).filter(
            APIRequestLog.api_key_id == key_id,
            APIRequestLog.requested_at >= from_date,
            APIRequestLog.response_time_ms.isnot(None)
        ).scalar()
        
        # Error rate
        error_count = APIRequestLog.query.filter(
            APIRequestLog.api_key_id == key_id,
            APIRequestLog.requested_at >= from_date,
            APIRequestLog.response_status >= 400
        ).count()
        
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'key_id': key_id,
            'total_requests': total_requests,
            'by_status': dict(by_status),
            'by_endpoint': dict(by_endpoint),
            'avg_response_time_ms': round(float(avg_response_time), 2) if avg_response_time else None,
            'error_rate': round(error_rate, 2),
            'total_all_time': api_key.total_requests,
            'last_used_at': api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            'period_days': days
        }
    
    @staticmethod
    def get_overall_api_stats(days=30):
        """Get overall API usage statistics"""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        # Total requests
        total_requests = APIRequestLog.query.filter(
            APIRequestLog.requested_at >= from_date
        ).count()
        
        # Active keys (used in period)
        active_keys = db.session.query(
            db.func.count(db.func.distinct(APIRequestLog.api_key_id))
        ).filter(APIRequestLog.requested_at >= from_date).scalar()
        
        # Requests over time
        daily_requests = db.session.query(
            db.func.date(APIRequestLog.requested_at).label('date'),
            db.func.count(APIRequestLog.log_id).label('count')
        ).filter(APIRequestLog.requested_at >= from_date)\
         .group_by(db.func.date(APIRequestLog.requested_at))\
         .order_by('date').all()
        
        # Top endpoints
        top_endpoints = db.session.query(
            APIRequestLog.endpoint,
            db.func.count(APIRequestLog.log_id).label('count')
        ).filter(APIRequestLog.requested_at >= from_date)\
         .group_by(APIRequestLog.endpoint)\
         .order_by(db.func.count(APIRequestLog.log_id).desc())\
         .limit(10).all()
        
        return {
            'total_requests': total_requests,
            'active_keys': active_keys,
            'daily_requests': [{'date': str(r.date), 'count': r.count} for r in daily_requests],
            'top_endpoints': [{'endpoint': r.endpoint, 'count': r.count} for r in top_endpoints],
            'period_days': days
        }
    
    # ==================== CLEANUP ====================
    @staticmethod
    def cleanup_old_logs(days=90):
        """Delete old request logs"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        deleted = APIRequestLog.query.filter(
            APIRequestLog.requested_at < cutoff
        ).delete()
        
        db.session.commit()
        return deleted
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def api_key_to_dict(api_key, include_sensitive=False):
        """Convert API key to dictionary"""
        if not api_key:
            return None
        
        result = {
            'key_id': api_key.key_id,
            'key_prefix': api_key.key_prefix,
            'name': api_key.name,
            'description': api_key.description,
            'client_name': api_key.client_name,
            'client_email': api_key.client_email,
            'scopes': api_key.scopes,
            'rate_limit_per_minute': api_key.rate_limit_per_minute,
            'rate_limit_per_day': api_key.rate_limit_per_day,
            'is_active': api_key.is_active,
            'is_revoked': api_key.is_revoked,
            'total_requests': api_key.total_requests,
            'last_used_at': api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            'expires_at': api_key.expires_at.isoformat() if api_key.expires_at else None,
            'created_at': api_key.created_at.isoformat() if api_key.created_at else None
        }
        
        if include_sensitive:
            result['allowed_ips'] = api_key.allowed_ips
            result['allowed_origins'] = api_key.allowed_origins
            result['revoked_at'] = api_key.revoked_at.isoformat() if api_key.revoked_at else None
            result['revoke_reason'] = api_key.revoke_reason
        
        return result
    
    @staticmethod
    def request_log_to_dict(log):
        """Convert request log to dictionary"""
        if not log:
            return None
        return {
            'log_id': log.log_id,
            'api_key_id': log.api_key_id,
            'endpoint': log.endpoint,
            'method': log.method,
            'ip_address': log.ip_address,
            'response_status': log.response_status,
            'response_time_ms': log.response_time_ms,
            'error_message': log.error_message,
            'requested_at': log.requested_at.isoformat() if log.requested_at else None
        }
