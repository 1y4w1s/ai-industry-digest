"""
Signal - 信息源健康检查
健康注册表 + 连通性检查 + 自动降级 + 告警触发

用法:
    python scripts/health_check.py          # 运行健康检查
    python scripts/health_check.py --status # 查看当前健康状态
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional

import requests
import yaml


class SourceHealthRegistry:
    """信息源健康注册表

    维护每个信息源的连续失败计数，自动判断状态：
    - OK:   连续失败 < 3 次
    - WARN: 连续失败 >= 3 次（应使用备用方式）
    - DOWN: 连续失败 >= 5 次（应发出告警）
    """

    REGISTRY_FILE = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "source_health.json"
    )

    MAX_WARN_COUNT = 3   # 3 次失败 → WARN
    MAX_DOWN_COUNT = 5   # 5 次失败 → DOWN

    def __init__(self, registry_path: str = None):
        self.registry_path = registry_path or self.REGISTRY_FILE
        self.registry = self._load()

    def _load(self) -> dict:
        """从文件加载注册表"""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"  [WARN] 健康注册表加载失败: {e}")
        return {}

    def _save(self):
        """保存注册表到文件"""
        try:
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(self.registry, f, ensure_ascii=False, indent=2)
        except OSError as e:
            print(f"  [WARN] 健康注册表保存失败: {e}")

    def get_status(self, source_id: str) -> str:
        """获取信息源当前状态: OK / WARN / DOWN"""
        record = self.registry.get(source_id, {})
        failures = record.get("consecutive_failures", 0)
        if failures >= self.MAX_DOWN_COUNT:
            return "DOWN"
        elif failures >= self.MAX_WARN_COUNT:
            return "WARN"
        return "OK"

    def record_success(self, source_id: str):
        """记录一次成功，重置失败计数"""
        self.registry[source_id] = {
            "status": "OK",
            "consecutive_failures": 0,
            "last_success": datetime.utcnow().isoformat(),
            "last_check": datetime.utcnow().isoformat()
        }
        self._save()

    def record_failure(self, source_id: str) -> str:
        """记录一次失败，返回当前状态"""
        record = self.registry.get(source_id, {"consecutive_failures": 0})
        record["consecutive_failures"] = record.get("consecutive_failures", 0) + 1
        record["last_failure"] = datetime.utcnow().isoformat()
        record["last_check"] = datetime.utcnow().isoformat()

        failures = record["consecutive_failures"]
        if failures >= self.MAX_DOWN_COUNT:
            record["status"] = "DOWN"
        elif failures >= self.MAX_WARN_COUNT:
            record["status"] = "WARN"
        else:
            record["status"] = "OK"

        self.registry[source_id] = record
        self._save()
        return record["status"]

    def should_use_fallback(self, source_id: str) -> bool:
        """WARN 状态：应使用备用采集方式"""
        return self.get_status(source_id) == "WARN"

    def should_alert(self, source_id: str) -> bool:
        """DOWN 状态：应发送告警"""
        return self.get_status(source_id) == "DOWN"

    def get_summary(self) -> dict:
        """获取所有信息源的健康摘要"""
        sources = {}
        for sid, record in self.registry.items():
            sources[sid] = {
                "status": record.get("status", "UNKNOWN"),
                "failures": record.get("consecutive_failures", 0),
                "last_check": record.get("last_check", ""),
            }
        return {
            "total": len(sources),
            "ok": sum(1 for s in sources.values() if s["status"] == "OK"),
            "warn": sum(1 for s in sources.values() if s["status"] == "WARN"),
            "down": sum(1 for s in sources.values() if s["status"] == "DOWN"),
            "sources": sources
        }


def check_source(source_config: dict) -> bool:
    """检查单个信息源是否可连通

    根据采集器类型使用不同的检查方式：
    - RSS:  尝试 GET feed URL，检查返回内容
    - API:  尝试 API 端点
    - Web:  尝试 GET 页面
    """
    collectors = source_config.get("collectors", [])
    name = source_config.get("name", "unknown")

    for coll in collectors:
        coll_type = coll.get("type")
        try:
            if coll_type == "rss":
                url = coll.get("url", "")
                resp = requests.get(
                    url,
                    timeout=10,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; AI-Industry-Digest/1.0)"}
                )
                if resp.status_code == 200 and len(resp.text) > 100:
                    return True

            elif coll_type == "api":
                api_type = coll.get("api_type", "")
                if api_type == "arxiv":
                    url = "http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=1"
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        return True
                else:
                    # 通用 API 检查
                    url = coll.get("params", {}).get("url", "")
                    if url:
                        resp = requests.get(url, timeout=10)
                        if resp.status_code == 200:
                            return True

            elif coll_type == "web":
                url = coll.get("url", "")
                resp = requests.get(
                    url,
                    timeout=10,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                )
                if resp.status_code == 200:
                    return True

        except requests.RequestException:
            continue

    return False


def load_sources() -> list:
    """从 sources.yaml 加载信息源配置"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "sources.yaml"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [s for s in data.get("sources", []) if s.get("enabled", True)]


