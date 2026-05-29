"""
认证相关API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from app.utils.auth import (create_access_token, get_password_hash,
                            verify_password)

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册

    参数：
    - username: 用户名（3-50字符）
    - password: 密码（6-100字符）
    - nickname: 昵称（可选）

    返回：
    - access_token: JWT Token
    - user_id: 用户ID
    """
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
        )

    # 创建用户
    user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        nickname=user_data.nickname or f"用户_{user_data.username}",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 生成Token
    token = create_access_token({"user_id": user.id})

    return TokenResponse(access_token=token, user_id=user.id)


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录

    参数：
    - username: 用户名
    - password: 密码

    返回：
    - access_token: JWT Token
    - user_id: 用户ID
    """
    # 查询用户
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    # 生成Token
    token = create_access_token({"user_id": user.id})

    return TokenResponse(access_token=token, user_id=user.id)
