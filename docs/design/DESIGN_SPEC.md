# Signal — 设计规范 (Design Spec)

> 版本: v1.0  
> 最后更新: 2026-06-04  
> 作用: 作为后续功能开发的视觉和交互标杆

---

## 一、品牌与调性

| 维度 | 规范 |
|------|------|
| 产品名 | **Signal** |
| 定位 | AI 行业资讯日报聚合平台 |
| 调性 | 简洁、克制、内容优先 |
| Logo | 衬线字体 `Source Serif 4`，首字母大写，无图标 |

---

## 二、颜色系统

### 2.1 浅色主题（默认）

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-bg-white` | `#FBFCFD` | 页面主背景 |
| `--color-bg-off` | `#F6F7F8` | 次级背景（AI 精读/对话区） |
| `--color-bg-hover` | `#F0F1F2` | 悬停背景 |
| `--color-bg-toolbar` | `#EDEEF0` | 工具条背景 |
| `--color-bg-sidebar` | `#FAFBFC` | 侧栏背景 |
| `--color-border-light` | `#E8EAED` | 分割线/边框 |
| `--color-border` | `#D8DCE0` | 活跃边框 |
| `--color-border-bold` | `#B0B4B8` | 输入框边框 |
| `--color-text-title` | `#1A1C1E` | 标题文字 |
| `--color-text-body` | `#2C2E32` | 正文文字 |
| `--color-text-muted` | `#686C72` | 次要文字 |
| `--color-text-label` | `#8C9096` | 标签文字 |
| `--color-high` | `#D4322E` | 高重要性（红色） |
| `--color-medium` | `#C8960A` | 中重要性（金色） |
| `--color-low` | `#8C9096` | 低重要性（灰色） |
| `--color-blue-link` | `#2864A8` | 链接/交互色 |
| `--color-success` | `#1E8E4A` | 成功状态 |

### 2.2 深色主题（待实现）

- 使用 `data-theme="dark"` 切换
- 所有 `--color-*` 变量反转
- 背景深色系（`#1A1A1A`），文字浅色系（`#E8EAED`）
- 跟随系统默认或用户手动选择

---

## 三、字体系统

| Token | 字体 | 用途 |
|-------|------|------|
| `--font-display` | `Source Serif 4`, Georgia, serif | 标题、Logo |
| `--font-body` | `Inter`, -apple-system, sans-serif | 正文、UI 文字 |
| `--font-mono` | `JetBrains Mono`, monospace | 代码块、技术内容 |

**字号方案：**
- 默认字号：`14px`（`--font-size-base`）
- 小：`13px`
- 中：`15px`
- 大：`17px`

---

## 四、布局结构

### 4.1 全局布局

```
┌────────────────────────────────────────┐
│  侧栏 (200px)    │  顶栏 (48px)         │
│  ─────────────   │  [🔍]               │
│  今日日报        │                      │
│  收藏            ├──────────────────────┤
│  浏览历史        │                      │
│  (设置)          │  内容区               │
│                  │  (Outlet)            │
│  ─────────────   │                      │
│  ● v2.0 · Signal │                      │
│  [用户名]        │                      │
│  [退出]          │                      │
└────────────────────────────────────────┘
```

