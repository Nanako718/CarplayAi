# CarPlay AI 智能助手 - 开发需求文档（最终版）

## 1. 项目概述

### 1.1 项目背景
开发一个基于CarPlay连接/断开事件的智能助手系统，通过iPhone快捷指令自动化采集用户出行数据，AI分析后提供个性化的语音播报服务。

### 1.2 核心价值
- 智能问候：上车时根据时间、天气、位置提供个性化问候
- 出行建议：根据天气、时间提供实用建议（如雨天提醒带伞、不适合洗车等）
- 通勤学习：自动识别家和工作地点，智能判断上下班场景
- 情感关怀：下班晚时提供安慰话语，节假日特殊问候
- AI播报：接入AI大模型，生成自然、多样化的播报内容

### 1.3 设计决策
| 决策项 | 方案选择 | 说明 |
|--------|----------|------|
| 工作地点 | 自动识别 + 用户确认 | 系统识别常去地点，用户可命名 |
| 班制处理 | 自动学习 | 通过历史数据学习用户实际工作时间 |
| 播报生成 | AI大模型 | 接入AI生成自然、多样的播报内容 |
| 播报格式 | 开发=纯文本，生产=音频 | 开发方便调试，生产直接播放 |

## 2. 功能需求

### 2.1 数据采集模块

#### 2.1.1 CarPlay连接事件（上车）
```
采集数据：
- CarPlay状态：连接
- 经度：xxxxx
- 纬度：xxxxx
- 位置：详细地址
- 时间：YYYY-MM-DD HH:mm:ss
- 天气信息：
  - 天气状况
  - 最高温
  - 最低温
  - 降水概率
```

#### 2.1.2 CarPlay断开事件（下车）
```
采集数据：
- CarPlay状态：未连接
- 经度：xxxxx
- 纬度：xxxxx
- 位置：详细地址
- 时间：YYYY-MM-DD HH:mm:ss
```

### 2.2 智能分析模块

#### 2.2.1 位置学习（多工作地点支持）

**地点类型定义**：
| 类型 | 说明 | 识别方式 |
|------|------|----------|
| 家 | 夜间停留地点 | 夜间(22:00-06:00)下车频次最高 |
| 工作地点1 | 主要工作地点 | 单次停留>4小时 且 频次>3次/周 |
| 工作地点2 | 次要工作地点 | 同上，但频次较低 |
| 工作地点N | 其他工作地点 | 同上 |

**识别算法**：
```python
def identify_location_type(cluster, user_events):
    """
    识别位置类型
    支持：1个家 + N个工作地点
    """
    # 1. 家识别：夜间下车频次最高
    night_visits = count_visits_in_time_range(events, 22, 6)
    if night_visits > total_visits * 0.3:
        return 'home', confidence
    
    # 2. 工作地点识别：长时间停留 + 高频次
    long_stays = count_long_stays(events, min_hours=4)
    weekly_frequency = calculate_weekly_frequency(events)
    
    if long_stays > 10 and weekly_frequency > 3:
        return 'work', confidence
    
    return 'other', 0
```

**用户确认机制**：
```json
// 系统识别后，推送给用户确认
{
  "detected_locations": [
    {
      "id": 1,
      "type": "home",
      "address": "xxx小区",
      "confidence": 0.95,
      "visit_count": 120,
      "status": "confirmed"
    },
    {
      "id": 2,
      "type": "work",
      "address": "xxx饭店",
      "confidence": 0.85,
      "visit_count": 45,
      "status": "pending_confirm",
      "user_name": null  // 用户可命名
    },
    {
      "id": 3,
      "type": "work",
      "address": "xxx KTV",
      "confidence": 0.72,
      "visit_count": 28,
      "status": "pending_confirm",
      "user_name": null
    }
  ]
}
```

#### 2.2.2 班制自动学习

