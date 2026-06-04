# AI Industry Digest — 设计文档

> **版本**: v2.0（最终版）  
> **日期**: 2026-06-03  
> **关联提案**: proposal.md

---

## 一、系统架构总览

```
                          ┌─────────────────────────────────────┐
                          │          用户浏览器（前端）            │
                          │   React/Vue SPA → Vercel 托管        │
                          │   最终阶段开发，前期用简陋 HTML 测试    │
                          └───────────────┬─────────────────────┘
                                          │ HTTPS
                                          ▼
                       ┌─────────────────────────────────────┐
                       │        API 网关（Vercel Functions）    │
                       │        请求路由 / 数据查询 / 缓存      │
                       └───────────────┬─────────────────────┘
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            │                             │                             │
            ▼                             ▼                             ▼
 ┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
 │    GitHub Actions     │    │     Supabase          │    │    DeepSeek API      │
 │  定时任务调度中心      │    │   PostgreSQL + Auth   │    │   AI 文本处理         │
 │                      │    │                      │    │                      │
 │  每天 6:00/12:00/18:00│───▶│  articles 表          │───▶│  摘要 + 标签 + 重要性  │
 │  触发抓取流程         │    │  daily_reports 表     │    │                      │
 │                      │    │  users 表             │    │  批处理优化：          │
 │  爬虫脚本运行于此     │    │  bookmarks 表         │    │  10 篇/次调用         │
 │                      │    │  reading_history 表   │    │                      │
 │  每周数据备份到此仓库  │    │  Auth: 邮箱+密码      │    │                      │
 │                      │    │  + GitHub OAuth       │    │                      │
 └──────────────────────┘    └──────────────────────┘    └──────────────────────┘
```

---

## 二、组件详情

### 2.1 数据采集层

#### 架构模式：管道 + 策略模式

```
  ┌─────────────┐
  │  调度器      │ ← GitHub Actions Cron 触发
  └──────┬──────┘
         │
  ┌──────▼────────────────────────────────────────────┐
  │  采集器工厂                                         │
  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
  │  │ RSS      │  │ API      │  │ 网页抓取 (兜底)   │  │
  │  │ 采集器   │  │ 采集器   │  │ requests + bs4   │  │
  │  └────┬─────┘  └────┬─────┘  └───────┬──────────┘  │
  │       │             │               │              │
  │       ▼             ▼               ▼              │
  │  ┌──────────────────────────────────────────────┐  │
  │  │  统一输出格式：Article(title, url, content,  │  │
  │  │  source_name, published_at)                  │  │
  │  └──────────────────────────────────────────────┘  │
  └────────────────────────────────────────────────────┘
```

#### 健康检查机制

```
  每次采集前检查源状态：

  连续 3 次失败 → 标记 WARN，尝试备用方式
  连续 5 次失败 → 标记 DOWN，发出告警
  恢复 1 次成功 → 重置为 OK
```

### 2.2 数据处理层（GitHub Actions 内运行）

#### 去重管道

```
  原始文章流
       │
       ▼
  ┌──────────────────────────────────────────────────────┐
  │  第一层：精确去重 (O(1) 哈希查表)                       │
  │  已处理 URL 集合 → 匹配则丢弃                           │
  └──────────────────────┬───────────────────────────────┘
                         ▼
  ┌──────────────────────────────────────────────────────┐
  │  第二层：模糊去重 (标题相似度)                           │
  │  • jieba 分词 → 计算 Jaccard 相似度                    │
  │  • 阈值 > 85% → 合并，保留最早/最权威来源                │
  │  • 其他来源 URL 记入 source_refs 字段                  │
  └──────────────────────┬───────────────────────────────┘
                         ▼
  ┌──────────────────────────────────────────────────────┐
  │  第三层：AI 辅助去重 (对 70%-85% 区间有疑的文章)          │
  │  调用 DeepSeek 判断是否为同一事件                        │
  │  每次判断约 200 tokens，仅对模糊文章使用                  │
  └──────────────────────┬───────────────────────────────┘
                         ▼
                   干净的文章池
```

