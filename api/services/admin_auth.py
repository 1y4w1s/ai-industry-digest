"""
Signal - 管理员权限校验服务
"""

from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from api.services.jwt_verify import verify_token
from api.models.database import get_db

security = HTTPBearer()
db = get_db()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """获取当前用户 ID"""
    token = credentials.credentials
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    return user_id


async def get_current_admin(
    user_id: str = Depends(get_current_user)
) -> str:
    """获取当前管理员用户 ID，非管理员抛出 403"""
    profile = db.get_or_create_profile(user_id)
    
    if profile.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )
    
    return user_id


def is_admin(user_id: str) -> bool:
    """检查用户是否是管理员"""
    try:
        profile = db.get_or_create_profile(user_id)
        return profile.get("role") == "admin"
    except Exception:
        return False


async def require_admin(user_id: str) -> None:
    """要求管理员权限，非管理员抛出异常"""
    if not is_admin(user_id):
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )
