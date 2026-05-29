#!/usr/bin/env python3
"""
生成过去100天的虚拟测试数据（直接写数据库，不调用API）
"""
import random
from datetime import datetime, timedelta
from app.database import SessionLocal, init_db
from app.models.event import Event
from app.models.broadcast import Broadcast
from app.models.location import Location
from app.models.schedule import UserSchedule
from app.models.user import User

# 位置配置
HOME = {"lng": 115.690116, "lat": 34.4222, "address": "豫苑路与富商大道交叉口西南60米"}
WORK = {"lng": 115.735172, "lat": 34.380119, "address": "商丘示范区中电科技园A区H栋"}

# 天气配置
WEATHERS = [
    {"condition": "局部多云", "temp_high": 21, "temp_low": 10, "precip": 0},
    {"condition": "晴", "temp_high": 28, "temp_low": 15, "precip": 0},
    {"condition": "多云", "temp_high": 24, "temp_low": 12, "precip": 10},
    {"condition": "阴", "temp_high": 20, "temp_low": 11, "precip": 20},
    {"condition": "小雨", "temp_high": 18, "temp_low": 10, "precip": 60},
]

# 播报模板
BROADCASTS = {
    "commute_to_work": [
        "早上好！今天也要元气满满！路上注意安全！",
        "早安！新的一天开始了，工作加油！",
        "早上好！今天天气不错，祝你工作顺利！",
    ],
    "normal_leave": [
        "下班啦！辛苦了，回家路上注意安全。",
        "下班快乐！早点休息哦。",
        "辛苦啦！路上注意安全，早点休息。",
    ],
    "overtime_leave": [
        "加班辛苦了！别太累了，注意休息。",
        "这么晚才下班，辛苦了！路上小心。",
        "加班到这么晚，辛苦啦！早点休息。",
    ],
    "late_night": [
        "夜深了，路上注意安全！早点休息。",
        "这么晚才回，辛苦了！好好休息。",
        "深夜回家，注意安全！别太累了。",
    ],
    "weekend_trip": [
        "周末愉快！好好享受周末时光！",
        "周末快乐！出行注意安全！",
        "周末好！祝你玩得开心！",
    ],
    "other": [
        "路上注意安全！",
        "一路顺风！",
        "注意安全！",
    ]
}

def get_season_temp(month):
    if month in [6, 7, 8]: return 10
    if month in [12, 1, 2]: return -10
    if month in [3, 4, 5]: return 0
    return -5

def offset(v, meters=30):
    return round(v + random.uniform(-meters, meters) * 0.00001, 6)

def get_weather(date):
    w = random.choice(WEATHERS).copy()
    w["temp_high"] += get_season_temp(date.month) + random.randint(-3, 3)
    w["temp_low"] += get_season_temp(date.month) + random.randint(-3, 3)
    return w

def detect_scene(hour, is_weekend, location_type):
    if is_weekend:
        return "weekend_trip"
    if hour >= 22 or hour < 5:
        return "late_night"
    if location_type == "home" and 6 <= hour < 10:
        return "commute_to_work"
    if location_type == "work" and 17 <= hour < 20:
        return "normal_leave"
    if location_type == "work" and hour >= 20:
        return "overtime_leave"
    return "other"

