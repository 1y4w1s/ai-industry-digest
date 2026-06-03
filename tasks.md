# AI Industry Digest — 开发任务清单（最终版）

> **版本**: v2.0  
> **日期**: 2026-06-03  
> **关联文档**: proposal.md, design.md

---

## 开发策略

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                  │
  │  先后端，再前端                                                    │
  │                                                                  │
  │  第 1-6 周：后端开发，配合 "简陋测试前端" 验证                      │
  │  第 7-8 周：正式前端开发（React/Vue）                               │
  │                                                                  │
  │  简陋测试前端 = 纯 HTML + JS + Supabase SDK，不涉及框架/构建       │
  │  每周末都有可验证的产出                                             │
  │                                                                  │
  └─────────────────────────────────────────────────────────────────┘
```

---

## 阶段一：基础采集（第 1 周）

> **目标**：跑通数据采集流水线，把 3 个稳定 RSS 源的内容抓下来存入数据库

### 1.1 项目初始化

- [x] 初始化 Python 项目结构（目录参考 design.md）
- [x] 编写 `requirements.txt`（feedparser, requests, beautifulsoup4, fake_useragent, supabase-py, jieba）
- [x] 配置 `config/sources.yaml` 信息源清单
- [x] 注册 Supabase 项目，在 SQL Editor 中执行建表语句（articles + daily_reports）
- [x] 测试 Supabase 连接（Python 写入一条测试数据）— ✅ 已验证，62 篇成功入库

### 1.2 RSS 采集器

- [x] 实现 `collector/base.py`（Article 数据模型 + 采集器抽象基类）
- [x] 实现 `collector/rss_collector.py`（feedparser 解析 RSS）
- [ ] 接入机器之心官方 RSS，验证能正确解析（需 .env 配置后验证）
- [ ] 接入量子位官方 RSS，验证能正确解析（需 .env 配置后验证）
- [x] 实现 `collector/arxiv_collector.py`（arXiv API 查询解析）- 已验证可正常采集

### 1.3 数据存储

- [x] 实现 Supabase 写入逻辑（入库去重：URL 已存在则跳过）
- [x] 编写单次运行测试脚本：`python run.py`
- [x] 验证：手动运行后，Supabase 控制台 articles 表能看到数据 — ✅ 62 篇

**阶段一验收标准**：
```
✅ 能采集 3 个以上信息源
✅ 文章正确存入 Supabase
✅ 重复运行不会产生重复记录
```

---

## 阶段二：AI 处理（第 2 周）

> **目标**：接入 DeepSeek API，实现摘要生成、标签分类、重要性判断

### 2.1 AI 处理器

- [x] 实现 `processor/ai_processor.py`（DeepSeek API 调用）
- [x] 设计并调试 Batch Prompt（10 篇/次批量处理）
- [x] 处理 API 异常（超时重试 2 次、格式校验、Token 超限截断）
- [x] 实现结果解析（从 JSON 响应提取 summary/tags/importance/reason）

### 2.2 去重管道

- [x] 实现 `processor/dedup.py` 第一层：URL 精确去重（集合查表）
- [x] 实现第二层：标题相似度去重（jieba 分词 + Jaccard 相似度，阈值 > 85%）
- [x] 实现第三层：AI 辅助去重（70%-85% 模糊区间调用 DeepSeek 判断）

### 2.3 日报生成器

- [x] 实现 `processor/reporter.py`
- [x] 按重要性分组文章（high / medium / low）
- [x] 调用 DeepSeek 生成今日概览 + 热点关键词
- [x] 写入 daily_reports 表（需要 Supabase 配置后验证）— ✅ 已验证

**阶段二验收标准**：
```
✅ 每篇文章有 AI 生成的摘要、标签、重要性
✅ 同一新闻不同来源被正确合并（source_refs 记录）
✅ 日报记录完整（概览 + 文章列表 + 关键词）
✅ 单次运行全流程耗时 < 5 分钟
```

---

## 阶段三：自动化调度（第 3 周）

> **目标**：实现全自动定时运行，零人工干预

### 3.1 GitHub Actions 配置

- [ ] 编写 `.github/workflows/daily_digest.yml`（Cron 触发）
- [ ] 配置 Cron 表达式：北京时间 6:00 / 12:00 / 18:00
- [ ] 在 GitHub 仓库配置 Secrets（SUPABASE_URL, SUPABASE_KEY, DEEPSEEK_API_KEY）

### 3.2 异常处理与告警

- [ ] 每次运行生成状态报告（采集成功数、AI 处理数、入库数、耗时、费用）
- [ ] 配置飞书 Webhook 推送运行结果
- [ ] 实现 Vercel Cron 备用触发（兜底，每天 1 次）

### 3.3 健康检查

- [ ] 实现 `scripts/health_check.py`：信息源健康注册表
- [ ] 实现自动降级逻辑（RSS 连续 3 次失败 → 网页抓取兜底）
- [ ] 连续 5 次失败 → 飞书告警通知

### 3.4 数据备份

- [ ] 编写 `.github/workflows/backup.yml`（每周日凌晨导出 Supabase 数据为 JSON）
- [ ] 验证备份文件可恢复

**阶段三验收标准**：
```
✅ GitHub Actions 按 Cron 自动运行
✅ 运行失败自动重试 + 飞书通知
✅ 某个源挂掉不影响其他源
✅ 连续运行 3 天无人工干预
✅ 每周有自动数据备份
```

---

## 阶段四：后端 API（第 4 周）

> **目标**：构建 FastAPI 接口，支持日报查询和用户系统

### 4.1 FastAPI 项目

- [ ] 初始化 `api/` 目录结构
- [ ] 实现 `api/main.py`（FastAPI 入口 + CORS 配置）
- [ ] 实现 `api/models/database.py`（Supabase 客户端）

### 4.2 内容接口

- [ ] `GET /api/reports` — 日报列表（分页，按日期倒序）
- [ ] `GET /api/reports/:date` — 单日报详情（包含文章列表）
- [ ] `GET /api/articles` — 文章搜索/过滤（关键词、标签、日期范围、分页）
- [ ] `GET /api/articles/:id` — 单篇文章详情

### 4.3 用户系统数据库

- [ ] 在 Supabase 执行新增表语句（user_profiles, bookmarks, reading_history, article_feedback）
- [ ] 配置 Supabase RLS（Row Level Security）保护用户数据

### 4.4 用户接口

- [ ] `POST /api/auth/register` — 注册（邮箱+密码）
- [ ] `POST /api/auth/login` — 登录
- [ ] `GET /api/auth/me` — 获取当前用户信息
- [ ] Supabase Auth 配置：开启 Email + Password，开启 GitHub OAuth

### 4.5 收藏与历史接口

- [ ] `POST /api/bookmarks` — 添加收藏
- [ ] `DELETE /api/bookmarks/:id` — 取消收藏
- [ ] `GET /api/bookmarks` — 获取收藏列表（登录用户）
- [ ] `POST /api/history` — 记录浏览历史（点击即记录）
- [ ] `GET /api/history` — 获取浏览历史（登录用户）

### 4.6 验证：简陋测试前端

- [ ] 创建 `test/test_index.html` — 调接口显示日报列表
- [ ] 创建 `test/test_article.html` — 调接口显示单篇文章
- [ ] 验证所有接口在 FastAPI `/docs` 页面可调通

**阶段四验收标准**：
```
✅ FastAPI 所有接口可调通
✅ 注册/登录流程可跑通
✅ 收藏/取消/列表功能正常
✅ 点击文章自动记录浏览历史
✅ 简陋前端能显示数据
```

---

## 阶段五：用户增强功能（第 5 周）

> **目标**：实现 PDF 导出、文章反馈、搜索优化

### 5.1 PDF 导出

- [ ] 调研并集成 `html2pdf.js`（纯前端方案）
- [ ] 生成单篇文章 PDF（标题 + 来源 + 摘要 + 原文内容）
- [ ] 添加"下载 PDF"按钮（仅在文章详情页）
- [ ] 测试 PDF 排版和中文渲染

### 5.2 文章反馈

- [ ] 实现 `POST /api/feedback` — 提交 👍/👎
- [ ] 前端每个文章底部加反馈按钮
- [ ] 统计反馈数据（用于后续迭代 Prompt）

### 5.3 搜索优化

- [ ] Supabase 配置 PostgreSQL 全文搜索（tsvector）
- [ ] 优化 `GET /api/articles` 搜索性能
- [ ] 搜索支持：标题模糊匹配 + 标签精确匹配 + 来源过滤

### 5.4 验证：用户功能测试

- [ ] 创建 `test/test_login.html` — 测试注册/登录/GitHub OAuth 完整流程
- [ ] 创建 `test/test_bookmark.html` — 测试收藏/取消/列表
- [ ] 创建 `test/test_pdf.html` — 测试 PDF 导出
- [ ] 创建 `test/test_feedback.html` — 测试文章反馈

**阶段五验收标准**：
```
✅ 单篇文章可正常导出 PDF（中文正常显示）
✅ 用户可对文章进行 👍/👎 反馈
✅ 搜索返回结果准确
✅ 登录流程用户无感流畅
```

---

## 阶段六：运维完善（第 6 周）

> **目标**：加固系统稳定性，处理边缘情况

### 6.1 API 保护

- [ ] 配置 Vercel Rate Limiting（每小时每 IP 最多 100 次请求）
- [ ] 完善 Supabase RLS 策略（用户只能访问自己的 bookmarks / history）

### 6.2 边缘情况处理

- [ ] 处理 Supabase 连接断开时的重试逻辑
- [ ] 处理 GitHub Actions 运行超时（设置 timeout-minutes）
- [ ] 处理 AI API 返回格式异常时的降级策略
- [ ] 处理空日报（当天无文章）的展示逻辑

### 6.3 数据完整性

- [ ] 实现每日运行后自动校验（articles 数 vs daily_reports 数）
- [ ] 验证备份恢复流程可执行

### 6.4 简陋前端完善

- [ ] 整合所有测试页面为一个可用的 mini 版前端
- [ ] FastAPI 静态文件托管 `test/` 目录
- [ ] 验证从首页 → 日报详情 → 登录 → 收藏的完整链路

**阶段六验收标准**：
```
✅ API 有基本防护措施
✅ 所有已知边缘情况有处理
✅ 完整用户链路可跑通
✅ 可展示给其他人看（哪怕 UI 简陋）
```

---

## 阶段七：正式前端开发（第 7 周）

> **目标**：构建美观可用的 React/Vue 前端

### 7.1 项目初始化

- [ ] 初始化 React（推荐）或 Vue 项目
- [ ] 配置项目路由（react-router-dom / vue-router）
- [ ] 配置 Supabase JS SDK
- [ ] 选择并引入 UI 框架（Tailwind CSS / Ant Design / 等）

### 7.2 页面开发

- [ ] 首页：日报列表（日期倒序，每日概览卡片）
- [ ] 日报详情页：当日文章列表（按重要性排序，收藏按钮，反馈按钮）
- [ ] 文章详情页：文章内容 + 摘要 + PDF 导出按钮
- [ ] 登录/注册页：邮箱+密码表单 + GitHub 登录按钮
- [ ] 收藏页：用户收藏列表（支持取消收藏）
- [ ] 历史页：用户浏览历史
- [ ] 搜索页：搜索框 + 过滤条件 + 结果列表

### 7.3 状态管理

- [ ] 登录状态管理（全局 auth context）
- [ ] 收藏状态管理（已收藏/未收藏切换）
- [ ] 加载状态 / 空状态 / 错误状态处理

**阶段七验收标准**：
```
✅ 所有页面基本可用
✅ 登录流程完整
✅ 收藏/历史功能正常
✅ 响应式布局基础
```

---

## 阶段八：前端打磨与上线（第 8 周）

> **目标**：精致 UI 打磨，部署上线

### 8.1 UI 打磨

- [ ] 设计系统统一（颜色、字体、间距、图标）
- [ ] 移动端适配完善（手机浏览器体验）
- [ ] 加载动画 / 过渡动画
- [ ] 夜间模式（可选，加分项）

### 8.2 部署上线

- [ ] 部署前端到 Vercel
- [ ] 配置自定义域名（可选）
- [ ] 配置 Vercel Functions 代理 API 请求
- [ ] 配置 Supabase 生产环境

### 8.3 发布准备

- [ ] 写 README.md（项目介绍 + 截图 + 技术栈 + 在线地址）
- [ ] 测试所有功能在手机上正常
- [ ] 检查 SEO 基础配置（title, description, og:image）

### 8.4 收集反馈

- [ ] 发布到 V2EX / 技术社区
- [ ] 设置反馈入口（内置反馈表单）
- [ ] 监控运行日志，修复首批 Bug

**阶段八验收标准**：
```
✅ 网站可公开访问
✅ 手机端体验良好
✅ 获得首批真实用户反馈
✅ 连续运行 N 天无故障
```

---

## 里程碑总览

```
  阶段            时间        核心产出                         验证方式
  ─────────────────────────────────────────────────────────────────────────────
  ① 基础采集      第 1 周    采集器 + 数据入库                  Supabase 控制台
  ② AI 处理       第 2 周    摘要/标签/去重/日报生成             Supabase 数据
  ③ 自动化调度    第 3 周    GitHub Actions + 告警 + 备份       GitHub 运行日志
  ④ 后端 API      第 4 周    FastAPI 接口 + 用户系统            /docs + 简陋前端
  ⑤ 用户增强      第 5 周    PDF + 反馈 + 搜索                 简陋测试页面
  ⑥ 运维完善      第 6 周    防护 + 边缘情况 + 端到端链路        完整用户链路
  ⑦ 正式前端      第 7 周    React/Vue 页面                    本地 dev 环境
  ⑧ 打磨上线      第 8 周    UI 打磨 + 部署 + 发布              vercel.app 在线