def main():
    parser = argparse.ArgumentParser(description="Signal - 信息源健康检查")
    parser.add_argument("--status", action="store_true", help="仅查看当前健康状态，不执行检查")
    args = parser.parse_args()

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sources = load_sources()
    registry = SourceHealthRegistry()

    # 仅查看状态
    if args.status:
        summary = registry.get_summary()
        print("=" * 50)
        print("  信息源健康状态")
        print("=" * 50)
        print(f"  总计: {summary['total']} 个")
        print(f"  ✅ OK:   {summary['ok']} 个")
        print(f"  ⚠️  WARN: {summary['warn']} 个")
        print(f"  ❌ DOWN: {summary['down']} 个")
        print()
        if summary["sources"]:
            print("  详情:")
            for sid, info in summary["sources"].items():
                status_icon = {"OK": "✅", "WARN": "⚠️", "DOWN": "❌"}.get(info["status"], "❓")
                print(f"    {status_icon} {sid}: {info['status']} (连续失败 {info['failures']} 次)")
        print("=" * 50)
        return

    # 执行健康检查
    results = []
    alerts = []

    print("=" * 50)
    print("  信息源健康检查")
    print(f"  时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 50)

    for source in sources:
        name = source.get("name", "unknown")
        sid = source.get("id", "unknown")
        current_status = registry.get_status(sid)
        status_icon = {"OK": "✅", "WARN": "⚠️", "DOWN": "❌"}.get(current_status, "❓")

        print(f"\n  {status_icon} [{name}] (当前: {current_status})", end="")

        ok = check_source(source)
        results.append(ok)
        if ok:
            registry.record_success(sid)
            failures = registry.registry.get(sid, {}).get("consecutive_failures", 0)
            print(f" → ✅ 正常 (已重置)")
        else:
            new_status = registry.record_failure(sid)
            failures = registry.registry.get(sid, {}).get("consecutive_failures", 0)
            print(f" → ❌ 失败 (连续 {failures} 次)")

            if new_status == "WARN":
                print(f"    ⚠️  已触发降级阈值 ({sid} 将使用备用采集方式)")
            elif new_status == "DOWN":
                msg = f"信息源 [{name}]({sid}) 连续失败 {failures} 次，已标记为 DOWN"
                print(f"    ❌ {msg}")
                alerts.append(msg)

    # 输出汇总
    print("\n" + "=" * 50)
    print("  检查汇总")
    ok_count = sum(1 for r in results if r)
    print(f"  ✅ 正常: {ok_count} / {len(sources)}")
    print(f"  ❌ 失败: {len(sources) - ok_count} / {len(sources)}")

    if alerts:
        print(f"\n  ⚠️  待处理告警 ({len(alerts)} 条):")
        for alert in alerts:
            print(f"    - {alert}")

    print("=" * 50)


if __name__ == "__main__":
    main()
