"""
用户作息模型
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class UserSchedule(Base):
    """用户作息表（用于班制学习）"""

    __tablename__ = "user_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False)  # 日期

    depart_time = Column(DateTime, nullable=True)  # 从家出发时间
    arrive_time = Column(DateTime, nullable=True)  # 到达工作地时间
    leave_time = Column(DateTime, nullable=True)  # 离开工作地时间
    return_time = Column(DateTime, nullable=True)  # 到家时间

    work_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # 关联
    user = relationship("User", back_populates="schedules")
    work_location = relationship("Location")

    def __repr__(self):
        return f"<UserSchedule(id={self.id}, date='{self.date}')>"
