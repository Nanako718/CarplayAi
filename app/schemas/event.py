"""
事件相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WeatherData(BaseModel):
    """天气数据"""
    condition: Optional[str] = Field(None, description="天气状况")
    temp_high: Optional[float] = Field(None, description="最高温")
    temp_low: Optional[float] = Field(None, description="最低温")
    precipitation_prob: Optional[float] = Field(None, description="降水概率")


class EventCreate(BaseModel):
    """事件创建"""
    event_type: str = Field(..., description="事件类型: connect/disconnect")
    latitude: float = Field(..., description="纬度")
    longitude: float = Field(..., description="经度")
    address: Optional[str] = Field(None, description="地址")
    weather: Optional[WeatherData] = Field(None, description="天气信息")
    timestamp: Optional[datetime] = Field(None, description="事件时间")


class EventResponse(BaseModel):
    """事件响应"""
    id: int
    event_type: str
    latitude: float
    longitude: float
    address: Optional[str]
    weather_condition: Optional[str]
    temperature_high: Optional[float]
    temperature_low: Optional[float]
    precipitation_prob: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
