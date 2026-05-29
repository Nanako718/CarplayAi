# CarPlay AI 智能助手 - 技术文档（最终版）

## 1. 系统架构

### 1.1 整体架构
```
┌─────────────────┐     ┌─────────────────────────────────────┐     ┌─────────────────┐
│   iPhone        │     │   后端服务 (FastAPI)                 │     │   数据库         │
│   快捷指令      │────▶│                                     │────▶│   SQLite (开发)  │
│                 │     │  ┌─────────┐  ┌─────────┐          │     │   PostgreSQL     │
└─────────────────┘     │  │ 事件处理 │  │ AI播报  │          │     │   (生产)         │
                        │  └────┬────┘  └────┬────┘          │     └─────────────────┘
                        │       │            │               │
                        │  ┌────▼────┐  ┌────▼────┐          │     ┌─────────────────┐
                        │  │位置学习 │  │ TTS合成 │          │────▶│   对象存储       │
                        │  │班制学习 │  │ (生产)  │          │     │   (音频文件)     │
                        │  └─────────┘  └─────────┘          │     └─────────────────┘
                        │                                     │
                        │  ┌─────────┐  ┌─────────┐          │     ┌─────────────────┐
                        │  │场景判断 │  │规则引擎 │          │────▶│   AI服务         │
                        │  └─────────┘  │(降级)   │          │     │ GPT-3.5/通义千问 │
                        │               └─────────┘          │     └─────────────────┘
                        └─────────────────────────────────────┘
```

### 1.2 技术栈选择

| 层级 | 技术选择 | 理由 |
|------|----------|------|
| 后端框架 | FastAPI | 高性能、异步支持、自动文档生成 |
| 数据库 | SQLite (开发) / PostgreSQL (生产) | 开发简单、生产稳定 |
| ORM | SQLAlchemy | 成熟稳定、支持多种数据库 |
| AI服务 | OpenAI GPT-3.5 / 通义千问 | 性价比高、速度快 |
| TTS服务 | 阿里云 / 腾讯云 | 音质好、多音色 |
| 对象存储 | 阿里云OSS / 腾讯云COS | 存储音频文件 |
| 缓存 | 本地缓存 (开发) / Redis (生产) | 避免重复AI调用 |
| 认证 | JWT | 无状态、易于实现 |
| 部署 | Docker + Uvicorn | 容器化部署、高性能ASGI服务器 |

## 2. 项目结构

```
carplay-ai/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI应用入口
│   ├── config.py                   # 配置文件
│   ├── database.py                 # 数据库连接
│   ├── models/                     # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py                 # 用户模型
│   │   ├── location.py             # 位置模型
│   │   ├── event.py                # 事件模型
│   │   ├── broadcast.py            # 播报模型
│   │   └── schedule.py             # 作息模型
│   ├── schemas/                    # Pydantic模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── event.py
│   │   ├── location.py
│   │   └── response.py
│   ├── routers/                    # API路由
│   │   ├── __init__.py
│   │   ├── auth.py                 # 认证接口
│   │   ├── events.py               # 事件接口
│   │   ├── user.py                 # 用户接口
│   │   └── locations.py            # 位置接口
│   ├── services/                   # 业务逻辑
│   │   ├── __init__.py
│   │   ├── event_service.py        # 事件处理
│   │   ├── location_service.py     # 位置学习
│   │   ├── schedule_service.py     # 班制学习
│   │   ├── scene_service.py        # 场景判断
│   │   ├── broadcast_service.py    # 播报生成（规则引擎）
│   │   ├── ai_service.py           # AI播报生成
│   │   └── tts_service.py          # TTS语音合成
│   ├── utils/                      # 工具函数
│   │   ├── __init__.py
│   │   ├── auth.py                 # JWT工具
│   │   ├── geo.py                  # 地理计算
│   │   └── time.py                 # 时间工具
│   └── middleware/                 # 中间件
│       ├── __init__.py
│       └── auth.py                 # 认证中间件
├── prompts/                        # AI Prompt模板
│   └── broadcast.txt               # 播报生成Prompt
├── tests/                          # 测试
├── requirements.txt                # 依赖
├── Dockerfile                      # Docker配置
├── docker-compose.yml              # Docker Compose
└── README.md                       # 项目说明
```

## 3. 核心模块设计

### 3.1 位置学习算法（多工作地点支持）

