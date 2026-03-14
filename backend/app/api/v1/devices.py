from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4, UUID
from app.database import get_db
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceResponse

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/register", response_model=DeviceResponse)
def register_device(device_data: DeviceCreate, db: Session = Depends(get_db)):
    """Register or get existing device by hash. Returns existing device if already registered.
    A trust score of 50.00 is assigned at first registration."""
    device = db.query(Device).filter(Device.device_hash == device_data.device_hash).first()

    if device:
        return device

    new_device = Device(
        device_id=uuid4(),
        device_hash=device_data.device_hash,
        device_trust_score=50.00,  # initial score assigned at registration
    )
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    return new_device


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: UUID, db: Session = Depends(get_db)):
    """Get device stats including current trust score (anonymous lookup by device UUID)."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device
