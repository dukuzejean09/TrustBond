# Existing blueprints
from app.routes.auth import auth_bp
from app.routes.users import users_bp
from app.routes.reports import reports_bp
from app.routes.alerts import alerts_bp
from app.routes.dashboard import dashboard_bp
from app.routes.ml import ml_bp
from app.routes.notifications import notifications_bp
from app.routes.analytics import analytics_bp
from app.routes.comments import comments_bp

# New blueprints for complete database coverage
from app.routes.devices import devices_bp
from app.routes.geography import geography_bp
from app.routes.incidents import incidents_bp
from app.routes.hotspots import hotspots_bp
from app.routes.police import police_bp
from app.routes.verification import verification_bp
from app.routes.ml_routes import ml_routes_bp
from app.routes.audit import audit_bp
from app.routes.feedback import feedback_bp
from app.routes.api_management import api_management_bp
from app.routes.public_map import public_map_bp
from app.routes.settings import settings_bp
from app.routes.analytics_routes import analytics_bp as analytics_routes_bp
from app.routes.notifications_routes import notifications_bp as notifications_routes_bp

__all__ = [
    # Existing blueprints
    'auth_bp', 'users_bp', 'reports_bp', 'alerts_bp', 
    'dashboard_bp', 'ml_bp', 'notifications_bp', 'analytics_bp', 'comments_bp',
    # New blueprints
    'devices_bp', 'geography_bp', 'incidents_bp', 'hotspots_bp',
    'police_bp', 'verification_bp', 'ml_routes_bp', 'audit_bp',
    'feedback_bp', 'api_management_bp', 'public_map_bp', 'settings_bp',
    'analytics_routes_bp', 'notifications_routes_bp'
]
