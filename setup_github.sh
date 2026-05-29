#!/bin/bash

# CarPlay AI - GitHub 仓库初始化脚本

set -e

echo "🚀 初始化 GitHub 仓库"
echo ""

# 检查是否已初始化 Git
if [ ! -d ".git" ]; then
    echo "📦 初始化 Git..."
    git init
fi

# 添加所有文件
echo "📁 添加文件..."
git add .

# 提交
echo "💾 提交代码..."
git commit -m "初始化 CarPlay AI 项目

- FastAPI 后端服务
- 小米 MiMo AI 播报生成
- 字节跳动 TTS 语音合成
- Docker 容器化
- GitHub Actions CI/CD
- 用户学习模型
- 场景智能判断

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"

# 提示用户
echo ""
echo "✅ Git 仓库已初始化！"
echo ""
echo "📋 下一步："
echo ""
echo "1. 在 GitHub 创建新仓库"
echo "   访问: https://github.com/new"
echo ""
echo "2. 添加远程仓库"
echo "   git remote add origin https://github.com/your-username/carplay-ai.git"
echo ""
echo "3. 推送代码"
echo "   git push -u origin main"
echo ""
echo "4. 配置 GitHub Secrets"
echo "   访问: https://github.com/your-username/carplay-ai/settings/secrets/actions"
echo ""
echo "   需要添加的 Secrets:"
echo "   - DOCKER_USERNAME: Docker Hub 用户名"
echo "   - DOCKER_PASSWORD: Docker Hub 密码"
echo "   - SERVER_HOST: 服务器 IP（可选）"
echo "   - SERVER_USER: 服务器用户名（可选）"
echo "   - SERVER_SSH_KEY: 服务器 SSH 私钥（可选）"
echo ""
echo "5. 推送代码触发 CI/CD"
echo "   git push origin main"
echo ""
