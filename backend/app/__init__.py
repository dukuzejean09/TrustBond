from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://trustbond:trustbond123@localhost:5432/trustbond'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 86400 * 7  # 7 days
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Enable CORS - Allow all origins for mobile app
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
            "expose_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 86400
        }
    })
    
    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'success': False,
            'error': 'Token has expired',
            'code': 'token_expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'success': False,
            'error': 'Invalid token',
            'code': 'invalid_token'
        }), 401
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({
            'success': False,
            'error': 'Missing authorization token',
            'code': 'missing_token'
        }), 401
    
    # Global error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad request',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
        }), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({
            'success': False,
            'error': 'File too large',
            'message': 'Maximum file size is 16MB'
        }), 413
    
    # Register existing blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.reports import reports_bp
    from app.routes.alerts import alerts_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.mobile import mobile_bp
    from app.routes.uploads import uploads_bp
    from app.routes.ml import ml_bp
    from app.routes.notifications import notifications_bp
    from app.routes.analytics import analytics_bp
    from app.routes.comments import comments_bp
    
    # Register new blueprints for complete database coverage
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
    
    # Existing blueprint registrations
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(mobile_bp, url_prefix='/api/mobile')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    app.register_blueprint(ml_bp, url_prefix='/api/ml')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(comments_bp, url_prefix='/api/comments')
    
    # New blueprint registrations
    app.register_blueprint(devices_bp, url_prefix='/api/devices')
    app.register_blueprint(geography_bp, url_prefix='/api/geography')
    app.register_blueprint(incidents_bp, url_prefix='/api/incidents')
    app.register_blueprint(hotspots_bp, url_prefix='/api/hotspots')
    app.register_blueprint(police_bp, url_prefix='/api/police')
    app.register_blueprint(verification_bp, url_prefix='/api/verification')
    app.register_blueprint(ml_routes_bp, url_prefix='/api/ml-models')
    app.register_blueprint(audit_bp, url_prefix='/api/audit')
    app.register_blueprint(feedback_bp, url_prefix='/api/feedback')
    app.register_blueprint(api_management_bp, url_prefix='/api/api-management')
    app.register_blueprint(public_map_bp, url_prefix='/api/public-map')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(analytics_routes_bp, url_prefix='/api/analytics-v2')
    app.register_blueprint(notifications_routes_bp, url_prefix='/api/notifications-v2')
    
    # Root API endpoint
    @app.route('/api')
    def api_root():
        return {
            'status': 'online',
            'service': 'TrustBond API',
            'version': '2.0.0',
            'endpoints': {
                'health': '/api/health',
                'auth': '/api/auth',
                'users': '/api/users',
                'reports': '/api/reports',
                'alerts': '/api/alerts',
                'dashboard': '/api/dashboard',
                'mobile': '/api/mobile',
                'uploads': '/api/uploads',
                'ml': '/api/ml',
                'notifications': '/api/notifications',
                'analytics': '/api/analytics',
                'comments': '/api/comments',
                # New endpoints
                'devices': '/api/devices',
                'geography': '/api/geography',
                'incidents': '/api/incidents',
                'hotspots': '/api/hotspots',
                'police': '/api/police',
                'verification': '/api/verification',
                'ml_models': '/api/ml-models',
                'audit': '/api/audit',
                'feedback': '/api/feedback',
                'api_management': '/api/api-management',
                'public_map': '/api/public-map',
                'settings': '/api/settings'
            },
            'mobile_endpoints': {
                'stats': '/api/mobile/stats',
                'emergency_contacts': '/api/mobile/emergency-contacts',
                'nearby_reports': '/api/mobile/nearby-reports',
                'crime_categories': '/api/mobile/crime-categories',
                'districts': '/api/mobile/districts',
                'app_config': '/api/mobile/app-config',
                'report_tips': '/api/mobile/report-tips',
                'faqs': '/api/mobile/faqs',
                'anonymous_report': '/api/reports/anonymous',
                'track_report': '/api/reports/track/<tracking_code>'
            },
            'ml_endpoints': {
                'verify_report': '/api/ml/verify',
                'hotspots': '/api/ml/hotspots',
                'public_safety_map': '/api/ml/public/safety-map',
                'device_profile': '/api/ml/device/profile'
            },
            'analytics_endpoints': {
                'overview': '/api/analytics/overview',
                'trends': '/api/analytics/trends',
                'geographic': '/api/analytics/geographic',
                'export_reports': '/api/analytics/export/reports',
                'activity_logs': '/api/analytics/activity-logs'
            },
            'device_endpoints': {
                'register': '/api/devices/register',
                'heartbeat': '/api/devices/heartbeat',
                'profile': '/api/devices/<device_id>/profile'
            },
            'geography_endpoints': {
                'provinces': '/api/geography/provinces',
                'districts': '/api/geography/districts',
                'sectors': '/api/geography/sectors',
                'resolve_location': '/api/geography/resolve'
            },
            'incident_endpoints': {
                'submit': '/api/incidents',
                'track': '/api/incidents/track/<tracking_code>',
                'categories': '/api/incidents/categories',
                'types': '/api/incidents/types'
            },
            'hotspot_endpoints': {
                'detect': '/api/hotspots/detect',
                'list': '/api/hotspots',
                'public_safety_map': '/api/public-map/data'
            }
        }
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'service': 'TrustBond API'}
    
    @app.route('/')
    def index():
        return {
            'message': 'TrustBond API - Rwanda National Police Crime Reporting System',
            'version': '2.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'users': '/api/users',
                'reports': '/api/reports',
                'alerts': '/api/alerts',
                'dashboard': '/api/dashboard',
                'devices': '/api/devices',
                'geography': '/api/geography',
                'incidents': '/api/incidents',
                'hotspots': '/api/hotspots'
            }
        }
    
    return app
