"""
Signal - 邮件简报退订落地页（改造计划 §1.3）
退订链接 ?token= 指向此处；此路由仅做后端落库，完全不涉及前端。
退订状态写入 newsletter_subscribers 表（见 scripts/migrations/003_newsletter_subscribers.sql）。
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, Response

from api.models.database import get_db

router = APIRouter()


def _page(title: str, message: str, ok: bool) -> str:
    """渲染一个简单的退订结果页（内联样式，无外部依赖）"""
    color = "#16a34a" if ok else "#dc2626"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
</head>
<body style="margin:0;font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;background:#f4f5f7;color:#1f2937">
<div style="max-width:480px;margin:64px auto;background:#fff;border-radius:12px;padding:32px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.08)">
<h1 style="font-size:20px;margin:0 0 12px;color:{color}">{title}</h1>
<p style="font-size:15px;line-height:1.6;color:#374151;margin:0">{message}</p>
<p style="font-size:13px;color:#9ca3af;margin-top:24px">Signal · 每日 AI 情报简报</p>
</div>
</body>
</html>"""


@router.get("/unsubscribe", response_class=HTMLResponse, tags=["邮件简报"])
async def unsubscribe(token: str = Query(..., description="退订令牌")):
    """退订落地页：凭 token 将订阅者标记为 unsubscribed（落库）"""
    now_iso = datetime.now(timezone.utc).isoformat()
    db = get_db()
    try:
        result = (
            db.client.table("newsletter_subscribers")
            .update({"status": "unsubscribed", "unsubscribed_at": now_iso})
            .eq("token", token)
            .execute()
        )
    except Exception as e:  # 网络/DB 异常，给用户明确反馈而非 500 白页
        return HTMLResponse(
            _page("退订失败", f"处理退订时出错，请稍后重试。({e})", ok=False),
            status_code=500,
        )

    if result.data:
        return HTMLResponse(
            _page("已退订", "你已成功退订 Signal 每日简报，后续将不再收到邮件。", ok=True)
        )
    return HTMLResponse(
        _page("链接无效", "退订链接无效，或你已退订。", ok=False),
        status_code=404,
    )


# 1px × 1px 透明 GIF（最小合法 GIF89a），用于打开追踪像素。
# 不携带任何颜色/元数据，对邮件客户端无害；仅作 GET 触发，不写 IP/UA。
_TRANSPARENT_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00"
    b"!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00"
    b"\x00\x02\x02D\x01\x00;"
)


@router.get("/track/open", response_class=Response, tags=["邮件简报"])
async def track_open(token: str = Query(..., description="订阅者退订令牌"),
                     article: str = Query(..., description="期标识（简报日期 YYYY-MM-DD）")):
    """打开追踪像素（改造计划 §1.5）。

    - 仅记录 token+article 维度的聚合打开，绝不写 IP / User-Agent / 设备指纹（隐私合规）。
    - 同 (token, article) 24h 内只记一次（去重在 DatabaseManager.record_open_event）。
    - 始终返回 1px 透明 GIF，即使写入失败也不影响邮件渲染。
    """
    db = get_db()
    try:
        db.record_open_event(token, article)
    except Exception:
        pass  # 追踪失败不应影响用户体验
    return Response(content=_TRANSPARENT_GIF, media_type="image/gif")
