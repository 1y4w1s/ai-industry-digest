# Signal — 产品内核

> 最后更新: 2026-07-03  
> 状态: 生效中

## 1. 一句话定位

**Signal 是 AI 行业日报聚合与阅读平台** —— 帮用户每天高效浏览、搜索、收藏 AI 资讯。

## 2. 核心用户路径（唯一主路径）

打开网站 → 看今日日报 → 点文章阅读 / 搜索 / 收藏 → 第二天再来看新日报

## 3. 必须有（P0）

- 多源自动采集（arXiv、RSS 等）
- AI 摘要、标签、重要性分级
- 日报生成与按日浏览
- 文章搜索、收藏、浏览历史
- 用户登录（Supabase Auth）

## 4. 可以有但不再扩展（迁出或冻结）

- 知识库上传 / RAG 问答 → **已迁至 [rag-knowledge-platform](../rag-knowledge-platform)**，Signal 内仅保留外链或后续 ingest 对接
- Agent、知识图谱、F-15 监控 → 属 RAG 项目，Signal 不再开发

## 5. 明确不做

- 不做文档上传与向量检索产品（独立项目负责）
- 不在 Signal 内继续堆 RAG / Agent 新功能
- 不做多租户 SaaS（现阶段）
- 不做 Java 后端栈

## 6. 与 RAG 项目的边界

| Signal 负责 | RAG 项目负责 |
|-------------|--------------|
| `articles`、`daily_reports` | `kb_*` 表 |
| 采集管道 `run.py` | 文档处理、检索、KB 对话 |
| 日报前端页面 | 知识库前端页面 |

可选集成：采集完成后 `POST` 文章到 RAG 的 `/api/v1/ingest`（尚未实现，见 `docs/SPLIT_PLAN.md`）。
