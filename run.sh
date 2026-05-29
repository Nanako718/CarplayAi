#!/bin/bash

# CarPlay AI 智能助手启动脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

print_info "🚗 CarPlay AI 智能助手启动脚本"
echo ""

# 1. 检查 Python 版本
print_info "检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    print_success "Python: $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    print_success "Python: $PYTHON_VERSION"
    PYTHON_CMD="python"
else
    print_error "未找到 Python，请先安装 Python 3.8+"
    exit 1
fi

# 2. 检查虚拟环境（可选）
if [ -d "venv" ]; then
    print_info "激活虚拟环境..."
    source venv/bin/activate
    print_success "虚拟环境已激活"
else
    print_info "未找到虚拟环境，使用系统 Python"
fi

# 3. 检查依赖
print_info "检查依赖..."
if ! $PYTHON_CMD -c "import fastapi" &> /dev/null; then
    print_warning "依赖未安装，正在安装..."
    pip install -r requirements.txt
    print_success "依赖安装完成"
else
    print_success "依赖已安装"
fi

# 4. 检查 .env 文件
if [ ! -f ".env" ]; then
    print_warning ".env 文件不存在，从 .env.example 复制..."
    cp .env.example .env
    print_warning "请编辑 .env 文件配置您的 API Key"
fi

# 5. 检查配置
print_info "检查配置..."
$PYTHON_CMD -c "
from app.config import settings
print(f'  环境: {settings.ENVIRONMENT}')
print(f'  数据库: {settings.DATABASE_URL}')
print(f'  AI服务: {\"✅ 已配置\" if settings.MIMO_API_KEY else \"❌ 未配置\"}')
print(f'  TTS服务: {\"✅ 已配置\" if settings.TTS_APP_ID else \"❌ 未配置\"}')
"
echo ""

# 6. 启动参数
HOST="${1:-0.0.0.0}"
PORT="${2:-8000}"
RELOAD="${3:-true}"

# 7. 启动服务
print_info "启动服务..."
print_info "地址: http://${HOST}:${PORT}"
print_info "文档: http://${HOST}:${PORT}/docs"
echo ""

if [ "$RELOAD" = "true" ]; then
    print_info "开发模式（自动重载）"
    uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
else
    print_info "生产模式"
    uvicorn app.main:app --host "$HOST" --port "$PORT"
fi