**学习算法**：
```python
class WorkScheduleLearner:
    """班制自动学习"""
    
    def learn_user_schedule(self, user_id):
        """
        学习用户的实际工作时间模式
        不预设白班/夜班，完全基于数据
        """
        # 1. 获取最近30天的"从家出发"事件
        depart_from_home = get_events(user_id, type='connect', from='home')
        
        # 2. 分析出发时间分布
        time_distribution = analyze_time_distribution(depart_from_home)
        
        # 3. 找出高频时段
        peak_hours = find_peak_hours(time_distribution, threshold=0.2)
        
        # 4. 返回用户的工作模式
        return {
            "typical_depart_times": peak_hours,  # [7, 8, 9] 或 [21, 22, 23]
            "schedule_type": classify_schedule(peak_hours),  # day/night/flexible
            "confidence": calculate_confidence(time_distribution)
        }
    
    def classify_schedule(self, peak_hours):
        """根据高频时段分类班制"""
        avg_hour = sum(peak_hours) / len(peak_hours)
        
        if 5 <= avg_hour < 12:
            return "day_shift"      # 白班
        elif 18 <= avg_hour or avg_hour < 3:
            return "night_shift"    # 夜班
        else:
            return "flexible"       # 弹性/倒班
```

**场景判断逻辑调整**：
```python
def detect_scene(user, event):
    """
    场景判断 - 基于用户实际模式
    """
    # 获取用户的工作时间模式
    user_schedule = get_user_schedule(user.id)
    typical_depart = user_schedule['typical_depart_times']
    
    # 判断是否在正常工作时间范围内
    current_hour = event.created_at.hour
    is_normal_work_time = any(
        abs(current_hour - t) <= 1 
        for t in typical_depart
    )
    
    # 判断场景
    if event.event_type == 'connect':
        location_type = get_location_type(user, event)
        
        if location_type == 'home':
            if is_normal_work_time:
                return 'commute_to_work'  # 正常上班
            else:
                return 'irregular_departure'  # 非正常时间出发
        
        elif location_type == 'work':
            # 从工作地点出发 = 下班
            work_duration = get_work_duration(user, event)
            if work_duration > 8:
                return 'overtime_leave'  # 加班下班
            else:
                return 'normal_leave'  # 正常下班
```

### 2.3 AI播报生成模块

#### 2.3.1 AI接入方案

**当前使用**：小米 MiMo-v2.5-pro
- API地址：https://api.xiaomimimo.com/v1
- OpenAI兼容格式
- 支持中文，质量好
- 速度快，性价比高

#### 2.3.2 AI Prompt设计

```python
BROADCAST_PROMPT = """
你是一个温暖贴心的车载AI助手。请根据以下信息生成一段简短的播报内容。

## 当前场景
- 场景类型：{scene}  # 如：上班通勤、下班回家、深夜回家
- 当前时间：{time}
- 出发地点：{from_location}
- 目的地：{to_location}

## 天气信息
- 天气：{weather_condition}
- 最高温：{temp_high}°C
- 最低温：{temp_low}°C
- 降水概率：{precipitation_prob}%

## 用户画像
- 作息模式：{schedule_type}  # 如：白班、夜班、弹性
- 通勤时长：约{commute_duration}分钟

## 要求
1. 长度控制在30-50字，适合TTS播放（约15秒）
2. 语气自然、亲切、温暖
3. 结合天气、时间、场景给出实用建议
4. 如果是深夜回家，表达关心和安慰
5. 如果是雨天，提醒带伞或注意安全
6. 避免重复，每次生成不同的表达

请直接输出播报内容，不要有其他说明。
"""
```

#### 2.3.3 AI生成示例

**场景：工作日早上，从家出发，天气晴**
```
输入：
- scene: commute_to_work
- time: 2024-01-15 08:30
- from: xxx小区
- work_schedule: day_shift
- weather: 晴天，25°C

AI输出示例（每次不同）：
1. "早上好！今天天气不错，适合出行。新的一天，加油哦！"
2. "早安！阳光明媚的一天开始了，祝你工作顺利！"
3. "嗨，早上好！今天温度适宜，记得多喝水哦。"
```

**场景：深夜11点，从KTV下班**
```
输入：
- scene: overtime_leave
- time: 2024-01-15 23:00
- from: xxx KTV
- work_schedule: flexible

AI输出示例：
1. "这么晚才下班，辛苦了！早点休息，别太累了。"
2. "夜深了，路上注意安全。今天辛苦啦，好好休息！"
3. "这么晚还在工作，真的很不容易。回家早点睡哦！"
```

**场景：雨天，周末出行**
```
输入：
- scene: weekend_trip
- time: 2024-01-20 10:00
- weather: 小雨，降水概率80%

AI输出示例：
1. "外面在下雨呢，记得带伞哦！雨天路滑，小心驾驶。"
2. "今天有雨，出门别忘了带伞。雨天视线不好，注意安全！"
3. "下雨天出门，一定要注意防雨哦。开车慢点！"
```

#### 2.3.4 AI调用优化

