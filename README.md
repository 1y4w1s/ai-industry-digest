# Signal — AI 行业日报聚合平台

> **线上地址**: [http://43.139.133.245:8080](http://43.139.133.245:8080)  
> **版本**: 2.0.0 | **许可证**: MIT

自动采集 → AI 处理 → 日报生成 → 阅读与搜索。  
**独立产品**：仅日报业务，不含知识库 / RAG / 文档上传。

---

## 快速上手

### 前置条件

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | ≥ 3.9 | 后端 |
| Node.js | ≥ 18 | 前端 |
| Supabase | — | 数据库 + 认证 |
| Redis | 可选 | 缓存 |

### 环境变量

复制 `.env.example` 为 `.env`，至少配置：

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
DEEPSEEK_API_KEY=sk-your-key
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
```

### 启动

```bash
# 后端（端口 8000）
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000

# 前端（端口 5173）
cd frontend && npm install && npm run dev

# 采集流水线（手动跑一次）
python run.py
```

### 测试

```bash
python -m pytest tests/ -v
# 当前：61+ 项测试（含 newsletter / metrics 留存埋点）
```

---

## 功能

| 模块 | 说明 |
|------|------|
| 日报首页 | 按日期浏览，来源分组，重要性标记 |
| 文章阅读 | AI 摘要、对话追问、TTS、收藏、PDF 导出 |
| 搜索 | 文章标题/摘要关键词搜索 |
| 用户系统 | Supabase Auth、收藏、历史、个人统计 |
| 管理后台 | 文章与用户统计 |
| 采集管道 | arXiv / RSS / HuggingFace 等多源自动采集 |

**不在本仓库**：文档上传、向量检索、知识库对话 → 见 RAG 项目。

---

## 架构

```
collector/  →  run.py  →  processor/  →  Supabase (articles, daily_reports)
                                              ↑
frontend/ (5173)  →  api/ (8000)  ──────────┘
```

### API 路由

| 路由 | 说明 |
|------|------|
| `/api/reports`, `/api/articles` | 日报与文章 |
| `/api/search` | 关键词搜索 |
| `/api/chat` | AI 对话（文章级 / 全局） |
| `/api/recommend` | 个性化推荐 |
| `/api/auth/*` | 用户认证与收藏 |
| `/api/admin/*` | 管理后台 |
| `/ws` | WebSocket |

---

## 测试索引

| 文件 | 覆盖 |
|------|------|
| `test_api.py` | API 路由 |
| `test_collect.py` | 采集器 |
| `test_database.py` | 数据库操作 |
| `test_tag_extractor.py` | 标签提取 |
| `test_retry.py` | AI 重试 |
| `test_jwt_verify.py` | JWT 验证 |
| `test_cache.py` | 缓存 |

---

## 部署

见 [`docs/ops/DEPLOY_GUIDE.md`](docs/ops/DEPLOY_GUIDE.md)。

---

## 邮件简报（产品核心）与 dogfood

产品=「推到邮箱的每日 AI 简报」，网站只是归档。简报由 GitHub Actions 每日 08:00（北京时间）自动推送。

**作者自己先订阅（dogfood，§1.5 验收关键）**：

```bash
# 把作者邮箱写进 newsletter_subscribers(active)，确保每日简报发到自己
python scripts/newsletter.py seed --email you@example.com
```

**过关标准**：作者本人**连续 2 周是日活**——每周一看飞书指标卡，且自己确实每天打开简报。

**留存三数（订阅 / 打开 / 退订）**：

```bash
# 跑出近 7 天三数并推飞书卡（CI 每周一自动跑）；离线/本地用 --no-push
python scripts/metrics.py --days 7 --no-push --json
```

- 订阅：`newsletter_subscribers` 表直接算在订/总计/已退订。
- 打开：邮件 HTML 含 1px 透明追踪像素（`/track/open`），落 `open_events`（只记 token 维度，**不写 IP/UA**）；同 (token,article) 24h 内算 1 次。
- 退订：`/unsubscribe` 落地页已落库 `status=unsubscribed`，直接统计；退订率 = 本期新增退订 / (期末在订 + 本期新增退订)。
- 上线前需在 Supabase 执行 `scripts/migrations/003_newsletter_subscribers.sql` 与 `scripts/migrations/004_open_and_send_events.sql`；CI 需配置 `FEISHU_WEBHOOK` secret。

---

| 文档 | 用途 |
|------|------|
| [`docs/PRODUCT_CORE.md`](docs/PRODUCT_CORE.md) | 产品边界与 P0 能力 |
| [`docs/TECH_STACK.md`](docs/TECH_STACK.md) | 技术栈与目录结构 |
| [`docs/ops/DEPLOY_GUIDE.md`](docs/ops/DEPLOY_GUIDE.md) | 部署与定时任务 |
| [`docs/ops/部署与排障记录.md`](docs/ops/部署与排障记录.md) | 线上排障笔记 |
| [`docs/INTERVIEW_PREP.md`](docs/INTERVIEW_PREP.md) | 面试准备（日报项目） |
| [`docs/技术面试/`](docs/技术面试/) | 分模块技术讲解 |
| [`docs/design/DESIGN_SPEC.md`](docs/design/DESIGN_SPEC.md) | UI 设计规范 |
