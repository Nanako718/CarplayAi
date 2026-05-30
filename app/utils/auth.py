"""
认证工具函数
"""

from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

# Bearer Token方案
security = HTTPBearer()


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    password_bytes = password.encode("utf-8")[:72]  # bcrypt 限制 72 字节
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    password_bytes = plain_password.encode("utf-8")[:72]
    hash_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hash_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT Token

    参数：
    - data: Token数据
    - expires_delta: 过期时间增量

    返回：
    - JWT Token字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    验证JWT Token

    参数：
    - token: JWT Token字符串

    返回：
    - Token数据 或 None（验证失败）
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    获取当前用户（依赖注入）

    参数：
    - credentials: Bearer Token
    - db: 数据库会话

    返回：
    - User对象

    异常：
    - 401: Token无效或过期
    - 404: 用户不存在
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 验证Token
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception

    # 获取用户ID
    user_id: int = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    # 查询用户
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return user