**缓存策略**：
```python
class AIBroadcastCache:
    """AI播报缓存 - 避免重复调用"""
    
    def __init__(self):
        self.cache = {}
        self.recent_broadcasts = {}  # 用户最近播报记录
    
    def get_cache_key(self, user_id, scene, weather, time_bucket):
        """
        生成缓存键
        time_bucket: 时间桶（如"morning_8"表示8点档）
        """
        return f"{user_id}_{scene}_{weather}_{time_bucket}"
    
    def should_call_ai(self, user_id, scene, weather, time_bucket):
        """判断是否需要调用AI"""
        key = self.get_cache_key(user_id, scene, weather, time_bucket)
        
        # 1. 检查是否有缓存
        if key in self.cache:
            return False
        
        # 2. 检查最近播报是否太相似
        recent = self.recent_broadcasts.get(user_id, [])
        if is_too_similar(scene, weather, recent):
            return False
        
        return True
```

**降级策略**：
```python
async def generate_broadcast(user, event, scene):
    """
    生成播报 - 带降级策略
    """
    try:
        # 1. 尝试AI生成（设置3秒超时）
        broadcast = await asyncio.wait_for(
            call_ai_broadcast(user, event, scene),
            timeout=3.0
        )
        return broadcast
    
    except asyncio.TimeoutError:
        # 2. AI超时，使用规则引擎降级
        logger.warning(f"AI调用超时，用户{user.id}，使用规则引擎")
        return rule_based_broadcast(user, event, scene)
    
    except Exception as e:
        # 3. AI异常，使用规则引擎降级
        logger.error(f"AI调用失败：{e}")
        return rule_based_broadcast(user, event, scene)
```

### 2.4 TTS语音合成模块

#### 2.4.1 方案选择

| 方案 | 优势 | 劣势 | 推荐 |
|------|------|------|------|
| iPhone本地TTS | 免费、无需后端处理 | 音质一般、无情感 | 开发阶段 |
| 云端TTS（字节跳动） | 音质好、多音色 | 需付费、增加延迟 | 生产环境 |

**当前使用**：字节跳动 TTS
- API地址：https://openspeech.bytedance.com/api/v3/tts/unidirectional/sse
- SSE流式返回
- 音色：zh_female_cancan_mars_bigtts（女声，活泼）
- 格式：mp3，采样率：24000

**音频处理策略**：
- 不存储音频文件
- 直接返回音频流给客户端
- 播放完成后自动销毁
- 节省存储成本

#### 2.4.2 接口设计

```python
# 开发模式：返回纯文本
@router.post("/api/v1/events")
async def create_event(event_data, response_type="text"):
    broadcast_text = await generate_broadcast(user, event, scene)
    
    if response_type == "text":
        # 开发模式：返回纯文本
        return {
            "code": 0,
            "data": {
                "broadcast_text": broadcast_text
            }
        }
    else:
        # 生产模式：返回音频流（不存储）
        audio_data = await text_to_speech(broadcast_text)
        return StreamingResponse(
            iter([audio_data]),
            media_type="audio/mpeg"
        )
```

#### 2.4.3 TTS接入（阿里云示例）

```python
import httpx

class TTSService:
    """TTS语音合成服务 - 直接返回音频流"""
    
    def __init__(self):
        self.api_key = settings.TTS_API_KEY
        self.endpoint = "https://nls-gateway.cn-shanghai.aliyuncs.com"
    
    async def synthesize_to_stream(self, text, voice="xiaoyun"):
        """
        文本转语音 - 返回音频二进制数据
        
        参数：
        - text: 要合成的文本
        - voice: 音色（xiaoyun=小云，xiaogang=小刚）
        
        返回：
        - 音频二进制数据（不存储，直接返回播放）
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.endpoint}/rest/v1/tts",
                json={
                    "appkey": self.api_key,
                    "text": text,
                    "voice": voice,
                    "format": "mp3"
                }
            )
            
            if response.status_code == 200:
                # 直接返回音频二进制，不存储
                return response.content
            else:
                return None
```

### 2.5 用户管理模块

#### 2.5.1 多用户支持
- 用户注册/登录（账号密码）
- 用户数据完全隔离
- 个性化配置