#### 3.1.1 位置聚合算法
```python
import math
from datetime import datetime, time
from typing import List, Dict, Tuple

class LocationClusterer:
    """位置聚合器 - 支持多工作地点"""
    
    def __init__(self, radius_meters: int = 200):
        self.radius = radius_meters  # 聚合半径（米）
    
    def cluster_locations(self, events: List[Dict]) -> List[Dict]:
        """
        将事件位置聚合为簇
        使用简单的距离聚合算法
        """
        clusters = []
        
        for event in events:
            merged = False
            for cluster in clusters:
                if self._is_in_cluster(event, cluster):
                    self._update_cluster(cluster, event)
                    merged = True
                    break
            
            if not merged:
                clusters.append(self._create_cluster(event))
        
        return clusters
    
    def _is_in_cluster(self, event: Dict, cluster: Dict) -> bool:
        """判断事件是否在簇内"""
        distance = self._calculate_distance(
            event['latitude'], event['longitude'],
            cluster['center_lat'], cluster['center_lng']
        )
        return distance <= self.radius
    
    def _calculate_distance(self, lat1: float, lng1: float, 
                          lat2: float, lng2: float) -> float:
        """计算两点距离（米）- Haversine公式"""
        R = 6371000  # 地球半径（米）
        
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _create_cluster(self, event: Dict) -> Dict:
        """创建新簇"""
        return {
            'center_lat': event['latitude'],
            'center_lng': event['longitude'],
            'address': event['address'],
            'visit_count': 1,
            'events': [event],
            'first_seen': event['created_at'],
            'last_seen': event['created_at']
        }
    
    def _update_cluster(self, cluster: Dict, event: Dict):
        """更新簇"""
        # 更新中心点（加权平均）
        total = cluster['visit_count']
        cluster['center_lat'] = (
            cluster['center_lat'] * total + event['latitude']
        ) / (total + 1)
        cluster['center_lng'] = (
            cluster['center_lng'] * total + event['longitude']
        ) / (total + 1)
        cluster['visit_count'] += 1
        cluster['events'].append(event)
        cluster['last_seen'] = event['created_at']


class LocationIdentifier:
    """位置类型识别器"""
    
    def identify_location_type(self, cluster: Dict, user_events: List[Dict]) -> Tuple[str, float]:
        """
        识别位置类型（家/工作地点）
        
        逻辑：
        1. 家：夜间(22:00-06:00)下车频次 > 30%
        2. 工作地点：单次停留>4小时 且 频次>3次/周
        """
        # 统计夜间访问
        night_visits = 0
        long_stays = 0
        total_disconnects = 0
        
        for event in user_events:
            if event['event_type'] == 'disconnect':
                total_disconnects += 1
                hour = event['created_at'].hour
                
                # 夜间访问 (22:00-06:00)
                if hour >= 22 or hour < 6:
                    night_visits += 1
        
        # 计算家置信度
        if total_disconnects > 0:
            night_ratio = night_visits / total_disconnects
            if night_ratio > 0.3:
                confidence = min(night_ratio * 1.5, 1.0)
                return 'home', confidence
        
        # 计算工作地点置信度
        # 基于访问频次和停留时长
        visit_count = cluster['visit_count']
        weeks_active = self._calculate_weeks_active(cluster)
        
        if weeks_active > 0:
            weekly_frequency = visit_count / weeks_active
            if weekly_frequency >= 3 and visit_count >= 10:
                confidence = min(weekly_frequency / 10, 1.0)
                return 'work', confidence
        
        return 'other', 0.0
    
    def _calculate_weeks_active(self, cluster: Dict) -> float:
        """计算活跃周数"""
        first_seen = cluster['first_seen']
        last_seen = cluster['last_seen']
        delta = last_seen - first_seen
        return max(delta.days / 7, 1)
```

### 3.2 班制自动学习

