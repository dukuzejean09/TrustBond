from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal


class IncidentTypeCreate(BaseModel):
    type_name: str
    description: Optional[str] = None
    severity_weight: Optional[Decimal] = Decimal("1.00")
    is_active: bool = True


class IncidentTypeUpdate(BaseModel):
    type_name: Optional[str] = None
    description: Optional[str] = None
    severity_weight: Optional[Decimal] = None
    is_active: Optional[bool] = None


class IncidentTypeResponse(BaseModel):
    incident_type_id: int
    type_name: str
    description: Optional[str]
    severity_weight: Decimal
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