#### 2.5.2 用户配置
```json
{
  "user_id": 123,
  "nickname": "张三",
  
  // 位置配置（系统学习 + 用户确认）
  "locations": {
    "home": {
      "address": "xxx小区",
      "lat": 34.xxx,
      "lng": 115.xxx,
      "confidence": 0.95,
      "confirmed": true
    },
    "work_places": [
      {
        "id": 1,
        "name": "饭店",  // 用户命名
        "address": "xxx路xxx号",
        "lat": 34.xxx,
        "lng": 115.xxx,
        "confidence": 0.85,
        "confirmed": true
      },
      {
        "id": 2,
        "name": "KTV",
        "address": "xxx广场",
        "lat": 34.xxx,
        "lng": 115.xxx,
        "confidence": 0.72,
        "confirmed": false  // 待确认
      }
    ]
  },
  
  // 班制配置（自动学习）
  "work_schedule": {
    "learned_type": "flexible",  // day_shift/night_shift/flexible
    "typical_depart_times": [8, 9, 21, 22],  // 高频出发时间
    "confidence": 0.78,
    "last_updated": "2024-01-15"
  },
  
  // 播报偏好
  "broadcast_preferences": {
    "voice": "xiaoyun",  // TTS音色
    "speed": 1.0,  // 语速
    "enable_weather_advice": true,
    "enable_care_message": true
  }
}
```

## 3. 非功能需求

### 3.1 性能要求
- API响应时间：< 3秒（含AI调用）
- 纯规则引擎响应：< 500ms
- 支持并发用户：1000+

### 3.2 可靠性
- 系统可用性：99.9%
- AI降级：AI不可用时自动切换规则引擎
- 数据持久化：用户数据永久保存

### 3.3 安全性
- 用户认证：JWT Token
- 数据加密：HTTPS传输
- 隐私保护：位置数据脱敏存储

### 3.4 可扩展性
- 支持多种AI模型切换
- 支持多种TTS服务切换
- 支持多种播报场景扩展

## 4. 数据模型

### 4.1 用户表 (users)
```sql
- id: 用户唯一标识
- username: 用户名（登录用）
- password_hash: 密码哈希
- nickname: 用户昵称
- created_at: 创建时间
- updated_at: 更新时间
```

### 4.2 位置表 (locations)
```sql
- id: 位置唯一标识
- user_id: 用户ID
- location_type: 位置类型 (home/work)
- name: 位置名称（用户命名，如"饭店"）
- latitude: 纬度
- longitude: 经度
- address: 地址
- confidence: 置信度
- is_confirmed: 是否已确认
- visit_count: 访问次数
- last_visit: 最后访问时间
- created_at: 创建时间
- updated_at: 更新时间
```

### 4.3 事件记录表 (events)
```sql
- id: 事件唯一标识
- user_id: 用户ID
- event_type: 事件类型 (connect/disconnect)
- latitude: 纬度
- longitude: 经度
- address: 地址
- from_location_id: 出发地点ID
- to_location_id: 到达地点ID
- weather_condition: 天气状况
- temperature_high: 最高温
- temperature_low: 最低温
- precipitation_prob: 降水概率
- created_at: 事件时间
```

### 4.4 播报记录表 (broadcasts)
```sql
- id: 播报ID
- user_id: 用户ID
- event_id: 关联事件ID
- content_text: 播报文本
- content_audio_url: 音频URL（生产环境）
- scene: 场景类型
- ai_model: 使用的AI模型
- ai_latency: AI响应时间
- is_fallback: 是否降级到规则引擎
- created_at: 创建时间
```

### 4.5 用户作息表 (user_schedules)
```sql
- id: 记录ID
- user_id: 用户ID
- date: 日期
- depart_time: 从家出发时间
- arrive_time: 到达工作地时间
- leave_time: 离开工作地时间
- return_time: 到家时间
- work_location_id: 工作地点ID
- created_at: 创建时间
```

## 5. 接口设计

### 5.1 数据上传接口
```
POST /api/v1/events
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "event_type": "connect",  // connect/disconnect
  "latitude": 34.xxx,
  "longitude": 115.xxx,
  "address": "商丘示范区中电科技园A区H栋",
  "weather": {
    "condition": "局部多云",
    "temp_high": 21,
    "temp_low": 10,
    "precipitation_prob": 0
  },
  "timestamp": "2026-05-26T08:30:00+08:00"
}

Response（开发模式）:
{
  "code": 0,
  "message": "success",
  "data": {
    "broadcast_text": "早上好！今天天气不错，适合出行。路上注意安全！",
    "broadcast_audio": null,
    "scene": "commute_to_work"
  }
}

Response（生产模式）:
{
  "code": 0,
  "message": "success",
  "data": {
    "broadcast_text": "早上好！今天天气不错，适合出行。路上注意安全！",
    "broadcast_audio": "https://xxx.oss.aliyuncs.com/broadcast/123.mp3",
    "scene": "commute_to_work"
  }
}
```

