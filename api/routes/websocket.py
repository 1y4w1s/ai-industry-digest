"""
Signal - WebSocket 路由
实时推送通知
"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional

from api.services.websocket_manager import ws_manager, MessageType
from api.services.jwt_verify import verify_token

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接端点

    连接方式:
    - 推荐: new WebSocket(url, [token])  -> 通过 Sec-WebSocket-Protocol header 传递
    - 兼容: ws://host/ws?token=xxx       -> 通过 URL query 传递

    消息格式:
    - 服务端发送: {"type": "...", "data": {...}, "timestamp": "..."}
    - 客户端发送: {"type": "ping"} 或 {"type": "pong"}
    """
    # 获取 token：优先从 Sec-WebSocket-Protocol header，兼容 URL query
    protocols = websocket.headers.get("sec-websocket-protocol", "")
    token = protocols.split(",")[0].strip() if protocols and protocols != "websocket" else None
    if not token:
        token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    user_id = verify_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # 接受连接（若通过 subprotocol 传递 token，需原样返回）
    if protocols and protocols != "websocket":
        await websocket.accept(subprotocol=token)
    else:
        await websocket.accept()

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
                    timeout=30
                )
            except asyncio.TimeoutError:
                # 心跳检测
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
                continue

            # 处理消息
            msg = json.loads(data)
            msg_type = msg.get("type", "")

            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif msg_type == "pong":
                pass
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"未知消息类型: {msg_type}"
                }))

    except WebSocketDisconnect:
        print(f"[WS] 用户 {user_id} 断开连接")
    except Exception as e:
        print(f"[WS] 连接错误: {e}")
    finally:
        ws_manager.disconnect(user_id)
