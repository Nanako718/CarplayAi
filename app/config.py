"""
配置管理模块
从 .env 文件加载配置
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "CarPlay AI Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development / production
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./carplay.db"

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # AI配置（小米 MiMo）
    MIMO_API_KEY: str = ""
    MIMO_BASE_URL: str = "https://api.xiaomimimo.com/v1"
    MIMO_MODEL: str = "mimo-v2.5-pro"

    # TTS配置（字节跳动）
    TTS_APP_ID: str = ""
    TTS_ACCESS_KEY: str = ""
    TTS_RESOURCE_ID: str = "seed-tts-2.0"
    TTS_DEFAULT_VOICE: str = "zh_female_cancan_mars_bigtts"

    # 位置聚合配置
    LOCATION_CLUSTER_RADIUS: int = 200  # 米
    LOCATION_CONFIDENCE_THRESHOLD: float = 0.7

    # 播报配置
    MAX_BROADCAST_LENGTH: int = 100  # 字符
    AI_TIMEOUT: float = 3.0  # 秒

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