```python
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class WorkScheduleLearner:
    """班制自动学习器"""
    
    def learn_user_schedule(self, user_id: int, events: List[Dict]) -> Dict:
        """
        学习用户的实际工作时间模式
        
        分析逻辑：
        1. 获取最近30天的"从家出发"事件
        2. 统计出发时间分布
        3. 找出高频时段
        4. 判断班制类型
        """
        # 1. 筛选从家出发的事件
        depart_from_home = [
            e for e in events
            if e['event_type'] == 'connect'
            and self._is_from_home(e)
            and e['created_at'] >= datetime.now() - timedelta(days=30)
        ]
        
        if not depart_from_home:
            return self._default_schedule()
        
        # 2. 统计出发时间分布
        hour_counts = Counter()
        for event in depart_from_home:
            hour_counts[event['created_at'].hour] += 1
        
        # 3. 找出高频时段（占比 > 15%）
        total = sum(hour_counts.values())
        peak_hours = [
            hour for hour, count in hour_counts.items()
            if count / total > 0.15
        ]
        
        # 4. 判断班制类型
        schedule_type = self._classify_schedule(peak_hours)
        
        return {
            'schedule_type': schedule_type,
            'typical_depart_times': sorted(peak_hours),
            'hour_distribution': dict(hour_counts),
            'confidence': self._calculate_confidence(hour_counts),
            'sample_size': total
        }
    
    def _classify_schedule(self, peak_hours: List[int]) -> str:
        """
        根据高频时段分类班制
        
        白班：5:00-12:00 出发
        夜班：18:00-02:00 出发
        弹性：时间分散
        """
        if not peak_hours:
            return 'unknown'
        
        avg_hour = sum(peak_hours) / len(peak_hours)
        
        # 白班判断
        if 5 <= avg_hour < 12:
            return 'day_shift'
        
        # 夜班判断
        if 18 <= avg_hour or avg_hour < 3:
            return 'night_shift'
        
        # 弹性/倒班
        return 'flexible'
    
    def _calculate_confidence(self, hour_counts: Counter) -> float:
        """计算置信度"""
        if not hour_counts:
            return 0.0
        
        total = sum(hour_counts.values())
        max_count = max(hour_counts.values())
        
        # 最高频时段占比越高，置信度越高
        return min(max_count / total * 2, 1.0)
    
    def _is_from_home(self, event: Dict) -> bool:
        """判断事件是否从家出发"""
        # 需要关联位置表判断
        # 简化实现：假设from_location_id存在
        return event.get('from_location_type') == 'home'
    
    def _default_schedule(self) -> Dict:
        """默认作息模式"""
        return {
            'schedule_type': 'unknown',
            'typical_depart_times': [8, 9],
            'hour_distribution': {},
            'confidence': 0.0,
            'sample_size': 0
        }
```

### 3.3 场景判断服务

```python
from datetime import datetime
from typing import Dict, Optional

class SceneService:
    """场景判断服务"""
    
    def __init__(self, db):
        self.db = db
        self.schedule_learner = WorkScheduleLearner()
    
    def detect_scene(self, user_id: int, event: Dict) -> str:
        """
        检测当前场景
        
        场景类型：
        - commute_to_work: 上班通勤（从家出发去工作）
        - normal_leave: 正常下班
        - overtime_leave: 加班下班（比平时晚2小时以上）
        - late_night: 深夜回家（22:00后）
        - weekend_trip: 周末出行
        - irregular_departure: 非正常时间出发
        """
        # 获取用户作息模式
        user_schedule = self._get_user_schedule(user_id)
        
        # 获取事件信息
        hour = event['created_at'].hour
        is_weekend = event['created_at'].weekday() >= 5
        location_type = self._get_location_type(user_id, event)
        
        # 周末场景
        if is_weekend:
            return 'weekend_trip'
        
        # 深夜场景
        if hour >= 22 or hour < 5:
            return 'late_night'
        
        # 从家出发
        if location_type == 'home' and event['event_type'] == 'connect':
            if self._is_normal_depart_time(hour, user_schedule):
                return 'commute_to_work'
            else:
                return 'irregular_departure'
        
        # 从工作地点出发（下班）
        if location_type == 'work' and event['event_type'] == 'connect':
            if self._is_overtime(hour, user_schedule):
                return 'overtime_leave'
            else:
                return 'normal_leave'
        
        return 'other'
    
    def _is_normal_depart_time(self, hour: int, schedule: Dict) -> bool:
        """判断是否在正常出发时间"""
        typical_times = schedule.get('typical_depart_times', [8, 9])
        
        # 在高频时段±1小时内
        return any(
            abs(hour - t) <= 1 
            for t in typical_times
        )
    
    def _is_overtime(self, hour: int, schedule: Dict) -> bool:
        """判断是否加班下班"""
        typical_times = schedule.get('typical_depart_times', [8, 9])
        
        if not typical_times:
            return False
        
        # 假设工作8小时
        avg_depart = sum(typical_times) / len(typical_times)
        normal_leave_hour = (avg_depart + 8) % 24
        
        # 比正常下班晚2小时以上
        if hour >= normal_leave_hour + 2:
            return True
        
        return False
    
    def _get_user_schedule(self, user_id: int) -> Dict:
        """获取用户作息模式"""
        # 从数据库或缓存获取
        # 简化实现
        return {
            'schedule_type': 'day_shift',
            'typical_depart_times': [8, 9]
        }
    
    def _get_location_type(self, user_id: int, event: Dict) -> str:
        """获取位置类型"""
        # 从数据库查询位置类型
        # 简化实现
        return event.get('from_location_type', 'unknown')
```

