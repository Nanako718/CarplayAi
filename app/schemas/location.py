"""
位置相关Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LocationResponse(BaseModel):
    """位置响应"""

    id: int
    location_type: str
    name: Optional[str]
    latitude: float
    longitude: float
    address: Optional[str]
    confidence: float
    is_confirmed: bool
    visit_count: int
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]

    class Config:
        from_attributes = True


class LocationConfirm(BaseModel):
    """位置确认"""

    location_id: int = Field(..., description="位置ID")


class LocationRename(BaseModel):
    """位置重命名"""

    location_id: int = Field(..., description="位置ID")
    name: str = Field(..., min_length=1, max_length=50, description="新名称")


class PendingLocationsResponse(BaseModel):
    """待确认位置响应"""

    pending_locations: list[LocationResponse]
