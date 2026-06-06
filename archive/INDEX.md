# Signal — 项目归档索引

> 归档时间：2026-06-06（第 3 次归档）
> 项目名称：AI 行业日报聚合平台 (Signal)
> 线上地址：http://43.139.133.245:8080

---

## 一、项目状态总览

| 维度 | 状态 | 说明 |
|------|------|------|
| 核心功能 | ✅ **完成** | 日报浏览、文章阅读、搜索、收藏、历史、AI 精读、AI 对话 |
| 安全认证 | ✅ **完成** | Supabase Auth + JWT + RLS 策略 + GitHub OAuth |
| 自动化采集 | ✅ **完成** | GitHub Actions 每天 6:00/12:00/18:00 自动采集→AI 处理→入库 |
| 自动化部署 | ✅ **完成** | git push → SCP 代码同步 → 服务器自动构建重启 |
| 用户系统 | ✅ **完成** | 邮箱注册登录 + GitHub OAuth + 个人中心 |
| 设置页面 | ✅ **完成** | 主题切换（亮/暗/系统）+ 字号调节（小/中/大） |
| 文章朗读 TTS | ✅ **完成** | 浏览器语音合成，支持分段朗读/暂停/继续/停止 |
| 日报归档日历 | ✅ **完成** | 按月浏览历史日报，点击跳转 |
| 阅读趋势统计 | ✅ **完成** | 月度折线图、阅读高峰时段、均篇字数 |
| 个人中心 | ✅ **完成** | 阅读计数、收藏数、连续天数、热力图、来源分布、昵称编辑 |
| 搜索结果高亮 | ✅ **完成** | 关键词在标题和摘要中金色高亮 |
| PDF 导出 | ✅ **完成** | 文章详情页支持导出为 PDF |
| 移动端适配 | ✅ **完成** | 侧栏抽屉、筛选滚动、文章阅读器纵向堆叠 |
| 单元测试 | ✅ **完成** | **42 项测试**（41 passed, 1 skipped） |
| **知识库管理** | ✅ **完成** | 文档上传、切片、实体识别、关系抽取、知识图谱可视化 |
| **知识库自动导入** | ✅ **完成** | 每天 cron 自动从日报文章导入知识库 |
| **AI 对话优化** | ✅ **完成** | 气泡可拖拽、点击拖拽分离、弹窗独立关闭、深色模式对比度修复 |
| **AI 个性化推荐** | ✅ **完成** | 标签画像 + 阅读深度追踪 + 推荐接口 + 前端 Widget |
| **知识库认证重构** | ✅ **完成** | 统一 JWT/Header/Query token 三通道认证 |
| **知识库公开/私有** | ✅ **完成** | 上传可见性开关 + 公共文档库（公开 OR 自己拥有权限模型） |
| **提示词个性化** | ✅ **完成** | 文章标签动态提示词 + 用户标签个性化提示词 |
| **AI 链接跳转** | ✅ **完成** | renderMd 支持 Markdown 链接语法 + SPA 导航 |
| **气泡弹窗互斥** | ✅ **完成** | 弹窗打开时气泡隐藏，关闭后重现 |
| **移动端面板折叠** | ✅ **完成** | 文章阅读器右侧面板可折叠/展开 |
| **文档重组** | ✅ **完成** | docs/ 分类 + 删除 _ref/ 冗余目录 + 统一引用路径 |

---

## 二、归档文件清单

### 2.1 规划文档

| 文件 | 说明 | 归档批次 |
|------|------|----------|
| [SPRINT_PLAN.md](./SPRINT_PLAN.md) | 攻坚冲刺计划 — 4 个 Phase 全部完成 | 第 1 批 |
| [ROADMAP.md](./ROADMAP.md) | 优化路线图 — 6 个阶段规划（已完成） | 第 2 批 |
| [PROJECT_PLAN.md](./PROJECT_PLAN.md) | 项目总体规划 v2.0（已完成） | 第 2 批 |

### 2.2 提案与任务书

| 文件 | 说明 | 归档批次 |
|------|------|----------|
| [PROPOSAL_AI_ENHANCEMENT.md](./PROPOSAL_AI_ENHANCEMENT.md) | AI 功能深度拓展提案 v4.0 — 知识库提案（已完成） | 第 2 批 |
| [优化任务书.md](./优化任务书.md) | 优化任务书（待定/未开始） | 第 1 批 |
| [优化任务书_20260606_归档.md](./优化任务书_20260606_归档.md) | 优化任务书归档备份 | 第 1 批 |

