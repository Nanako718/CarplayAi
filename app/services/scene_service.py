"""
场景判断服务模块
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Optional
from app.models.event import Event
from app.models.location import Location
from app.models.user import User
from app.services.schedule_service import ScheduleService
from app.services.location_service import LocationService
from app.utils.geo import is_in_radius
from app.config import settings


class SceneService:
    """场景判断服务"""

    # 场景类型常量
    COMMUTE_TO_WORK = 'commute_to_work'  # 上班通勤
    NORMAL_LEAVE = 'normal_leave'  # 正常下班
    OVERTIME_LEAVE = 'overtime_leave'  # 加班下班
    LATE_NIGHT = 'late_night'  # 深夜回家
    WEEKEND_TRIP = 'weekend_trip'  # 周末出行
    IRREGULAR_DEPARTURE = 'irregular_departure'  # 非正常时间出发
    OTHER = 'other'  # 其他

    def __init__(self, db: Session):
        self.db = db
        self.schedule_service = ScheduleService(db)
        self.location_service = LocationService(db)
        self.cluster_radius = settings.LOCATION_CLUSTER_RADIUS

    def detect_scene(self, user_id: int, event: Event) -> str:
        """
        检测当前场景

        参数：
        - user_id: 用户ID
        - event: 事件对象

        返回：
        - 场景类型字符串
        """
        hour = event.created_at.hour
        is_weekend = event.created_at.weekday() >= 5

        # 获取用户班制
        user_schedule = self.schedule_service.get_user_schedule(user_id)

        # 识别位置类型
        location_type = self._get_location_type(user_id, event)

        # 深夜/凌晨场景（优先级最高，不管是不是周末）
        if hour >= 22 or hour < 6:
            return self.LATE_NIGHT

        # 从家出发 → 上班（不管是不是周末）
        if location_type == 'home' and event.event_type == 'connect':
            if self._is_normal_depart_time(hour, user_schedule):
                return self.COMMUTE_TO_WORK
            else:
                return self.IRREGULAR_DEPARTURE

        # 从工作地点出发 → 下班（不管是不是周末）
        if location_type == 'work' and event.event_type == 'connect':
            if self._is_overtime(hour, user_schedule):
                return self.OVERTIME_LEAVE
            else:
                return self.NORMAL_LEAVE

        # 冷启动：没有位置数据时，根据时间判断
        if location_type == 'unknown':
            # 早上7-10点 → 可能是上班
            if 7 <= hour <= 10:
                return self.COMMUTE_TO_WORK
            # 晚上17-22点 → 可能是下班
            elif 17 <= hour < 22:
                if hour >= 20:
                    return self.OVERTIME_LEAVE
                else:
                    return self.NORMAL_LEAVE

        # 周末场景
        if is_weekend:
            return self.WEEKEND_TRIP

        return self.OTHER

    def _get_location_type(self, user_id: int, event: Event) -> str:
        """获取位置类型"""
        location = self.location_service.identify_location(
            user_id,
            event.latitude,
            event.longitude
        )

        if location:
            return location.location_type

        return 'unknown'

    def _is_normal_depart_time(self, hour: int, schedule: Dict) -> bool:
        """判断是否在正常出发时间"""
        typical_times = schedule.get('typical_depart_times', [8, 9])

        # 如果没有学习数据，使用默认规则
        if not typical_times or schedule.get('confidence', 0) < 0.3:
            # 默认：7-10点为正常上班时间
            return 7 <= hour <= 10

        # 在高频时段±1小时内
        return any(
            abs(hour - t) <= 1
            for t in typical_times
        )

    def _is_overtime(self, hour: int, schedule: Dict) -> bool:
        """判断是否加班下班"""
        typical_times = schedule.get('typical_depart_times', [8, 9])

        # 如果没有学习数据，使用默认规则
        if not typical_times or schedule.get('confidence', 0) < 0.3:
            # 默认：20点以后算加班
            return hour >= 20

        # 假设工作8小时
        avg_depart = sum(typical_times) / len(typical_times)
        normal_leave_hour = (avg_depart + 8) % 24

        # 比正常下班晚2小时以上
        if hour >= normal_leave_hour + 2:
            return True

        return False

    def get_scene_description(self, scene: str) -> str:
        """获取场景描述"""
        descriptions = {
            self.COMMUTE_TO_WORK: '上班通勤，从家出发去工作',
            self.NORMAL_LEAVE: '正常下班，从工作地点回家',
            self.OVERTIME_LEAVE: '加班下班，比平时晚',
            self.LATE_NIGHT: '深夜回家',
            self.WEEKEND_TRIP: '周末出行',
            self.IRREGULAR_DEPARTURE: '非正常时间出发',
            self.OTHER: '其他场景'
        }
        return descriptions.get(scene, '未知场景')
