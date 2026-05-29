# CarPlay AI 智能助手

基于 CarPlay 连接/断开事件的智能助手系统，通过 iPhone 快捷指令自动化采集用户出行数据，AI 分析后提供个性化的语音播报服务。

## 功能特性

- 🚗 **CarPlay 事件采集**：自动采集上车/下车事件
- 📍 **智能位置学习**：自动识别家和工作地点（支持多个）
- ⏰ **班制自动学习**：学习用户的实际工作时间模式
- 🎯 **场景智能判断**：上班通勤、下班回家、深夜回家等
- 🤖 **AI 播报生成**：使用小米 MiMo 生成自然、多样的播报
- 🔊 **TTS 语音合成**：使用字节跳动 TTS 生成高质量语音
- 👥 **多用户支持**：用户数据完全隔离

## 技术栈

- **后端框架**：FastAPI
- **数据库**：SQLite (开发) / PostgreSQL (生产)
- **AI 模型**：小米 MiMo-v2.5-pro
- **TTS 服务**：字节跳动
- **认证**：JWT

## 快速开始

### 1. 克隆项目

```bash
cd CarplayAI
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

编辑 `.env` 文件，填入你的配置：

```bash
# AI配置（小米 MiMo）
MIMO_API_KEY=your-mimo-api-key

# TTS配置（字节跳动）
TTS_APP_ID=your-app-id
TTS_ACCESS_KEY=your-access-key
TTS_RESOURCE_ID=your-resource-id
```

### 5. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

### 6. 访问 API 文档

打开浏览器访问：http://localhost:8000/docs

## API 接口

### 认证接口

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录

### 事件接口

- `POST /api/v1/events` - 上传 CarPlay 事件

### 位置接口

- `GET /api/v1/locations` - 获取所有位置
- `GET /api/v1/locations/pending` - 获取待确认位置
- `POST /api/v1/locations/confirm` - 确认位置
- `POST /api/v1/locations/rename` - 重命名位置

### 用户接口

- `GET /api/v1/user/profile` - 获取用户资料
- `PUT /api/v1/user/profile` - 更新用户资料
- `GET /api/v1/user/schedule` - 获取用户班制

## 项目结构

```
carplay-ai/
├── app/
│   ├── main.py              # 主应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── models/              # 数据模型
│   ├── schemas/             # Pydantic模型
│   ├── routers/             # API路由
│   ├── services/            # 业务逻辑
│   └── utils/               # 工具函数
├── .env                     # 环境变量
├── .env.example             # 环境变量示例
├── requirements.txt         # 依赖列表
└── README.md                # 项目说明
```

## 开发说明

### 开发模式

```bash
# 启动开发服务器（自动重载）
uvicorn app.main:app --reload --port 8000

# 运行测试
pytest
```

### 生产模式

```bash
# 使用 Docker 部署
docker-compose up -d

# 或直接运行
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## License

MIT
