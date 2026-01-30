"""Seed script to create default admin user and sample data"""
from app import create_app, db
from app.models import (
    User, UserRole, UserStatus, 
    Report, CrimeCategory, ReportStatus, ReportPriority, 
    Alert, AlertType, AlertStatus,
    DeviceProfile, TrustScore, TrustClassification, VerificationStatus,
    Hotspot, HotspotSeverity, HotspotStatus,
    Notification, NotificationType, NotificationPriority,
    ActivityLog, ActivityType
)
from datetime import datetime, timedelta
import random

app = create_app()

def seed_database():
    with app.app_context():
        # Create tables
        db.create_all()
        
        print("=" * 60)
        print("TrustBond Database Seeding")
        print("=" * 60)
        
        # ==================== USERS ====================
        
        # Check if admin exists
        admin = User.query.filter_by(email='admin@rnp.gov.rw').first()
        if not admin:
            admin = User(
                email='admin@rnp.gov.rw',
                first_name='System',
                last_name='Administrator',
                phone='+250788000001',
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("✓ Created admin user: admin@rnp.gov.rw / admin123")
        
        # Create multiple officers for different districts
        officers_data = [
            {
                'email': 'officer@rnp.gov.rw',
                'first_name': 'John',
                'last_name': 'Mugabo',
                'phone': '+250788000002',
                'badge_number': 'RNP-001',
                'station': 'Kigali Central Station',
                'rank': 'Inspector',
                'district': 'Gasabo'
            },
            {
                'email': 'officer2@rnp.gov.rw',
                'first_name': 'Alice',
                'last_name': 'Mukamana',
                'phone': '+250788000004',
                'badge_number': 'RNP-002',
                'station': 'Musanze Police Station',
                'rank': 'Sergeant',
                'district': 'Musanze'
            },
            {
                'email': 'officer3@rnp.gov.rw',
                'first_name': 'Pierre',
                'last_name': 'Habimana',
                'phone': '+250788000005',
                'badge_number': 'RNP-003',
                'station': 'Rubavu Police Station',
                'rank': 'Inspector',
                'district': 'Rubavu'
            }
        ]
        
        officers = []
        for officer_data in officers_data:
            officer = User.query.filter_by(email=officer_data['email']).first()
            if not officer:
                officer = User(
                    email=officer_data['email'],
                    first_name=officer_data['first_name'],
                    last_name=officer_data['last_name'],
                    phone=officer_data['phone'],
                    badge_number=officer_data['badge_number'],
                    station=officer_data['station'],
                    rank=officer_data['rank'],
                    district=officer_data.get('district'),
                    role=UserRole.OFFICER,
                    status=UserStatus.ACTIVE
                )
                officer.set_password('officer123')
                db.session.add(officer)
                print(f"✓ Created officer: {officer_data['email']} / officer123")
            officers.append(officer)
        
        # Create sample citizen
        citizen = User.query.filter_by(email='citizen@example.com').first()
        if not citizen:
            citizen = User(
                email='citizen@example.com',
                first_name='Marie',
                last_name='Uwimana',
                phone='+250788000003',
                national_id='1199080000000000',
                province='Kigali City',
                district='Gasabo',
                sector='Kimironko',
                role=UserRole.CITIZEN,
                status=UserStatus.ACTIVE
            )
            citizen.set_password('citizen123')
            db.session.add(citizen)
            print("✓ Created citizen user: citizen@example.com / citizen123")
        
        db.session.commit()
        
        # ==================== SAMPLE REPORTS ====================
        
        # Refresh users from DB
        admin = User.query.filter_by(email='admin@rnp.gov.rw').first()
        citizen = User.query.filter_by(email='citizen@example.com').first()
        officer = User.query.filter_by(email='officer@rnp.gov.rw').first()
        
        if Report.query.count() < 10:
            # Rwanda districts with coordinates
            locations = [
                {'district': 'Gasabo', 'sector': 'Kimironko', 'lat': -1.9403, 'lng': 30.1044},
                {'district': 'Gasabo', 'sector': 'Remera', 'lat': -1.9536, 'lng': 30.1106},
                {'district': 'Kicukiro', 'sector': 'Gikondo', 'lat': -1.9706, 'lng': 30.0719},
                {'district': 'Nyarugenge', 'sector': 'Nyamirambo', 'lat': -1.9761, 'lng': 30.0456},
                {'district': 'Musanze', 'sector': 'Muhoza', 'lat': -1.4997, 'lng': 29.6350},
                {'district': 'Rubavu', 'sector': 'Gisenyi', 'lat': -1.6810, 'lng': 29.2592},
                {'district': 'Huye', 'sector': 'Ngoma', 'lat': -2.5966, 'lng': 29.7394}
            ]
            
            sample_reports = [
                {
                    'title': 'Phone Theft at Bus Station',
                    'description': 'My phone was stolen while waiting for a bus at Nyabugogo station. The thief ran towards the market area.',
                    'category': CrimeCategory.THEFT,
                    'status': ReportStatus.INVESTIGATING,
                    'priority': ReportPriority.MEDIUM,
                    'days_ago': 2
                },
                {
                    'title': 'Suspicious Activity Near School',
                    'description': 'Unknown individuals loitering near the primary school during drop-off hours.',
                    'category': CrimeCategory.OTHER,
                    'status': ReportStatus.PENDING,
                    'priority': ReportPriority.HIGH,
                    'days_ago': 1
                },
                {
                    'title': 'Traffic Accident on KN 5 Ave',
                    'description': 'Two vehicles collided near Kigali Convention Center. One person was injured.',
                    'category': CrimeCategory.TRAFFIC_VIOLATION,
                    'status': ReportStatus.RESOLVED,
                    'priority': ReportPriority.HIGH,
                    'resolution_notes': 'Case resolved. Insurance claims processed. Traffic violations issued.',
                    'days_ago': 5
                },
                {
                    'title': 'Vandalism at Community Center',
                    'description': 'Windows broken and graffiti painted on the community center walls overnight.',
                    'category': CrimeCategory.VANDALISM,
                    'status': ReportStatus.UNDER_REVIEW,
                    'priority': ReportPriority.MEDIUM,
                    'days_ago': 3
                },
                {
                    'title': 'Online Fraud Attempt',
                    'description': 'Received suspicious messages asking for bank details claiming to be from a bank.',
                    'category': CrimeCategory.CYBERCRIME,
                    'status': ReportStatus.PENDING,
                    'priority': ReportPriority.MEDIUM,
                    'days_ago': 0
                },
                {
                    'title': 'Domestic Dispute',
                    'description': 'Loud argument heard from neighboring house, concerns about safety.',
                    'category': CrimeCategory.DOMESTIC_VIOLENCE,
                    'status': ReportStatus.INVESTIGATING,
                    'priority': ReportPriority.CRITICAL,
                    'days_ago': 1
                },
                {
                    'title': 'Robbery at Store',
                    'description': 'Armed robbery at a convenience store. Suspects fled on motorcycle.',
                    'category': CrimeCategory.ROBBERY,
                    'status': ReportStatus.INVESTIGATING,
                    'priority': ReportPriority.CRITICAL,
                    'days_ago': 4
                },
                {
                    'title': 'Drug Activity Suspected',
                    'description': 'Suspicious activity observed behind the shopping complex, possible drug dealing.',
                    'category': CrimeCategory.DRUG_RELATED,
                    'status': ReportStatus.UNDER_REVIEW,
                    'priority': ReportPriority.HIGH,
                    'days_ago': 6
                }
            ]
            
            for i, report_data in enumerate(sample_reports):
                location = random.choice(locations)
                is_anonymous = random.choice([True, False])
                
                report = Report(
                    report_number=f'RNP-2026-{10001 + i}',
                    title=report_data['title'],
                    description=report_data['description'],
                    category=report_data['category'],
                    status=report_data['status'],
                    priority=report_data['priority'],
                    province='Kigali City' if location['district'] in ['Gasabo', 'Kicukiro', 'Nyarugenge'] else 'Northern Province' if location['district'] == 'Musanze' else 'Western Province',
                    district=location['district'],
                    sector=location['sector'],
                    latitude=location['lat'] + random.uniform(-0.01, 0.01),
                    longitude=location['lng'] + random.uniform(-0.01, 0.01),
                    reporter_id=None if is_anonymous else citizen.id,
                    is_anonymous=is_anonymous,
                    tracking_code=f'ANON-{random.randint(10000, 99999)}' if is_anonymous else None,
                    assigned_to=officer.id if report_data['status'] in [ReportStatus.INVESTIGATING, ReportStatus.UNDER_REVIEW] else None,
                    resolution_notes=report_data.get('resolution_notes'),
                    created_at=datetime.utcnow() - timedelta(days=report_data['days_ago'])
                )
                
                if report_data['status'] == ReportStatus.RESOLVED:
                    report.resolved_at = datetime.utcnow() - timedelta(days=report_data['days_ago'] - 2)
                
                db.session.add(report)
            
            print(f"✓ Created {len(sample_reports)} sample reports")
        
        db.session.commit()
        
        # ==================== ALERTS ====================
        
        if Alert.query.count() == 0:
            alerts = [
                Alert(
                    title='Community Safety Awareness Week',
                    message='Join us for community safety workshops throughout the week. Report any suspicious activities.',
                    alert_type=AlertType.SECURITY,
                    is_nationwide=True,
                    created_by=admin.id
                ),
                Alert(
                    title='Weather Warning - Heavy Rains Expected',
                    message='Heavy rainfall expected in the Northern Province. Exercise caution while driving.',
                    alert_type=AlertType.WEATHER,
                    district='Musanze',
                    is_nationwide=False,
                    created_by=admin.id
                ),
                Alert(
                    title='Missing Person Alert',
                    message='Please help locate missing child. Contact police if you have any information.',
                    alert_type=AlertType.EMERGENCY,
                    is_nationwide=True,
                    created_by=admin.id
                )
            ]
            
            for alert in alerts:
                db.session.add(alert)
            
            print(f"✓ Created {len(alerts)} sample alerts")
        
        # ==================== DEVICE PROFILES ====================
        
        if DeviceProfile.query.count() == 0:
            devices = [
                DeviceProfile(
                    device_fingerprint='a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2',
                    platform='android',
                    app_version='1.0.0',
                    total_reports=5,
                    trusted_reports=4,
                    delayed_reports=1,
                    suspicious_reports=0,
                    trust_score=0.85,
                    typical_latitude=-1.9403,
                    typical_longitude=30.1044
                ),
                DeviceProfile(
                    device_fingerprint='f2e1d0c9b8a7z6y5x4w3v2u1t0s9r8q7p6o5n4m3l2k1j0i9h8g7f6e5d4c3b2a1',
                    platform='ios',
                    app_version='1.0.0',
                    total_reports=3,
                    trusted_reports=3,
                    delayed_reports=0,
                    suspicious_reports=0,
                    trust_score=0.95
                )
            ]
            
            for device in devices:
                db.session.add(device)
            
            print("✓ Created sample device profiles")
        
        db.session.commit()
        
        # ==================== WELCOME NOTIFICATION ====================
        
        if Notification.query.count() == 0:
            notification = Notification(
                title='Welcome to TrustBond',
                message='Thank you for using TrustBond to help keep your community safe.',
                notification_type=NotificationType.SYSTEM_MESSAGE,
                priority=NotificationPriority.MEDIUM,
                is_broadcast=True
            )
            db.session.add(notification)
            print("✓ Created welcome notification")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("✅ Database seeded successfully!")
        print("=" * 60)
        print("\nTest Credentials:")
        print("-" * 40)
        print("Admin:   admin@rnp.gov.rw / admin123")
        print("Officer: officer@rnp.gov.rw / officer123")
        print("Citizen: citizen@example.com / citizen123")
        print("-" * 40)

if __name__ == '__main__':
    seed_database()
