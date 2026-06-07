"""
Signal - WebSocket 路由
实时推送通知
"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from api.services.websocket_manager import ws_manager, MessageType
from api.services.jwt_verify import verify_token

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket 连接端点

    连接方式: ws://host/ws?token={jwt_token}

    消息格式:
    - 服务端发送: {"type": "...", "data": {...}, "timestamp": "..."}
    - 客户端发送: {"type": "ping"} 或 {"type": "pong"}
    """
    # 验证 token
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    user_id = verify_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # 接受连接
    await ws_manager.connect(websocket, user_id)

    try:
        # 发送连接成功消息
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "WebSocket 连接成功",
            "user_id": user_id,
        }))

        # 消息循环
        while True:
            try:
                # 等待消息（带超时，用于心跳检测）
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0  # 60秒超时
                )

                # 解析消息
                try:
                    message = json.loads(data)
                    msg_type = message.get("type")
                except json.JSONDecodeError:
                    continue

                # 处理心跳
                if msg_type == "ping":
                    ws_manager.update_heartbeat(websocket)
                    await websocket.send_text(json.dumps({
                        "type": MessageType.PONG,
                        "timestamp": __import__('datetime').datetime.now().isoformat()
                    }))
                elif msg_type == "pong":
                    ws_manager.update_heartbeat(websocket)

            except asyncio.TimeoutError:
                # 超时，检查心跳
                import time
                last_heartbeat = ws_manager._last_heartbeat.get(websocket, 0)
                if time.time() - last_heartbeat > 120:  # 2分钟无心跳则断开
                    print(f"[WS] 用户 {user_id} 心跳超时，断开连接")
                    break
                # 发送 ping 要求心跳
                await websocket.send_text(json.dumps({"type": "ping"}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS] 错误: {e}")
    finally:
        ws_manager.disconnect(websocket, user_id)


# 导出路由
__all__ = ["router"]