### 5.2 用户配置接口
```
GET /api/v1/user/profile
PUT /api/v1/user/profile

Response:
{
  "user_id": 123,
  "nickname": "张三",
  "locations": { ... },
  "work_schedule": { ... },
  "broadcast_preferences": { ... }
}
```

### 5.3 位置管理接口
```
GET /api/v1/locations                    # 获取所有位置
POST /api/v1/locations/{id}/confirm      # 确认位置
PUT /api/v1/locations/{id}/name          # 命名位置
DELETE /api/v1/locations/{id}            # 删除位置
```

### 5.4 位置学习结果接口
```
GET /api/v1/locations/pending            # 获取待确认的位置

Response:
{
  "pending_locations": [
    {
      "id": 5,
      "type": "work",
      "address": "xxx KTV",
      "lat": 34.xxx,
      "lng": 115.xxx,
      "confidence": 0.72,
      "visit_count": 28,
      "first_seen": "2024-01-01",
      "last_seen": "2024-01-15"
    }
  ]
}
```

## 6. 业务流程

### 6.1 上车流程
```
1. CarPlay连接触发
2. 快捷指令采集位置、天气数据
3. 调用API上传数据
4. 后端处理：
   a. 记录事件
   b. 识别出发地点（家/工作地点）
   c. 判断场景（上班/下班/周末出行）
   d. 调用AI生成播报（3秒超时）
   e. AI失败则降级到规则引擎
   f. 返回播报文本/音频URL
5. 快捷指令播放音频 或 TTS朗读文本
```

### 6.2 位置学习流程
```
1. 每次下车事件触发位置分析
2. 与已有位置聚合对比（200米半径）
3. 更新位置聚合数据
4. 重新计算置信度
5. 置信度 > 70% 时，推送给用户确认
6. 用户确认后，标记为正式位置
```

### 6.3 班制学习流程
```
1. 每天下班事件触发班制分析
2. 统计最近30天的出发时间分布
3. 识别高频时段
4. 更新用户的作息模式
5. 用于场景判断和AI播报
```

## 7. 开发阶段

### Phase 1: MVP (2周)
- [ ] 基础API服务搭建（FastAPI）
- [ ] 数据库设计（SQLAlchemy + SQLite）
- [ ] 用户注册/登录（JWT）
- [ ] 事件上传接口
- [ ] 基础播报生成（规则引擎）
- [ ] 简单位置聚合

### Phase 2: 智能化 (2周)
- [ ] 位置学习算法（多工作地点）
- [ ] 班制自动学习
- [ ] 场景判断优化
- [ ] 用户位置确认机制
- [ ] 位置命名功能

### Phase 3: AI接入 (1.5周)
- [ ] AI播报生成（GPT-3.5/国产模型）
- [ ] Prompt设计和优化
- [ ] AI降级策略
- [ ] AI调用缓存
- [ ] 播报多样性测试

### Phase 4: TTS接入 (1周)
- [ ] TTS服务接入（阿里云/腾讯云）
- [ ] 音频文件生成和存储
- [ ] 音频URL返回
- [ ] 开发/生产模式切换

### Phase 5: 优化 (1周)
- [ ] 性能优化（缓存、索引）
- [ ] 错误处理完善
- [ ] 日志和监控
- [ ] 部署文档

**总计：约 7-8 周**

## 8. 验收标准

### 8.1 功能验收
- [ ] CarPlay连接数据成功上传
- [ ] 多工作地点正确识别（支持3个以上）
- [ ] 用户可确认和命名工作地点
- [ ] 班制自动学习准确率 > 80%
- [ ] AI播报生成成功（3秒内响应）
- [ ] AI不可用时自动降级到规则引擎
- [ ] 多用户数据完全隔离

### 8.2 性能验收
- [ ] AI播报响应时间 < 3秒
- [ ] 规则引擎响应时间 < 500ms
- [ ] 系统稳定运行7天无故障
- [ ] 支持100并发用户

### 8.3 用户体验验收
- [ ] 播报内容自然、多样（无重复感）
- [ ] 位置识别准确率 > 85%
- [ ] 播报生成成功率 > 99%
- [ ] 语音播放流畅
