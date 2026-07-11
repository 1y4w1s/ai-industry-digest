"""
Signal - 播客 RSS / TTS 单元测试（改造计划 §2.2）
仅覆盖纯逻辑与路由集成，不连 Supabase、不真调 TTS（edge-tts 用 importorskip）。

验收映射：
  - build_script 用 mock 数据产出非空播报稿、含「主线」与「So What（so_what 内容）」字样
  - 给定日期列表，RSS XML well-formed、每项 enclosure 为绝对 URL、length 为整数、仅列确有音频的日期
  - text_to_mp3 在 edge-tts 未安装时测试 skip（pytest.importorskip），不强制环境
  - 后端缺失时 text_to_mp3 显式抛错（由上层捕获做优雅降级）
"""

import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch

import pytest

from collector.base import Article
from scripts.podcast import build_script, _fetch_day_articles
from api.routes import podcast as podcast_route
from api.services import tts as tts_module


# ── 辅助：构造 mock 文章（含 so_what，且共享实体以便聚类出主线）────

def _mk_article(title, so_what, importance="high", day="2026-07-10",
                 tags=None):
    return Article(
        title=title,
        url=f"https://example.com/{title}",
        source_name="机器之心",
        raw_content="",
        published_at=datetime.fromisoformat(f"{day}T09:00:00+00:00"),
        summary=f"摘要：{title}",
        tags=tags or ["大模型", "OpenAI"],
        importance=importance,
        so_what=so_what,
    )


def _demo_articles():
    return [
        _mk_article("OpenAI 发布 GPT-6，推理成本下降 70%",
                     "对中小团队意味着 API 成本大幅下降。"),
        _mk_article("GPT-6 发布后媒体解读：长上下文翻倍",
                     "可以更低门槛把多模态能力塞进产品。"),
        _mk_article("某独角兽被曝裁员 30%", None, importance="low",
                     tags=["行业"]),  # 不同标签，不共享实体 → 独立聚类
    ]


# ── build_script：纯函数 ──────────────────────────────

def test_build_script_nonempty_with_main_thread_and_so_what():
    arts = _demo_articles()
    script = build_script(arts, date(2026, 7, 10))
    assert isinstance(script, str)
    assert script.strip()  # 非空
    # 今日主线（cluster_stories 同源）：两条 GPT-6 报道应并成一条主线
    assert "主线" in script
    # so_what 观点层被朗读
    assert "So What" in script
    # 具体的 so_what 内容出现在稿中
    assert "API 成本大幅下降" in script
    # 不应含 HTML 标签（避免 TTS 念标签）
    assert "<" not in script and ">" not in script


def test_build_script_empty_articles_returns_empty():
    assert build_script([], date(2026, 7, 10)) == ""


def test_build_script_top_n_respected():
    arts = _demo_articles()
    short = build_script(arts, date(2026, 7, 10), top_n=1)
    # top_n 只限制「精选文章」条数：每条精选含 "来自机器之心。" 标记
    assert short.count("来自机器之心。") == 1
    # 主线部分仍展示全部聚类主线（与 top_n 无关）
    assert "主线 1" in short and "主线 2" in short


# ── _list_podcast_dates：仅识别日期命名 mp3 ───────────────

def test_list_podcast_dates_only_dated_mp3(tmp_path, monkeypatch):
    # 造两个合法日期 mp3 + 一个非日期命名文件 + 一个无效日期文件
    (tmp_path / "2026-07-10.mp3").write_bytes(b"\x00" * 1234)
    (tmp_path / "2026-07-09.mp3").write_bytes(b"\x00" * 567)
    (tmp_path / "notes.txt").write_bytes(b"ignore")
    (tmp_path / "foo.mp3").write_bytes(b"\x00" * 10)  # 非日期命名，跳过
    monkeypatch.setattr(podcast_route, "PODCAST_DIR", tmp_path)

    items = podcast_route._list_podcast_dates(30)
    assert len(items) == 2
    # 按日期降序
    assert items[0][0] == date(2026, 7, 10)
    assert items[1][0] == date(2026, 7, 9)
    # 字节长度正确
    assert items[0][1] == 1234
    assert items[1][1] == 567


def test_list_podcast_dates_truncates_to_n(tmp_path, monkeypatch):
    for i in range(5):
        (tmp_path / f"2026-07-{10 - i:02d}.mp3").write_bytes(b"\x00" * 10)
    monkeypatch.setattr(podcast_route, "PODCAST_DIR", tmp_path)
    items = podcast_route._list_podcast_dates(3)
    assert len(items) == 3


def test_list_podcast_dates_empty_when_no_dir(tmp_path, monkeypatch):
    missing = tmp_path / "does_not_exist"
    monkeypatch.setattr(podcast_route, "PODCAST_DIR", missing)
    assert podcast_route._list_podcast_dates() == []


# ── _build_rss：well-formed + 绝对 URL + length 整数 ─────

