"""
播报生成服务模块（规则引擎 - AI降级方案）
"""

import random
from datetime import datetime
from typing import Dict, List


class BroadcastService:
    """规则引擎播报服务"""

    def __init__(self):
        # 模板库
        self.templates = {
            "greeting": {
                "morning": [
                    "早上好！",
                    "早安！",
                    "新的一天开始了！",
                    "嗨，早上好！",
                ],
                "afternoon": [
                    "下午好！",
                    "午后好！",
                ],
                "evening": [
                    "晚上好！",
                    "辛苦了一天！",
                ],
                "night": [
                    "这么晚才回，辛苦了！",
                    "夜深了，注意休息！",
                ],
            },
            "weather_advice": {
                "rain": [
                    "今天有雨，记得带伞。",
                    "外面下雨了，注意防雨。",
                    "雨天路滑，小心驾驶。",
                ],
                "hot": [
                    "今天高温，注意防暑。",
                    "天气炎热，多喝水。",
                ],
                "cold": [
                    "今天很冷，多穿点。",
                    "天气寒冷，注意保暖。",
                ],
                "weekend_rain": [
                    "今天有雨，不适合洗车哦。",
                    "下雨天，洗车可以改天。",
                ],
            },
            "scene_content": {
                "commute_to_work": [
                    "今天也要元气满满！",
                    "工作加油！",
                    "祝你工作顺利！",
                ],
                "normal_leave": [
                    "下班啦，回家路上注意安全。",
                    "辛苦啦，早点休息。",
                ],
                "overtime_leave": [
                    "加班辛苦了，别太累了。",
                    "这么晚才下班，注意休息。",
                ],
                "late_night": [
                    "路上注意安全，早点休息。",
                    "夜深了，小心驾驶。",
                ],
                "weekend_trip": [
                    "周末愉快！",
                    "好好享受周末时光！",
                ],
            },
            "care": {
                "default": [
                    "路上注意安全！",
                    "一路顺风！",
                    "注意安全！",
                ],
                "commute": [
                    "路上注意安全，工作加油！",
                    "平安到达，工作顺利！",
                ],
                "return_home": [
                    "早点休息哦！",
                    "好好休息！",
                ],
            },
        }

        # 最近使用记录（去重用）
        self.recent_used = {}

    def generate_broadcast(self, user_id: int, event: Dict, scene: str) -> str:
        """
        规则引擎生成播报

        参数：
        - user_id: 用户ID
        - event: 事件数据
        - scene: 场景类型

        返回：
        - 播报文本
        """
        parts = []
        hour = event.get("created_at", datetime.now()).hour

        # 1. 问候语
        greeting = self._select_greeting(hour)
        parts.append(greeting)

        # 2. 天气建议
        weather_advice = self._select_weather_advice(event)
        if weather_advice:
            parts.append(weather_advice)

        # 3. 场景内容
        scene_content = self._select_scene_content(scene)
        if scene_content:
            parts.append(scene_content)

        # 4. 关怀语
        care = self._select_care(scene)
        parts.append(care)

        return "".join(parts)

    def _select_greeting(self, hour: int) -> str:
        """选择问候语"""
        if 6 <= hour < 12:
            pool = self.templates["greeting"]["morning"]
        elif 12 <= hour < 18:
            pool = self.templates["greeting"]["afternoon"]
        elif 18 <= hour < 22:
            pool = self.templates["greeting"]["evening"]
        else:
            pool = self.templates["greeting"]["night"]

        return self._random_select("greeting", pool)

    def _select_weather_advice(self, event: Dict) -> str:
        """选择天气建议"""
        weather = event.get("weather_condition", "")
        precip_prob = event.get("precipitation_prob", 0)
        temp_high = event.get("temperature_high", 25)
        temp_low = event.get("temperature_low", 15)
        is_weekend = event.get("created_at", datetime.now()).weekday() >= 5

        # 雨天建议
        if precip_prob and precip_prob > 60:
            if is_weekend:
                return self._random_select(
                    "weather_rain", self.templates["weather_advice"]["weekend_rain"]
                )
            else:
                return self._random_select(
                    "weather_rain", self.templates["weather_advice"]["rain"]
                )

        # 高温建议
        if temp_high and temp_high > 35:
            return self._random_select(
                "weather_hot", self.templates["weather_advice"]["hot"]
            )

        # 低温建议
        if temp_low and temp_low < 5:
            return self._random_select(
                "weather_cold", self.templates["weather_advice"]["cold"]
            )

        return ""

    def _select_scene_content(self, scene: str) -> str:
        """选择场景内容"""
        pool = self.templates["scene_content"].get(scene, [])
        if pool:
            return self._random_select(f"scene_{scene}", pool)
        return ""

    def _select_care(self, scene: str) -> str:
        """选择关怀语"""
        if scene in ["commute_to_work"]:
            pool = self.templates["care"]["commute"]
        elif scene in ["normal_leave", "overtime_leave", "late_night"]:
            pool = self.templates["care"]["return_home"]
        else:
            pool = self.templates["care"]["default"]

        return self._random_select("care", pool)

    def _random_select(self, category: str, pool: List[str]) -> str:
        """随机选择（带去重）"""
        if not pool:
            return ""

        # 获取最近使用
        recent = self.recent_used.get(category, [])

        # 过滤最近使用过的
        available = [t for t in pool if t not in recent]
        if not available:
            available = pool
            recent = []

        # 随机选择
        selected = random.choice(available)

        # 更新最近使用
        recent.append(selected)
        if len(recent) > 3:
            recent = recent[-3:]
        self.recent_used[category] = recent

        return selected
