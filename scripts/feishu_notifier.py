"""
Signal - 飞书 Webhook 通知模块
用于发送运行状态报告和告警到飞书群机器人
"""

import os
import json
from datetime import datetime
from typing import Optional

import httpx
from dotenv import load_dotenv

load_dotenv()


class FeishuNotifier:
    """飞书机器人通知"""

    def __init__(self):
        self.webhook_url = os.getenv("FEISHU_WEBHOOK")

    def is_configured(self) -> bool:
        """检查是否配置了 Webhook"""
        return bool(self.webhook_url)

    def send_report(self, stats: dict) -> bool:
        """发送运行状态报告"""
        if not self.is_configured():
            print("  [FEISHU] 未配置 Webhook，跳过报告发送")
            return False

        msg = self._build_report_message(stats)
        return self._send(msg)

    def send_alert(self, title: str, content: str) -> bool:
        """发送告警消息"""
        if not self.is_configured():
            print("  [FEISHU] 未配置 Webhook，跳过告警")
            return False

        msg = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": f"⚠️ {title}",
                        "content": [
                            [{"tag": "text", "text": content}]
                        ]
                    }
                }
            }
        }
        return self._send(msg)

    def _build_report_message(self, stats: dict) -> dict:
        """构建运行报告卡片消息"""
        status_emoji = "✅" if stats.get("success", False) else "❌"
        return {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": f"{status_emoji} Signal 运行报告",
                        "content": [
                            [{"tag": "text", "text": f"时间: {stats.get('time', 'N/A')}"}],
                            [{"tag": "text", "text": f"采集源: {stats.get('sources_success', 0)} 成功, {stats.get('sources_failed', 0)} 失败"}],
                            [{"tag": "text", "text": f"采集文章: {stats.get('articles_collected', 0)} 篇"}],
                            [{"tag": "text", "text": f"AI 处理: {stats.get('ai_processed', 0)} 篇成功, {stats.get('ai_failed', 0)} 篇失败"}],
                            [{"tag": "text", "text": f"入库: 新增 {stats.get('db_inserted', 0)} 篇, 跳过 {stats.get('db_skipped', 0)} 篇"}],
                            [{"tag": "text", "text": f"耗时: {stats.get('elapsed', 0):.1f} 秒"}],
                            [{"tag": "text", "text": f"费用: ¥{stats.get('cost', 0):.4f}"}],
                        ]
                    }
                }
            }
        }

    def _send(self, msg: dict) -> bool:
        """发送消息到飞书 Webhook"""
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.post(self.webhook_url, json=msg)
                resp.raise_for_status()
                result = resp.json()
                if result.get("code") == 0:
                    print("  [FEISHU] ✅ 消息发送成功")
                    return True
                else:
                    print(f"  [FEISHU] ❌ 发送失败: {result}")
                    return False
        except Exception as e:
            print(f"  [FEISHU] ❌ 发送异常: {e}")
            return False