def test_build_rss_well_formed_and_absolute_enclosure():
    import xml.etree.ElementTree as ET

    items = [(date(2026, 7, 10), 1234), (date(2026, 7, 9), 567)]
    base = "https://1y4w1s.icu:8080"
    xml = podcast_route._build_rss(items, base)

    root = ET.fromstring(xml)  # 解析成功 = well-formed
    assert root.tag == "rss"
    channel = root.find("channel")
    assert channel is not None

    iters = channel.findall("item")
    assert len(iters) == 2

    for it in iters:
        enc = it.find("enclosure")
        assert enc is not None
        url = enc.get("url")
        # enclosure 为绝对 https URL
        assert url.startswith("https://1y4w1s.icu:8080/podcast/")
        assert url.endswith(".mp3")
        # type 与 length
        assert enc.get("type") == "audio/mpeg"
        length = enc.get("length")
        assert length is not None
        assert isinstance(int(length), int)  # length 为整数
        # length > 0
        assert int(length) > 0

    # 仅列确有音频的日期：两条 item 对应两个日期
    dates = sorted(
        it.find("guid").text.rsplit("/", 1)[-1].replace(".mp3", "")
        for it in iters
    )
    assert dates == ["2026-07-09", "2026-07-10"]


def test_build_rss_empty_items_still_valid():
    import xml.etree.ElementTree as ET
    xml = podcast_route._build_rss([], "https://1y4w1s.icu:8080")
    root = ET.fromstring(xml)
    assert root.find("channel") is not None
    assert root.find("channel").findall("item") == []


# ── 路由集成：TestClient + 模拟 media 目录（不连 Supabase）──

def _make_app_client():
    with patch("api.models.database.create_client"):
        with patch("api.models.database.DatabaseManager._create_client"):
            from api.main import app
            from fastapi.testclient import TestClient
            return TestClient(app)


def test_route_podcast_xml_lists_existing_audio(tmp_path, monkeypatch):
    # 造两个音频文件，模拟 media/podcast
    (tmp_path / "2026-07-10.mp3").write_bytes(b"\x00" * 2048)
    (tmp_path / "2026-07-09.mp3").write_bytes(b"\x00" * 1024)
    monkeypatch.setattr(podcast_route, "PODCAST_DIR", tmp_path)
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://signal.example.com")

    client = _make_app_client()
    resp = client.get("/podcast.xml")

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/rss+xml")
    body = resp.text
    assert "<rss" in body and "<channel>" in body
    # 仅列确有音频的 2 个日期
    assert body.count("<item>") == 2
    # enclosure 绝对 URL + length 整数
    assert "https://signal.example.com/podcast/2026-07-10.mp3" in body
    assert 'type="audio/mpeg"' in body
    # length 字段存在且为整数
    import re
    for m in re.finditer(r'length="(\d+)"', body):
        assert int(m.group(1)) > 0


def test_route_podcast_xml_empty_when_no_audio(tmp_path, monkeypatch):
    monkeypatch.setattr(podcast_route, "PODCAST_DIR", tmp_path)
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://signal.example.com")
    client = _make_app_client()
    resp = client.get("/podcast.xml")
    assert resp.status_code == 200
    assert "<item>" not in resp.text  # 无音频则不列


# ── text_to_mp3：后端缺失时显式抛错（上层据此降级）─────

def test_text_to_mp3_raises_when_no_backend(monkeypatch):
    # 模拟两个后端都不可用
    monkeypatch.setattr(tts_module, "edge_tts", None)
    monkeypatch.setattr(tts_module, "OpenAI", None)
    monkeypatch.setenv("OPENAI_API_KEY", "")
    with pytest.raises(ImportError):
        tts_module.text_to_mp3("hello", "out.mp3")


def test_text_to_mp3_raises_on_empty_text(monkeypatch):
    monkeypatch.setattr(tts_module, "edge_tts", None)
    monkeypatch.setattr(tts_module, "OpenAI", None)
    with pytest.raises(ValueError):
        tts_module.text_to_mp3("   ", "out.mp3")


def test_default_provider_prefers_openai_when_key_set(monkeypatch):
    monkeypatch.setattr(tts_module, "OpenAI", object())
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert tts_module._default_provider() == "openai"

    monkeypatch.setenv("OPENAI_API_KEY", "")
    assert tts_module._default_provider() == "edge"


# ── 真实 TTS（仅当 edge-tts 已安装时跑；否则 skip，不强制环境）──

def test_text_to_mp3_real_edge(tmp_path):
    edge_tts = pytest.importorskip("edge_tts")  # 未安装则整条 skip
    out = tmp_path / "say.mp3"
    # 若网络不可用会真实失败；用 try 包裹，仅验证「装了就能合成」的接口契约
    try:
        size = tts_module.text_to_mp3("测试一下播客音频生成。", str(out))
    except RuntimeError as e:
        pytest.skip(f"edge-tts 已安装但合成失败（可能无网络）：{e}")
    assert out.exists()
    assert size > 0
