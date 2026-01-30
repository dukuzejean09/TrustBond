from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import enum


class UserRole(enum.Enum):
    CITIZEN = 'citizen'
    OFFICER = 'officer'
    ADMIN = 'admin'
    SUPER_ADMIN = 'super_admin'


class UserStatus(enum.Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    national_id = db.Column(db.String(20), unique=True)
    role = db.Column(db.Enum(UserRole), default=UserRole.CITIZEN, nullable=False)
    status = db.Column(db.Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    profile_image = db.Column(db.String(255))
    
    # Location info
    province = db.Column(db.String(50))
    district = db.Column(db.String(50))
    sector = db.Column(db.String(50))
    cell = db.Column(db.String(50))
    
    # For officers
    badge_number = db.Column(db.String(20), unique=True)
    station = db.Column(db.String(100))
    rank = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    reports = db.relationship('Report', backref='reporter', lazy='dynamic', foreign_keys='Report.reporter_id')
    assigned_reports = db.relationship('Report', backref='assigned_officer', lazy='dynamic', foreign_keys='Report.assigned_to')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'firstName': self.first_name,
            'lastName': self.last_name,
            'phone': self.phone,
            'nationalId': self.national_id,
            'role': self.role.value,
            'status': self.status.value,
            'profileImage': self.profile_image,
            'province': self.province,
            'district': self.district,
            'sector': self.sector,
            'cell': self.cell,
            'badgeNumber': self.badge_number,
            'station': self.station,
            'rank': self.rank,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'lastLogin': self.last_login.isoformat() if self.last_login else None
        }
    
    def __repr__(self):
        return f'<User {self.email}>'
