# CarPlay AI 智能助手 - 部署指南

## 📦 Docker 部署

### 1. 本地开发

```bash
# 构建镜像
docker build -t carplay-ai .

# 运行容器
docker run -d \
  --name carplay-ai \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  carplay-ai

# 查看日志
docker logs -f carplay-ai

# 停止容器
docker stop carplay-ai
```

### 2. Docker Compose 部署

```bash
# 复制环境变量
cp .env.example .env

# 编辑 .env 文件，填入配置
vim .env

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. 生产环境部署

```bash
# 使用 Nginx 反向代理
docker-compose --profile production up -d
```

---

## 🚀 GitHub Actions CI/CD

### 1. 配置 Secrets

在 GitHub 仓库的 Settings > Secrets and variables > Actions 中添加：

| Secret | 说明 |
|--------|------|
| `DOCKER_USERNAME` | Docker Hub 用户名 |
| `DOCKER_PASSWORD` | Docker Hub 密码 |
| `SERVER_HOST` | 服务器 IP 地址 |
| `SERVER_USER` | 服务器用户名 |
| `SERVER_SSH_KEY` | 服务器 SSH 私钥 |

### 2. 推送代码触发 CI/CD

```bash
# 推送到 main 分支
git push origin main

# CI/CD 流程：
# 1. 代码检查 (lint)
# 2. 单元测试 (test)
# 3. Docker 构建 (build)
# 4. 部署到服务器 (deploy)
```

### 3. 查看构建状态

在 GitHub 仓库的 Actions 页面查看构建状态。

---

## 🔧 环境变量配置

### .env 文件示例

```bash
# 应用配置
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here

# 数据库配置
DATABASE_URL=sqlite:///./data/carplay.db

# AI配置（小米 MiMo）
MIMO_API_KEY=your-mimo-api-key
MIMO_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5-pro

# TTS配置（字节跳动）
TTS_APP_ID=your-app-id
TTS_ACCESS_KEY=your-access-key
TTS_RESOURCE_ID=seed-tts-2.0
TTS_DEFAULT_VOICE=zh_female_xiaohe_uranus_bigtts

# 播报配置
AI_TIMEOUT=30.0
```

---

## 📊 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/health

# 响应示例
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## 🔍 故障排查

### 1. 查看容器日志

```bash
# Docker
docker logs carplay-ai

# Docker Compose
docker-compose logs app
```

### 2. 进入容器调试

```bash
# 进入容器
docker exec -it carplay-ai bash

# 查看配置
python -c "from app.config import settings; print(settings)"
```

### 3. 重启服务

```bash
# Docker
docker restart carplay-ai

# Docker Compose
docker-compose restart
```

---

## 📁 目录结构

```
/opt/carplay-ai/
├── app/                    # 应用代码
├── data/                   # 数据库文件
│   └── carplay.db
├── logs/                   # 日志文件
├── .env                    # 环境变量
├── docker-compose.yml
├── Dockerfile
└── nginx/                  # Nginx配置（可选）
    ├── nginx.conf
    └── ssl/
```

---

## 🔐 安全建议

1. **修改默认密码** - 更改 `SECRET_KEY`
2. **使用 HTTPS** - 配置 Nginx + SSL
3. **限制访问** - 配置防火墙
4. **定期备份** - 备份 `data/` 目录
5. **监控日志** - 定期检查 `logs/` 目录
