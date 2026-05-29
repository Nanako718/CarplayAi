"""
位置服务模块
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List, Tuple
from app.models.location import Location
from app.models.event import Event
from app.models.user import User
from app.config import settings
from app.utils.geo import calculate_distance, is_in_radius, get_center_point


class LocationService:
    """位置服务（支持多工作地点）"""

    def __init__(self, db: Session):
        self.db = db
        self.cluster_radius = settings.LOCATION_CLUSTER_RADIUS
        self.confidence_threshold = settings.LOCATION_CONFIDENCE_THRESHOLD

    def identify_location(
        self,
        user_id: int,
        latitude: float,
        longitude: float
    ) -> Optional[Location]:
        """
        识别位置（匹配已有位置）

        参数：
        - user_id: 用户ID
        - latitude: 纬度
        - longitude: 经度

        返回：
        - Location对象 或 None
        """
        # 获取用户所有位置
        locations = (
            self.db.query(Location)
            .filter(Location.user_id == user_id)
            .all()
        )

        # 查找匹配的位置
        for location in locations:
            if is_in_radius(
                latitude, longitude,
                location.latitude, location.longitude,
                self.cluster_radius
            ):
                # 更新访问信息
                location.visit_count += 1
                location.last_seen = datetime.now()
                self.db.commit()

                return location

        return None

    def update_clusters(self, user: User, event: Event) -> None:
        """
        更新位置聚合（下车时调用）

        参数：
        - user: 用户对象
        - event: 事件对象
        """
        # 只处理下车事件
        if event.event_type != 'disconnect':
            return

        # 查找匹配的位置（200米范围内）
        location = self.identify_location(
            user.id,
            event.latitude,
            event.longitude
        )

        if location:
            # 更新已有位置
            self._update_location_center(location, event)
        else:
            # 创建新位置前，再次检查是否真的不存在
            # 防止因浮点数精度问题导致重复创建
            all_locations = self.get_user_locations(user.id)
            is_duplicate = False

            for loc in all_locations:
                if is_in_radius(
                    event.latitude, event.longitude,
                    loc.latitude, loc.longitude,
                    self.cluster_radius
                ):
                    # 已存在相近位置，更新而不是创建
                    self._update_location_center(loc, event)
                    is_duplicate = True
                    break

            if not is_duplicate:
                # 确实是新位置，创建
                self._create_new_location(user, event)

    def _update_location_center(self, location: Location, event: Event) -> None:
        """更新位置中心点（加权平均）"""
        total = location.visit_count
        location.latitude = (
            location.latitude * total + event.latitude
        ) / (total + 1)
        location.longitude = (
            location.longitude * total + event.longitude
        ) / (total + 1)
        location.address = event.address

        self.db.commit()

    def _create_new_location(self, user: User, event: Event) -> Location:
        """创建新位置"""
        location = Location(
            user_id=user.id,
            location_type='unknown',  # 待识别
            latitude=event.latitude,
            longitude=event.longitude,
            address=event.address,
            visit_count=1,
            first_seen=event.created_at,
            last_seen=event.created_at
        )

        self.db.add(location)
        self.db.commit()

        # 触发位置类型识别
        self._identify_location_type(user.id)

        return location

    def _identify_location_type(self, user_id: int) -> None:
        """
        识别位置类型（家/工作地点）

        逻辑：
        1. 家：夜间(22:00-06:00)下车频次 > 30%
        2. 工作地点：单次停留>4小时 且 频次>3次/周
        """
        # 获取用户所有未知类型的位置
        unknown_locations = (
            self.db.query(Location)
            .filter(Location.user_id == user_id)
            .filter(Location.location_type == 'unknown')
            .all()
        )

        for location in unknown_locations:
            if location.visit_count < 5:
                continue  # 访问次数太少，跳过

            # 获取该位置的下车事件
            events = (
                self.db.query(Event)
                .filter(Event.user_id == user_id)
                .filter(Event.event_type == 'disconnect')
                .all()
            )

            # 计算与该位置的距离
            nearby_events = [
                e for e in events
                if is_in_radius(
                    e.latitude, e.longitude,
                    location.latitude, location.longitude,
                    self.cluster_radius
                )
            ]

            if not nearby_events:
                continue

            # 统计夜间访问
            night_visits = sum(
                1 for e in nearby_events
                if e.created_at.hour >= 22 or e.created_at.hour < 6
            )

            night_ratio = night_visits / len(nearby_events)

            # 识别家
            if night_ratio > 0.3:
                location.location_type = 'home'
                location.confidence = min(night_ratio * 1.5, 1.0)

                # 如果置信度够高，自动确认
                if location.confidence >= self.confidence_threshold:
                    location.is_confirmed = True

                self.db.commit()
                continue

            # 识别工作地点
            weekly_frequency = self._calculate_weekly_frequency(location)
            if weekly_frequency >= 3 and location.visit_count >= 10:
                location.location_type = 'work'
                location.confidence = min(weekly_frequency / 10, 1.0)

                self.db.commit()

    def _calculate_weekly_frequency(self, location: Location) -> float:
        """计算每周访问频率"""
        if not location.first_seen or not location.last_seen:
            return 0

        delta = location.last_seen - location.first_seen
        weeks = max(delta.days / 7, 1)

        return location.visit_count / weeks

    def get_user_locations(self, user_id: int) -> List[Location]:
        """获取用户所有位置"""
        return (
            self.db.query(Location)
            .filter(Location.user_id == user_id)
            .all()
        )

    def get_pending_locations(self, user_id: int) -> List[Location]:
        """获取待确认的位置"""
        return (
            self.db.query(Location)
            .filter(Location.user_id == user_id)
            .filter(Location.is_confirmed == False)
            .filter(Location.confidence >= 0.5)
            .all()
        )

    def confirm_location(self, location_id: int, user_id: int) -> Optional[Location]:
        """确认位置"""
        location = (
            self.db.query(Location)
            .filter(Location.id == location_id)
            .filter(Location.user_id == user_id)
            .first()
        )

        if location:
            location.is_confirmed = True
            self.db.commit()

        return location

    def rename_location(
        self,
        location_id: int,
        user_id: int,
        name: str
    ) -> Optional[Location]:
        """重命名位置"""
        location = (
            self.db.query(Location)
            .filter(Location.id == location_id)
            .filter(Location.user_id == user_id)
            .first()
        )

        if location:
            location.name = name
            self.db.commit()

        return location
