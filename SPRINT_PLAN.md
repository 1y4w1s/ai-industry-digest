# AI 行业资讯聚合平台 — 攻坚冲刺计划

> **版本**: v2.1  
> **更新日期**: 2026-06-04  
> **线上地址**: [http://43.139.133.245:8080](http://43.139.133.245:8080)  
> **投入节奏**: 集中攻坚（5+ 小时/周）  
> **核心原则**: 安全先行 → 自动化运转 → 功能补全 → 体验打磨

---

## 总体路线

```
Phase 1 ─── 安全加固 + 自动化采集 ─── 让系统自主安全运转
      |
Phase 2 ─── 功能补全 ─── PDF 导出 + 搜索高亮
      |
Phase 3 ─── 设置页面 ─── 夜间模式 + 字号 + 语言偏好
      |
Phase 4 ─── 个人中心改版 ─── 统计 + 热力图 + 阅读习惯 + 账号管理
```

---

## Phase 1：安全加固 + 自动化采集（优先）

### 1.1 替换 Supabase 密钥（安全 P0）

**目标**：消除前端 bundle 中暴露的 service_role 密钥风险

| 步骤 | 操作 | 文件 |
|------|------|------|
| 1 | 登录 Supabase 控制台 → Settings → API，复制 **anon public key** | — |
| 2 | 替换 `frontend/.env` 中的 `VITE_SUPABASE_ANON_KEY` 为 anon key | [frontend/.env](file:///d:/ai-industry-digest/frontend/.env) |
| 3 | 确认后端根目录 `.env` 仍保留 service_role key（后端不需要改动） | `./.env` |
| 4 | 构建前端并部署到服务器 | `npm run build` → scp |
| 5 | 验证登录/注册/收藏/历史功能正常 | 浏览器测试 |

**预期效果**：前端使用 anon key（受限权限），后端保留 service_role（管理权限），各司其职。即使 anon key 泄露，攻击者也只能访问自己的数据。

### 1.2 配置 Supabase RLS 策略（安全 P0）

**目标**：为各用户数据表添加行级安全策略

需要配置 RLS 的表：

| 表名 | RLS 策略 |
|------|----------|
| `bookmarks` | 用户只能 SELECT/INSERT/UPDATE/DELETE 自己的收藏 (`user_id = auth.uid()`) |
| `reading_history` | 用户只能 SELECT/INSERT/UPDATE/DELETE 自己的历史 (`user_id = auth.uid()`) |
| `article_feedback` | 用户只能 SELECT/INSERT/UPDATE 自己的反馈 (`user_id = auth.uid()`) |
| `user_profiles` | 用户只能 SELECT/UPDATE 自己的资料 (`id = auth.uid()`) |

**不开放给前端的表**（仅后端通过 service_role 访问）：`articles`、`daily_reports`。

### 1.3 配置 GitHub OAuth 登录

**目标**：用户可以用 GitHub 账号一键登录

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | GitHub 侧：Settings → Developer settings → OAuth Apps → 新建应用 | 回调 URL: `https://vobpkdrujixghvttgkuq.supabase.co/auth/v1/callback` |
| 2 | Supabase 侧：Authentication → Providers → GitHub → 填写 Client ID 和 Secret | — |
| 3 | 前端 LoginPage 添加「使用 GitHub 登录」按钮 | 调用 `supabase.auth.signInWithOAuth({ provider: 'github' })` |

### 1.4 配置 GitHub Actions（自动化 P0）

**目标**：让定时采集流水线跑起来，系统自主运转

| 步骤 | 操作 |
|------|------|
| 1 | GitHub 仓库 → Settings → Secrets and variables → Actions |
| 2 | 添加 `SUPABASE_URL`（从根目录 `.env` 获取） |
| 3 | 添加 `SUPABASE_KEY`（从根目录 `.env` 获取，即 service_role key） |
| 4 | 添加 `DEEPSEEK_API_KEY`（从根目录 `.env` 获取） |
| 5 | 手动触发一次 workflow 验证：仓库 → Actions → daily digest → Run workflow |
| 6 | 检查 Supabase 数据库是否有新数据写入 |
| 7 | 可选：配置 `FEISHU_WEBHOOK` Secret 开启飞书通知 |

**定时计划**（已在 daily.yml 中配置）：
- 北京时间 6:00 → 采集早间资讯
- 北京时间 12:00 → 采集午间更新
- 北京时间 18:00 → 采集晚间资讯

---

## Phase 2：功能补全

### 2.1 浏览器打印 PDF

**目标**：文章详情页支持导出/打印为 PDF，零依赖

方案：使用 `window.print()` + `@media print` CSS

| 步骤 | 操作 | 文件 |
|------|------|------|
| 1 | ArticleReader 添加「打印/导出 PDF」按钮 | [ArticleReader.jsx](file:///d:/ai-industry-digest/frontend/src/components/ArticleReader.jsx) |
| 2 | 添加 `@media print` CSS 样式（隐藏侧栏、导航、按钮，只保留文章正文） | 内联或 index.css |
| 3 | 调用 `window.print()` 触发浏览器打印对话框 | — |
| 4 | 用户可选择「另存为 PDF」 | 浏览器原生支持 |

**优势**：零依赖、零维护、中文渲染完美、用户可控制纸张/边距。

### 2.2 搜索结果高亮

**目标**：搜索页中匹配的关键词用高亮标记

| 步骤 | 操作 | 文件 |
|------|------|------|
| 1 | 编写纯函数 `highlightText(text, keyword)`，将匹配部分包裹 `<mark>` 标签 | [SearchPage.jsx](file:///d:/ai-industry-digest/frontend/src/pages/SearchPage.jsx) |
| 2 | 在文章标题和摘要渲染时调用高亮函数 | — |
| 3 | 添加 `mark` 标签 CSS 样式（浅黄色背景） | [index.css](file:///d:/ai-industry-digest/frontend/src/index.css) |

---

## Phase 3：设置页面（SettingsPage）

**目标**：独立的页面外观配置页面，管理阅读体验偏好

| 分区 | 功能 | 实现方式 |
|------|------|----------|
| **主题** | 浅色 / 深色 / 跟随系统 | CSS 变量 + `data-theme` 属性，偏好存 localStorage |
| **字号** | 小 / 中 / 大 | CSS 变量 `--font-size-base`，三档切换 |
| **语言偏好** | 中文 / 英文 / 全部 | 传给后端 API 作为过滤参数 |

### 路由与导航

- 路由：`/settings`
- 侧栏（Layout）新增导航项：**设置**（在「浏览历史」下方）
- 设计：延续现有设计风格，简洁的选项卡片式布局

### 夜间模式技术方案

- 使用 CSS 自定义属性（variables）定义颜色，现有 `@theme` 中的色值扩展出 dark 版本
- 通过 `<html data-theme="dark">` 属性切换
- 默认跟随系统 `prefers-color-scheme` 媒体查询
- 手动切换后持久化到 `localStorage`
- 新建 `ThemeContext` 统一管理主题状态

### 文件改动

| 文件 | 改动 |
|------|------|
| `frontend/src/pages/SettingsPage.jsx` | **新建** — 设置页组件 |
| `frontend/src/context/ThemeContext.jsx` | **新建** — 主题/字号/语言上下文 |
| `frontend/src/components/Layout.jsx` | 侧栏添加「设置」入口，注入 ThemeContext |
| `frontend/src/App.jsx` | 添加 `/settings` 路由 |
| `frontend/src/index.css` | 添加 dark 主题 CSS 变量 + 字号变量 |

---

## Phase 4：个人中心改版（ProfilePage）

### 4.1 新增后端聚合接口 `GET /api/auth/stats`

**目标**：一次调用返回所有统计数据，避免前端大量计算，对性能友好

```json
{
  "total_read": 128,
  "total_bookmarks": 23,
  "streak_days": 5,
  "daily_counts": [
    { "date": "2026-06-04", "count": 3 },
    { "date": "2026-06-03", "count": 5 }
  ],
  "source_distribution": [
    { "source": "机器之心", "count": 45 },
    { "source": "arXiv", "count": 32 }
  ],
  "tag_frequency": [
    { "tag": "LLM", "count": 38 },
    { "tag": "多模态", "count": 22 }
  ],
  "importance_distribution": {
    "high": 28,
    "medium": 45,
    "low": 55
  }
}
```

#### 实现方式

- 后端 [routes/auth.py](file:///d:/ai-industry-digest/api/routes/auth.py) 新增 `GET /stats` 路由
- [database.py](file:///d:/ai-industry-digest/api/models/database.py) 新增 `get_user_stats()` 方法
- 客户端 [client.js](file:///d:/ai-industry-digest/frontend/src/api/client.js) 新增 `api.getStats()` 方法

### 4.2 个人中心页面布局

| 分区 | 功能 | 数据来源 |
|------|------|----------|
| **用户信息** | 头像、昵称、邮箱、编辑昵称、改密码 | Supabase Auth |
| **打卡统计** | 总阅读数、总收藏数、连续阅读天数 | `/auth/stats` |
| **月度热力图** | 近 30 天阅读日历（类似 GitHub 贡献图） | `/auth/stats` → `daily_counts` |
| **阅读习惯** | 来源分布、标签云、重要性偏好 | `/auth/stats` → `source_distribution`、`tag_frequency`、`importance_distribution` |
| **账户操作** | 退出登录 | 已有 |

#### 版本演进

- **第一阶段**：实现基础统计 + 打卡 + 习惯展示（数据驱动）
- **第二阶段**：添加昵称编辑、密码修改功能

#### 文件改动

| 文件 | 改动 |
|------|------|
| `api/routes/auth.py` | 新增 `GET /stats` 路由 |
| `api/models/database.py` | 新增 `get_user_stats()` 方法 |
| `frontend/src/api/client.js` | 新增 `api.getStats()` 方法 |
| `frontend/src/pages/ProfilePage.jsx` | **重写** — 新布局 + 统计 + 习惯展示 |

---

## 任务优先级矩阵

| 任务 | 优先级 | 预估工时 | 依赖 |
|------|--------|----------|------|
| 替换 anon key（前端 .env） | 🔴 P0 | 15min | Supabase 控制台 |
| 配置 RLS 策略（SQL 脚本） | 🔴 P0 | 30min | 上一步完成 |
| GitHub OAuth 配置 | 🔴 P0 | 30min | Supabase + GitHub 控制台 |
| GitHub Secrets 配置 | 🔴 P0 | 15min | 根目录 .env 文件 |
| 验证 Actions 首次运行 | 🔴 P0 | 15min | 上一步完成 |
| 浏览器打印 PDF | 🟡 P1 | 1h | — |
| 搜索结果高亮 | 🟡 P1 | 1h | — |
| 设置页面（主题+字号+语言） | 🟡 P1 | 3h | — |
| 后端统计接口 `/auth/stats` | 🟡 P1 | 1.5h | — |
| 个人中心改版（统计+热力图+习惯） | 🟢 P2 | 3h | 后端 stats 接口完成 |
| 昵称编辑 + 改密码 | 🟢 P2 | 1h | 个人中心改版完成 |

---

## 文件改动总清单

### Phase 1 — 安全 + 自动化
| 文件 | 改动 |
|------|------|
| `frontend/.env` | 替换 `VITE_SUPABASE_ANON_KEY` 为 anon key |
| `frontend/src/pages/LoginPage.jsx` | 添加「使用 GitHub 登录」按钮 |
| GitHub 仓库 Settings | 添加 3 个 Secrets |

### Phase 2 — 功能补全
| 文件 | 改动 |
|------|------|
| `frontend/src/components/ArticleReader.jsx` | 添加打印按钮 + `@media print` 样式 |
| `frontend/src/pages/SearchPage.jsx` | 关键词高亮逻辑 |
| `frontend/src/index.css` | 添加 `mark` 标签样式 |

### Phase 3 — 设置页面
| 文件 | 改动 |
|------|------|
| `frontend/src/pages/SettingsPage.jsx` | **新建** |
| `frontend/src/context/ThemeContext.jsx` | **新建** |
| `frontend/src/components/Layout.jsx` | 侧栏添加「设置」入口 |
| `frontend/src/App.jsx` | 添加 `/settings` 路由 + ThemeProvider |
| `frontend/src/index.css` | 添加 dark 主题 CSS 变量 + 字号变量 |

### Phase 4 — 个人中心
| 文件 | 改动 |
|------|------|
| `api/routes/auth.py` | 新增 `GET /stats` |
| `api/models/database.py` | 新增 `get_user_stats()` |
| `frontend/src/api/client.js` | 新增 `api.getStats()` |
| `frontend/src/pages/ProfilePage.jsx` | **重写** |

---

## 验证清单

### Phase 1
- [ ] 前端使用 anon key，登录/注册正常
- [ ] 收藏/取消/列表功能正常
- [ ] 浏览历史记录正常
- [ ] GitHub OAuth 登录正常
- [ ] Actions 定时采集正常（触发后检查 Supabase 数据）

### Phase 2
- [ ] PDF 导出正常（中文排版正常，隐藏无关元素）
- [ ] 搜索关键词高亮显示

### Phase 3
- [ ] 浅色/深色/跟随系统三种模式正常切换
- [ ] 字号三档切换有效
- [ ] 语言偏好切换有效
- [ ] 所有偏好刷新后保持

### Phase 4
- [ ] `/auth/stats` 接口返回数据正确
- [ ] 个人中心显示总阅读数、总收藏数、连续天数
- [ ] 月度热力图正确渲染
- [ ] 来源分布/标签云/重要性偏好正确展示
- [ ] 昵称编辑、密码修改可用
