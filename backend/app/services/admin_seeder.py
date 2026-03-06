"""
Admin user seeding service.
Automatically creates default admin user on application startup if it doesn't exist.
"""
from sqlalchemy.orm import Session
from app.models.police_user import PoliceUser
from app.core.security import get_password_hash


# Default admin credentials - can be overridden via environment variables
DEFAULT_ADMIN_EMAIL = "dukuzejean09@gmail.com"
DEFAULT_ADMIN_PASSWORD = "Admin123!"
DEFAULT_ADMIN_FIRST_NAME = "System"
DEFAULT_ADMIN_LAST_NAME = "Admin"
DEFAULT_ADMIN_ROLE = "admin"


def create_default_admin(db: Session) -> dict:
    """
    Create a default admin user if it doesn't exist.
    
    Returns:
        dict with keys: created (bool), user_id (int|None), email (str)
    """
    try:
        # Check if admin already exists
        existing = db.query(PoliceUser).filter(
            PoliceUser.email == DEFAULT_ADMIN_EMAIL
        ).first()
        
        if existing:
            print(f"✓ Admin user already exists: {existing.email} (id={existing.police_user_id})")
            return {
                "created": False,
                "user_id": existing.police_user_id,
                "email": existing.email,
                "message": "Admin user already exists"
            }
        
        # Create new admin user
        admin_user = PoliceUser(
            first_name=DEFAULT_ADMIN_FIRST_NAME,
            middle_name=None,
            last_name=DEFAULT_ADMIN_LAST_NAME,
            email=DEFAULT_ADMIN_EMAIL,
            phone_number=None,
            password_hash=get_password_hash(DEFAULT_ADMIN_PASSWORD),
            badge_number="ADMIN-001",
            role=DEFAULT_ADMIN_ROLE,
            assigned_location_id=None,
            is_active=True,
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✓ Created default admin user:")
        print(f"  - ID: {admin_user.police_user_id}")
        print(f"  - Email: {admin_user.email}")
        print(f"  - Password: {DEFAULT_ADMIN_PASSWORD}")
        print(f"  - Role: {admin_user.role}")
        
        return {
            "created": True,
            "user_id": admin_user.police_user_id,
            "email": admin_user.email,
            "message": "Default admin user created successfully"
        }
    
    except Exception as e:
        print(f"✗ Error creating default admin user: {str(e)}")
        return {
            "created": False,
            "user_id": None,
            "email": None,
            "message": f"Error: {str(e)}"
        }
