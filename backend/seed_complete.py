"""
TrustBond Comprehensive Database Seed Script
Seeds all tables with initial/sample data for testing and development
"""
from app import create_app, db
from app.models import (
    # Device Management
    Device, DeviceTrustHistory,
    # Geography
    Province, District, Sector, Cell, Village,
    # Taxonomy
    IncidentCategory, IncidentType,
    # Reports
    IncidentReport,
    # Evidence
    ReportEvidence,
    # Rules
    VerificationRule, RuleExecutionLog,
    # ML
    MLModel, MLPrediction, MLTrainingData,
    # Hotspots
    Hotspot, HotspotReport, HotspotHistory, ClusteringRun,
    # Police
    PoliceUser, PoliceSession,
    # Notifications
    Notification,
    # Analytics
    DailyStatistic, IncidentTypeTrend,
    # Public Map
    PublicSafetyZone,
    # System
    SystemSetting,
    # Audit
    ActivityLog, DataChangeAudit,
    # Feedback
    AppFeedback, FeedbackAttachment,
    # API
    APIKey, APIRequestLog
)
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random
import uuid

app = create_app()


def seed_database():
    with app.app_context():
        # Create tables
        db.create_all()
        
        print("=" * 70)
        print("TrustBond Comprehensive Database Seeding")
        print("=" * 70)
        
        # ==================== RWANDA ADMINISTRATIVE GEOGRAPHY ====================
        print("\n--- Seeding Rwanda Administrative Geography ---")
        
        # Check if provinces already exist
        if Province.query.count() == 0:
            provinces_data = [
                {'name': 'Kigali City', 'code': 'KC'},
                {'name': 'Northern Province', 'code': 'NP'},
                {'name': 'Southern Province', 'code': 'SP'},
                {'name': 'Eastern Province', 'code': 'EP'},
                {'name': 'Western Province', 'code': 'WP'}
            ]
            
            for prov_data in provinces_data:
                province = Province(
                    province_name=prov_data['name'],
                    province_code=prov_data['code']
                )
                db.session.add(province)
            db.session.commit()
            print(f"✓ Created {len(provinces_data)} provinces")
            
            # Add districts for Kigali City
            kigali = Province.query.filter_by(province_code='KC').first()
            kigali_districts = [
                {'name': 'Gasabo', 'code': 'GS', 'lat': -1.9403, 'lng': 30.0978},
                {'name': 'Kicukiro', 'code': 'KI', 'lat': -1.9917, 'lng': 30.0847},
                {'name': 'Nyarugenge', 'code': 'NY', 'lat': -1.9547, 'lng': 30.0613}
            ]
            
            for dist_data in kigali_districts:
                district = District(
                    province_id=kigali.province_id,
                    district_name=dist_data['name'],
                    district_code=dist_data['code'],
                    center_latitude=dist_data['lat'],
                    center_longitude=dist_data['lng']
                )
                db.session.add(district)
            db.session.commit()
            print(f"✓ Created {len(kigali_districts)} districts for Kigali City")
            
            # Add sample sectors for Gasabo
            gasabo = District.query.filter_by(district_code='GS').first()
            gasabo_sectors = [
                {'name': 'Remera', 'code': 'REM'},
                {'name': 'Kimironko', 'code': 'KIM'},
                {'name': 'Kacyiru', 'code': 'KAC'},
                {'name': 'Gisozi', 'code': 'GIS'},
                {'name': 'Kimihurura', 'code': 'KMH'}
            ]
            
            for sec_data in gasabo_sectors:
                sector = Sector(
                    district_id=gasabo.district_id,
                    sector_name=sec_data['name'],
                    sector_code=sec_data['code']
                )
                db.session.add(sector)
            db.session.commit()
            print(f"✓ Created {len(gasabo_sectors)} sectors for Gasabo")
        
        # ==================== INCIDENT CATEGORIES & TYPES ====================
        print("\n--- Seeding Incident Categories & Types ---")
        
        if IncidentCategory.query.count() == 0:
            categories_data = [
                {
                    'name': 'Theft & Robbery',
                    'code': 'THEFT',
                    'icon': 'shield-alert',
                    'color': '#E53935',
                    'types': [
                        {'name': 'Pickpocketing', 'code': 'PICK', 'severity': 'medium'},
                        {'name': 'Home Burglary', 'code': 'BURG', 'severity': 'high'},
                        {'name': 'Vehicle Theft', 'code': 'VTHF', 'severity': 'high'},
                        {'name': 'Armed Robbery', 'code': 'AROB', 'severity': 'critical'},
                        {'name': 'Phone Snatching', 'code': 'PHSN', 'severity': 'medium'}
                    ]
                },
                {
                    'name': 'Violence & Assault',
                    'code': 'VIOLENCE',
                    'icon': 'alert-triangle',
                    'color': '#D32F2F',
                    'types': [
                        {'name': 'Physical Assault', 'code': 'PASS', 'severity': 'high'},
                        {'name': 'Domestic Violence', 'code': 'DOMV', 'severity': 'high'},
                        {'name': 'Street Fighting', 'code': 'STFT', 'severity': 'medium'},
                        {'name': 'Sexual Assault', 'code': 'SXAS', 'severity': 'critical'}
                    ]
                },
                {
                    'name': 'Fraud & Scams',
                    'code': 'FRAUD',
                    'icon': 'credit-card',
                    'color': '#FF9800',
                    'types': [
                        {'name': 'Mobile Money Fraud', 'code': 'MMFR', 'severity': 'medium'},
                        {'name': 'Online Scam', 'code': 'ONSC', 'severity': 'medium'},
                        {'name': 'Identity Theft', 'code': 'IDTH', 'severity': 'high'},
                        {'name': 'Investment Fraud', 'code': 'INVF', 'severity': 'high'}
                    ]
                },
                {
                    'name': 'Traffic Incidents',
                    'code': 'TRAFFIC',
                    'icon': 'car',
                    'color': '#2196F3',
                    'types': [
                        {'name': 'Hit and Run', 'code': 'HITR', 'severity': 'high'},
                        {'name': 'Reckless Driving', 'code': 'RCKD', 'severity': 'medium'},
                        {'name': 'DUI/Drunk Driving', 'code': 'DUID', 'severity': 'high'}
                    ]
                },
                {
                    'name': 'Property Damage',
                    'code': 'PROPERTY',
                    'icon': 'home',
                    'color': '#9C27B0',
                    'types': [
                        {'name': 'Vandalism', 'code': 'VAND', 'severity': 'medium'},
                        {'name': 'Arson', 'code': 'ARSN', 'severity': 'critical'},
                        {'name': 'Graffiti', 'code': 'GRAF', 'severity': 'low'}
                    ]
                },
                {
                    'name': 'Drugs & Substances',
                    'code': 'DRUGS',
                    'icon': 'pill',
                    'color': '#795548',
                    'types': [
                        {'name': 'Drug Dealing', 'code': 'DRUG', 'severity': 'high'},
                        {'name': 'Drug Use in Public', 'code': 'DPUB', 'severity': 'medium'}
                    ]
                },
                {
                    'name': 'Suspicious Activity',
                    'code': 'SUSPICIOUS',
                    'icon': 'eye',
                    'color': '#607D8B',
                    'types': [
                        {'name': 'Loitering', 'code': 'LOIT', 'severity': 'low'},
                        {'name': 'Suspicious Person', 'code': 'SUSP', 'severity': 'medium'},
                        {'name': 'Suspicious Vehicle', 'code': 'SUSV', 'severity': 'medium'}
                    ]
                },
                {
                    'name': 'Other',
                    'code': 'OTHER',
                    'icon': 'help-circle',
                    'color': '#9E9E9E',
                    'types': [
                        {'name': 'Noise Complaint', 'code': 'NOIS', 'severity': 'low'},
                        {'name': 'Other Incident', 'code': 'OTHR', 'severity': 'low'}
                    ]
                }
            ]
            
            for cat_data in categories_data:
                category = IncidentCategory(
                    category_name=cat_data['name'],
                    category_code=cat_data['code'],
                    icon_name=cat_data['icon'],
                    color_hex=cat_data['color']
                )
                db.session.add(category)
                db.session.flush()  # Get the ID
                
                for type_data in cat_data['types']:
                    inc_type = IncidentType(
                        category_id=category.category_id,
                        type_name=type_data['name'],
                        type_code=type_data['code'],
                        default_severity=type_data['severity']
                    )
                    db.session.add(inc_type)
            
            db.session.commit()
            print(f"✓ Created {len(categories_data)} incident categories with types")
        
        # ==================== VERIFICATION RULES ====================
        print("\n--- Seeding Verification Rules ---")
        
        if VerificationRule.query.count() == 0:
            rules_data = [
                {
                    'code': 'LOCATION_IN_RWANDA',
                    'name': 'Location Within Rwanda',
                    'description': 'Validates that report coordinates fall within Rwanda borders',
                    'weight': 15,
                    'config': {
                        'min_lat': -2.84,
                        'max_lat': -1.05,
                        'min_lng': 28.86,
                        'max_lng': 30.90
                    },
                    'order': 1
                },
                {
                    'code': 'LOCATION_ACCURACY',
                    'name': 'GPS Accuracy Check',
                    'description': 'Validates GPS accuracy is within acceptable range',
                    'weight': 10,
                    'config': {'max_accuracy_meters': 100},
                    'order': 2
                },
                {
                    'code': 'REPORT_FRESHNESS',
                    'name': 'Report Freshness',
                    'description': 'Checks if incident timestamp is recent',
                    'weight': 10,
                    'config': {'max_age_hours': 24},
                    'order': 3
                },
                {
                    'code': 'DESCRIPTION_LENGTH',
                    'name': 'Description Quality',
                    'description': 'Validates description meets minimum length',
                    'weight': 10,
                    'config': {'min_length': 20, 'max_length': 5000},
                    'order': 4
                },
                {
                    'code': 'MOTION_DETECTED',
                    'name': 'Device Motion Check',
                    'description': 'Checks if device motion data indicates real-world usage',
                    'weight': 5,
                    'config': {},
                    'order': 5
                },
                {
                    'code': 'DEVICE_TRUST',
                    'name': 'Device Trust Score',
                    'description': 'Validates device trust score meets threshold',
                    'weight': 20,
                    'config': {'min_trust_score': 30},
                    'order': 6
                },
                {
                    'code': 'DUPLICATE_CHECK',
                    'name': 'Duplicate Detection',
                    'description': 'Checks for similar reports from same device',
                    'weight': 10,
                    'config': {
                        'time_window_hours': 1,
                        'distance_meters': 100
                    },
                    'order': 7
                },
                {
                    'code': 'SPAM_CHECK',
                    'name': 'Spam Detection',
                    'description': 'Checks for spam patterns and rate limiting',
                    'weight': 10,
                    'config': {
                        'max_reports_per_hour': 5,
                        'max_reports_per_day': 20
                    },
                    'order': 8
                },
                {
                    'code': 'TIME_CONSISTENCY',
                    'name': 'Time Consistency',
                    'description': 'Validates time consistency between device and server',
                    'weight': 5,
                    'config': {'max_time_drift_minutes': 30},
                    'order': 9
                },
                {
                    'code': 'EVIDENCE_REQUIRED',
                    'name': 'Evidence Check',
                    'description': 'Bonus for including evidence with report',
                    'weight': 5,
                    'config': {'bonus_for_evidence': True},
                    'order': 10
                }
            ]
            
            for rule_data in rules_data:
                rule = VerificationRule(
                    rule_code=rule_data['code'],
                    rule_name=rule_data['name'],
                    description=rule_data['description'],
                    weight=rule_data['weight'],
                    rule_config=rule_data['config'],
                    execution_order=rule_data['order'],
                    is_active=True
                )
                db.session.add(rule)
            
            db.session.commit()
            print(f"✓ Created {len(rules_data)} verification rules")
        
        # ==================== POLICE USERS ====================
        print("\n--- Seeding Police Users ---")
        
        if PoliceUser.query.count() == 0:
            users_data = [
                {
                    'email': 'admin@rnp.gov.rw',
                    'first_name': 'System',
                    'last_name': 'Administrator',
                    'phone': '+250788000001',
                    'badge_number': 'RNP-ADMIN-001',
                    'rank': 'Commissioner',
                    'role': 'super_admin',
                    'permissions': ['all']
                },
                {
                    'email': 'commander@rnp.gov.rw',
                    'first_name': 'Jean',
                    'last_name': 'Habimana',
                    'phone': '+250788000002',
                    'badge_number': 'RNP-CMD-001',
                    'rank': 'Superintendent',
                    'role': 'commander',
                    'permissions': ['view_reports', 'manage_reports', 'view_analytics', 'manage_officers']
                },
                {
                    'email': 'officer@rnp.gov.rw',
                    'first_name': 'Marie',
                    'last_name': 'Uwimana',
                    'phone': '+250788000003',
                    'badge_number': 'RNP-OFF-001',
                    'rank': 'Inspector',
                    'role': 'officer',
                    'permissions': ['view_reports', 'update_reports', 'view_analytics']
                },
                {
                    'email': 'analyst@rnp.gov.rw',
                    'first_name': 'Claude',
                    'last_name': 'Mugisha',
                    'phone': '+250788000004',
                    'badge_number': 'RNP-ANL-001',
                    'rank': 'Analyst',
                    'role': 'analyst',
                    'permissions': ['view_reports', 'view_analytics', 'export_data']
                }
            ]
            
            gasabo = District.query.filter_by(district_code='GS').first()
            
            for user_data in users_data:
                user = PoliceUser(
                    email=user_data['email'],
                    password_hash=generate_password_hash('password123'),
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    phone_number=user_data['phone'],
                    badge_number=user_data['badge_number'],
                    rank=user_data['rank'],
                    role=user_data['role'],
                    permissions=user_data['permissions'],
                    assigned_district_id=gasabo.district_id if gasabo else None,
                    is_active=True
                )
                db.session.add(user)
            
            db.session.commit()
            print(f"✓ Created {len(users_data)} police users (password: password123)")
        
        # ==================== SYSTEM SETTINGS ====================
        print("\n--- Seeding System Settings ---")
        
        if SystemSetting.query.count() == 0:
            settings_data = [
                # General
                {'key': 'app_name', 'value': 'TrustBond', 'type': 'string', 'category': 'general'},
                {'key': 'app_version', 'value': '2.0.0', 'type': 'string', 'category': 'general'},
                {'key': 'maintenance_mode', 'value': 'false', 'type': 'boolean', 'category': 'general'},
                
                # Verification
                {'key': 'min_trust_score', 'value': '30', 'type': 'integer', 'category': 'verification'},
                {'key': 'auto_verify_threshold', 'value': '80', 'type': 'integer', 'category': 'verification'},
                {'key': 'max_reports_per_hour', 'value': '5', 'type': 'integer', 'category': 'verification'},
                
                # Hotspots
                {'key': 'hotspot_min_reports', 'value': '3', 'type': 'integer', 'category': 'hotspots'},
                {'key': 'hotspot_radius_meters', 'value': '500', 'type': 'integer', 'category': 'hotspots'},
                {'key': 'hotspot_time_window_days', 'value': '30', 'type': 'integer', 'category': 'hotspots'},
                
                # Notifications
                {'key': 'enable_push_notifications', 'value': 'true', 'type': 'boolean', 'category': 'notifications'},
                {'key': 'notification_retention_days', 'value': '90', 'type': 'integer', 'category': 'notifications'},
                
                # Privacy
                {'key': 'data_retention_days', 'value': '365', 'type': 'integer', 'category': 'privacy'},
                {'key': 'anonymize_after_days', 'value': '180', 'type': 'integer', 'category': 'privacy'},
                
                # API
                {'key': 'api_rate_limit', 'value': '100', 'type': 'integer', 'category': 'api'},
                {'key': 'api_rate_window_seconds', 'value': '60', 'type': 'integer', 'category': 'api'}
            ]
            
            for setting_data in settings_data:
                setting = SystemSetting(
                    setting_key=setting_data['key'],
                    setting_value=setting_data['value'],
                    value_type=setting_data['type'],
                    category=setting_data['category']
                )
                db.session.add(setting)
            
            db.session.commit()
            print(f"✓ Created {len(settings_data)} system settings")
        
        # ==================== SAMPLE DEVICES ====================
        print("\n--- Seeding Sample Devices ---")
        
        if Device.query.count() == 0:
            devices_data = []
            for i in range(5):
                device = Device(
                    device_fingerprint=f'device_fingerprint_{i+1}_{uuid.uuid4().hex[:8]}',
                    platform='android' if i % 2 == 0 else 'ios',
                    os_version=f'14.{i}',
                    app_version='2.0.0',
                    manufacturer='Samsung' if i % 2 == 0 else 'Apple',
                    model=f'Galaxy S{20+i}' if i % 2 == 0 else f'iPhone {12+i}',
                    trust_score=random.randint(50, 95),
                    total_reports=random.randint(0, 20),
                    verified_reports=random.randint(0, 15),
                    is_blocked=False
                )
                db.session.add(device)
                devices_data.append(device)
            
            db.session.commit()
            print(f"✓ Created {len(devices_data)} sample devices")
        
        # ==================== SAMPLE INCIDENTS ====================
        print("\n--- Seeding Sample Incident Reports ---")
        
        if IncidentReport.query.count() == 0:
            devices = Device.query.all()
            incident_types = IncidentType.query.all()
            
            if devices and incident_types:
                reports_data = []
                for i in range(10):
                    device = random.choice(devices)
                    inc_type = random.choice(incident_types)
                    
                    # Random location in Kigali
                    lat = -1.94 + (random.random() - 0.5) * 0.1
                    lng = 30.06 + (random.random() - 0.5) * 0.1
                    
                    report = IncidentReport(
                        device_id=device.device_id,
                        incident_type_id=inc_type.type_id,
                        tracking_code=f'TRK-{uuid.uuid4().hex[:8].upper()}',
                        description=f'Sample incident report #{i+1}. This is a test report for development purposes.',
                        latitude=lat,
                        longitude=lng,
                        location_accuracy=random.uniform(5, 50),
                        incident_datetime=datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
                        status='pending' if i % 3 == 0 else ('verified' if i % 3 == 1 else 'investigating'),
                        trust_score=random.randint(40, 95),
                        is_anonymous=True
                    )
                    db.session.add(report)
                    reports_data.append(report)
                
                db.session.commit()
                print(f"✓ Created {len(reports_data)} sample incident reports")
        
        # ==================== SAMPLE HOTSPOTS ====================
        print("\n--- Seeding Sample Hotspots ---")
        
        if Hotspot.query.count() == 0:
            gasabo = District.query.filter_by(district_code='GS').first()
            if gasabo:
                hotspots_data = [
                    {
                        'lat': -1.9403,
                        'lng': 30.0978,
                        'name': 'Remera Bus Park Area',
                        'severity': 'medium',
                        'count': 8
                    },
                    {
                        'lat': -1.9520,
                        'lng': 30.0920,
                        'name': 'Kimironko Market',
                        'severity': 'high',
                        'count': 15
                    },
                    {
                        'lat': -1.9350,
                        'lng': 30.1050,
                        'name': 'Gisozi Memorial Area',
                        'severity': 'low',
                        'count': 3
                    }
                ]
                
                for hs_data in hotspots_data:
                    hotspot = Hotspot(
                        district_id=gasabo.district_id,
                        centroid_latitude=hs_data['lat'],
                        centroid_longitude=hs_data['lng'],
                        radius_meters=500,
                        report_count=hs_data['count'],
                        severity_level=hs_data['severity'],
                        status='active',
                        detected_at=datetime.utcnow() - timedelta(days=random.randint(1, 7))
                    )
                    db.session.add(hotspot)
                
                db.session.commit()
                print(f"✓ Created {len(hotspots_data)} sample hotspots")
        
        # ==================== ML MODEL ====================
        print("\n--- Seeding ML Model ---")
        
        if MLModel.query.count() == 0:
            model = MLModel(
                model_name='TrustScorer',
                model_type='trust_scoring',
                version='1.0.0',
                description='Machine learning model for trust score prediction',
                algorithm='RandomForest',
                hyperparameters={
                    'n_estimators': 100,
                    'max_depth': 10,
                    'min_samples_split': 5
                },
                feature_names=[
                    'device_age_days', 'total_reports', 'verified_ratio',
                    'location_consistency', 'time_consistency', 'description_quality'
                ],
                training_samples=1000,
                accuracy_score=0.87,
                is_active=True
            )
            db.session.add(model)
            db.session.commit()
            print("✓ Created ML model configuration")
        
        # ==================== API KEY ====================
        print("\n--- Seeding API Key ---")
        
        if APIKey.query.count() == 0:
            api_key = APIKey(
                key_name='Mobile App Production',
                api_key=f'tb_prod_{uuid.uuid4().hex}',
                key_type='mobile',
                permissions=['submit_report', 'track_report', 'view_public_data'],
                rate_limit=100,
                is_active=True
            )
            db.session.add(api_key)
            db.session.commit()
            print(f"✓ Created API key: {api_key.api_key}")
        
        # ==================== SUMMARY ====================
        print("\n" + "=" * 70)
        print("SEEDING COMPLETE - SUMMARY")
        print("=" * 70)
        print(f"Provinces: {Province.query.count()}")
        print(f"Districts: {District.query.count()}")
        print(f"Sectors: {Sector.query.count()}")
        print(f"Incident Categories: {IncidentCategory.query.count()}")
        print(f"Incident Types: {IncidentType.query.count()}")
        print(f"Verification Rules: {VerificationRule.query.count()}")
        print(f"Police Users: {PoliceUser.query.count()}")
        print(f"System Settings: {SystemSetting.query.count()}")
        print(f"Devices: {Device.query.count()}")
        print(f"Incident Reports: {IncidentReport.query.count()}")
        print(f"Hotspots: {Hotspot.query.count()}")
        print(f"ML Models: {MLModel.query.count()}")
        print(f"API Keys: {APIKey.query.count()}")
        print("=" * 70)
        print("\nDefault Login Credentials:")
        print("  Email: admin@rnp.gov.rw")
        print("  Password: password123")
        print("=" * 70)


if __name__ == '__main__':
    seed_database()
