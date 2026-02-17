"""Device endpoints — pseudonymous device registration & trust scores."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.device import DeviceCreate, DeviceResponse
from app.services.device_service import DeviceService

router = APIRouter()


@router.post("/register", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
):
    """Register a new anonymous device via SHA-256 hash, or return existing."""
    device = DeviceService.get_or_create(db, data.device_hash)
    return device


@router.get("/{device_hash}", response_model=DeviceResponse)
async def get_device(
    device_hash: str,
    db: Session = Depends(get_db),
):
    """Retrieve device record with trust score and report counts."""
    device = DeviceService.get_by_hash(db, device_hash)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )
    return device
