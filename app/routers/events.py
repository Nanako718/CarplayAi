"""
事件相关API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import time
from app.database import get_db
from app.models.user import User
from app.schemas.event import EventCreate
from app.schemas.response import ApiResponse, BroadcastResponse
from app.utils.auth import get_current_user
from app.services.event_service import EventService
from app.services.location_service import LocationService
from app.services.scene_service import SceneService
from app.services.ai_service import AIBroadcastService
from app.services.tts_service import TTSService

router = APIRouter(prefix="/api/v1/events", tags=["事件"])


@router.post("")
async def create_event(
    event_data: EventCreate,
    response_type: str = Query("text", description="返回类型: audio/text"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传CarPlay事件

    参数：
    - event_data: 事件数据
    - response_type: 返回类型
      - "audio": 返回音频流（生产环境，不存储）
      - "text": 返回纯文本（开发环境）

    返回：
    - audio模式：音频流（audio/mpeg）
    - text模式：JSON（包含播报文本）
    """
    start_time = time.time()

    # 1. 创建事件记录
    event_service = EventService(db)
    event = event_service.create_event(current_user, event_data)

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
    ai_service = AIBroadcastService()
    ai_start = time.time()

    # 尝试AI生成
    broadcast_text = await ai_service.generate_broadcast(
        current_user.id,
        {
            'created_at': event.created_at,
            'weather_condition': event.weather_condition,
            'temperature_high': event.temperature_high,
            'temperature_low': event.temperature_low,
            'precipitation_prob': event.precipitation_prob,
            'address': event.address
        },
        scene
    )

    is_fallback = False
    ai_latency = 0

    if broadcast_text:
        ai_latency = time.time() - ai_start
    else:
        # AI失败，降级到规则引擎
        is_fallback = True
        from app.services.broadcast_service import BroadcastService
        rule_engine = BroadcastService()
        broadcast_text = rule_engine.generate_broadcast(
            current_user.id,
            {
                'created_at': event.created_at,
                'weather_condition': event.weather_condition,
                'temperature_high': event.temperature_high,
                'temperature_low': event.temperature_low,
                'precipitation_prob': event.precipitation_prob,
                'address': event.address
            },
            scene
        )

    # 6. 根据返回类型处理
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
            return ApiResponse(
                code=0,
                message="TTS失败，返回文本",
                data=BroadcastResponse(
                    broadcast_text=broadcast_text,
                    scene=scene,
                    is_fallback=True,
                    latency=round(total_latency, 3)
                )
            )
    else:
        # 开发模式：返回纯文本
        return ApiResponse(
            code=0,
            message="success",
            data=BroadcastResponse(
                broadcast_text=broadcast_text,
                scene=scene,
                is_fallback=is_fallback,
                latency=round(total_latency, 3)
            )
        )
