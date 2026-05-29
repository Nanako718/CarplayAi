"""
CarPlay AI 智能助手 - 主应用入口
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.routers import auth_router, events_router, locations_router, user_router

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CarPlay AI 智能助手后端服务",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(events_router)
app.include_router(locations_router)
app.include_router(user_router)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=FileResponse)
async def root():
    """首页（注册/登录页面）"""
    return FileResponse("static/index.html")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    logger.info(f"📦 环境: {settings.ENVIRONMENT}")
    logger.info(f"🗄️ 数据库: {settings.DATABASE_URL}")

    # 初始化数据库
    init_db()
    logger.info("✅ 数据库初始化完成")

    # 检查AI配置
    if settings.MIMO_API_KEY:
        logger.info("🤖 AI服务: 小米 MiMo 已配置")
    else:
        logger.warning("⚠️ AI服务: 未配置 MIMO_API_KEY")

    # 检查TTS配置
    if settings.TTS_APP_ID:
        logger.info("🔊 TTS服务: 字节跳动 已配置")
    else:
        logger.warning("⚠️ TTS服务: 未配置 TTS_APP_ID")

    logger.info(f"✅ 服务启动成功！访问 http://localhost:8000/docs 查看API文档")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("👋 服务关闭中...")


@app.get("/api/info")
async def api_info():
    """API信息"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": settings.APP_VERSION}
