"""Police user endpoints — officer management with role-based access."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_police_users():
    """List officers, filterable by role and assigned_location_id."""
    # TODO: paginated list from police_users
    pass


@router.post("/")
async def create_police_user():
    """Admin creates officer (first_name, last_name, email, phone, badge_number, role, assigned_location_id)."""
    # TODO: admin-only, hash password
    pass


@router.get("/{police_user_id}")
async def get_police_user(police_user_id: int):
    """Get single officer detail."""
    pass


@router.patch("/{police_user_id}")
async def update_police_user(police_user_id: int):
    """Update officer details, toggle is_active."""
    pass
