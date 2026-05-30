"""
事件相关Schema
"""

import re
from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator


def parse_number(value: Union[str, float, int, None]) -> Optional[float]:
    """解析数字，支持带单位的字符串如 '32°C', '15度'"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # 提取数字部分
        match = re.search(r"-?\d+\.?\d*", value)
        if match:
            return float(match.group())
    return None


class WeatherData(BaseModel):
    """天气数据"""

    condition: Optional[str] = Field(None, description="天气状况")
    temp_high: Optional[Union[float, str]] = Field(None, description="最高温")
    temp_low: Optional[Union[float, str]] = Field(None, description="最低温")
    precipitation_prob: Optional[Union[float, str]] = Field(
        None, description="降水概率"
    )

    @field_validator("temp_high", "temp_low", "precipitation_prob", mode="before")
    @classmethod
    def parse_temp(cls, v):
        """解析温度，支持 '32°C' 格式"""
        return parse_number(v)


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
