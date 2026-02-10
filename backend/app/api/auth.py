"""Authentication endpoints — JWT login for police_users."""

from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


@router.post("/login")
async def login():
    """Authenticate police officer and return JWT token."""
    # TODO: implement JWT login against police_users table
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")


@router.post("/refresh")
async def refresh_token():
    """Refresh an expiring JWT token."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")
