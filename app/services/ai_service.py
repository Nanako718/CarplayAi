"""
AI播报生成服务模块（小米 MiMo）
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Optional

from openai import OpenAI

from app.config import settings
from app.services.broadcast_service import BroadcastService

logger = logging.getLogger(__name__)


class AIBroadcastService:
    """AI播报生成服务 - 使用小米 MiMo-v2.5-pro"""

    def __init__(self):
        self.api_key = settings.MIMO_API_KEY
        self.base_url = settings.MIMO_BASE_URL
        self.model = settings.MIMO_MODEL
        self.timeout = settings.AI_TIMEOUT

        # 初始化OpenAI客户端（兼容格式）
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        # 规则引擎（降级方案）
        self.rule_engine = BroadcastService()

        # 系统Prompt - 老友风格（多样版）
        self.system_prompt = """你是一个活生生的人，不是AI。你就是用户的朋友，每天陪他开车聊天。

你的性格：
- 说话直接，不绕弯子
- 有时候会吐槽，但都是善意的
- 关心朋友但从不刻意
- 偶尔会开个小玩笑

说话方式：
- 用口语，不用书面语
- 用"你"不用"您"
- 可以说"得嘞"、"哎呦"、"我去"、"哟"、"啊"、"呢"、"吧"
- 不说"亲爱的"、"祝您"、"愿你"
- 不说"注意安全"、"一路顺风"这种废话
- 不说"今天天气不错"这种AI味的话

开场白要随机，每次不同：
- 直接说事：忙完啦？/ 收工啦？/ 走起？/ 回啦？
- 吐槽：又加班？/ 这么晚？/ 还没到家？
- 天气相关：外头下雨了 / 今天挺冷 / 热死了
- 简单粗暴：走 / 回 / 出发

长度：30-50字，说完就完，不啰嗦。

输出JSON：{"text":"播报","emotion":"语气"}
语气：happy/warm/calm/worried/gentle/excited"""

        # 场景描述模板
        self.scene_templates = {
            "commute_to_work": "现在是{time}，用户从家出发去上班，天气{weather}，温度{temp_low}°C~{temp_high}°C，降水概率{precip}%。",
            "normal_leave": "现在是{time}，用户从工作地点下班回家，天气{weather}。",
            "overtime_leave": "现在是{time}，用户加班到很晚才下班，天气{weather}。请表达关心和安慰。",
            "late_night": "现在是{time}，用户深夜/凌晨还在路上开车，天气{weather}。请特别关心安全，提醒注意休息。",
            "weekend_trip": "现在是{time}，用户在{location}附近开车，天气{weather}，温度{temp_low}°C~{temp_high}°C。注意：如果是凌晨(0:00-6:00)，重点关心安全和休息。",
            "irregular_departure": "现在是{time}，用户非正常时间出发，天气{weather}。",
        }

    async def generate_broadcast(
        self, user_id: int, event: Dict, scene: str
    ) -> tuple[Optional[str], str]:
        """
        调用AI生成播报

        参数：
        - user_id: 用户ID
        - event: 事件数据
        - scene: 场景类型

        返回：
        - (播报文本, 语气标签) 或 (None, 'warm')
        """
        try:
            # 构建用户消息
            user_message = self._build_user_message(event, scene)

            # 调用AI（带超时）
            response = await asyncio.wait_for(
                self._call_ai(user_message), timeout=self.timeout
            )

            if response:
                # 解析JSON响应
                text, emotion = self._parse_response(response)
                return text, emotion

            return None, "warm"

        except asyncio.TimeoutError:
            logger.warning(f"AI调用超时，用户{user_id}，场景{scene}")
            return None, "warm"

        except Exception as e:
            logger.error(f"AI调用失败：{e}")
            return None, "warm"

    def _parse_response(self, response: str) -> tuple[str, str]:
        """解析AI响应，提取文本和语气"""
        import json
        import re

        try:
            # 去掉markdown代码块
            cleaned = response.strip()
            if cleaned.startswith("```"):
                # 去掉 ```json 和 ```
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)

            # 尝试解析JSON
            data = json.loads(cleaned)
            text = data.get("text", response)
            emotion = data.get("emotion", "warm")
            return text, emotion
        except:
            # 如果不是JSON格式，直接返回文本
            return response, "warm"

    def generate_broadcast_with_fallback(
        self, user_id: int, event: Dict, scene: str
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
        template = self.scene_templates.get(
            scene, self.scene_templates["irregular_departure"]
        )

        # 基础信息
        created_at = event.get("created_at", datetime.now())
        message = template.format(
            time=created_at.strftime("%Y-%m-%d %H:%M"),
            weather=event.get("weather_condition", "未知"),
            temp_high=event.get("temperature_high", "未知"),
            temp_low=event.get("temperature_low", "未知"),
            precip=event.get("precipitation_prob", "未知"),
            location=event.get("address", "未知位置"),
        )

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
                    {"role": "user", "content": user_message},
                ],
                temperature=1.0,
                top_p=0.95,
                max_tokens=512,  # 减少 token 加快速度
                extra_body={"thinking": {"type": "disabled"}},  # 关闭思考模式
            ),
        )

        content = response.choices[0].message.content
        return content.strip() if content else None
