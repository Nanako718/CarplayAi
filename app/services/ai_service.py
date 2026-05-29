"""
AI播报生成服务模块（小米 MiMo）
"""
import asyncio
import os
from typing import Dict, Optional
from datetime import datetime
from openai import OpenAI
from app.config import settings
from app.services.broadcast_service import BroadcastService

import logging

logger = logging.getLogger(__name__)


class AIBroadcastService:
    """AI播报生成服务 - 使用小米 MiMo-v2.5-pro"""

    def __init__(self):
        self.api_key = settings.MIMO_API_KEY
        self.base_url = settings.MIMO_BASE_URL
        self.model = settings.MIMO_MODEL
        self.timeout = settings.AI_TIMEOUT

        # 初始化OpenAI客户端（兼容格式）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # 规则引擎（降级方案）
        self.rule_engine = BroadcastService()

        # 系统Prompt
        self.system_prompt = """你是一个温暖贴心的车载AI助手。你的任务是根据用户当前的场景、天气、时间等信息，生成简短、自然、温暖的播报内容。

要求：
1. 长度控制在30-50字，适合TTS播放（约15秒）
2. 语气自然、亲切、温暖，像朋友一样
3. 结合天气、时间、场景给出实用建议
4. 如果是深夜回家，表达关心和安慰
5. 如果是雨天，提醒带伞或注意安全
6. 避免重复，每次生成不同的表达
7. 不要使用emoji，纯文本输出
8. 直接输出播报内容，不要有其他说明"""

        # 场景描述模板
        self.scene_templates = {
            'commute_to_work': '现在是{time}，用户从家出发去上班，天气{weather}，温度{temp_low}°C~{temp_high}°C，降水概率{precip}%。',
            'normal_leave': '现在是{time}，用户从工作地点下班回家，天气{weather}。',
            'overtime_leave': '现在是{time}，用户加班到很晚才下班，天气{weather}。请表达关心和安慰。',
            'late_night': '现在是{time}，用户深夜还在路上，天气{weather}。请特别关心安全和休息。',
            'weekend_trip': '现在是{time}，周末出行，天气{weather}，温度{temp_low}°C~{temp_high}°C。',
            'irregular_departure': '现在是{time}，用户非正常时间出发，天气{weather}。'
        }

    async def generate_broadcast(
        self,
        user_id: int,
        event: Dict,
        scene: str
    ) -> Optional[str]:
        """
        调用AI生成播报

        参数：
        - user_id: 用户ID
        - event: 事件数据
        - scene: 场景类型

        返回：
        - 成功：播报文本
        - 失败：None（触发降级）
        """
        try:
            # 构建用户消息
            user_message = self._build_user_message(event, scene)

            # 调用AI（带超时）
            response = await asyncio.wait_for(
                self._call_ai(user_message),
                timeout=self.timeout
            )

            return response

        except asyncio.TimeoutError:
            logger.warning(f"AI调用超时，用户{user_id}，场景{scene}")
            return None

        except Exception as e:
            logger.error(f"AI调用失败：{e}")
            return None

    def generate_broadcast_with_fallback(
        self,
        user_id: int,
        event: Dict,
        scene: str
    ) -> tuple[str, bool]:
        """
        生成播报（带降级）

        参数：
        - user_id: 用户ID
        - event: 事件数据
        - scene: 场景类型

        返回：
        - (播报文本, 是否降级)
        """
        # 尝试AI生成
        try:
            loop = asyncio.get_event_loop()
            broadcast_text = loop.run_until_complete(
                self.generate_broadcast(user_id, event, scene)
            )

            if broadcast_text:
                return broadcast_text, False
        except Exception as e:
            logger.error(f"AI调用异常：{e}")

        # 降级到规则引擎
        logger.info(f"降级到规则引擎，用户{user_id}，场景{scene}")
        broadcast_text = self.rule_engine.generate_broadcast(user_id, event, scene)
        return broadcast_text, True

    def _build_user_message(self, event: Dict, scene: str) -> str:
        """构建用户消息"""
        template = self.scene_templates.get(scene, self.scene_templates['irregular_departure'])

        # 基础信息
        created_at = event.get('created_at', datetime.now())
        message = template.format(
            time=created_at.strftime('%Y-%m-%d %H:%M'),
            weather=event.get('weather_condition', '未知'),
            temp_high=event.get('temperature_high', '未知'),
            temp_low=event.get('temperature_low', '未知'),
            precip=event.get('precipitation_prob', '未知')
        )

        # 添加位置信息
        if event.get('address'):
            message += f"位置：{event['address']}。"

        return message

    async def _call_ai(self, user_message: str) -> str:
        """调用小米 MiMo API"""
        # 使用同步客户端在线程池中运行
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=1.0,  # 提高随机性，增加多样性
                top_p=0.95,
                max_tokens=200
            )
        )

        return response.choices[0].message.content.strip()
