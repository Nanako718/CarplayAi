"""
位置模型
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Location(Base):
    """位置表（支持多工作地点）"""

    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_type = Column(String, nullable=False)  # home / work
    name = Column(String, nullable=True)  # 用户命名，如"饭店"、"KTV"

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String, nullable=True)

    confidence = Column(Float, default=0.0)  # 置信度
    is_confirmed = Column(Boolean, default=False)  # 是否已确认
    visit_count = Column(Integer, default=0)  # 访问次数

    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联
    user = relationship("User", back_populates="locations")

    def __repr__(self):
        return (
            f"<Location(id={self.id}, type='{self.location_type}', name='{self.name}')>"
        )
