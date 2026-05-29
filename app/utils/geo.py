"""
地理计算工具函数
"""

import math
from typing import Tuple


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    计算两点距离（米）- Haversine公式

    参数：
    - lat1, lng1: 第一个点的经纬度
    - lat2, lng2: 第二个点的经纬度

    返回：
    - 距离（米）
    """
    R = 6371000  # 地球半径（米）

    # 转换为弧度
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1

    # Haversine公式
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def is_in_radius(
    lat1: float, lng1: float, lat2: float, lng2: float, radius_meters: float
) -> bool:
    """
    判断两点是否在指定半径内

    参数：
    - lat1, lng1: 第一个点的经纬度
    - lat2, lng2: 第二个点的经纬度
    - radius_meters: 半径（米）

    返回：
    - True: 在半径内
    - False: 不在半径内
    """
    distance = calculate_distance(lat1, lng1, lat2, lng2)
    return distance <= radius_meters


def get_center_point(locations: list[Tuple[float, float]]) -> Tuple[float, float]:
    """
    计算多个点的中心点

    参数：
    - locations: 经纬度列表 [(lat, lng), ...]

    返回：
    - 中心点 (lat, lng)
    """
    if not locations:
        raise ValueError("位置列表不能为空")

    lat_sum = sum(loc[0] for loc in locations)
    lng_sum = sum(loc[1] for loc in locations)

    return lat_sum / len(locations), lng_sum / len(locations)
