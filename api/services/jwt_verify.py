"""
Signal - JWT 验证工具
从 Supabase JWKS 端点获取公钥并验证 JWT token
"""

import os
import re
import time
from typing import Optional

import jwt
from jwt import PyJWKClient

# Supabase 项目配置
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://vobpkdrujixghvttgkuq.supabase.co")
JWKS_URL = f"{SUPABASE_URL}/.well-known/jwks.json"

# 缓存 JWKS 客户端（减少 HTTP 请求）
_jwks_client: Optional[PyJWKClient] = None
_jwks_cache_time = 0
_JWKS_TTL = 3600  # 1 小时重新获取一次


def _get_jwks_client() -> PyJWKClient:
    """获取缓存的 JWKS 客户端"""
    global _jwks_client, _jwks_cache_time
    now = time.time()
    if _jwks_client is None or now - _jwks_cache_time > _JWKS_TTL:
        _jwks_client = PyJWKClient(JWKS_URL, cache_keys=True)
        _jwks_cache_time = now
    return _jwks_client


# Demo 用户配置
DEMO_USER_ID = "demo-user"
DEMO_USER_UUID = "00000000-0000-0000-0000-000000000001"
UUID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'


def verify_token(token: str) -> Optional[str]:
    """验证 JWT token 并返回 user_id (sub)
    
    验证链路：
      1. demo-user → 返回 demo UUID
      2. 已经是 UUID → 直接返回
      3. JWT → 从 Supabase JWKS 获取公钥验证签名 → 返回 sub
      4. 全部失败 → 返回 None
    """
    if not token:
        return None
    
    # 去掉 Bearer 前缀
    if token.startswith("Bearer "):
        token = token[7:]
    
    # 1. demo 用户
    if token == DEMO_USER_ID:
        return DEMO_USER_UUID
    
    # 2. 已经是 UUID
    if re.match(UUID_PATTERN, token.lower()):
        return token
    
    # 3. JWT 验证
    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        decoded = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience="authenticated",
            options={"verify_exp": True},
        )
        user_id = decoded.get("sub")
        if user_id:
            return user_id
    except jwt.ExpiredSignatureError:
        pass  # token 过期
    except Exception:
        pass  # 其他验证失败
    
    return None