#### AI 批处理优化

```
  30 篇文章 → 3 次批处理调用（10 篇/次）
  每次 Prompt："以下有 10 篇 AI 行业新闻，请为每篇生成摘要、标签、重要性。输出 JSON 数组。"
  API 调用减少 90%，Token 消耗降低约 30%
```

### 2.3 数据存储层

#### 数据库选择：Supabase PostgreSQL

| 特性 | 免费层限制 | 本项目用量估算 |
|------|-----------|---------------|
| 存储空间 | 500 MB | ~180 MB/年 + 用户数据量极小 |
| 连接数 | 15 同时 | 前端 API 轻量，够用 |
| 带宽 | 5 GB/月 | 前端数据量小，够用 |
| Auth 用户数 | 10 万 | MVP 足够 |
| 自动休眠 | 7 天不活跃冻结 | 每日有读写，不会冻结 |

#### 表结构设计

```sql
-- =============================================
-- 核心内容表
-- =============================================

-- 表 1: articles（文章主表）
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,           -- 原文链接（唯一约束）
    source_name TEXT NOT NULL,           -- 来源名称
    raw_content TEXT,                    -- 原始正文/描述
    summary TEXT,                        -- AI 生成的摘要
    tags TEXT[],                         -- 标签数组 ["融资","产品"]
    importance TEXT CHECK (importance IN ('high', 'medium', 'low')),
    importance_reason TEXT,              -- 重要性判断理由
    source_refs TEXT[],                  -- 同事件其他来源 URL
    published_at TIMESTAMPTZ,            -- 原文发布时间
    created_at TIMESTAMPTZ DEFAULT NOW(),-- 抓取时间
    updated_at TIMESTAMPTZ DEFAULT NOW() -- 更新时间
);
CREATE INDEX idx_articles_published_at ON articles(published_at DESC);
CREATE INDEX idx_articles_importance ON articles(importance);
CREATE INDEX idx_articles_tags ON articles USING GIN(tags);

-- 表 2: daily_reports（日报索引）
CREATE TABLE daily_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_date DATE UNIQUE NOT NULL,    -- 日报日期
    article_ids UUID[] NOT NULL,         -- 当天收录的文章 ID 列表
    summary_insight TEXT,                -- AI 生成的今日概览
    trending_keywords TEXT[],            -- 今日热点关键词
    trend_analysis TEXT,                 -- 趋势分析（可选）
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_daily_reports_date ON daily_reports(report_date DESC);


-- =============================================
-- 用户系统表
-- =============================================

-- 表 3: user_profiles（用户扩展信息）
-- 注：users 表由 Supabase Auth 自动管理（auth.users）
-- 这里用于存储用户的额外信息
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    nickname TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 表 4: bookmarks（收藏）
CREATE TABLE bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    note TEXT,                          -- 用户可添加备注
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, article_id)         -- 同一用户不能重复收藏
);
CREATE INDEX idx_bookmarks_user ON bookmarks(user_id, created_at DESC);
CREATE INDEX idx_bookmarks_article ON bookmarks(article_id);

-- 表 5: reading_history（浏览历史）
-- 点击文章标题即记录，同一天同一篇文章只记录一次
CREATE TABLE reading_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    read_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, article_id, DATE(read_at))  -- 每天每篇只记一次
);
CREATE INDEX idx_history_user ON reading_history(user_id, read_at DESC);

-- 表 6: article_feedback（文章反馈）
CREATE TABLE article_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    feedback TEXT CHECK (feedback IN ('thumbs_up', 'thumbs_down')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, article_id)
);
```

### 2.4 用户认证系统

#### 技术方案：Supabase Auth

