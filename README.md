# Signal — AI 行业日报聚合平台

> **线上地址**: [线上实例](https://your-domain.com)（私有部署）  
> **版本**: 2.0.0 | **许可证**: MIT

自动采集 → AI 处理 → 日报生成 → 阅读与搜索。  
**独立产品**：仅日报业务，不含知识库 / RAG / 文档上传。

---

## 快速上手

### 前置条件

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | ≥ 3.11 | 后端 |
| Node.js | ≥ 18 | 前端 |
| Supabase | — | 数据库 + 认证 |
| Redis | 可选 | 缓存 + 限流 |

### 环境变量

复制 `.env.example` 为 `.env`，至少配置：

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
DEEPSEEK_API_KEY=your-deepseek-api-key
```

完整变量列表见 `.env.example`。

### 启动

```bash
# 后端（端口 8000）
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000

# 前端（端口 5173）
cd frontend && npm install && npm run dev

# Docker 部署（含 Redis）
docker compose up -d --build

# 采集流水线（手动跑一次）
python run.py
```

### 测试

```bash
python -m pytest tests/ -v
# 当前：183+ 项测试
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
| `/api/search` | 关键词搜索（全文 + 模糊） |
| `/api/chat` | AI 对话（文章级 / 全局） |
| `/api/recommend` | 个性化推荐（基于标签画像） |
| `/api/comments` | 评论区 |
| `/api/github-agents` | GitHub 开源项目推荐 |
| `/api/main-thread` | 今日主线（事件聚类） |
| `/api/auth/*` | 用户认证、收藏、历史 |
| `/api/admin/*` | 管理后台 |
| `/ws` | WebSocket（实时通知） |
| `/podcast.xml` | 播客 RSS |
| `/digest/{date}` | 公开归档页（SEO） |

---

## 测试索引

| 文件 | 覆盖 |
|------|------|
| `test_api.py` | API 路由（认证/收藏/历史/反馈） |
| `test_cache.py` | 缓存服务 |
| `test_cluster_stories.py` | 故事聚类 |
| `test_collect.py` | 采集器（RSS / API） |
| `test_comments.py` | 评论区 |
| `test_database.py` | 数据库操作 |
| `test_github_agents.py` | GitHub 推荐 |
| `test_jwt_verify.py` | JWT 验证 |
| `test_metrics.py` | 留存指标（像素追踪） |
| `test_newsletter.py` | 邮件简报渲染 |
| `test_podcast.py` | 播客 RSS 生成 |
| `test_public_digest.py` | 公开归档页 |
| `test_retry.py` | AI 处理重试 |
| `test_so_what.py` | So What 观点层 |
| `test_social_collect.py` | 社交采集（HN/GitHub/Reddit） |
| `test_subscribe.py` | 邮件订阅 |
| `test_tag_extractor.py` | 标签提取 |

---

## 部署

Docker 部署（推荐）：
```bash
docker compose up -d --build
```

GitHub Actions 每日自动采集 + 邮件简报 + 播客生成，配置见 `.github/workflows/`。

---

## 文档

| 文档 | 用途 |
|------|------|
| [`docs/PRODUCT_CORE.md`](docs/PRODUCT_CORE.md) | 产品边界与 P0 能力 |
| [`docs/TECH_STACK.md`](docs/TECH_STACK.md) | 技术栈与目录结构 |
| [`docs/ops/DEPLOY_GUIDE.md`](docs/ops/DEPLOY_GUIDE.md) | 部署与定时任务 |
| [`docs/design/DESIGN_SPEC.md`](docs/design/DESIGN_SPEC.md) | UI 设计规范 |
