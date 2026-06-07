"""
Signal - 管理员 API 路由
包含缓存统计、系统监控等管理功能
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from services.cache import cache
from services.jwt_verify import verify_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """获取当前用户 ID"""
    token = credentials.credentials
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    return user_id


@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息

    Returns:
        {
            "available": bool,
            "hits": int,
            "misses": int,
            "errors": int,
            "hit_rate": float,
            "used_memory": str,
            "keys": int
        }
    """
    return cache.get_stats()


@router.post("/cache/clear")
async def clear_cache(pattern: str = "*", user_id: str = Depends(get_current_user)) -> Dict[str, Any]:
    """清除缓存

    Args:
        pattern: 缓存键模式，默认清除所有

    Returns:
        {"deleted": int}
    """
    # TODO: 添加管理员权限检查
    deleted = cache.delete_pattern(pattern)
    return {"deleted": deleted}


@router.post("/cache/reset-stats")
async def reset_cache_stats(user_id: str = Depends(get_current_user)) -> Dict[str, str]:
    """重置缓存统计"""
    # TODO: 添加管理员权限检查
    cache.reset_stats()
    return {"status": "ok"}
