"""
Signal - WebSocket 连接管理器
支持实时推送通知给在线用户
"""

import asyncio
import json
import time
from typing import Dict, Set, Optional, Any
from datetime import datetime
from fastapi import WebSocket


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # user_id -> set of WebSocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        # 心跳记录
        self._last_heartbeat: Dict[WebSocket, float] = {}
        # 统计
        self._stats = {
            "total_connections": 0,
            "messages_sent": 0,
        }

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """接受新连接"""
        await websocket.accept()
        
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)
        
        self._last_heartbeat[websocket] = time.time()
        self._stats["total_connections"] += 1
        
        print(f"[WS] 用户 {user_id} 连接，当前在线: {self.get_online_count()}")

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """断开连接"""
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]
        
        if websocket in self._last_heartbeat:
            del self._last_heartbeat[websocket]
        
        print(f"[WS] 用户 {user_id} 断开，当前在线: {self.get_online_count()}")

    async def send_to_user(self, user_id: str, message: Dict[str, Any]) -> bool:
        """发送消息给指定用户的所有连接"""
        if user_id not in self._connections:
            return False
        
        message["timestamp"] = datetime.now().isoformat()
        message_json = json.dumps(message, ensure_ascii=False)
        
        disconnected = set()
        for websocket in self._connections[user_id]:
            try:
                await websocket.send_text(message_json)
                self._stats["messages_sent"] += 1
            except Exception as e:
                print(f"[WS] 发送失败: {e}")
                disconnected.add(websocket)
        
        # 清理断开的连接
        for ws in disconnected:
            self.disconnect(ws, user_id)
        
        return len(disconnected) == 0

    async def broadcast(self, message: Dict[str, Any]) -> int:
        """广播消息给所有在线用户"""
        message["timestamp"] = datetime.now().isoformat()
        message_json = json.dumps(message, ensure_ascii=False)
        
        sent_count = 0
        for user_id, connections in list(self._connections.items()):
            disconnected = set()
            for websocket in connections:
                try:
                    await websocket.send_text(message_json)
                    sent_count += 1
                    self._stats["messages_sent"] += 1
                except Exception:
                    disconnected.add(websocket)
            
            for ws in disconnected:
                self.disconnect(ws, user_id)
        
        return sent_count

    def update_heartbeat(self, websocket: WebSocket) -> None:
        """更新心跳时间"""
        self._last_heartbeat[websocket] = time.time()

    def is_connected(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return user_id in self._connections and len(self._connections[user_id]) > 0

    def get_online_count(self) -> int:
        """获取在线用户数"""
        return len(self._connections)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "online_users": self.get_online_count(),
            "total_connections": self._stats["total_connections"],
            "messages_sent": self._stats["messages_sent"],
        }


# 全局连接管理器
ws_manager = ConnectionManager()


# 消息类型常量
class MessageType:
    BOOKMARK_ADDED = "bookmark_added"
    BOOKMARK_REMOVED = "bookmark_removed"
    HISTORY_UPDATED = "history_updated"
    TASK_COMPLETED = "task_completed"
    ANNOUNCEMENT = "announcement"
    PONG = "pong"
