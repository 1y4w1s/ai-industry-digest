"""
Signal - 服务端 TTS 封装（改造计划 §2.2：播客 RSS）

把文本合成 mp3，供每日简报音频形态使用。

设计约束遵守：
  - 默认用 edge-tts（免费、无需 API key、轻量），仅在 `pip install edge-tts` 后可用。
  - OpenAI TTS 作为可选后端：当环境变量 OPENAI_API_KEY 存在且 openai 已安装时启用。
  - 两个后端均为**可选依赖**（try/except 延迟导入），缺失时 text_to_mp3 抛 ImportError，
    由上层（scripts/podcast.generate）捕获并优雅降级，绝不悄悄产出空文件。
  - text_to_mp3 返回写入文件的字节长度，供 RSS 的 <enclosure length> 字段使用。
  - 不假定任何既有 TTS 能力：仓库里只有浏览器 Web Speech API（前端 ArticleReader），
    那只能客户端朗读、产不出 mp3，因此这里是从零新增的服务端 TTS 步骤。

用法：
  from api.services.tts import text_to_mp3
  size = text_to_mp3("今天 AI 圈发生了……", "output/2026-07-10.mp3")
"""

from __future__ import annotations

import os
import asyncio
from typing import Optional

# ── 可选依赖：延迟导入，缺失即置 None，由 text_to_mp3 在调用时显式报错 ──
try:
    import edge_tts  # 免费、无需 key；`pip install edge-tts`
except Exception:  # pragma: no cover - 依赖环境差异
    edge_tts = None

try:
    from openai import OpenAI  # 可选；有 OPENAI_API_KEY 时启用
except Exception:  # pragma: no cover - 依赖环境差异
    OpenAI = None


# 默认语音（中文，自然女声；edge-tts 用，OpenAI 走其 voice 参数）
DEFAULT_EDGE_VOICE = "zh-CN-XiaoxiaoNeural"
DEFAULT_OPENAI_MODEL = "tts-1"
DEFAULT_OPENAI_VOICE = "alloy"


def _default_provider() -> str:
    """选择后端：有 OPENAI_API_KEY 且 openai 可用 → openai；否则 edge-tts。"""
    if os.getenv("OPENAI_API_KEY") and OpenAI is not None:
        return "openai"
    return "edge"


def _tts_edge(text: str, out_path: str, voice: Optional[str] = None) -> None:
    if edge_tts is None:
        raise ImportError(
            "未安装 edge-tts：请执行 `pip install edge-tts`（免费、无需 API key）。"
        )

    voice = voice or DEFAULT_EDGE_VOICE

    async def _run() -> None:
        communicate = edge_tts.Communicate(text, voice)
        with open(out_path, "wb") as f:
            async for chunk in communicate.stream():
                if chunk.get("type") == "audio":
                    f.write(chunk["data"])

    asyncio.run(_run())


def _tts_openai(text: str, out_path: str, voice: Optional[str] = None,
                model: Optional[str] = None) -> None:
    if OpenAI is None:
        raise ImportError(
            "未安装 openai：请执行 `pip install openai`（仅在使用 OpenAI TTS 时需要）。"
        )
    client = OpenAI()
    model = model or DEFAULT_OPENAI_MODEL
    voice = voice or DEFAULT_OPENAI_VOICE
    with client.audio.speech.with_streaming_response.create(
        model=model, voice=voice, input=text
    ) as response:
        response.stream_to_file(out_path)


def text_to_mp3(text: str, out_path: str,
                voice: Optional[str] = None,
                provider: Optional[str] = None) -> int:
    """把文本合成为 mp3 并写入 out_path，返回文件字节长度。

    Args:
        text: 待合成文本（建议为纯文本，避免 HTML 标签）。
        out_path: 输出 mp3 路径（父目录若不存在由调用方负责创建）。
        voice: 指定语音（可选，后端各自有默认）。
        provider: 强制后端 "edge" | "openai"；缺省自动选择（见 _default_provider）。

    Returns:
        int: 写入的字节数（供 RSS enclosure length 使用）。

    Raises:
        ValueError: 文本为空。
        ImportError: 所选后端依赖未安装。
        RuntimeError: 合成失败（网络/服务错误等）——由上层捕获做优雅降级。
    """
    if not text or not text.strip():
        raise ValueError("text_to_mp3: 文本为空，无法合成。")

    provider = provider or _default_provider()

    try:
        if provider == "openai":
            _tts_openai(text, out_path, voice=voice)
        else:
            _tts_edge(text, out_path, voice=voice)
    except ImportError:
        raise
    except Exception as e:  # 网络/服务/编码等任何失败都上抛，由上层决定是否跳过当天
        raise RuntimeError(f"TTS 合成失败（{provider}）：{e}") from e

    try:
        size = os.path.getsize(out_path)
    except OSError as e:
        raise RuntimeError(f"TTS 输出文件不可读：{e}") from e

    if size == 0:
        raise RuntimeError("TTS 输出文件为空（0 字节），疑似合成失败。")

    return size
