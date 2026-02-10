"""Device endpoints — pseudonymous device registration & trust scores."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register_device():
    """Register a new anonymous device via SHA-256 hash."""
    # TODO: create or return existing device record by device_hash
    pass


@router.get("/{device_hash}")
async def get_device(device_hash: str):
    """Retrieve device record with trust score and report counts."""
    # TODO: query devices table by device_hash
    pass
