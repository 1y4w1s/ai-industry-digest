# AI 行业资讯聚合平台 — 项目计划书

> **版本**: v2.0  
> **更新日期**: 2026-06-04  
> **状态**: 已上线运行  
> **线上地址**: [http://43.139.133.245:8080](http://43.139.133.245:8080)

---

## 项目概述

基于 React + FastAPI 的 AI 行业资讯聚合平台，自动采集多源 AI 资讯，经 AI 处理生成摘要、标签和重要性评级，提供搜索、阅读、收藏、历史记录等功能。

### 技术栈

| 层 | 技术 |
|------|------|
| 前端 | React 19 + Vite 8 + Tailwind CSS v4 + React Router 7 |
| 后端 | FastAPI + Python 3.10 |
| 数据库 | Supabase (PostgreSQL) |
| 认证 | Supabase Auth (邮箱+密码) |
| AI | DeepSeek API (摘要生成、标签分类、重要性判断、去重) |
| 部署 | Nginx 反向代理（Ubuntu 22.04） |
| 自动化 | GitHub Actions (Cron 定时采集) |

---

## 已完成功能

### 数据采集层 ✅

| 功能 | 详情 |
|------|------|
| arXiv 学术论文采集 | cs.AI / cs.LG / cs.CL 分类，每日最多 50 篇 |
| 量子位 RSS 采集 | qbitai.com RSS feed |
| 机器之心 RSS 采集 | jiqizhixin.com RSS feed |
| 36氪 AI 频道采集 | 36kr.com RSS + RSSHub 备用源 |
| GitHub Trending 采集 | 代码已实现，配置中暂未启用 |
| URL 精确去重 | 写入前按 URL 查重，已存在则跳过 |
| 标题相似度去重 | jieba 分词 + Jaccard 相似度，阈值 85% |
| AI 辅助去重 | 70%-85% 模糊区间调用 DeepSeek 判断 |

### AI 处理层 ✅

| 功能 | 详情 |
|------|------|
| 摘要生成 | DeepSeek Batch Prompt，每批 10 篇 |
| 标签分类 | AI 自动打标签 |
| 重要性排序 | High / Medium / Low 三级 |
| 日报生成 | 每日概览 + 热点关键词 + 按重要性分组 |
| API 异常处理 | 超时重试 2 次、格式校验、Token 超限截断 |

### 后端 API ✅

| 接口 | 功能 |
|------|------|
| `GET /api/reports` | 日报列表（分页，按日期倒序） |
| `GET /api/reports/:date` | 单日报详情（含文章列表） |
| `GET /api/articles` | 文章搜索/过滤（关键词、标签、日期范围、分页） |
| `GET /api/articles/:id` | 单篇文章详情 |
| `POST /api/auth/register` | 注册 |
| `POST /api/auth/login` | 登录 |
| `GET /api/auth/me` | 获取用户信息 |
| `POST /api/auth/bookmarks` | 添加收藏 |
| `DELETE /api/auth/bookmarks/:id` | 取消收藏 |
| `GET /api/auth/bookmarks` | 获取收藏列表 |
| `POST /api/auth/history` | 记录浏览历史 |
| `GET /api/auth/history` | 获取浏览历史 |
| `POST /api/auth/feedback` | 提交文章反馈 👍/👎 |
| `POST /api/chat` | AI 对话（推荐/问答） |
| 速率限制 | 每 IP 每分钟最多 30 次请求 |
| 数据库重试 | Supabase 连接断开自动重试（最多 3 次） |

### 前端页面 ✅

| 页面 | 路由 | 功能 |
|------|------|------|
| 首页 | `/` | 日报列表 + 详情面板 + 文章分组 + Hero 文章 |
| 文章阅读 | — | 阅读模式 + 收藏按钮 + AI 对话 |
| 搜索页 | `/search` | 关键词搜索 + 过滤 + AI 推荐面板 |
| 登录/注册 | `/login` | 邮箱+密码登录/注册/密码重置 |
| 收藏页 | `/bookmarks` | 收藏列表 + 取消收藏（需登录） |
| 历史页 | `/history` | 浏览历史按日期分组（需登录） |
| 个人中心 | `/profile` | 用户信息 + 快捷入口（需登录） |
| AI 对话浮窗 | — | 全局 AI 问答 |

### 运维与部署 ✅

| 项目 | 状态 |
|------|------|
| Nginx 反向代理（端口 8080） | 已部署运行 |
| 后端 FastAPI（端口 8000） | 已部署运行 |
| GitHub Actions 定时采集（daily.yml） | 代码就绪，需配置 Secrets |
| 健康检查（health_check.py） | 代码就绪 |
| 飞书通知（feishu_notifier.py） | 代码就绪 |
| 数据备份（backup.yml） | 代码就绪 |
| 数据完整性校验（daily_verify.py） | 代码就绪 |
| 响应式布局 | 已实现（移动端 + 桌面端） |

---

## 待完成任务

按优先级从高到低排列。

### P0 — 核心自动化（让系统自主运转）

#### 1. 配置 GitHub Actions Secrets

让定时采集流水线跑起来的关键一步。需要在 GitHub 仓库配置 3 个 Secrets：

| Secret | 说明 | 获取方式 |
|--------|------|----------|
| `SUPABASE_URL` | Supabase 项目 URL | Supabase 控制台 → Settings → API |
| `SUPABASE_KEY` | Supabase service_role key | 同上（注意：不是 anon key） |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | DeepSeek 开发者平台 |

配置后 GitHub Actions 会在北京时间 **6:00 / 12:00 / 18:00** 自动运行采集-处理-日报全流程。

#### 2. 配置飞书 Webhook（可选）

| Secret | 说明 |
|--------|------|
| `FEISHU_WEBHOOK` | 飞书机器人 Webhook URL |

每次运行完成后会推送状态报告（采集数、处理数、耗时、费用）。

---

### P1 — 用户体验完善

#### 3. PDF 导出

- [ ] 集成 html2pdf.js 或 print.js
- [ ] 文章详情页添加「下载 PDF」按钮
- [ ] 确保中文排版正常

#### 4. 搜索结果样式优化

- [ ] 搜索结果页的卡片的样式已比较完善，可微调
- [ ] 搜索高亮关键词

#### 5. 夜间模式（加分项）

- [ ] 实现 dark mode CSS 变量
- [ ] 添加切换按钮
- [ ] 持久化用户偏好

---

### P2 — 部署与发布优化

#### 6. GitHub OAuth 登录

- [ ] Supabase 控制台开启 GitHub OAuth
- [ ] 前端添加「使用 GitHub 登录」按钮

#### 7. SEO 基础

- [ ] 配置 `<head>` 中的 title、description、og:image
- [ ] 生成 sitemap.xml

#### 8. README 与项目展示

- [ ] 编写 README.md（项目介绍 + 截图 + 技术栈 + 在线地址）
- [ ] 可选：发布到 V2EX / 技术社区收集反馈

---

## 项目结构

```
ai-industry-digest/
├── api/                          # 后端（FastAPI）
│   ├── main.py                   # 入口 + CORS + 速率限制
│   ├── models/
│   │   └── database.py           # Supabase 数据库操作
│   └── routes/
│       ├── auth.py               # 用户认证 + 收藏/历史/反馈
│       ├── chat.py               # AI 对话接口
│       └── content.py            # 文章/日报内容接口
├── collector/                    # 数据采集
│   ├── base.py                   # 数据模型 + 采集器基类
│   ├── arxiv_collector.py        # arXiv API 采集
│   └── rss_collector.py          # RSS 采集
├── config/
│   └── sources.yaml              # 信息源配置
├── frontend/                     # 前端（React）
│   └── src/
│       ├── api/client.js         # API 客户端
│       ├── context/AuthContext.jsx # 认证上下文
│       ├── components/           # 组件
│       │   ├── ArticleCard.jsx
│       │   ├── ArticleReader.jsx
│       │   ├── Layout.jsx
│       │   ├── AIChatBubble.jsx
│       │   ├── AIRecommendPanel.jsx
│       │   └── ...
│       └── pages/                # 页面
│           ├── Home.jsx
│           ├── SearchPage.jsx
│           ├── LoginPage.jsx
│           ├── BookmarksPage.jsx
│           ├── HistoryPage.jsx
│           └── ProfilePage.jsx
├── processor/                    # AI 处理
│   ├── ai_processor.py           # DeepSeek API 调用
│   ├── dedup.py                  # 三层去重
│   └── reporter.py               # 日报生成
├── scripts/                      # 运维脚本
│   ├── health_check.py           # 信息源健康检查
│   ├── feishu_notifier.py        # 飞书通知
│   ├── backup.py                 # 数据导出备份
│   ├── daily_verify.py           # 数据完整性校验
│   ├── backfill_ai.py            # AI 处理回溯
│   └── rebuild_reports.py        # 日报重建
├── .github/workflows/
│   ├── daily.yml                 # 定时采集流水线
│   └── backup.yml                # 每周备份
├── test/
│   └── index.html                # 简陋测试前端（备查）
├── run.py                        # 全流程运行入口
├── requirements.txt              # Python 依赖
└── .env.example                  # 环境变量模板
```

---

## 服务管理速查

### 服务器（Ubuntu @ 43.139.133.245）

```bash
# 查看服务状态
ps aux | grep uvicorn | grep -v grep

# 重启后端
pkill -f uvicorn
cd /opt/ai-industry-digest
/home/ubuntu/.local/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# 查看日志
tail -f /opt/ai-industry-digest/backend.log

# 手动运行采集
cd /opt/ai-industry-digest && python run.py

# 重启 Nginx
sudo systemctl restart nginx
```

### 本地开发

```bash
# 安装依赖
pip install -r requirements.txt
cd frontend && npm install

# 启动后端
uvicorn api.main:app --reload --port 8000

# 启动前端（开发模式）
cd frontend && npm run dev

# 前端构建
cd frontend && npm run build
```

---

## 更新日志

| 日期 | 版本 | 变更 |
|------|------|------|
| 2026-06-04 | v2.0 | 修复收藏/历史页面字段名 BUG，更新项目计划书 |