def main():
    print("🚗 生成过去100天虚拟数据（直接写数据库）...")
    print(f"📍 家：{HOME['address']}")
    print(f"📍 公司：{WORK['address']}")
    print()

    # 初始化数据库
    init_db()

    # 获取用户
    db = SessionLocal()
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        print("❌ 用户不存在，请先注册")
        return

    # 创建家和公司位置
    home_loc = Location(
        user_id=user.id,
        location_type="home",
        name="家",
        latitude=HOME["lat"],
        longitude=HOME["lng"],
        address=HOME["address"],
        confidence=0.95,
        is_confirmed=True,
        visit_count=0,
        first_seen=datetime.now(),
        last_seen=datetime.now()
    )

    work_loc = Location(
        user_id=user.id,
        location_type="work",
        name="公司",
        latitude=WORK["lat"],
        longitude=WORK["lng"],
        address=WORK["address"],
        confidence=0.95,
        is_confirmed=True,
        visit_count=0,
        first_seen=datetime.now(),
        last_seen=datetime.now()
    )

    db.add(home_loc)
    db.add(work_loc)
    db.commit()

    print(f"✅ 创建位置：家(ID:{home_loc.id}) 公司(ID:{work_loc.id})")
    print()

    # 时间范围
    today = datetime(2026, 5, 30)
    start = today - timedelta(days=99)

    print(f"📅 {start.strftime('%Y-%m-%d')} → {today.strftime('%Y-%m-%d')}")
    print()

    event_count = 0
    broadcast_count = 0

    for day in range(100):
        date = start + timedelta(days=day)
        is_weekend = date.weekday() >= 5
        w = get_weather(date)

        # 早上从家出发
        t1 = date.replace(hour=random.randint(7, 8), minute=random.randint(0, 59))
        e1 = Event(
            user_id=user.id,
            event_type="connect",
            latitude=offset(HOME["lat"]),
            longitude=offset(HOME["lng"]),
            address=HOME["address"],
            from_location_id=home_loc.id,
            weather_condition=w["condition"],
            temperature_high=w["temp_high"],
            temperature_low=w["temp_low"],
            precipitation_prob=w["precip"],
            created_at=t1
        )
        db.add(e1)
        event_count += 1

        # 到公司
        t2 = t1 + timedelta(minutes=random.randint(30, 50))
        e2 = Event(
            user_id=user.id,
            event_type="disconnect",
            latitude=offset(WORK["lat"]),
            longitude=offset(WORK["lng"]),
            address=WORK["address"],
            to_location_id=work_loc.id,
            weather_condition=w["condition"],
            temperature_high=w["temp_high"],
            temperature_low=w["temp_low"],
            precipitation_prob=w["precip"],
            created_at=t2
        )
        db.add(e2)
        event_count += 1

        # 早上播报
        scene1 = "commute_to_work"
        b1 = Broadcast(
            user_id=user.id,
            event_id=None,  # 后面更新
            content_text=random.choice(BROADCASTS[scene1]),
            scene=scene1,
            ai_model="rule_engine",
            ai_latency=0,
            is_fallback=True,
            created_at=t1
        )
        db.add(b1)
        broadcast_count += 1

        # 晚上从公司出发
        h = random.randint(21, 22) if random.random() < 0.2 else random.randint(17, 19)
        t3 = date.replace(hour=h, minute=random.randint(0, 59))
        e3 = Event(
            user_id=user.id,
            event_type="connect",
            latitude=offset(WORK["lat"]),
            longitude=offset(WORK["lng"]),
            address=WORK["address"],
            from_location_id=work_loc.id,
            weather_condition=w["condition"],
            temperature_high=w["temp_high"],
            temperature_low=w["temp_low"],
            precipitation_prob=w["precip"],
            created_at=t3
        )
        db.add(e3)
        event_count += 1

        # 到家
        t4 = t3 + timedelta(minutes=random.randint(30, 50))
        e4 = Event(
            user_id=user.id,
            event_type="disconnect",
            latitude=offset(HOME["lat"]),
            longitude=offset(HOME["lng"]),
            address=HOME["address"],
            to_location_id=home_loc.id,
            weather_condition=w["condition"],
            temperature_high=w["temp_high"],
            temperature_low=w["temp_low"],
            precipitation_prob=w["precip"],
            created_at=t4
        )
        db.add(e4)
        event_count += 1

        # 晚上播报
        scene2 = detect_scene(h, is_weekend, "work")
        b2 = Broadcast(
            user_id=user.id,
            event_id=None,
            content_text=random.choice(BROADCASTS[scene2]),
            scene=scene2,
            ai_model="rule_engine",
            ai_latency=0,
            is_fallback=True,
            created_at=t3
        )
        db.add(b2)
        broadcast_count += 1

        # 更新位置访问次数
        home_loc.visit_count += 2
        work_loc.visit_count += 2

        # 记录作息
        schedule = UserSchedule(
            user_id=user.id,
            date=date,
            depart_time=t1,
            arrive_time=t2,
            leave_time=t3,
            return_time=t4,
            work_location_id=work_loc.id
        )
        db.add(schedule)

        print(f"📅 {date.strftime('%Y-%m-%d')} {w['condition']:4} {w['temp_high']:3}°C")

    db.commit()
    db.close()

    print()
    print(f"✅ 完成！")
    print(f"   事件：{event_count} 条")
    print(f"   播报：{broadcast_count} 条")
    print(f"   位置：2 个")
    print(f"   作息：100 条")

if __name__ == "__main__":
    main()
