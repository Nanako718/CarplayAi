"""
通用响应Schema
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """通用API响应"""

    code: int = Field(0, description="状态码: 0=成功")
    message: str = Field("success", description="消息")
    data: Optional[Any] = Field(None, description="数据")


class BroadcastResponse(BaseModel):
    """播报响应"""

    broadcast_text: str = Field(..., description="播报文本")
    scene: str = Field(..., description="场景类型")
    is_fallback: bool = Field(False, description="是否降级")
    latency: Optional[float] = Field(None, description="响应时间(秒)")
