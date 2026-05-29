"""
位置相关API
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.location import (LocationConfirm, LocationRename,
                                  LocationResponse, PendingLocationsResponse)
from app.schemas.response import ApiResponse
from app.services.location_service import LocationService
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/locations", tags=["位置"])


@router.get("", response_model=ApiResponse)
async def get_locations(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    获取用户所有位置

    返回：
    - 位置列表（家、工作地点等）
    """
    location_service = LocationService(db)
    locations = location_service.get_user_locations(current_user.id)

    return ApiResponse(
        code=0,
        message="success",
        data=[LocationResponse.from_orm(loc) for loc in locations],
    )


@router.get("/pending", response_model=PendingLocationsResponse)
async def get_pending_locations(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    获取待确认的位置

    返回：
    - 待确认位置列表
    """
    location_service = LocationService(db)
    locations = location_service.get_pending_locations(current_user.id)

    return PendingLocationsResponse(
        pending_locations=[LocationResponse.from_orm(loc) for loc in locations]
    )


@router.post("/confirm", response_model=ApiResponse)
async def confirm_location(
    data: LocationConfirm,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    确认位置

    参数：
    - location_id: 位置ID

    返回：
    - 确认结果
    """
    location_service = LocationService(db)
    location = location_service.confirm_location(data.location_id, current_user.id)

    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="位置不存在")

    return ApiResponse(
        code=0, message="确认成功", data=LocationResponse.from_orm(location)
    )


@router.post("/rename", response_model=ApiResponse)
async def rename_location(
    data: LocationRename,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    重命名位置

    参数：
    - location_id: 位置ID
    - name: 新名称

    返回：
    - 重命名结果
    """
    location_service = LocationService(db)
    location = location_service.rename_location(
        data.location_id, current_user.id, data.name
    )

    if not location:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="位置不存在")

    return ApiResponse(
        code=0, message="重命名成功", data=LocationResponse.from_orm(location)
    )
