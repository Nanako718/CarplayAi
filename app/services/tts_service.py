"""
TTS语音合成服务模块（字节跳动）
"""
import json
import base64
import httpx
from typing import Optional
from app.config import settings

import logging

logger = logging.getLogger(__name__)


class TTSService:
    """TTS语音合成服务 - 字节跳动"""

    def __init__(self):
        self.app_id = settings.TTS_APP_ID
        self.access_key = settings.TTS_ACCESS_KEY
        self.resource_id = settings.TTS_RESOURCE_ID
        self.endpoint = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
        self.default_voice = settings.TTS_DEFAULT_VOICE

        # 音色配置
        self.voices = {
            'cancan': 'zh_female_cancan_mars_bigtts',  # 灿灿（女声，活泼）
            'default': self.default_voice,
        }

    async def synthesize_to_stream(
        self,
        text: str,
        voice: str = 'default'
    ) -> Optional[bytes]:
        """
        文本转语音 - 返回音频二进制数据

        参数：
        - text: 要合成的文本
        - voice: 音色

        返回：
        - 音频二进制数据 或 None

        特点：
        - HTTP Chunked流式返回
        - 不存储音频文件
        - 直接返回给客户端播放
        - 用完即销毁
        """
        try:
            # 构建请求头
            headers = {
                "X-Api-App-Id": self.app_id,
                "X-Api-Access-Key": self.access_key,
                "X-Api-Resource-Id": self.resource_id,
                "Content-Type": "application/json",
                "Connection": "keep-alive"
            }

            # 构建请求体
            payload = {
                "user": {
                    "uid": "carplay_user"
                },
                "req_params": {
                    "text": text,
                    "speaker": self.voices.get(voice, self.voices['default']),
                    "audio_params": {
                        "format": "mp3",
                        "sample_rate": 24000
                    }
                }
            }

            # 调用TTS API（HTTP Chunked流式）
            audio_data = await self._call_tts_api(headers, payload)

            return audio_data

        except Exception as e:
            logger.error(f"TTS调用异常：{e}")
            return None

    async def _call_tts_api(
        self,
        headers: dict,
        payload: dict
    ) -> Optional[bytes]:
        """调用字节跳动TTS API（HTTP Chunked流式）"""
        audio_data = bytearray()

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=30.0
            ) as response:
                if response.status_code != 200:
                    logger.error(f"TTS API错误：{response.status_code}")
                    return None

                # 解析HTTP Chunked流
                async for line in response.aiter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # 成功响应（音频数据）
                        if data.get("code", 0) == 0 and "data" in data and data["data"]:
                            chunk = base64.b64decode(data["data"])
                            audio_data.extend(chunk)
                            continue

                        # 文本响应（时间戳）
                        if data.get("code", 0) == 0 and "sentence" in data and data["sentence"]:
                            logger.debug(f"句子数据：{data}")
                            continue

                        # 完成响应
                        if data.get("code", 0) == 20000000:
                            if 'usage' in data:
                                logger.info(f"用量：{data['usage']}")
                            break

                        # 错误响应
                        if data.get("code", 0) > 0:
                            logger.error(f"TTS错误：{data}")
                            return None

                    except json.JSONDecodeError:
                        continue

        return bytes(audio_data) if audio_data else None
