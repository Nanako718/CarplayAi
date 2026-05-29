"""
用户相关API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.user import UserProfileUpdate, UserResponse
from app.services.schedule_service import ScheduleService
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/user", tags=["用户"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    获取用户资料

    返回：
    - 用户信息
    """
    return UserResponse.from_orm(current_user)


@router.put("/profile", response_model=ApiResponse)
async def update_profile(
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新用户资料

    参数：
    - nickname: 昵称

    返回：
    - 更新结果
    """
    if data.nickname:
        current_user.nickname = data.nickname
        db.commit()
        db.refresh(current_user)

    return ApiResponse(
        code=0, message="更新成功", data=UserResponse.from_orm(current_user)
    )


@router.get("/schedule", response_model=ApiResponse)
async def get_schedule(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    获取用户班制信息（自动学习）

    返回：
    - 班制类型
    - 典型出发时间
    - 置信度
    """
    schedule_service = ScheduleService(db)
    schedule = schedule_service.get_user_schedule(current_user.id)

    return ApiResponse(code=0, message="success", data=schedule)