### 2.3 设计文档

| 文件 | 说明 |
|------|------|
| [DESIGN_SPEC.md](..docs/design/DESIGN_SPEC.md) | 设计规范文档 |
| [KB_FRONTEND_DESIGN.md](..docs/design/KB_FRONTEND_DESIGN.md) | 知识库前端设计文档 v1.1 |
| [AI_PERSONALIZATION_ARCH.md](..docs/design/AI_PERSONALIZATION_ARCH.md) | AI 个性化与安全增强架构设计 v1.0（待实施） |
| [design.md](./design.md) | 原始设计方案（归档） |
| [proposal.md](./proposal.md) | 原始技术提案（归档） |
| [design-system/](./design-system/) | 设计系统细节（模块架构、主页设计、重设计稿等） |

### 2.4 部署与运维

| 文件 | 说明 |
|------|------|
| [DEPLOY_GUIDE.md](..docs/ops/DEPLOY_GUIDE.md) | 部署指南 |
| [服务器代码全集.md](..docs/ops/服务器代码全集.md) | 服务器端完整代码参考 |
| [部署与排障记录.md](..docs/ops/部署与排障记录.md) | 部署问题和解决方案记录 |

### 2.5 配置与流程

| 文件 | 说明 |
|------|------|
| [scripts/deploy.sh](..scripts/deploy.sh) | 部署脚本 |
| [.github/workflows/deploy.yml](..github/workflows/deploy.yml) | 自动部署工作流 |
| [.github/workflows/daily.yml](..github/workflows/daily.yml) | 定时采集工作流 |
| [.github/workflows/backup.yml](..github/workflows/backup.yml) | 数据备份工作流 |
| [pytest.ini](..pytest.ini) | 测试配置 |
| [requirements.txt](..requirements.txt) | Python 依赖 |

### 2.6 测试

| 文件 | 说明 |
|------|------|
| [tests/test_database.py](..tests/test_database.py) | 数据库层单元测试（10 项） |
| [tests/test_api.py](..tests/test_api.py) | API 层单元测试（10 项） |
| [tests/test_kb.py](..tests/test_kb.py) | 知识库单元测试（11 项） |
| [tests/test_tag_extractor.py](..tests/test_tag_extractor.py) | TagExtractor 单元测试（10 项） |
| [test_verify.py](..test_verify.py) | 快速验证脚本 |

---

## 三、知识库模块速查

### 3.1 数据流

```
用户上传 / 自动导入
    ↓
kb_documents（文档记录）
    ↓ split_into_chunks()
kb_chunks（切片）
    ↓ AIProcessor.extract_knowledge()
kb_entities（实体） + kb_relations（关系）
    ↓ API
知识图谱可视化（Canvas 力导向图）
```

### 3.2 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/kb/health` | GET | 健康检查 |
| `/api/kb/documents` | GET | 文档列表（支持搜索/筛选/分页） |
| `/api/kb/documents` | POST | 上传文档 |
| `/api/kb/documents/{id}` | GET | 文档详情 |
| `/api/kb/documents/{id}` | DELETE | 删除文档 |
| `/api/kb/documents/{id}/process` | POST | 处理文档（切片+实体+关系） |
| `/api/kb/documents/{id}/chunks` | GET | 获取切片列表 |
| `/api/kb/documents/{id}/graph` | GET | 获取知识图谱数据 |
| `/api/kb/documents/{id}/preview` | GET | 预览文档内容 |
| `/api/kb/documents/{id}/download` | GET | 下载原文件 |
| `/api/kb/documents/{id}/tags` | PUT | 修改文档标签 |
| `/api/kb/batch/delete` | POST | 批量删除 |
| `/api/kb/batch/process` | POST | 批量处理 |

### 3.3 定时任务

```
每天 3:00  采集 → AI 处理 → 日报生成 → 知识库自动导入
           KB_IMPORT=true python3 run.py
```

