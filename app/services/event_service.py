"""
事件服务模块
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.user import User
from app.schemas.event import EventCreate


class EventService:
    """事件服务"""

    def __init__(self, db: Session):
        self.db = db

    def create_event(self, user: User, event_data: EventCreate) -> Event:
        """
        创建事件记录

        参数：
        - user: 用户对象
        - event_data: 事件数据

        返回：
        - Event对象
        """
        event = Event(
            user_id=user.id,
            event_type=event_data.event_type,
            latitude=event_data.latitude,
            longitude=event_data.longitude,
            address=event_data.address,
            weather_condition=(
                event_data.weather.condition if event_data.weather else None
            ),
            temperature_high=(
                event_data.weather.temp_high if event_data.weather else None
            ),
            temperature_low=event_data.weather.temp_low if event_data.weather else None,
            precipitation_prob=(
                event_data.weather.precipitation_prob if event_data.weather else None
            ),
            created_at=event_data.timestamp or datetime.now(),
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return event

    def get_user_events(
        self, user_id: int, event_type: Optional[str] = None, limit: int = 100
    ) -> list[Event]:
        """
        获取用户事件列表

        参数：
        - user_id: 用户ID
        - event_type: 事件类型过滤
        - limit: 返回数量限制

        返回：
        - Event列表
        """
        query = self.db.query(Event).filter(Event.user_id == user_id)

        if event_type:
            query = query.filter(Event.event_type == event_type)

        return query.order_by(Event.created_at.desc()).limit(limit).all()

    def get_recent_events(self, user_id: int, days: int = 30) -> list[Event]:
        """
        获取最近N天的事件

        参数：
        - user_id: 用户ID
        - days: 天数

        返回：
        - Event列表
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)

        return (
            self.db.query(Event)
            .filter(Event.user_id == user_id)
            .filter(Event.created_at >= cutoff)
            .order_by(Event.created_at.desc())
            .all()
        )
