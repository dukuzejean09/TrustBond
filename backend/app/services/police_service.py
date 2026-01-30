"""
Police Service - Police user management and authentication
"""
from app import db
from app.models.police_users import PoliceUser, PoliceSession
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid
import secrets


class PoliceService:
    """Service for police user management"""
    
    # ==================== USER RETRIEVAL ====================
    @staticmethod
    def get_all_users(filters=None, page=1, per_page=20):
        """Get all police users with optional filters"""
        query = PoliceUser.query
        
        if filters:
            if filters.get('role'):
                query = query.filter_by(role=filters['role'])
            if filters.get('is_active') is not None:
                query = query.filter_by(is_active=filters['is_active'])
            if filters.get('district_id'):
                query = query.filter_by(district_id=filters['district_id'])
            if filters.get('station_id'):
                query = query.filter_by(station_id=filters['station_id'])
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query = query.filter(
                    db.or_(
                        PoliceUser.username.ilike(search),
                        PoliceUser.full_name.ilike(search),
                        PoliceUser.badge_number.ilike(search),
                        PoliceUser.email.ilike(search)
                    )
                )
        
        return query.order_by(PoliceUser.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get police user by ID"""
        return PoliceUser.query.get(user_id)
    
    @staticmethod
    def get_user_by_username(username):
        """Get police user by username"""
        return PoliceUser.query.filter_by(username=username).first()
    
    @staticmethod
    def get_user_by_email(email):
        """Get police user by email"""
        return PoliceUser.query.filter_by(email=email).first()
    
    @staticmethod
    def get_user_by_badge_number(badge_number):
        """Get police user by badge number"""
        return PoliceUser.query.filter_by(badge_number=badge_number).first()
    
    # ==================== USER MANAGEMENT ====================
    @staticmethod
    def create_user(user_data, created_by_user_id=None):
        """Create a new police user"""
        # Check for existing username
        if PoliceService.get_user_by_username(user_data['username']):
            raise ValueError("Username already exists")
        
        # Check for existing email
        if user_data.get('email') and PoliceService.get_user_by_email(user_data['email']):
            raise ValueError("Email already exists")
        
        # Check for existing badge number
        if user_data.get('badge_number') and PoliceService.get_user_by_badge_number(user_data['badge_number']):
            raise ValueError("Badge number already exists")
        
        user = PoliceUser(
            username=user_data['username'],
            password_hash=generate_password_hash(user_data['password']),
            full_name=user_data.get('full_name'),
            email=user_data.get('email'),
            phone=user_data.get('phone'),
            role=user_data.get('role', 'officer'),
            badge_number=user_data.get('badge_number'),
            rank=user_data.get('rank'),
            station_id=user_data.get('station_id'),
            district_id=user_data.get('district_id'),
            sector_id=user_data.get('sector_id'),
            permissions=user_data.get('permissions', {}),
            created_by=created_by_user_id
        )
        
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def update_user(user_id, update_data, updated_by_user_id=None):
        """Update police user"""
        user = PoliceUser.query.get(user_id)
        if not user:
            return None
        
        # Check unique constraints if updating
        if update_data.get('username') and update_data['username'] != user.username:
            if PoliceService.get_user_by_username(update_data['username']):
                raise ValueError("Username already exists")
        
        if update_data.get('email') and update_data['email'] != user.email:
            if PoliceService.get_user_by_email(update_data['email']):
                raise ValueError("Email already exists")
        
        if update_data.get('badge_number') and update_data['badge_number'] != user.badge_number:
            if PoliceService.get_user_by_badge_number(update_data['badge_number']):
                raise ValueError("Badge number already exists")
        
        # Update allowed fields
        allowed_fields = [
            'username', 'full_name', 'email', 'phone', 'role', 
            'badge_number', 'rank', 'station_id', 'district_id', 
            'sector_id', 'permissions', 'is_active', 'profile_picture'
        ]
        
        for field in allowed_fields:
            if field in update_data:
                setattr(user, field, update_data[field])
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        return user
    
    @staticmethod
    def delete_user(user_id):
        """Delete/deactivate a police user"""
        user = PoliceUser.query.get(user_id)
        if user:
            user.is_active = False
            user.deactivated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def change_password(user_id, old_password, new_password):
        """Change user password"""
        user = PoliceUser.query.get(user_id)
        if not user:
            return False, "User not found"
        
        if not check_password_hash(user.password_hash, old_password):
            return False, "Current password is incorrect"
        
        user.password_hash = generate_password_hash(new_password)
        user.password_changed_at = datetime.utcnow()
        user.must_change_password = False
        db.session.commit()
        return True, "Password changed successfully"
    
    @staticmethod
    def reset_password(user_id, new_password, admin_user_id):
        """Admin password reset"""
        user = PoliceUser.query.get(user_id)
        if not user:
            return False, "User not found"
        
        user.password_hash = generate_password_hash(new_password)
        user.password_changed_at = datetime.utcnow()
        user.must_change_password = True
        user.password_reset_by = admin_user_id
        db.session.commit()
        return True, "Password reset successfully"
    
    # ==================== AUTHENTICATION ====================
    @staticmethod
    def authenticate(username, password, ip_address=None, user_agent=None):
        """Authenticate user and create session"""
        user = PoliceService.get_user_by_username(username)
        
        if not user:
            return None, "Invalid username or password"
        
        # Check account status
        if not user.is_active:
            return None, "Account is deactivated"
        
        if user.is_locked:
            if user.locked_until and user.locked_until > datetime.utcnow():
                return None, f"Account is locked until {user.locked_until}"
            else:
                # Unlock if lock period has passed
                user.is_locked = False
                user.locked_until = None
                user.failed_login_count = 0
        
        # Verify password
        if not check_password_hash(user.password_hash, password):
            user.failed_login_count = (user.failed_login_count or 0) + 1
            user.last_failed_login_at = datetime.utcnow()
            
            # Lock account after 5 failed attempts
            if user.failed_login_count >= 5:
                user.is_locked = True
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            
            db.session.commit()
            return None, "Invalid username or password"
        
        # Successful login
        user.failed_login_count = 0
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address
        user.login_count = (user.login_count or 0) + 1
        
        # Create session
        session = PoliceSession(
            session_id=str(uuid.uuid4()),
            user_id=user.user_id,
            token=secrets.token_hex(32),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        db.session.add(session)
        db.session.commit()
        
        return {
            'user': user,
            'session': session,
            'must_change_password': user.must_change_password
        }, "Login successful"
    
    @staticmethod
    def logout(session_id):
        """Logout and invalidate session"""
        session = PoliceSession.query.get(session_id)
        if session:
            session.is_active = False
            session.logged_out_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def validate_session(session_id, token):
        """Validate session token"""
        session = PoliceSession.query.filter_by(
            session_id=session_id,
            token=token,
            is_active=True
        ).first()
        
        if not session:
            return None
        
        if session.expires_at < datetime.utcnow():
            session.is_active = False
            db.session.commit()
            return None
        
        # Extend session
        session.last_activity_at = datetime.utcnow()
        session.expires_at = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        
        return session.user
    
    @staticmethod
    def get_active_sessions(user_id):
        """Get all active sessions for a user"""
        return PoliceSession.query.filter_by(
            user_id=user_id,
            is_active=True
        ).filter(PoliceSession.expires_at > datetime.utcnow()).all()
    
    @staticmethod
    def invalidate_all_sessions(user_id):
        """Invalidate all sessions for a user"""
        PoliceSession.query.filter_by(user_id=user_id, is_active=True)\
            .update({'is_active': False, 'logged_out_at': datetime.utcnow()})
        db.session.commit()
    
    # ==================== PERMISSIONS ====================
    @staticmethod
    def has_permission(user_id, permission):
        """Check if user has a specific permission"""
        user = PoliceUser.query.get(user_id)
        if not user:
            return False
        
        # Superadmin has all permissions
        if user.role == 'superadmin':
            return True
        
        # Check role-based permissions
        role_permissions = {
            'admin': ['manage_users', 'manage_reports', 'manage_hotspots', 'view_analytics', 'manage_settings'],
            'supervisor': ['manage_reports', 'manage_hotspots', 'view_analytics'],
            'officer': ['view_reports', 'update_reports']
        }
        
        if permission in role_permissions.get(user.role, []):
            return True
        
        # Check custom permissions
        return user.permissions.get(permission, False) if user.permissions else False
    
    @staticmethod
    def update_permissions(user_id, permissions, admin_user_id):
        """Update user permissions"""
        user = PoliceUser.query.get(user_id)
        if not user:
            return None
        
        user.permissions = permissions
        user.updated_at = datetime.utcnow()
        db.session.commit()
        return user
    
    # ==================== ACTIVITY TRACKING ====================
    @staticmethod
    def get_user_activity_summary(user_id, days=30):
        """Get user activity summary"""
        user = PoliceUser.query.get(user_id)
        if not user:
            return None
        
        from_date = datetime.utcnow() - timedelta(days=days)
        
        # Get session count
        session_count = PoliceSession.query.filter(
            PoliceSession.user_id == user_id,
            PoliceSession.created_at >= from_date
        ).count()
        
        return {
            'user_id': user_id,
            'login_count': user.login_count or 0,
            'sessions_last_30_days': session_count,
            'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
            'reports_reviewed': user.reports_reviewed or 0,
            'reports_verified': user.reports_verified or 0,
            'verification_accuracy_pct': float(user.verification_accuracy_pct) if user.verification_accuracy_pct else None
        }
    
    # ==================== SERIALIZATION ====================
    @staticmethod
    def user_to_dict(user, include_sensitive=False):
        """Convert user to dictionary"""
        if not user:
            return None
        
        result = {
            'user_id': user.user_id,
            'username': user.username,
            'full_name': user.full_name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
            'badge_number': user.badge_number,
            'rank': user.rank,
            'station_id': user.station_id,
            'district_id': user.district_id,
            'sector_id': user.sector_id,
            'is_active': user.is_active,
            'profile_picture': user.profile_picture,
            'login_count': user.login_count,
            'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None
        }
        
        if include_sensitive:
            result['permissions'] = user.permissions
            result['is_locked'] = user.is_locked
            result['locked_until'] = user.locked_until.isoformat() if user.locked_until else None
            result['failed_login_count'] = user.failed_login_count
            result['must_change_password'] = user.must_change_password
            result['reports_reviewed'] = user.reports_reviewed
            result['reports_verified'] = user.reports_verified
            result['verification_accuracy_pct'] = float(user.verification_accuracy_pct) if user.verification_accuracy_pct else None
        
        return result
    
    @staticmethod
    def session_to_dict(session):
        """Convert session to dictionary"""
        if not session:
            return None
        return {
            'session_id': session.session_id,
            'user_id': session.user_id,
            'ip_address': session.ip_address,
            'is_active': session.is_active,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'last_activity_at': session.last_activity_at.isoformat() if session.last_activity_at else None,
            'expires_at': session.expires_at.isoformat() if session.expires_at else None
        }