```
  ┌─────────────────────────────────────────────────────────────┐
  │                    Supabase Auth                             │
  ├─────────────────────────────────────────────────────────────┤
  │                                                              │
  │  支持的登录方式：                                              │
  │                                                              │
  │  ✅ 邮箱 + 密码（主力登录方案）                                  │
  │     - 注册：邮箱 + 设置密码 → 可选发送确认邮件                   │
  │     - 登录：邮箱 + 输入密码                                    │
  │     - 找回密码：Supabase 内置重置密码流程                        │
  │     - 国内邮箱完全可访问，无需魔法                               │
  │                                                              │
  │  ✅ GitHub OAuth（快捷登录方案）                                 │
  │     - 用户点击 GitHub 图标 → 跳转授权 → 自动登录                │
  │     - 国内可直接访问 GitHub                                    │
  │                                                              │
  │  ❌ Google OAuth（暂不启用，国内需要魔法）                       │
  │  ❌ Magic Link（暂不启用，国内邮箱可能收不到）                   │
  │                                                              │
  └─────────────────────────────────────────────────────────────┘
```

#### 前端集成代码示意

```javascript
// Supabase 客户端初始化
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// 注册
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure-password',
})

// 登录
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password',
})

// GitHub OAuth 登录
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'github',
})

// 监听认证状态
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_IN') { /* 用户已登录 */ }
  if (event === 'SIGNED_OUT') { /* 用户已登出 */ }
})
```

### 2.5 前端展示层

#### 开发策略：两阶段

```
  阶段一：简陋测试前端（第 4-6 周，与后端同步开发）
  ┌─────────────────────────────────────────────┐
  │  纯 HTML + JavaScript + Supabase JS SDK      │
  │  FastAPI 静态文件托管                        │
  │  目的：验证 API 和登录流程是否正确             │
  │  不涉及框架、构建工具、UI 设计                 │
  └─────────────────────────────────────────────┘

  阶段二：正式前端（第 7-8 周，最终阶段）
  ┌─────────────────────────────────────────────┐
  │  React / Vue                                │
  │  Vercel 托管                                 │
  │  精致 UI + 响应式设计                        │
  └─────────────────────────────────────────────┘
```

#### 正式前端页面路由

```
  /                    → 首页（最新日报列表，按日期倒序）
  /daily/:date         → 某日日报详情（含收藏按钮）
  /login               → 登录页（邮箱+密码 / GitHub）
  /register            → 注册页
  /bookmarks           → 收藏列表（需登录）
  /history             → 浏览历史（需登录）
  /search?q=&tag=&    → 搜索/过滤
  /about               → 关于本项目
```

### 2.6 PDF 导出方案

#### 技术选型：纯前端 html2pdf.js

```
  为什么选纯前端方案？
  ┌─────────────────────────────────────────────┐
  │  ✅ 零服务器成本，浏览器直接生成              │
  │  ✅ 不需要额外的后端服务                      │
  │  ✅ 支持自定义样式和排版                      │
  │  ⚠️ 大文档时浏览器可能卡顿（单篇文章无问题）   │
  └─────────────────────────────────────────────┘

  实现方式：
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
  <script>
    const element = document.getElementById('article-content');
    html2pdf().from(element).save('article.pdf');
  </script>
```

#### PDF 导出内容

```
  ┌─────────────────────────────────────────────┐
  │            单篇文章 PDF                       │
  ├─────────────────────────────────────────────┤
  │                                              │
  │  AI Industry Digest · PDF 导出               │
  │  ─────────────────────────────────           │
  │                                              │
  │  标题：DeepSeek 发布新推理模型                │
  │  来源：机器之心 · 2026-06-03                 │
  │  标签：[产品发布] [AI]                       │
  │  原文链接：https://...                       │
  │                                              │
  │  AI 摘要：                                    │
  │  DeepSeek 今日发布...                        │
  │                                              │
  │  原文内容：                                   │
  │  (文章正文全文)                               │
  │                                              │
  │  ─────────────────────────────────           │
  │  由 AI Industry Digest 自动生成               │
  └─────────────────────────────────────────────┘
```

