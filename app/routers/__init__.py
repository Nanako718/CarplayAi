"""
API路由模块
"""

from app.routers.auth import router as auth_router
from app.routers.events import router as events_router
from app.routers.locations import router as locations_router
from app.routers.user import router as user_router

__all__ = ["auth_router", "events_router", "locations_router", "user_router"]
