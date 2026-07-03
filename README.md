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
# 当前：61 项日报相关测试
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

## 文档

- 产品边界：[`docs/PRODUCT_CORE.md`](docs/PRODUCT_CORE.md)
- 协作规则：[`AGENTS.md`](AGENTS.md)
- 历史拆分记录（已归档）：[`docs/archive/SPLIT_PLAN.md`](docs/archive/SPLIT_PLAN.md)
