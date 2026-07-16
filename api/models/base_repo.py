"""
Signal · 仓储层基类
所有 Repository 继承此类，统一管理 Supabase 客户端连接。
"""

from typing import Optional
from supabase import Client


class BaseRepository:
    """仓储基类，持有 Supabase 客户端引用"""

    def __init__(self, client: Client):
        self._client = client

    @property
    def client(self) -> Client:
        return self._client