### 3.4 AI播报生成服务（小米 MiMo）

```python
import asyncio
import os
from openai import OpenAI
from typing import Dict, Optional
from datetime import datetime

class AIBroadcastService:
    """AI播报生成服务 - 使用小米 MiMo-v2.5-pro"""
    
    def __init__(self):
        self.api_key = os.environ.get("MIMO_API_KEY")
        self.base_url = "https://api.xiaomimimo.com/v1"
        self.model = "mimo-v2.5-pro"
        self.timeout = 3.0  # 3秒超时
        
        # 初始化OpenAI客户端（兼容格式）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        # Prompt模板
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
            'normal_leave': '现在是{time}，用户从工作地点下班回家，今天工作了{work_hours}小时，天气{weather}。',
            'overtime_leave': '现在是{time}，用户加班到很晚才下班，天气{weather}。请表达关心和安慰。',
            'late_night': '现在是{time}，用户深夜还在路上，天气{weather}。请特别关心安全和休息。',
            'weekend_trip': '现在是{time}，周末出行，天气{weather}，温度{temp_low}°C~{temp_high}°C。',
            'irregular_departure': '现在是{time}，用户非正常时间出发，天气{weather}。'
        }
    
    async def generate_broadcast(self, user_id: int, event: Dict, scene: str) -> Optional[str]:
        """
        调用AI生成播报
        
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
    
    def _build_user_message(self, event: Dict, scene: str) -> str:
        """构建用户消息"""
        template = self.scene_templates.get(scene, self.scene_templates['irregular_departure'])
        
        # 基础信息
        message = template.format(
            time=event['created_at'].strftime('%Y-%m-%d %H:%M'),
            weather=event.get('weather_condition', '未知'),
            temp_high=event.get('temperature_high', '未知'),
            temp_low=event.get('temperature_low', '未知'),
            precip=event.get('precipitation_prob', '未知'),
            work_hours=self._calculate_work_hours(event)
        )
        
        # 添加位置信息
        if event.get('from_address'):
            message += f"出发地：{event['from_address']}。"
        
        # 添加班制信息
        schedule_type = event.get('schedule_type', 'unknown')
        if schedule_type != 'unknown':
            schedule_desc = {
                'day_shift': '白班作息',
                'night_shift': '夜班作息',
                'flexible': '弹性工作'
            }.get(schedule_type, '')
            if schedule_desc:
                message += f"用户是{schedule_desc}。"
        
        return message
    
    def _calculate_work_hours(self, event: Dict) -> int:
        """计算工作时长（小时）"""
        # 简化实现，实际需要从数据库查询
        return 8
    
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


class BroadcastCache:
    """播报缓存 - 避免重复AI调用"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
        self.recent_broadcasts = {}  # 用户最近播报
    
    def get_cache_key(self, user_id: int, scene: str, weather: str, time_bucket: str) -> str:
        """生成缓存键"""
        return f"{user_id}_{scene}_{weather}_{time_bucket}"
    
    def get_time_bucket(self, hour: int) -> str:
        """时间分桶"""
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def should_call_ai(self, user_id: int, scene: str, weather: str, hour: int) -> bool:
        """判断是否需要调用AI"""
        time_bucket = self.get_time_bucket(hour)
        key = self.get_cache_key(user_id, scene, weather, time_bucket)
        
        # 检查缓存
        if key in self.cache:
            cache_time, _ = self.cache[key]
            if (datetime.now() - cache_time).seconds < self.ttl:
                return False
        
        return True
    
    def get_cached_broadcast(self, user_id: int, scene: str, weather: str, hour: int) -> Optional[str]:
        """获取缓存的播报"""
        time_bucket = self.get_time_bucket(hour)
        key = self.get_cache_key(user_id, scene, weather, time_bucket)
        
        if key in self.cache:
            cache_time, broadcast = self.cache[key]
            if (datetime.now() - cache_time).seconds < self.ttl:
                return broadcast
        
        return None
    
    def set_cache(self, user_id: int, scene: str, weather: str, hour: int, broadcast: str):
        """设置缓存"""
        time_bucket = self.get_time_bucket(hour)
        key = self.get_cache_key(user_id, scene, weather, time_bucket)
        self.cache[key] = (datetime.now(), broadcast)
```

