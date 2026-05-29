"""
事件模型
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Event(Base):
    """事件表（CarPlay连接/断开）"""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String, nullable=False)  # connect / disconnect

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String, nullable=True)

    # 关联位置（出发地/目的地）
    from_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    to_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)

    # 天气信息
    weather_condition = Column(String, nullable=True)
    temperature_high = Column(Float, nullable=True)
    temperature_low = Column(Float, nullable=True)
    precipitation_prob = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.now)

    # 关联
    user = relationship("User", back_populates="events")
    from_location = relationship("Location", foreign_keys=[from_location_id])
    to_location = relationship("Location", foreign_keys=[to_location_id])

    def __repr__(self):
        return f"<Event(id={self.id}, type='{self.event_type}')>"
