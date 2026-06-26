"""
F-15 MetricAggregator — 聚合查询

提供仪表盘所需的聚合数据：
  - dashboard()：一次调用返回完整概览
  - 各维度分析（检索质量 / 性能 / 路由分布 / 压缩效果）

设计原则：
  - 查询时实时聚合（数据量≤百万级，无需预聚合）
  - 所有方法有降级返回值
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from api.models.database import get_db


class MetricAggregator:
    """指标聚合器"""

    def dashboard(self, days: int = 7) -> Dict[str, Any]:
        """仪表盘概览（一次调用返回完整数据）"""
        since = (datetime.now() - timedelta(days=days)).isoformat()

        try:
            db = get_db()

            # 1. 检索总量 & 用户数
            search_count = self._count(db, "search", since)
            error_count = self._count(db, "error", since)
            zero_result = self._count_zero_result(db, since)

            # 2. 延迟指标
            latencies = self._query_latencies(db, since)
            p50 = self._percentile(latencies, 50)
            p95 = self._percentile(latencies, 95)
            p99 = self._percentile(latencies, 99)
            avg_latency = round(sum(latencies) / len(latencies)) if latencies else 0

            # 3. 检索质量
            avg_top_score = self._avg_top_score(db, since)

            # 4. 路由分布
            route_dist = self._route_distribution(db, since)

            # 5. 压缩效果
            compress = self._compression_stats(db, since)

            # 6. 错误统计
            top_errors = self._top_errors(db, since)

            return {
                "period": {"days": days},
                "summary": {
                    "total_searches": search_count,
                    "total_errors": error_count,
                    "error_rate": round(error_count / max(search_count, 1), 4),
                    "zero_result_rate": round(zero_result / max(search_count, 1), 4),
                    "avg_latency_ms": avg_latency,
                    "p50_latency_ms": p50,
                    "p95_latency_ms": p95,
                    "p99_latency_ms": p99,
                    "avg_top_score": round(avg_top_score, 3),
                },
                "routing": route_dist,
                "compression": compress,
                "errors": {
                    "total": error_count,
                    "top": top_errors,
                },
            }
        except Exception as e:
            print(f"[MetricAggregator] dashboard 查询失败: {e}")
            return {"period": {"days": days}, "summary": {}, "routing": {}, "compression": {}, "errors": {}}

    def recent_searches(self, limit: int = 20) -> List[Dict]:
        """最近检索记录"""
        try:
            db = get_db()
            result = db.client.table("kb_metrics") \
                .select("query, user_id, latency_ms, final_count, top_scores, route, mode, created_at") \
                .eq("metric_type", "search") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            return result.data or []
        except Exception:
            return []

    # ── 内部辅助方法 ──────────────────────────────────

    def _count(self, db, metric_type: str, since: str) -> int:
        """按类型统计总数"""
        result = db.client.table("kb_metrics") \
            .select("id", count="exact") \
            .eq("metric_type", metric_type) \
            .gte("created_at", since) \
            .execute()
        return result.count or 0

    def _count_zero_result(self, db, since: str) -> int:
        """统计返回 0 条结果的检索"""
        result = db.client.table("kb_metrics") \
            .select("id", count="exact") \
            .eq("metric_type", "search") \
            .eq("final_count", 0) \
            .gte("created_at", since) \
            .execute()
        return result.count or 0

    def _query_latencies(self, db, since: str) -> List[int]:
        """查询延迟数据"""
        result = db.client.table("kb_metrics") \
            .select("latency_ms") \
            .eq("metric_type", "search") \
            .gte("created_at", since) \
            .order("created_at", desc=True) \
            .limit(1000) \
            .execute()
        return [r["latency_ms"] for r in (result.data or []) if r.get("latency_ms")]

    def _percentile(self, values: List[int], p: int) -> int:
        """计算百分位数"""
        if not values:
            return 0
        sorted_vals = sorted(values)
        idx = max(0, min(len(sorted_vals) - 1, int(len(sorted_vals) * p / 100)))
        return sorted_vals[idx]

    def _avg_top_score(self, db, since: str) -> float:
        """平均 Top1 分数（兼容 JSON 字符串和 JSONB 数组两种存储格式）"""
        result = db.client.table("kb_metrics") \
            .select("top_scores") \
            .eq("metric_type", "search") \
            .gte("created_at", since) \
            .limit(500) \
            .execute()
        scores = []
        for r in (result.data or []):
            ts = r.get("top_scores")
            if ts is None:
                continue
            # 兼容旧数据：JSON 字符串
            if isinstance(ts, str):
                try:
                    import json
                    ts = json.loads(ts)
                except (json.JSONDecodeError, TypeError):
                    continue
            if isinstance(ts, list) and len(ts) > 0:
                scores.append(max(ts))
        return sum(scores) / len(scores) if scores else 0.0

    def _route_distribution(self, db, since: str) -> Dict:
        """路由分布统计"""
        result = db.client.table("kb_metrics") \
            .select("route") \
            .eq("metric_type", "search") \
            .gte("created_at", since) \
            .limit(2000) \
            .execute()

        dist = {}
        for r in (result.data or []):
            route = r.get("route") or "unknown"
            dist[route] = dist.get(route, 0) + 1
        return dist

    def _compression_stats(self, db, since: str) -> Dict:
        """压缩效果统计"""
        result = db.client.table("kb_metrics") \
            .select("original_chars, compressed_chars, compress_mode") \
            .eq("metric_type", "compress") \
            .gte("created_at", since) \
            .limit(500) \
            .execute()

        if not result.data:
            return {"avg_ratio": 0, "mode_distribution": {}, "avg_compressed_chars": 0}

        ratios = []
        mode_dist = {}
        total_compressed = 0
        for r in result.data:
            orig = r.get("original_chars", 0) or 0
            comp = r.get("compressed_chars", 0) or 0
            if orig > 0:
                ratios.append(comp / orig)
            total_compressed += comp
            mode = r.get("compress_mode") or "extract"
            mode_dist[mode] = mode_dist.get(mode, 0) + 1

        return {
            "avg_ratio": round(sum(ratios) / len(ratios), 3) if ratios else 0,
            "mode_distribution": mode_dist,
            "avg_compressed_chars": round(total_compressed / len(result.data)),
        }

    def _top_errors(self, db, since: str) -> List[Dict]:
        """最常见的错误"""
        result = db.client.table("kb_metrics") \
            .select("error_msg") \
            .eq("metric_type", "error") \
            .gte("created_at", since) \
            .limit(500) \
            .execute()

        counts = {}
        for r in (result.data or []):
            msg = (r.get("error_msg") or "未知错误")[:80]
            counts[msg] = counts.get(msg, 0) + 1

        sorted_msgs = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [{"msg": msg, "count": cnt} for msg, cnt in sorted_msgs[:5]]


# 单例
_aggregator = None


def get_metric_aggregator() -> MetricAggregator:
    global _aggregator
    if _aggregator is None:
        _aggregator = MetricAggregator()
    return _aggregator