```

---

## 关键命令速查

### 安装依赖

```bash
pip install feedparser requests beautifulsoup4 fake-useragent supabase jieba
pip install "fastapi[standard]" uvicorn
```

### Supabase 建表

在 Supabase 管理后台 → SQL Editor 中执行 `design.md` 中的完整建表语句（6 张表）。

### GitHub Actions Secrets 配置

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：

| 名称 | 说明 |
|------|------|
| `SUPABASE_URL` | Supabase 项目 URL |
| `SUPABASE_KEY` | Supabase service_role key |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 |
| `FEISHU_WEBHOOK` | 飞书机器人 Webhook URL |

### 运行测试

```bash
# 全流程运行
python run.py

# 启动 FastAPI（含简陋前端静态文件）
uvicorn api.main:app --reload
# 访问 http://localhost:8000/docs 查看接口
# 访问 http://localhost:8000/test/ 查看简陋前端
```

---

## 功能完整性清单

```
  核心功能                                   状态        阶段
  ───────────────────────────────────────────────────────────
  ✅ 多源 RSS 采集                          已规划      阶段一
  ✅ arXiv 学术论文采集                      已规划      阶段一
  ✅ GitHub Trending 采集                   已规划      阶段一
  ✅ 三层去重管道（URL + 相似度 + AI）        已规划      阶段二
  ✅ AI 摘要生成                             已规划      阶段二
  ✅ AI 标签分类 + 重要性排序                 已规划      阶段二
  ✅ 日报生成（概览 + 关键词 + 趋势）         已规划      阶段二
  ✅ GitHub Actions 定时调度                已规划      阶段三
  ✅ 飞书告警通知                            已规划      阶段三
  ✅ 数据备份                               已规划      阶段三
  ✅ 健康检查 + 自动降级                     已规划      阶段三
  ✅ FastAPI 接口                           已规划      阶段四
  ✅ 邮箱+密码登录                          已规划      阶段四
  ✅ GitHub OAuth 登录                      已规划      阶段四
  ✅ 文章收藏                                已规划      阶段四
  ✅ 浏览历史                                已规划      阶段四
  ✅ PDF 导出（单篇）                        已规划      阶段五
  ✅ 用户反馈 👍/👎                         已规划      阶段五
  ✅ 搜索优化（全文搜索）                     已规划      阶段五
  ✅ API 防护（Rate Limit + RLS）           已规划      阶段六
  ✅ 边缘情况处理                            已规划      阶段六
  ✅ 正式前端（React/Vue）                   已规划      阶段七
  ✅ 移动端适配                              已规划      阶段八
  ✅ 部署上线 + 社区发布                     已规划      阶段八
```