### 3.5 规则引擎（降级方案）

```python
import random
from typing import Dict, List

class RuleBasedBroadcastService:
    """规则引擎播报服务 - AI降级方案"""
    
    def __init__(self):
        # 模板库
        self.templates = {
            'greeting': {
                'morning': [
                    "早上好！",
                    "早安！",
                    "新的一天开始了！",
                    "嗨，早上好！",
                ],
                'afternoon': [
                    "下午好！",
                    "午后好！",
                ],
                'evening': [
                    "晚上好！",
                    "辛苦了一天！",
                ],
                'night': [
                    "这么晚才回，辛苦了！",
                    "夜深了，注意休息！",
                ]
            },
            'weather_advice': {
                'rain': [
                    "今天有雨，记得带伞。",
                    "外面下雨了，注意防雨。",
                    "雨天路滑，小心驾驶。",
                ],
                'hot': [
                    "今天高温，注意防暑。",
                    "天气炎热，多喝水。",
                ],
                'cold': [
                    "今天很冷，多穿点。",
                    "天气寒冷，注意保暖。",
                ],
                'weekend_rain': [
                    "今天有雨，不适合洗车哦。",
                    "下雨天，洗车可以改天。",
                ]
            },
            'scene_content': {
                'commute_to_work': [
                    "今天也要元气满满！",
                    "工作加油！",
                    "祝你工作顺利！",
                ],
                'normal_leave': [
                    "下班啦，回家路上注意安全。",
                    "辛苦啦，早点休息。",
                ],
                'overtime_leave': [
                    "加班辛苦了，别太累了。",
                    "这么晚才下班，注意休息。",
                ],
                'late_night': [
                    "路上注意安全，早点休息。",
                    "夜深了，小心驾驶。",
                ],
                'weekend_trip': [
                    "周末愉快！",
                    "好好享受周末时光！",
                ]
            },
            'care': {
                'default': [
                    "路上注意安全！",
                    "一路顺风！",
                    "注意安全！",
                ],
                'commute': [
                    "路上注意安全，工作加油！",
                    "平安到达，工作顺利！",
                ],
                'return_home': [
                    "早点休息哦！",
                    "好好休息！",
                ]
            }
        }
        
        # 最近使用记录（去重用）
        self.recent_used = {}
    
    def generate_broadcast(self, user_id: int, event: Dict, scene: str) -> str:
        """
        规则引擎生成播报
        """
        parts = []
        hour = event['created_at'].hour
        
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
        
        return ''.join(parts)
    
    def _select_greeting(self, hour: int) -> str:
        """选择问候语"""
        if 6 <= hour < 12:
            pool = self.templates['greeting']['morning']
        elif 12 <= hour < 18:
            pool = self.templates['greeting']['afternoon']
        elif 18 <= hour < 22:
            pool = self.templates['greeting']['evening']
        else:
            pool = self.templates['greeting']['night']
        
        return self._random_select('greeting', pool)
    
    def _select_weather_advice(self, event: Dict) -> str:
        """选择天气建议"""
        weather = event.get('weather_condition', '')
        precip_prob = event.get('precipitation_prob', 0)
        temp_high = event.get('temperature_high', 25)
        temp_low = event.get('temperature_low', 15)
        is_weekend = event['created_at'].weekday() >= 5
        
        # 雨天建议
        if precip_prob > 60:
            if is_weekend:
                return self._random_select('weather_rain', self.templates['weather_advice']['weekend_rain'])
            else:
                return self._random_select('weather_rain', self.templates['weather_advice']['rain'])
        
        # 高温建议
        if temp_high > 35:
            return self._random_select('weather_hot', self.templates['weather_advice']['hot'])
        
        # 低温建议
        if temp_low < 5:
            return self._random_select('weather_cold', self.templates['weather_advice']['cold'])
        
        return ''
    
    def _select_scene_content(self, scene: str) -> str:
        """选择场景内容"""
        pool = self.templates['scene_content'].get(scene, [])
        if pool:
            return self._random_select(f'scene_{scene}', pool)
        return ''
    
    def _select_care(self, scene: str) -> str:
        """选择关怀语"""
        if scene in ['commute_to_work']:
            pool = self.templates['care']['commute']
        elif scene in ['normal_leave', 'overtime_leave', 'late_night']:
            pool = self.templates['care']['return_home']
        else:
            pool = self.templates['care']['default']
        
        return self._random_select('care', pool)
    
    def _random_select(self, category: str, pool: List[str]) -> str:
        """随机选择（带去重）"""
        if not pool:
            return ''
        
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
```

