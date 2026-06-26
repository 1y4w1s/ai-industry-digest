# Signal — AI 行业日报聚合平台

> **线上地址**: [http://43.139.133.245:8080](http://43.139.133.245:8080)
> **版本**: 2.0.0 | **许可证**: MIT

自动采集 → AI 处理 → 日报生成 → 知识库 → 个性化推荐，全链路自动化。

---

## 📋 目录

- [快速上手](#-快速上手)
- [功能导览](#-功能导览)
- [如何验证变更](#-如何验证变更)
- [项目架构](#-项目架构)
- [API 参考](#-api-参考)
- [开发工作流](#-开发工作流)
- [部署指南](#-部署指南)
- [测试覆盖](#-测试覆盖)
- [常见问题](#-常见问题)

---

## 🚀 快速上手

### 前置条件

| 依赖 | 版本要求 | 用途 |
|------|---------|------|
| Python | ≥ 3.9 | 后端运行环境 |
| Node.js | ≥ 18 | 前端构建 |
| PostgreSQL | ≥ 14 | 数据存储（含 pgvector） |
| Redis | ≥ 6 | 缓存服务 |

### 1. 环境变量

复制 `.env.example` 为 `.env`，填入以下关键配置：

```bash
# Supabase（数据库 + 认证）
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# DeepSeek（AI 改写/摘要）
DEEPSEEK_API_KEY=sk-your-key

# Redis 缓存（可选，不配则缓存降级）
REDIS_URL=redis://localhost:6379

# CORS 允许的域名
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
```

### 2. 启动后端

```bash
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000
# 访问: http://localhost:8000/docs (Swagger)
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
# 访问: http://localhost:5173
```

### 4. 运行测试

```bash
# 全量测试（506 项）
python -m pytest tests/ -v

# 带覆盖率
python -m pytest tests/ --cov=api.services --cov-report=term

# 指定模块
python -m pytest tests/test_f14_query_suggestion.py -v
```

---

## 🎯 功能导览

### 首页日报

按日期浏览 AI 行业日报，来源分组（arXiv / RSS / Hugging Face），重要性标记。

- **导航**: 顶部日期栏切换日期
- **筛选**: 按来源/标签过滤
- **阅读**: 点击卡片进入详情

### 文章阅读器

AI 精读摘要 + 原文 + AI 对话 + TTS 朗读 + 导出。

| 功能 | 操作 |
|------|------|
| AI 摘要 | 自动生成，文章顶部显示 |
| AI 对话 | 右下角聊天按钮，可追问文章内容 |
| TTS 朗读 | 点击 🔊 按钮 |
| 收藏 | 点击 ❤️ 按钮 |
| PDF 导出 | 点击导出按钮 |

### 搜索与知识库

**全文搜索**：支持混合检索（向量 + 关键词 + 知识图谱），智能纠错，主题推荐。

**知识库**：
- 上传文档：支持 PDF / DOCX / TXT / MD
- 预览：在线查看文档内容
- 知识图谱：可视化实体关系网络
- 图片提取：PDF/DOCX 中嵌入的图片自动提取

### AI 对话

- **文章级对话**: 基于当前文章内容问答
- **全局对话**: 跨文章的知识问答
- 基于知识图谱的实体关系查询（如"OpenAI 的投资方有哪些？"）

### 个性化推荐

基于阅读历史、对话记录、收藏标签的推荐 Widget。

### 用户系统

- 邮箱注册 / GitHub OAuth 登录
- 阅读历史追踪
- 收藏管理
- 个人统计与趋势

### 管理后台

- 监控仪表盘（搜索量/延迟/错误统计）
- 系统指标查看

---

## ✅ 如何验证变更

### 修改后端代码后

```bash
# 1. 运行涉及模块的测试
python -m pytest tests/test_retrieval_integration.py -v --tb=short

# 2. 运行全量测试确保不破坏已有功能
python -m pytest tests/ -v --tb=short

# 3. 检查覆盖率（仅计算 api.services）
python -m pytest tests/ --cov=api.services --cov-report=term

# 4. 手动启动后端验证 API
python -m uvicorn api.main:app --reload --port 8000
curl http://localhost:8000/api/reports
```

### 修改前端代码后

```bash
cd frontend
npm run dev     # 开发模式，热更新
npm run build   # 生产构建
```

### 修改数据库后

```bash
# 执行 migration
python scripts/migrate.py

# 手动执行 SQL（如有新增 migration）
# 文件在 scripts/migration_*.sql
```

### 完整的验证清单

| 检查项 | 命令/操作 | 预期结果 |
|--------|----------|---------|
| 单元测试 | `pytest tests/ -v` | 506 passed |
| 覆盖率 | `pytest --cov=api.services` | 核心模块 ≥ 90% |
| API 可用 | `curl /api/reports` | 返回 200 JSON |
| 前端构建 | `npm run build` | 无报错 |
| WebSocket | 浏览器打开页面 | 右下角连接状态 ✅ |

### 测试文件索引

| 文件 | 覆盖模块 | 用例数 |
|------|---------|-------|
| `tests/test_coverage_p0.py` | reranker/retrieval/aggregator/compression/query_suggestion | 79 |
| `tests/test_coverage_p1.py` | websocket/image_extractor/cache/jwt_verify | 58 |
| `tests/test_coverage_deep.py` | 检索全流程/图谱/精排/压缩 | 33 |
| `tests/test_retrieval_integration.py` | RRF 融合/纠错/日志/监控 API | 54 |
| `tests/test_f07_f08_*.py` | 精排器 + 压缩器 | 8 |
| `tests/test_f09_router.py` | 查询路由 | 4 |
| `tests/test_f10_metadata.py` | 元数据增强 | 8 |
| `tests/test_f11_document_tracker.py` | 文档增量更新 | 8 |
| `tests/test_f12_graph.py` | 知识图谱检索 | 12 |
| `tests/test_f13_multimodal.py` | 图片提取 + 图片描述 | 14 |
| `tests/test_f14_query_suggestion.py` | 查询建议 + 拼写纠正 | 20 |
| `tests/test_f15_monitor.py` | 监控采集 + 聚合器 | 10 |
| `tests/test_jwt_verify.py` | JWT 验证 | 8 |
| `tests/test_retry.py` | AI 重试逻辑 | 6 |
| `tests/test_tag_extractor.py` | 标签提取 | 10 |
| `tests/test_cache.py` | 缓存服务 | 6 |
| `tests/test_kb.py` | 知识库常量 | 11 |

---

## 🏗 项目架构

```
ai-industry-digest/
├── api/                        # FastAPI 后端
│   ├── main.py                 # 应用入口（路由挂载/中间件）
│   ├── models/                 # 数据模型
│   │   └── database.py         # Supabase DB 管理器
│   ├── routes/                 # API 路由
│   │   ├── content.py          # 日报内容
│   │   ├── auth.py             # 认证
│   │   ├── chat.py             # AI 对话
│   │   ├── kb.py               # 知识库 CRUD
│   │   ├── search.py           # 全文搜索
│   │   ├── recommend.py        # 个性化推荐
│   │   ├── admin.py            # 管理后台
│   │   ├── monitor.py          # 监控仪表盘
│   │   ├── websocket.py        # WebSocket 实时推送
│   │   └── agent_router.py     # AI Agent 路由
│   └── services/               # 核心服务层
│       ├── retrieval.py        # 高级检索（RRF 三路融合）
│       ├── reranker.py         # Cross-encoder 精排
│       ├── compression.py      # 上下文压缩
│       ├── router.py           # 查询意图路由
│       ├── graph_retrieval.py  # 知识图谱检索
│       ├── query_suggestion.py # 查询建议/拼写纠正
│       ├── embedding.py        # 向量嵌入（外部 API）
│       ├── intent_classifier.py# 意图分类（外部 API）
│       ├── metadata.py         # 元数据抽取
│       ├── document_tracker.py # 文档版本追踪
│       ├── image_extractor.py  # PDF/DOCX 图片提取
│       ├── image_caption.py    # 图片描述
│       ├── cache.py            # Redis 缓存
│       ├── websocket_manager.py# WebSocket 连接管理
│       ├── jwt_verify.py       # JWT 令牌验证
│       └── monitor/            # 监控子系统
│           ├── collector.py    # 指标采集器
│           ├── aggregator.py   # 指标聚合器
│           └── router.py       # 监控路由
├── frontend/                   # React + Vite 前端
│   └── src/
│       ├── pages/              # 页面组件
│       ├── components/         # 通用组件
│       ├── context/            # React Context
│       ├── hooks/              # 自定义 Hooks
│       ├── lib/                # 工具库
│       └── utils/              # 工具函数
├── collector/                  # 多源采集器
├── processor/                  # AI 处理管道
├── scripts/                    # 运维脚本
│   ├── deploy.sh               # 一键部署
│   ├── migrate.py              # 数据库迁移
│   └── migration_*.sql         # SQL 迁移文件
├── tests/                      # 506 项单元测试
└── docs/                       # 文档
    ├── ops/DEPLOY_GUIDE.md     # 部署指南
    └── architecture/           # 架构设计文档
```

### 检索流程图

```
用户查询
    │
    ▼
┌─────────────┐    ┌───────────────┐
│  意图路由    │───→│  Query 改写   │ (DeepSeek API)
└──────┬──────┘    └───────┬───────┘
       │                   │
       ▼                   ▼
┌──────────────────────────────────────┐
│        三路并行检索                   │
│                                      │
│  ┌──────────┐ ┌──────────┐ ┌───────┐ │
│  │ 向量检索  │ │ 关键词检索 │ │图谱检索│ │
│  │(50% 权重)│ │(30% 权重) │ │(20%)  │ │
│  └────┬─────┘ └────┬─────┘ └───┬───┘ │
│       │            │            │      │
│       ▼            ▼            ▼      │
│  ┌──────────────────────────────────┐  │
│  │      RRF 三路融合                │  │
│  └──────────────┬───────────────────┘  │
└─────────────────┼──────────────────────┘
                  │
                  ▼
┌─────────────────────────────┐
│  Cross-encoder 二次精排      │
│  (MiniLM-L-6-v2 → sigmoid)  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  上下文压缩 + Query 建议     │
│  (extract/summarize/truncate)│
└─────────────┬───────────────┘
              │
              ▼
           结果输出
```

---

## 📡 API 参考

可在浏览器中打开 `http://localhost:8000/docs` 查看完整 Swagger 文档。

### 核心端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/reports` | 获取日报列表 |
| GET | `/api/reports/{date}` | 获取指定日期日报 |
| GET | `/api/articles/{id}` | 获取文章详情 |
| GET | `/api/search` | 全文搜索（支持混合检索） |
| POST | `/api/chat` | AI 对话 |
| POST | `/api/chat/article/{id}` | 文章级 AI 对话 |
| GET | `/api/kb/documents` | 知识库文档列表 |
| POST | `/api/kb/upload` | 上传知识库文档 |
| GET | `/api/kb/graph` | 知识图谱数据 |
| GET | `/api/recommend` | 个性化推荐 |
| GET | `/api/monitor/dashboard` | 监控仪表盘 |
| POST | `/api/auth/login` | 用户登录 |
| WS | `/ws` | WebSocket 实时推送 |

### 搜索 API 参数

```
GET /api/search?q=查询词&mode=hybrid&limit=10

参数:
  q       - 查询关键词
  mode    - 检索模式: hybrid(默认) | vector | keyword
  rerank  - 是否精排: true(默认) | false
  limit   - 返回条数: 1-50(默认10)
```

---

## 🔄 开发工作流

### 1. 本地开发

```bash
# 终端 1: 后端（热重载）
python -m uvicorn api.main:app --reload --port 8000

# 终端 2: 前端（热更新）
cd frontend && npm run dev
```

### 2. 提交代码

```bash
git add <相关文件>
git commit -m "简明描述改动内容"
git push origin master    # 自动触发 GitHub Actions 部署
```

### 3. 部署

推送 `master` 分支后，GitHub Actions 自动执行：
1. SCP 同步代码到服务器
2. 更新 Python 依赖
3. 构建前端
4. 重启后端服务

约 2-3 分钟后，访问 [http://43.139.133.245:8080](http://43.139.133.245:8080) 查看效果。

---

## 🚢 部署指南

详细部署文档：[docs/ops/DEPLOY_GUIDE.md](./docs/ops/DEPLOY_GUIDE.md)

### 服务器信息

| 项目 | 值 |
|------|-----|
| 服务器 IP | `43.139.133.245` |
| Web 端口 | `8080`（Nginx 反向代理 → 后端 `8000`）|
| 项目路径 | `/opt/ai-industry-digest` |
| 部署脚本 | `bash /opt/ai-industry-digest/scripts/deploy.sh` |
| 后端日志 | `tail -f /opt/ai-industry-digest/backend.log` |
| 采集日志 | `tail -f /opt/ai-industry-digest/daily.log` |

### 一键手动部署

```bash
# SSH 登录后
cd /opt/ai-industry-digest && git pull origin master && bash scripts/deploy.sh
```

### 定时任务

| 时间 | 任务 |
|------|------|
| 每天 3:00 | AI 采集 + 日报生成 + 知识库导入 |
| 每天 6:00/12:00/18:00 | GitHub Actions 定时采集 |

---

## 📊 测试覆盖

### 当前覆盖率（84%）

| 模块 | 覆盖率 | 说明 |
|------|--------|------|
| `websocket_manager.py` | **100%** | WebSocket 连接管理 |
| `monitor/*` | **100%** | 监控采集/聚合/路由 |
| `image_extractor.py` | **97%** | PDF/DOCX 图片提取 |
| `query_suggestion.py` | **96%** | 查询建议/拼写纠正 |
| `cache.py` | **95%** | Redis 缓存服务 |
| `compression.py` | **95%** | 上下文压缩 |
| `graph_retrieval.py` | **95%** | 知识图谱检索 |
| `retrieval.py` | **95%** | 高级检索（三路融合）|
| `router.py` | **94%** | 查询意图路由 |
| `jwt_verify.py` | **98%** | JWT 令牌验证 |
| `reranker.py` | **90%** | Cross-encoder 精排 |
| **整体** | **84%** | 1664 语句，267 未覆盖 |

> 剩余未覆盖行集中在外部 LLM API 依赖模块（embedding/intent_classifier/agent）和第三方库未安装的 ImportError 分支，不影响核心功能。

---

## ❓ 常见问题

### 部署后页面空白

```bash
# 查看后端日志
tail -20 /opt/ai-industry-digest/backend.log

# 重启后端
pkill -f uvicorn
cd /opt/ai-industry-digest && nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
```

### 搜索没结果

1. 检查 `.env` 中 `SUPABASE_URL` 和 `SUPABASE_KEY` 是否正确
2. 确认 `search_kb_by_embedding` RPC 函数已创建（执行 `scripts/search_kb_by_embedding.sql`）
3. 知识库中需要有已导入的文档

### API 返回 502

通常是后端服务未启动或崩溃：

```bash
ps aux | grep uvicorn
tail -20 /opt/ai-industry-digest/backend.log
```

### git push 失败

```bash
# 如果提示认证失败，改用 SSH 协议
git remote set-url origin git@github.com:1y4w1s/ai-industry-digest.git
ssh -T git@github.com  # 验证 SSH 连接
```

---

*Signal — 让 AI 行业信息不再碎片化*