| 区域 | 尺寸 | 说明 |
|------|------|------|
| 侧栏 | `200px` | 固定宽度，深色背景 (#FAFBFC) |
| 顶栏 | `48px` | 固定高度，白色背景 |
| 内容区 | `flex-1` | 自适应，溢出滚动 |
| 右侧面板 | `280px` | 首页热词/洞察面板，可折叠 |
| 文章详情右侧 | `380px` | 深入对话面板 |

### 4.2 断点

| 断点 | 行为 |
|------|------|
| < `1024px` | 侧栏隐藏，顶部汉堡图标展开 |
| ≥ `1024px` | 侧栏固定显示 |

### 4.3 页面布局

**首页（日报视图）：**
```
[筛选栏 (FilterBar)]
──────────────
[日期导航 (DateNav)]
[数据统计 (DataStats)]
[头条文章 (HeroArticle)]
[来源分组 (ArticleGroup)]
  ├── 机器之心 (3篇)
  ├── arXiv (5篇)
  └── ...
```

**文章详情页：**
```
[← 返回]  [文章标题]                   ← 顶栏
────────────────────────────────────────
[左侧: 文章内容]    [右侧: 深入对话]    ← 380px
  AI 精读              预设问题列表
  标题                 对话消息流
  来源·日期 [★收藏]    输入框 / 发送
  正文
  ─────────
  [导出 PDF]
```

**登录页：**
```
居中卡片 (400px max)
  Logo: Signal
  标题: 登录 / 注册
  邮箱输入框
  密码输入框
  ── 或 ──
  [⬡ 使用 GitHub 登录]    ← 黑色按钮
  忘记密码 / 切换注册
```

---

## 五、组件规范

### 5.1 按钮

| 类型 | 样式 | 示例 |
|------|------|------|
| 主按钮 | 蓝色填充 `#2864A8` | 「登录」「发送」 |
| 文字按钮 | 无背景，蓝色文字 | 「返回」「注册」 |
| 轮廓按钮 | 无背景，灰色边框 `#D8DCE0` | 「导出 PDF」 |
| 危险按钮 | 红色文字 `#D4322E` | 「退出登录」 |
| GitHub 登录 | 黑色填充 `#1A1C1E` + GitHub 图标 | 「使用 GitHub 登录」 |

### 5.2 卡片/区块

- **圆角：** `4px`（标准）、`6px`（登录卡片）、`12px`（预留）
- **阴影：** 登录卡片 `0 4px 24px rgba(0,0,0,0.08)`
- **AI 精读区块：** 浅灰背景 `#F6F7F8` + 圆角 `4px` + 内边距 `16px`

### 5.3 标签 (Tags)

- 浅灰背景 `#E8EAED`
- 文字 `#686C72`
- 字号 `12px`
- 圆角 `4px`
- 内边距 `4px 8px`

### 5.4 筛选栏 (FilterBar)

- 重要性筛选：`全部 / 高 / 中 / 低`
- 来源筛选：下拉列表
- 标签筛选：横向滚动标签组
- 活跃筛选数显示 badge

### 5.5 日期导航 (DateNav)

- 默认显示最近 3 天
- 点击「展开」显示 7 天
- 点击「更早」下拉选择
- 选中态：浅灰背景 `#E8EAED` + 中等字重

### 5.6 文章卡片 (ArticleCard)

| 模式 | 展示内容 |
|------|---------|
| compact | 标题 + 来源·日期 + 重要性指示器 |
| detailed | 同上 + 摘要/正文片段 |

- 标题默认为常规字重，高重要性文章加粗（weight: 500）
- 来源·日期灰字 `#8C9096`，字号 `11px`
- 重要性左侧条：红色 `3px`（高）/ 金色（中）/ 灰色（低）

### 5.7 收藏按钮

- SVG 五角星图标
- 已收藏：金色实心 `#C8960A` + 文字「已收藏」
- 未收藏：灰色空心 `#8C9096` + 文字「收藏」
- 位置：文章信息区右侧，与「在新窗口阅读」并列

---

## 六、交互规范

### 6.1 过渡动画

| 场景 | 动画 |
|------|------|
| 页面载入 | `fadeIn` — 0.3s ease-out |
| 侧栏展开/收起 | `translateX` — 0.3s |
| 右侧面板折叠 | `width` + `opacity` — 0.3s |
| 文章出现 | `slideInUp` — 0.3s ease-out |

### 6.2 加载状态

- 三圆点跳动动画
- 居中显示
- 无骨架屏（保持简洁）

### 6.3 错误状态

- 居中图标 + 文字 + 操作按钮
- 可「重试」或「返回」

### 6.4 缓存策略

- 首页日报列表缓存到 `localStorage`（key: `signal_home_cache`）
- 网络请求失败时显示缓存 + 黄色提示条「数据加载失败 · 显示 N 分钟前的缓存」
- 设置偏好（主题/字号/语言）存 `localStorage`

---

## 七、PDF 导出

| 维度 | 方案 |
|------|------|
| 技术栈 | `html2canvas` + `jsPDF` |
| 触发方式 | 点击「导出 PDF」按钮 → 直接下载 |
| 用户操作 | 零操作，无需弹窗/新窗口 |
| 中文支持 | 浏览器渲染 → canvas 截图，100% 正确 |
| 分页 | 自动按 A4 高度拆分，支持超长文章 |
| 内容 | 仅标题 + 来源·日期 + 正文 |
| 字体 | `Source Serif 4` / `Noto Serif CJK SC` / `STSong` |
| 后台不可见 div | `position: fixed; top: -9999px; width: 794px` |

---

## 八、功能路由

| 路径 | 页面 | 权限 | 侧栏入口 |
|------|------|------|---------|
| `/` | 首页（今日日报） | 公开 | 今日日报 |
| `/search` | 搜索页 | 公开 | （顶栏搜索） |
| `/bookmarks` | 收藏 | 需登录 | 收藏 |
| `/history` | 浏览历史 | 需登录 | 浏览历史 |
| `/profile` | 个人中心 | 需登录 | （底部头像） |
| `/settings` | 设置页 | 公开 | 待添加 |
| `/login` | 登录/注册 | 公开 | 无侧栏 |

---

## 九、后端接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/reports` | GET | 日报列表（分页，按日期倒序） |
| `/api/reports/{date}` | GET | 单日报详情（含文章列表） |
| `/api/articles` | GET | 文章搜索/过滤 |
| `/api/articles/{id}` | GET | 文章详情 |
| `/api/sources` | GET | 信息来源列表 |
| `/api/tags` | GET | 标签列表 |
| `/api/stats` | GET | 系统统计 |
| `/api/proxy?url=` | GET | 文章代理 |
| `/api/auth/signup` | POST | 注册 |
| `/api/auth/login` | POST | 登录 |
| `/api/auth/logout` | POST | 登出 |
| `/api/bookmarks` | GET/POST | 收藏列表/添加 |
| `/api/bookmarks/{id}` | DELETE | 取消收藏 |
| `/api/history` | GET/POST | 浏览历史 |
| `/api/chat` | POST | 文章对话 |

---

## 十、数据定义

### 日报文章分组

```
articles: {
  high:    [...],   // 高重要性
  medium:  [...],   // 中重要性
  low:     [...]    // 低重要性
}
```

### 文章对象

```json
{
  "id": "uuid",
  "title": "string",
  "url": "string",
  "source_name": "string",
  "raw_content": "string",
  "summary": "string",
  "tags": ["string"],
  "importance": "high|medium|low",
  "importance_reason": "string",
  "published_at": "ISO datetime",
  "source_refs": ["string"]
}
```

### 日报对象

```json
{
  "report_date": "YYYY-MM-DD",
  "total_articles": "number",
  "source_count": "number",
  "summary_insight": "string",
  "trending_keywords": ["string"],
  "articles": { "high": [], "medium": [], "low": [] }
}
```

---

## 十一、已确认但未实现的功能

| 功能 | Phase | 状态 |
|------|-------|------|
| 深色主题 | Phase 3 | 待实现 |
| 字号调整 | Phase 3 | 待实现 |
| 语言偏好 | Phase 3 | 待实现 |
| 个人中心（统计+热力图+习惯） | Phase 4 | 待实现 |
| 后端 `/api/auth/stats` | Phase 4 | 待实现 |
| 搜索结果高亮 | Phase 2 | 待实现 |
| 昵称编辑/改密码 | Phase 4 | 待实现 |
