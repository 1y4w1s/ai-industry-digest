"""
Signal - JWT 验证工具
使用 Supabase 客户端验证 JWT token

认证链路（严格模式）：
  1. demo-user → 返回 demo UUID（仅未登录浏览公开内容）
  2. JWT → 使用 Supabase auth.get_user() 验证 → 返回 user_id
  3. 全部失败 → 返回 None

  不再接受裸 UUID 作为认证凭证。
"""

import os
from typing import Optional

from supabase import create_client, Client

# Demo 用户配置
DEMO_USER_ID = "demo-user"
DEMO_USER_UUID = "00000000-0000-0000-0000-000000000001"

# Supabase 客户端（延迟初始化）
_supabase_client: Optional[Client] = None


def _get_supabase_client() -> Client:
    """获取缓存的 Supabase 客户端"""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL", "https://vobpkdrujixghvttgkuq.supabase.co")
        key = os.getenv("SUPABASE_KEY", "")
        if not url or not key:
            raise ValueError("请设置环境变量 SUPABASE_URL 和 SUPABASE_KEY")
        _supabase_client = create_client(url, key)
    return _supabase_client


def verify_token(token: str) -> Optional[str]:
    """验证 JWT token 并返回 user_id (sub)
    
    验证链路（严格模式）：
      1. demo-user → 返回 demo UUID（仅用于未登录浏览公开内容）
      2. JWT → 使用 Supabase auth.get_user() 验证 → 返回 user_id
      3. 全部失败 → 返回 None
    """
    if not token:
        return None
    
    # 去掉 Bearer 前缀
    if token.startswith("Bearer "):
        token = token[7:]
    
    # 1. demo 用户（仅限未登录浏览公开内容）
    if token == DEMO_USER_ID:
        return DEMO_USER_UUID
    
    # 2. 使用 Supabase 客户端验证 JWT
    try:
        supabase = _get_supabase_client()
        response = supabase.auth.get_user(token)
        if response.user and response.user.id:
            return response.user.id
    except Exception as e:
        print(f"[JWT] 验证失败: {type(e).__name__}: {str(e)[:100]}")
    
    return None  # 验证失败
