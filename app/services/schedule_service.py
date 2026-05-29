"""
班制学习服务模块
"""

from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.event import Event
from app.models.location import Location
from app.models.schedule import UserSchedule
from app.utils.geo import is_in_radius


class ScheduleService:
    """班制自动学习服务"""

    def __init__(self, db: Session):
        self.db = db
        self.cluster_radius = settings.LOCATION_CLUSTER_RADIUS

    def learn_user_schedule(self, user_id: int) -> Dict:
        """
        学习用户的实际工作时间模式

        参数：
        - user_id: 用户ID

        返回：
        - 班制信息字典
        """
        # 获取最近30天的事件
        cutoff = datetime.now() - timedelta(days=30)

        events = (
            self.db.query(Event)
            .filter(Event.user_id == user_id)
            .filter(Event.created_at >= cutoff)
            .order_by(Event.created_at)
            .all()
        )

        if not events:
            return self._default_schedule()

        # 获取用户的家位置
        home_location = (
            self.db.query(Location)
            .filter(Location.user_id == user_id)
            .filter(Location.location_type == "home")
            .filter(Location.is_confirmed == True)
            .first()
        )

        if not home_location:
            return self._default_schedule()

        # 筛选从家出发的事件
        depart_from_home = [
            e
            for e in events
            if e.event_type == "connect"
            and is_in_radius(
                e.latitude,
                e.longitude,
                home_location.latitude,
                home_location.longitude,
                self.cluster_radius,
            )
        ]

        if not depart_from_home:
            return self._default_schedule()

        # 统计出发时间分布
        hour_counts = Counter()
        for event in depart_from_home:
            hour_counts[event.created_at.hour] += 1

        # 找出高频时段（占比 > 15%）
        total = sum(hour_counts.values())
        peak_hours = [
            hour for hour, count in hour_counts.items() if count / total > 0.15
        ]

        # 判断班制类型
        schedule_type = self._classify_schedule(peak_hours)

        return {
            "schedule_type": schedule_type,
            "typical_depart_times": sorted(peak_hours),
            "hour_distribution": dict(hour_counts),
            "confidence": self._calculate_confidence(hour_counts),
            "sample_size": total,
        }

    def _classify_schedule(self, peak_hours: List[int]) -> str:
        """
        根据高频时段分类班制

        白班：5:00-12:00 出发
        夜班：18:00-02:00 出发
        弹性：时间分散
        """
        if not peak_hours:
            return "unknown"

        avg_hour = sum(peak_hours) / len(peak_hours)

        # 白班判断
        if 5 <= avg_hour < 12:
            return "day_shift"

        # 夜班判断
        if 18 <= avg_hour or avg_hour < 3:
            return "night_shift"

        # 弹性/倒班
        return "flexible"

    def _calculate_confidence(self, hour_counts: Counter) -> float:
        """计算置信度"""
        if not hour_counts:
            return 0.0

        total = sum(hour_counts.values())
        max_count = max(hour_counts.values())

        # 最高频时段占比越高，置信度越高
        return min(max_count / total * 2, 1.0)

    def _default_schedule(self) -> Dict:
        """默认作息模式"""
        return {
            "schedule_type": "unknown",
            "typical_depart_times": [8, 9],
            "hour_distribution": {},
            "confidence": 0.0,
            "sample_size": 0,
        }

    def get_user_schedule(self, user_id: int) -> Dict:
        """
        获取用户班制（优先从缓存/数据库读取）

        参数：
        - user_id: 用户ID

        返回：
        - 班制信息字典
        """
        # 这里可以添加缓存逻辑
        # 暂时直接调用学习函数
        return self.learn_user_schedule(user_id)

    def record_schedule(
        self,
        user_id: int,
        date: datetime,
        depart_time: Optional[datetime] = None,
        arrive_time: Optional[datetime] = None,
        leave_time: Optional[datetime] = None,
        return_time: Optional[datetime] = None,
        work_location_id: Optional[int] = None,
    ) -> UserSchedule:
        """
        记录用户作息

        参数：
        - user_id: 用户ID
        - date: 日期
        - depart_time: 从家出发时间
        - arrive_time: 到达工作地时间
        - leave_time: 离开工作地时间
        - return_time: 到家时间
        - work_location_id: 工作地点ID

        返回：
        - UserSchedule对象
        """
        schedule = UserSchedule(
            user_id=user_id,
            date=date,
            depart_time=depart_time,
            arrive_time=arrive_time,
            leave_time=leave_time,
            return_time=return_time,
            work_location_id=work_location_id,
        )

        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)

        return schedule
