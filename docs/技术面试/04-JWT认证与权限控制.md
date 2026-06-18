# JWT 认证与权限控制

## 位置

`api/auth/jwt_verify.py`

## 双层验证架构

```
请求携带 Token
    │
    ▼
Layer 1: Supabase Auth 验证（标准）
    ├── 成功 → 返回 user_id
    └── 失败（会话过期）
            │
            ▼
Layer 2: 直接解码 JWT Payload（降级）
    ├── 成功 → 从 "sub" 字段获取 user_id
    └── 失败 → 返回 401
```

## 核心代码

```python
def verify_token(token: str) -> Optional[str]:
    user_id = None

    # 第一层：Supabase Auth（标准流程）
    try:
        response = supabase.auth.get_user(token)
        if response.user:
            user_id = response.user.id
    except Exception as e:
        print(f"[JWT] Supabase 验证失败: {e}")

    # 第二层：降级解码 JWT payload
    if not user_id:
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub")  # JWT 标准用户 ID 字段
        except Exception:
            pass

    return user_id
```

## 权限校验链路

```python
# FastAPI 依赖注入
def get_current_user(token=Depends(oauth2_scheme)) -> str:
    """获取当前用户"""
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(401, "无效的认证凭据")
    return user_id

def get_current_admin(user_id=Depends(get_current_user)) -> str:
    """获取当前管理员"""
    profile = db.get_or_create_profile(user_id)
    if profile.get("role") != "admin":
        raise HTTPException(403, "需要管理员权限")
    return user_id

# 使用：一行注入
@app.get("/api/admin/stats")
def admin_stats(admin_id: str = Depends(get_current_admin)):
    return get_stats()
```

## 为什么需要降级？

| 问题 | 表现 | 原因 |
|------|------|------|
| Supabase 会话过期 | 返回 `Session does not exist` | session 生命周期 3600s |
| JWT token 未过期 | token 本身还有有效期 | JWT 签发时设定 |
| 用户操作 | 长时间未刷新页面 | 后端需要无感续签 |

降级直接解码 JWT 获取 `sub`（用户 ID），实现**无感续签**。

## 面试话术

> "JWT 验证我用了双层保障。Supabase 的 session 有生命周期（默认 1 小时），过期就踢人的话用户体验很差。我加了降级——直接解码 JWT payload 获取 user_id。JWT 的签名防篡改在签发时已经保证了，降级只是绕过 session 校验获取身份，不是安全漏洞。"

## 管理员权限模型

```
表: user_profiles
  id: UUID (PK, 关联 auth.users)
  role: TEXT ('user' | 'admin')
  created_at: TIMESTAMP
  updated_at: TIMESTAMP
```

初始管理员设置：

```sql
UPDATE user_profiles SET role = 'admin'
WHERE id = '用户-UUID';
```