### 3.6 TTS语音合成服务（字节跳动）

```python
import asyncio
import json
import base64
import httpx
from typing import Optional
from fastapi.responses import StreamingResponse

class TTSService:
    """TTS语音合成服务 - 字节跳动"""
    
    def __init__(self):
        self.app_id = settings.TTS_APP_ID
        self.access_key = settings.TTS_ACCESS_KEY
        self.resource_id = settings.TTS_RESOURCE_ID
        self.endpoint = "https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse"
        
        # 音色配置
        self.voices = {
            'cancan': 'zh_female_cancan_mars_bigtts',  # 灿灿（女声，活泼）
            'default': 'zh_female_cancan_mars_bigtts',
        }
    
    async def synthesize_to_stream(self, text: str, voice: str = 'default') -> Optional[bytes]:
        """
        文本转语音 - 返回音频二进制数据
        
        参数：
        - text: 要合成的文本
        - voice: 音色
        
        返回：
        - 音频二进制数据 或 None
        
        特点：
        - SSE流式返回
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
            
            # 调用TTS API（SSE流式）
            audio_data = await self._call_tts_api(headers, payload)
            
            return audio_data
        
        except Exception as e:
            logger.error(f"TTS调用异常：{e}")
            return None
    
    async def _call_tts_api(self, headers: dict, payload: dict) -> Optional[bytes]:
        """调用字节跳动TTS API（SSE流式）"""
        audio_data = bytearray()
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=10.0
            ) as response:
                if response.status_code != 200:
                    logger.error(f"TTS API错误：{response.status_code}")
                    return None
                
                # 解析SSE流
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    # 跳过注释
                    if line.startswith(":"):
                        continue
                    
                    # 解析data字段
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)
                            
                            # 成功响应
                            if data.get("code", 0) == 0 and "data" in data:
                                chunk = base64.b64decode(data["data"])
                                audio_data.extend(chunk)
                            
                            # 完成响应
                            elif data.get("code", 0) == 20000000:
                                break
                            
                            # 错误响应
                            elif data.get("code", 0) > 0:
                                logger.error(f"TTS错误：{data}")
                                return None
                        
                        except json.JSONDecodeError:
                            continue
        
        return bytes(audio_data) if audio_data else None


def create_audio_response(audio_data: bytes) -> StreamingResponse:
    """
    创建音频流响应
    
    特点：
    - Content-Type: audio/mpeg
    - 直接返回音频流
    - 不缓存、不存储
    - 快捷指令直接播放
    """
    return StreamingResponse(
        iter([audio_data]),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

## 4. 数据库设计

### 4.1 SQLAlchemy模型

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    nickname = Column(String, default="")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    locations = relationship("Location", back_populates="user")
    events = relationship("Event", back_populates="user")
    broadcasts = relationship("Broadcast", back_populates="user")
    schedules = relationship("UserSchedule", back_populates="user")


class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    location_type = Column(String)  # home / work
    name = Column(String, nullable=True)  # 用户命名，如"饭店"
    
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String)
    
    confidence = Column(Float, default=0.0)
    is_confirmed = Column(Boolean, default=False)
    visit_count = Column(Integer, default=0)
    
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    user = relationship("User", back_populates="locations")


class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_type = Column(String)  # connect / disconnect
    
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String)
    
    from_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    to_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    
    weather_condition = Column(String, nullable=True)
    temperature_high = Column(Float, nullable=True)
    temperature_low = Column(Float, nullable=True)
    precipitation_prob = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联
    user = relationship("User", back_populates="events")
    from_location = relationship("Location", foreign_keys=[from_location_id])
    to_location = relationship("Location", foreign_keys=[to_location_id])


class Broadcast(Base):
    __tablename__ = "broadcasts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    
    content_text = Column(String)
    content_audio_url = Column(String, nullable=True)
    
    scene = Column(String)
    ai_model = Column(String, nullable=True)
    ai_latency = Column(Float, nullable=True)
    is_fallback = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联
    user = relationship("User", back_populates="broadcasts")
    event = relationship("Event")


class UserSchedule(Base):
    __tablename__ = "user_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime)
    
    depart_time = Column(DateTime, nullable=True)
    arrive_time = Column(DateTime, nullable=True)
    leave_time = Column(DateTime, nullable=True)
    return_time = Column(DateTime, nullable=True)
    
    work_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联
    user = relationship("User", back_populates="schedules")
    work_location = relationship("Location")
```

