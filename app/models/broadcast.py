"""
播报模型
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Broadcast(Base):
    """播报表"""
    __tablename__ = "broadcasts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)

    content_text = Column(String, nullable=False)  # 播报文本

    scene = Column(String, nullable=True)  # 场景类型
    ai_model = Column(String, nullable=True)  # 使用的AI模型
    ai_latency = Column(Float, nullable=True)  # AI响应时间
    is_fallback = Column(Boolean, default=False)  # 是否降级到规则引擎

    created_at = Column(DateTime, default=datetime.now)

    # 关联
    user = relationship("User", back_populates="broadcasts")
    event = relationship("Event")

    def __repr__(self):
        return f"<Broadcast(id={self.id}, scene='{self.scene}')>"