### 3.4 前端路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/knowledge` | KnowledgeBasePage | 知识库管理（表格/筛选/批量/上传/图谱/预览） |
| `/knowledge?graph=id` | 图谱抽屉 | 知识图谱可视化 |
| `/knowledge?preview=id` | 预览抽屉 | 文档内容预览 |

### 3.5 数据库表

| 表 | 说明 |
|----|------|
| `kb_documents` | 文档记录（含 source/hit_count/chunks_count） |
| `kb_chunks` | 文档切片 |
| `kb_entities` | 识别出的实体 |
| `kb_relations` | 实体间关系 |
| `kb_entity_chunks` | 实体-切片关联 |
| `kb_imported_articles` | 已导入的日报文章追踪 |

### 3.6 新增迁移脚本

| 文件 | 说明 |
|------|------|
| `scripts/migration_user_tags.sql` | 用户标签画像表（个性化推荐） |
| `scripts/migration_kb_public.sql` | 知识库公开/私有列（公共知识库体系） |

---

## 四、关键链路速查

### 4.1 数据流（完整）

```
信息源 (arXiv/RSS)
    ↓ 采集器 (collector/*)
原始文章
    ↓ 去重 (processor/dedup.py)
    ↓ AI 处理 (processor/ai_processor.py) — 摘要/标签/重要性
    ↓ 日报生成 (processor/reporter.py)
Supabase 数据库 (articles / daily_reports)
    ↓ API (FastAPI /api/*)
前端 (React + Vite)
    ↓
用户浏览器

自动导入：
  articles → import_to_kb.py → kb_documents → kb_chunks → kb_entities / kb_relations
```

### 4.2 自动化工作流

| 工作流 | 触发条件 | 操作 |
|--------|---------|------|
| `daily.yml` | 每天 6:00/12:00/18:00 | 采集→去重→AI→生成日报→入库 |
| `deploy.yml` | git push to master | SCP 同步代码→pip install→npm build→重启后端 |
| `backup.yml` | 手动触发 | 备份数据库到 JSON |
| `cron (手动配置)` | 每天 3:00 | KB_IMPORT=true run.py → 全流程 + 知识库导入 |

### 4.3 前端路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | Home | 首页日报列表 |
| `/?article=id` | ArticleReader | 文章详情阅读 |
| `/?date=YYYY-MM-DD` | Home | 带日期参数直接跳转 |
| `/search?q=xxx` | SearchPage | 搜索结果 |
| `/archive` | ArchivePage | 日报归档日历 |
| `/bookmarks` | BookmarksPage | 收藏列表 |
| `/history` | HistoryPage | 浏览历史 |
| `/profile` | ProfilePage | 个人中心 |
| `/knowledge` | KnowledgeBasePage | 知识库管理 |
| `/settings` | SettingsPage | 设置 |
| `/login` | LoginPage | 登录/注册 |

---

## 五、技术栈摘要

| 层 | 技术 |
|----|------|
| 前端框架 | React 18 + Vite |
| 样式 | Tailwind CSS v4 + CSS 变量 |
| 构建工具 | Vite |
| 后端框架 | FastAPI (Python) |
| 数据库 | Supabase (PostgreSQL) |
| 认证 | Supabase Auth (JWT) |
| AI | DeepSeek API（摘要/标签/实体识别/关系抽取） |
| 采集 | feedparser + httpx + BeautifulSoup |
| 部署 | GitHub Actions + SCP + uvicorn |
| CI | pytest (31 tests: 20 后端 + 11 知识库) |
| 定时任务 | cron（每天 3:00 全流程 + KB 导入） |

---

> 本归档文件由 2026-06-06 生成，第 3 次归档。
> 本次归档包括：
>   第 1 批：PROPOSAL_AI_ENHANCEMENT.md、优化任务书
>   第 2 批：ROADMAP.md、SPRINT_PLAN.md、PROJECT_PLAN.md
>   第 3 批：AI 个性化推荐、用户画像、阅读深度追踪、安全加固、知识库公共/私有切换、认证重构、提示词个性化、移动端折叠、文档重组
> 新增模块：DOMPurify 安全防护、user_tags 画像、TagExtractor、推荐系统、RecommendationWidget、知识库公开权限
> 新增测试：test_tag_extractor.py（10 项），全量测试 41 passing / 1 skipped
> 新增迁移：migration_user_tags.sql、migration_kb_public.sql
