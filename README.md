# CarPlay AI 智能助手

基于 CarPlay 连接/断开事件的智能助手系统，通过 iPhone 快捷指令自动化采集用户出行数据，AI 分析后提供个性化的语音播报服务。

[![CI/CD](https://github.com/your-username/carplay-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/carplay-ai/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ 功能特性

- 🚗 **CarPlay 事件采集**：自动采集上车/下车事件
- 📍 **智能位置学习**：自动识别家和工作地点（支持多个）
- ⏰ **班制自动学习**：学习用户的实际工作时间模式
- 🎯 **场景智能判断**：上班通勤、下班回家、深夜回家等
- 🤖 **AI 播报生成**：使用小米 MiMo 生成自然、多样的播报
- 🔊 **TTS 语音合成**：使用字节跳动 TTS 生成高质量语音
- 👥 **多用户支持**：用户数据完全隔离

## 🛠️ 技术栈

- **后端框架**：FastAPI
- **数据库**：SQLite (开发) / PostgreSQL (生产)
- **AI 模型**：小米 MiMo-v2.5-pro
- **TTS 服务**：字节跳动
- **认证**：JWT
- **容器化**：Docker

## 🚀 快速开始

### 方式一：本地开发

```bash
# 1. 克隆项目
git clone https://github.com/your-username/carplay-ai.git
cd carplay-ai

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的配置

# 5. 启动服务
./run.sh
```

### 方式二：Docker 部署

```bash
# 1. 克隆项目
git clone https://github.com/your-username/carplay-ai.git
cd carplay-ai

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的配置

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f
```

### 方式三：Docker Hub

```bash
docker run -d \
  --name carplay-ai \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  your-username/carplay-ai:latest
```

## 📖 API 文档

启动服务后访问：http://localhost:8000/docs

### 主要接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/events` | POST | 上传 CarPlay 事件 |
| `/api/v1/locations` | GET | 获取所有位置 |
| `/api/v1/user/profile` | GET | 获取用户资料 |

## 📱 快捷指令配置

详见 [SHORTCUT_GUIDE.md](./SHORTCUT_GUIDE.md)

## 🏗️ 项目结构

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
├── static/                  # 前端页面
├── .github/workflows/       # CI/CD 流程
├── Dockerfile               # Docker 配置
├── docker-compose.yml       # Docker Compose
├── .env.example             # 环境变量示例
├── requirements.txt         # 依赖列表
└── README.md                # 项目说明
```

## 🧪 开发

```bash
# 运行测试
pytest

# 代码检查
flake8 app/
black --check app/

# 格式化代码
black app/
isort app/
```

## 📦 部署

详见 [DEPLOY.md](./DEPLOY.md)

## 📄 License

MIT
