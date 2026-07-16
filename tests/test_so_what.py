"""
Signal - 观点层（So What）单元测试
验证：
  1. 字段存在：Article / AIResult 均含可空 so_what 字段，旧文默认 NULL 兼容。
  2. 解耦：so_what 由独立 LLM 步骤产出，失败不影响事实底（summary）字段。
  3. 质量：抽 10 篇样例判「像人说的话、非标题党」，并验证标题党/空值被拒。

运行: python -m pytest tests/test_so_what.py -v
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import patch
import pytest

from collector.base import Article
from processor.ai_processor import AIProcessor, AIResult


# ── 测试数据 ──────────────────────────────────

def _make_articles(n=2, prefix="S"):
    return [
        Article(
            title=f"{prefix}标题{i}",
            url=f"https://test.com/{prefix}{i}",
            source_name="测试源",
            raw_content=f"这是第{i}篇关于AI的内容，介绍了一项新进展。",
        )
        for i in range(n)
    ]


# 真实感样例：口语、平实、非标题党（代表模型应产出的风格）
SAMPLE_SO_WHAT = [
    "对做应用的团队来说，这套开源方案能省掉不少自己搭基建的时间。",
    "如果你已经在用同类工具，可以留意下接口是否兼容，免得后面迁移踩坑。",
    "普通用户暂时感受不到变化，但厂商之间的价格战可能要开始了。",
    "想上手的话，官方文档和示例比第三方教程更靠谱，建议直接从源码看。",
    "这条对合规团队是个提醒：相关监管口径可能很快要跟着更新。",
    "对中小公司算利好，原本买不起的能力现在门槛明显低了。",
    "做产品的可以想想怎么把它接进现有流程，别只当新闻划过。",
    "研究者值得跟一下，复现成本低，说不定能直接用到自己项目里。",
    "短期别急着跟风，等社区踩完坑再决定要不要上生产环境。",
    "对招聘方是个信号：这类岗位的能力要求可能要往这个方向调整了。",
]

# 标题党 / 夸张词（与 ai_processor.CLICKBAIT_WORDS 保持一致口径）
CLICKBAIT_WORDS = [
    "核弹级", "炸裂", "颠覆", "史诗级", "逆天", "封神", "王炸", "炸场",
    "惊呆", "震惊", "狂飙", "杀疯了", "绝绝子", "炸天", "逆天改命",
    "史上最", "吊打", "完爆", "一雪前耻", "原地封神",
]


def is_human_like(so_what) -> tuple:
    """粗判：像人说的话、非标题党。返回 (是否通过, 失败原因)。"""
    if not so_what or not isinstance(so_what, str):
        return False, "空值或非字符串"
    text = so_what.strip()
    if len(text) < 8:
        return False, "过短，不像完整观点"
    if len(text) > 120:
        return False, "过长，偏离'一句观点'设定"
    for w in CLICKBAIT_WORDS:
        if w in text:
            return False, f"含标题党词汇：{w}"
    return True, ""


# ── 1. 字段存在 ──────────────────────────────

class TestSoWhatFieldExists:
    def test_article_has_so_what_field(self):
        """Article 必须带可空 so_what 字段，旧文默认 NULL 兼容"""
        a = Article(title="t", url="u", source_name="s", raw_content="c")
        assert hasattr(a, "so_what")
        assert a.so_what is None

    def test_airesult_has_so_what_field(self):
        """AIResult 必须带可空 so_what 字段（默认 None，不影响既有构造）"""
        r = AIResult(summary="s", tags=["其他"], importance="low", reason="r")
        assert hasattr(r, "so_what")
        assert r.so_what is None

    def test_airesult_so_what_roundtrip(self):
        """构造时传入 so_what 应原样保留"""
        r = AIResult(summary="s", tags=["其他"], importance="low", reason="r",
                     so_what="对你来说能省点事。")
        assert r.so_what == "对你来说能省点事。"


# ── 2. 解耦与流程 ────────────────────────────

class TestSoWhatDecoupling:
    @patch.object(AIProcessor, "_call_api")
    def test_process_articles_populates_so_what(self, mock_call):
        """process_articles 应为每篇填充 so_what，且事实底 summary 不被污染"""
        articles = _make_articles(2)
        summary_resp = {
            "choices": [{"message": {"content": json.dumps([
                {"article_index": 1, "summary": "事实摘要1", "tags": ["其他"],
                 "importance": "low", "reason": "x"},
                {"article_index": 2, "summary": "事实摘要2", "tags": ["其他"],
                 "importance": "low", "reason": "x"},
            ])}}]
        }
        so_what_resp = {
            "choices": [{"message": {"content": json.dumps([
                {"article_index": 1, "so_what": SAMPLE_SO_WHAT[0]},
                {"article_index": 2, "so_what": SAMPLE_SO_WHAT[1]},
            ])}}]
        }
        # 第一次调用=事实层，第二次调用=观点层
        mock_call.side_effect = [summary_resp, so_what_resp]

        proc = AIProcessor(batch_size=10)
        result = proc.process_articles(articles)

        for a in result:
            assert a.so_what is not None, "每篇都应带 so_what"
            assert a.summary is not None, "事实底 summary 必须保留"
            # 观点层不得回写进事实字段
            assert "对你" not in a.summary
            assert a.summary.startswith("事实摘要")

    @patch.object(AIProcessor, "_call_api")
    def test_so_what_failure_keeps_fact_layer(self, mock_call):
        """观点层 LLM 失败时，so_what 置空但不污染 summary（优雅降级）"""
        articles = _make_articles(2)
        summary_resp = {
            "choices": [{"message": {"content": json.dumps([
                {"article_index": 1, "summary": "事实摘要A", "tags": ["其他"],
                 "importance": "low", "reason": "x"},
                {"article_index": 2, "summary": "事实摘要B", "tags": ["其他"],
                 "importance": "low", "reason": "x"},
            ])}}]
        }
        # 第二次调用（观点层）返回 None 模拟失败
        mock_call.side_effect = [summary_resp, None]

        proc = AIProcessor(batch_size=10)
        result = proc.process_articles(articles)

        for a in result:
            assert a.so_what is None, "观点层失败应置空，而非抛错"
            assert a.summary is not None, "事实底必须仍在"

    def test_build_prompt_is_decoupled(self):
        """观点层 prompt 应独立于事实层，含 So What 指引与标题党黑名单"""
        proc = AIProcessor(batch_size=10)
        prompt = proc._build_so_what_prompt(_make_articles(1))
        assert "So What" in prompt
        assert "核弹级" in prompt  # 黑名单出现在约束里
        assert "摘要" in prompt    # 基于事实底
        # 不应要求输出 tags/importance（那是事实层的事）
        assert "importance" not in prompt

    def test_parse_so_what_response_handles_garbage(self):
        """观点层响应解析容错：非数组/坏 JSON 时整批置空"""
        proc = AIProcessor(batch_size=10)
        bad = {"choices": [{"message": {"content": "不是合法 JSON"}}]}
        assert proc._parse_so_what_response(bad, 3) == [None, None, None]
        not_list = {"choices": [{"message": {"content": json.dumps({"a": 1})}}]}
        assert proc._parse_so_what_response(not_list, 2) == [None, None]


# ── 3. 质量门槛：像人说的话、非标题党 ──────────

class TestSoWhatQuality:
    def test_ten_samples_are_human_like(self):
        """抽 10 篇样例，均判为「像人说的话、非标题党」"""
        assert len(SAMPLE_SO_WHAT) >= 10, "验收要求至少抽 10 篇"
        for i, s in enumerate(SAMPLE_SO_WHAT):
            ok, msg = is_human_like(s)
            assert ok, f"样本#{i} 未通过质量门槛: {msg} -> {s}"

    def test_clickbait_rejected(self):
        """标题党/夸张文案必须被判不合格"""
        bad = "核弹级突破！这款模型直接颠覆整个行业，封神之作，震惊所有人！"
        ok, msg = is_human_like(bad)
        assert not ok, msg

    def test_empty_rejected(self):
        assert not is_human_like("")[0]
        assert not is_human_like(None)[0]

    def test_too_short_rejected(self):
        ok, msg = is_human_like("好。")
        assert not ok, msg

    def test_blacklist_aligned_with_processor(self):
        """测试用黑名单应与处理器口径一致，避免两侧标准漂移"""
        from processor.ai_processor import AIProcessor as AP
        assert set(CLICKBAIT_WORDS) == set(AP.CLICKBAIT_WORDS)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