## 5. API实现

### 5.1 事件上传接口（完整版）

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import time

router = APIRouter()

@router.post("/api/v1/events")
async def create_event(
    event_data: EventCreate,
    response_type: str = "audio",  # audio / text
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传CarPlay事件
    
    参数：
    - response_type: 返回类型
      - "audio": 返回音频流（生产环境，不存储）
      - "text": 返回纯文本（开发环境）
    
    完整流程：
    1. 记录事件
    2. 识别位置
    3. 判断场景
    4. 生成播报（AI优先，规则引擎降级）
    5. 返回音频流 或 纯文本
    """
    start_time = time.time()
    
    # 1. 创建事件记录
    event = Event(
        user_id=current_user.id,
        event_type=event_data.event_type,
        latitude=event_data.latitude,
        longitude=event_data.longitude,
        address=event_data.address,
        weather_condition=event_data.weather.condition if event_data.weather else None,
        temperature_high=event_data.weather.temp_high if event_data.weather else None,
        temperature_low=event_data.weather.temp_low if event_data.weather else None,
        precipitation_prob=event_data.weather.precipitation_prob if event_data.weather else None,
        created_at=event_data.timestamp or datetime.now()
    )
    db.add(event)
    db.commit()
    
    # 2. 识别位置
    location_service = LocationService(db)
    from_location = location_service.identify_location(
        current_user.id, 
        event_data.latitude, 
        event_data.longitude
    )
    
    if from_location:
        event.from_location_id = from_location.id
        db.commit()
    
    # 3. 触发位置学习（下车时）
    if event_data.event_type == 'disconnect':
        location_service.update_clusters(current_user, event)
    
    # 4. 判断场景
    scene_service = SceneService(db)
    scene = scene_service.detect_scene(current_user.id, event)
    
    # 5. 生成播报
    broadcast_text = None
    is_fallback = False
    ai_model = None
    ai_latency = 0
    
    # 尝试AI生成
    ai_service = AIBroadcastService()
    ai_start = time.time()
    
    broadcast_text = await ai_service.generate_broadcast(
        current_user.id, event, scene
    )
    
    if broadcast_text:
        ai_latency = time.time() - ai_start
        ai_model = settings.AI_MODEL
    else:
        # AI失败，降级到规则引擎
        is_fallback = True
        rule_service = RuleBasedBroadcastService()
        broadcast_text = rule_service.generate_broadcast(
            current_user.id, event, scene
        )
    
    # 6. 保存播报记录（只保存文本，不保存音频）
    broadcast = Broadcast(
        user_id=current_user.id,
        event_id=event.id,
        content_text=broadcast_text,
        scene=scene,
        ai_model=ai_model,
        ai_latency=ai_latency,
        is_fallback=is_fallback
    )
    db.add(broadcast)
    db.commit()
    
    # 7. 根据返回类型处理
    total_latency = time.time() - start_time
    
    if response_type == "audio":
        # 生产模式：返回音频流（不存储）
        tts_service = TTSService()
        audio_data = await tts_service.synthesize_to_stream(broadcast_text)
        
        if audio_data:
            # 直接返回音频流，用完即销毁
            return StreamingResponse(
                iter([audio_data]),
                media_type="audio/mpeg",
                headers={
                    "X-Scene": scene,
                    "X-Latency": str(round(total_latency, 3)),
                    "Cache-Control": "no-cache, no-store, must-revalidate"
                }
            )
        else:
            # TTS失败，降级返回文本
            return {
                "code": 0,
                "message": "TTS失败，返回文本",
                "data": {
                    "broadcast_text": broadcast_text,
                    "scene": scene,
                    "is_fallback": True
                }
            }
    else:
        # 开发模式：返回纯文本
        return {
            "code": 0,
            "message": "success",
            "data": {
                "broadcast_text": broadcast_text,
                "scene": scene,
                "is_fallback": is_fallback,
                "latency": round(total_latency, 3)
            }
        }
```

## 6. 配置管理

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "CarPlay AI Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development / production
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./carplay.db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30
    
    # AI配置（小米 MiMo）
    MIMO_API_KEY: str = ""  # 环境变量
    MIMO_BASE_URL: str = "https://api.xiaomimimo.com/v1"
    MIMO_MODEL: str = "mimo-v2.5-pro"
    
    # TTS配置（字节跳动）
    TTS_APP_ID: str = ""
    TTS_ACCESS_KEY: str = ""
    TTS_RESOURCE_ID: str = ""
    TTS_DEFAULT_VOICE: str = "zh_female_cancan_mars_bigtts"
    
    # 位置聚合配置
    LOCATION_CLUSTER_RADIUS: int = 200  # 米
    LOCATION_CONFIDENCE_THRESHOLD: float = 0.7
    
    # 播报配置
    MAX_BROADCAST_LENGTH: int = 100  # 字符
    AI_TIMEOUT: float = 3.0  # 秒
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 环境变量配置（.env文件）

```bash
# 应用配置
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here

# AI配置（小米 MiMo）
MIMO_API_KEY=your-mimo-api-key

# TTS配置（字节跳动）
TTS_APP_ID=your-app-id
TTS_ACCESS_KEY=your-access-key
TTS_RESOURCE_ID=your-resource-id

# 数据库配置
DATABASE_URL=sqlite:///./carplay.db
```

## 7. 部署配置

### 7.1 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 开发模式
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 7.2 docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://user:password@db:5432/carplay
      - SECRET_KEY=${SECRET_KEY}
      - AI_API_KEY=${AI_API_KEY}
      - TTS_API_KEY=${TTS_API_KEY}
    volumes:
      - ./data:/app/data
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=carplay
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

## 8. 监控和日志

```python
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 关键日志点
# 1. 事件接收
logger.info(f"收到事件: user_id={user_id}, type={event_type}, location={address}")

# 2. AI调用
logger.info(f"AI调用: user_id={user_id}, model={model}, latency={latency}s")

# 3. AI降级
logger.warning(f"AI降级: user_id={user_id}, reason={reason}")

# 4. 位置识别
logger.info(f"位置识别: user_id={user_id}, location_type={type}, confidence={confidence}")
```

## 9. 安全考虑

### 9.1 数据安全
- 位置数据加密存储
- 敏感信息脱敏
- 定期数据备份

### 9.2 接口安全
- JWT Token认证
- 请求频率限制
- 输入数据验证

### 9.3 部署安全
- HTTPS强制
- 环境变量管理
- 容器安全扫描

## 10. 扩展性设计

### 10.1 AI模型切换
```python
class AIModelFactory:
    """AI模型工厂 - 支持多种模型切换"""
    
    @staticmethod
    def create_model(model_name: str):
        if model_name == "gpt-3.5-turbo":
            return OpenAIService(model="gpt-3.5-turbo")
        elif model_name == "gpt-4":
            return OpenAIService(model="gpt-4")
        elif model_name == "qwen":
            return QwenService()
        elif model_name == "ernie":
            return ErnieService()
        else:
            raise ValueError(f"未知模型：{model_name}")
```

### 10.2 插件化设计
```python
class BroadcastPlugin:
    """播报插件接口"""
    
    def process(self, context: Dict) -> Optional[str]:
        """处理并返回内容片段"""
        pass

class WeatherPlugin(BroadcastPlugin):
    """天气插件"""
    
    def process(self, context: Dict) -> Optional[str]:
        weather = context.get('weather')
        if weather and weather.get('precipitation_prob', 0) > 60:
            return "今天有雨，记得带伞。"
        return None

class ScenePlugin(BroadcastPlugin):
    """场景插件"""
    
    def process(self, context: Dict) -> Optional[str]:
        scene = context.get('scene')
        # 根据场景返回内容
        pass
```