### 2.7 定时调度与运维

#### 主调度：GitHub Actions

```yaml
# .github/workflows/daily_digest.yml
on:
  schedule:
    - cron: '0 22,4,10 * * *'   # 北京时间 6:00、12:00、18:00
jobs:
  collect_and_process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: python collector/run.py
      - run: python processor/ai_processor.py
      - run: python processor/reporter.py
```

#### 备用调度：Vercel Cron（兜底）

#### 数据备份：GitHub Actions 每周一次

```yaml
# .github/workflows/backup.yml
on:
  schedule:
    - cron: '0 0 * * 0'  # 每周日凌晨
jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - run: python scripts/backup.py  # 导出 Supabase 数据为 JSON
      - uses: actions/upload-artifact@v3
        with:
          name: db-backup-$(date +%Y%m%d)
          path: backup/
```

### 2.8 错误处理策略

#### 采集失败：重试 → 降级 → 跳过 → 告警

#### AI 处理异常：重试 → 截断 → 跳过

#### API 保护：Vercel Rate Limiting + Supabase RLS

---

## 三、数据流完整时序图

```
  时间线
  ──────────────────────────────────────────────────────────────►

  GitHub Actions 触发（6:00 / 12:00 / 18:00）
       │
       ▼
  ① 采集阶段（~60s）
     ├── RSS 源并行抓取 + 健康检查
     ├── arXiv API 查询
     └── GitHub API 查询
       │
       ▼
  ② 去重阶段（~10s）
     三层去重管道 → 干净文章池
       │
       ▼
  ③ AI 处理阶段（~30s）
     批处理调用 DeepSeek → 摘要 + 标签 + 重要性
       │
       ▼
  ④ 入库阶段（~5s）
     写入 Supabase articles + daily_reports
       │
       ▼
  ⑤ 运行报告推送
     飞书 Webhook 通知

  总耗时：约 2-3 分钟
  月成本：约 ¥2（DeepSeek API）
```

---

## 四、项目目录结构

```
ai-industry-digest/
├── .github/
│   └── workflows/
│       ├── daily_digest.yml          # 日报定时任务
│       └── backup.yml                # 每周数据备份
│
├── collector/                        # 数据采集模块
│   ├── __init__.py
│   ├── base.py                       # 采集器基类
│   ├── rss_collector.py              # RSS 采集器
│   ├── arxiv_collector.py            # arXiv API 采集器
│   ├── github_collector.py           # GitHub API 采集器
│   └── web_scraper.py               # 网页抓取（兜底）
│
├── processor/                        # AI 处理模块
│   ├── __init__.py
│   ├── dedup.py                      # 去重管道
│   ├── ai_processor.py              # DeepSeek API 调用
│   └── reporter.py                  # 日报生成
│
├── api/                              # API 层
│   ├── __init__.py
│   ├── main.py                      # FastAPI 入口
│   ├── routes/
│   │   ├── articles.py              # 文章查询接口
│   │   ├── reports.py               # 日报查询接口
│   │   ├── bookmarks.py             # 收藏接口
│   │   └── history.py               # 历史记录接口
│   └── models/
│       └── database.py              # Supabase 连接
│
├── scripts/
│   ├── backup.py                    # 数据备份脚本
│   └── health_check.py             # 源健康检查
│
├── frontend/                         # 正式前端（最终阶段）
│   └── src/
│
├── test/                             # 简陋测试前端
│   ├── test_index.html               # 日报列表测试
│   ├── test_article.html             # 文章详情测试
│   └── test_login.html              # 登录流程测试
│
├── config/
│   └── sources.yaml                 # 信息源配置
│
├── requirements.txt                 # Python 依赖
├── vercel.json                      # Vercel 部署配置
├── proposal.md
├── design.md
└── tasks.md
```
