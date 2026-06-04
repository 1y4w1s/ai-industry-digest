# Signal — P0-3 品牌名清理执行计划

> 任务 ID: P0-3
> 目标：将代码中所有 `AI Industry Digest` 旧名替换为 `Signal`
> 预估工时: 20 分钟

---

## 一、改动总览

| # | 改动 | 文件 | 类型 | 工时 |
|---|------|------|------|------|
| 1 | HTML title | `frontend/index.html` | 替换 | 1 min |
| 2 | API 标题/描述 | `api/main.py`（3 处）| 替换 | 2 min |
| 3 | 后端代码注释头 | 11 个 `.py` 文件 | 替换 | 5 min |
| 4 | 前端 favicon | `frontend/public/favicon.svg` | **重设计** | 5 min |
| 5 | Docker/脚本描述 | `run.py`、`scripts/*.py` | 替换 | 3 min |
| 6 | SQL 注释 | `scripts/*.sql` | 替换 | 1 min |
| 7 | 旧设计文档 | `design.md`、`proposal.md`、`tasks.md` | ⏸ 不动 | 0 min |
| 8 | 构建验证 | — | — | 2 min |
| | **合计** | | | **~20 min** |

---

## 二、详细改动

### 改动 1 — HTML title

**文件：** `frontend/index.html`

```
当前: <title>Signal — AI Industry Digest</title>
目标: <title>Signal — AI 行业日报</title>
```

保留「Signal」品牌名，副标题改为中文「AI 行业日报」。

---

### 改动 2 — API 元数据

**文件：** `api/main.py`

| 行 | 当前 | 目标 |
|----|------|------|
| 2 | `AI Industry Digest - FastAPI 入口` | `Signal - FastAPI 入口` |
| 19 | `title="AI Industry Digest API"` | `title="Signal API"` |
| 79 | `"name": "AI Industry Digest"` | `"name": "Signal"` |

---

### 改动 3 — 后端文件注释头（11 个文件）

全部替换第一行的 `AI Industry Digest - ` 为 `Signal - `。

| 文件 | 当前 | 目标 |
|------|------|------|
| `api/models/database.py` | `AI Industry Digest - 数据库管理` | `Signal - 数据库管理` |
| `api/routes/auth.py` | `AI Industry Digest - 用户认证...` | `Signal - 用户认证...` |
| `api/routes/chat.py` | `AI Industry Digest - AI 对话接口` | `Signal - AI 对话接口` |
| `api/routes/content.py` | `AI Industry Digest - 内容接口路由` | `Signal - 内容接口路由` |
| `collector/base.py` | `AI Industry Digest - 数据采集基类` | `Signal - 数据采集基类` |
| `collector/arxiv_collector.py` | `AI Industry Digest - arXiv API 采集器` | `Signal - arXiv API 采集器` |
| `collector/rss_collector.py` | `AI Industry Digest - RSS 采集器` | `Signal - RSS 采集器` |
| `processor/reporter.py` | `AI Industry Digest - 日报生成器` | `Signal - 日报生成器` |
| `processor/dedup.py` | `AI Industry Digest - 去重管道` | `Signal - 去重管道` |
| `processor/ai_processor.py` | `AI Industry Digest - AI 处理器` | `Signal - AI 处理器` |
| `run.py` | `AI Industry Digest - 全流程运行入口` | `Signal - 全流程运行入口` |

**5 个脚本文件的注释头和 print 语句：**

| 文件 | 替换内容 |
|------|---------|
| `scripts/health_check.py` | 注释头 + `description` + print |
| `scripts/daily_verify.py` | 注释头 + print |
| `scripts/backfill_ai.py` | 注释头 + print |
| `scripts/rebuild_reports.py` | 注释头 + print |
| `scripts/feishu_notifier.py` | 注释头 + 飞书消息 title |

**3 个 SQL 文件：**

| 文件 | 替换内容 |
|------|---------|
| `scripts/init_schema.sql` | 注释头 |
| `scripts/migration_rls.sql` | 注释头 |
| `scripts/migration_fulltext_search.sql` | 注释头 |

---

### 改动 4 — Favicon（重设计）

**文件：** `frontend/public/favicon.svg`

**当前：** Vite 默认紫色闪电 Logo（与 Signal 无关）

**目标：** 纯文字 "S" 图标

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="4" fill="#1A1C1E"/>
  <text x="16" y="22" font-family="'Source Serif 4', Georgia, serif" font-size="20" font-weight="700" fill="#FFFFFF" text-anchor="middle">S</text>
</svg>
```

**设计：** 黑色圆角方形底色 + 白色衬线 "S"，和品牌色一致（`#1A1C1E`）。

---

### 改动 5 — 配置文件

**文件：** `config/sources.yaml`

```
当前: # AI Industry Digest - 信息源配置
目标: # Signal - 信息源配置
```

---

### 不改的文件

| 文件 | 不改为理由 |
|------|-----------|
| `design.md` | 旧设计草稿，后续删除 |
| `proposal.md` | 项目提案，保留历史 |
| `tasks.md` | 旧任务清单，保留历史 |
| `design/V3_REDESIGN.md` | 第 3 行已注明原名，保留不改 |
| `design/ROADMAP.md` | 内部文档，第 22 行已有现状说明 |
| `README.md` | 如果有，后续整体重写 |
| Git 仓库名 `ai-industry-digest` | 需要 GitHub 操作，后续 P1-1 |

---

## 三、执行顺序

```
Step 1: frontend/index.html + favicon.svg       (3 min)  ← 用户最可见
Step 2: api/main.py                             (2 min)  ← API 入口
Step 3: 11 个后端 .py 文件注释头                  (5 min)  ← 批量替换
Step 4: 5 个脚本文件                             (3 min)  ← 含 print 语句
Step 5: 3 个 SQL 文件 + config                   (2 min)  ← 简单替换
Step 6: 构建验证                                 (2 min)
────────────────────────────────────────
合计: 约 20 分钟
```

使用 `grep` + 批量替换工具可大幅压缩时间。

---

## 四、验收标准

| # | 验收项 | 通过条件 |
|---|--------|---------|
| 1 | HTML title | 显示 `Signal — AI 行业日报` |
| 2 | 浏览器 Tab 图标 | 显示黑底白字 "S" |
| 3 | API 文档标题 | Swagger UI 显示 `Signal API` |
| 4 | 后端文件注释 | 所有 `.py` 文件头为 `Signal - xxx` |
| 5 | 构建 | `npm run build` + `uvicorn` 启动无报错 |

---

*文档版本 v1.0 | 纯替换，不改功能逻辑*
