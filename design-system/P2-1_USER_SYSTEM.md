# Signal — P2-1 用户系统完善执行计划

> 功能：收藏 / 历史记录 / 个人中心
> 后端状态：API 已完成
> 前端状态：需新建 3 个页面 + 改造 4 个现有组件
> 预估工时：3h

---

## 一、现状

### 1.1 已完成（不需改动）

```
后端:
  GET  /auth/me           → 用户资料
  POST /auth/bookmarks    → 添加收藏
  DELETE /auth/bookmarks/{id} → 取消收藏
  GET  /auth/bookmarks    → 收藏列表（分页）
  POST /auth/history      → 记录浏览历史（ArticleReader 已在调用）
  GET  /auth/history      → 历史列表（分页）
  POST /auth/feedback     → 文章反馈

数据库:
  bookmarks / reading_history / article_feedback / user_profiles 表已建

前端 API 客户端:
  api.getBookmarks() / addBookmark() / removeBookmark()  ← 已存在
  api.getHistory() / addHistory()                         ← 已存在
  api.addHistory(articleId)                               ← ArticleReader 已在调用
```

### 1.2 需完成

```
前端:
  pages/Bookmarks.jsx    ← 新建（收藏列表页）
  pages/History.jsx      ← 新建（浏览历史页）
  pages/Profile.jsx      ← 新建（个人中心页 + 设置）

组件改造:
  ArticleReader.jsx      ← 改造（加收藏/取消按钮）
  Layout.jsx             ← 改造（侧边栏加导航入口）
  App.jsx                ← 改造（加路由）
  
认证:
  AuthContext.jsx        ← 改造（接入真实 API 或保留 demo + 增加 feedback）
```

---

## 二、改动清单

### 2.1 收藏页 — `pages/Bookmarks.jsx`（~80 行）

**功能：**
- 展示当前用户收藏的文章列表
- 每篇文章可点击进入阅读模式
- 每篇文章可取消收藏
- 分页

**路由：** `/bookmarks`

**UI：**
```
收藏的文章

┌──────────────────────────────────────┐
│ ArticleCard (detailed variant)       │
│                         [取消收藏]    │  ← 灰色小字
├──────────────────────────────────────┤
│ ArticleCard                          │
│                         [取消收藏]    │
└──────────────────────────────────────┘

分页（如果有）
```

**依赖：** `api.getBookmarks()`, `api.removeBookmark()`, `ArticleCard`

**估时：** 30 min

---

### 2.2 历史记录页 — `pages/History.jsx`（~70 行）

**功能：**
- 展示当前用户的浏览历史
- 按时间倒序，每天分组（今天 / 昨天 / 更早）
- 每篇文章可点击阅读
- 分页

**路由：** `/history`

**UI：**
```
浏览历史

今天
├── ArticleCard
├── ArticleCard

昨天
├── ArticleCard

06/01 周日
├── ArticleCard

分页
```

**依赖：** `api.getHistory()`, `ArticleCard`

**估时：** 25 min

---

### 2.3 个人中心页 — `pages/Profile.jsx`（~100 行）

**功能：**
- 展示用户头像 / 昵称
- 收藏和历史的计数
- 反馈入口
- 退出登录

**路由：** `/profile`

**UI：**
```
  ┌──────────────────────────────┐
  │          (头像圈)             │
  │        Demo User              │
  │    加入时间: 2026-06          │
  ├──────────────────────────────┤
  │   📑 收藏的文章     12 篇  →  │
  │   📖 浏览历史      34 篇  →  │
  ├──────────────────────────────┤
  │   ⚙️ 设置                    │
  │   💬 意见反馈                │
  │   🚪 退出登录                │
  └──────────────────────────────┘
```

**依赖：** `useAuth`

**估时：** 30 min

---

### 2.4 ArticleReader 改造 — 收藏按钮（~10 行）

**改动：** 在 Top bar 右侧、来源旁边加一个收藏图标按钮

```
[← 返回]  [文章标题...]              [♡ arXiv · 06/03]
                                      ↑ 空心/实心切换
```

**逻辑：**
- 加载文章时，检查是否已收藏（可从当前 article 的 `is_bookmarked` 字段判断）
- 点击收藏 → `api.addBookmark(articleId)`
- 点击取消 → `api.removeBookmark(bookmarkId)`
- 需要确认后端返回 `is_bookmarked` 字段

**估时：** 10 min

---

### 2.5 Layout 侧边栏改造（~5 行）

**改动：** `NAV_ITEMS` 增加导航项

```js
const NAV_ITEMS = [
  { path: '/', label: '今日日报' },
  { path: '/bookmarks', label: '收藏' },
  { path: '/history', label: '浏览历史' },
];
```

**路由激活判断：** 当前路径匹配时高亮

**估时：** 3 min

---

### 2.6 App.jsx 添加路由（~8 行）

```jsx
<Route path="bookmarks" element={<BookmarksPage onReadArticle={setReaderArticle} />} />
<Route path="history" element={<HistoryPage onReadArticle={setReaderArticle} />} />
<Route path="profile" element={<ProfilePage />} />
```

**估时：** 2 min

---

### 2.7 AuthContext 改造 — 接入真实 API（可选，30min）

**当前状态：** demo 模式，login() 接收一个假 userData，存到 localStorage

**可升级方向：**
- 点击「登录」→ 调 `/api/auth/login` → 获取 JWT → 存到 localStorage
- 所有 `request()` 调用自动在 `Authorization` header 中带上 token
- 点击「退出」→ 清除 token
- 用户打开页面时用缓存的 token 调 `/api/auth/me` 获取资料

**或者不升级认证系统，保持 demo 模式。** 当前 demo 用户 id 为 `demo-user`，后端 `get_user_id()` 从 `Authorization` header 取 ID 而非验证 JWT。所以只要前端在 `request()` 中传入 `Authorization: Bearer demo-user` 即可。

**改动：**
- `api/client.js`：在所有请求中自动加入 `Authorization: Bearer demo-user` header
- `AuthContext.jsx`：登录成功后调 `/api/auth/me` 获取真实资料

**估时：** 20 min

---

## 三、执行顺序

```
Step 1: AuthContext + api/client 打通 demo 认证    (15 min)  ← 基础
Step 2: Layout 侧边栏加导航项                       (3 min)  ← 入口
Step 3: App.jsx 加路由                             (2 min)  ← 路由
Step 4: Bookmarks 收藏页                           (30 min) ← 核心
Step 5: History 历史记录页                         (25 min) ← 核心
Step 6: ArticleReader 加收藏按钮                   (10 min) ← 增强
Step 7: Profile 个人中心页                         (30 min) ← 收尾
Step 8: 构建验证                                   (3 min)
────────────────────────────────────────
合计: 约 2h
```

---

## 四、不改的

| 不改 | 原因 |
|------|------|
| 不接入真实的 Supabase Auth | 后端当前 `get_user_id()` 直接从 header 取字符串，不做 JWT 验证，所以 demo token 够用 |
| 不改造后端 API | 收藏/历史/反馈/资料接口已可用 |
| 不添加「文章反馈」(👍/👎) | API 有但暂不接入 UI，后续 P2-4 |
| 不添加笔记功能 | bookmark note 字段留空 |

---

## 五、验收标准

| # | 验收项 | 通过条件 |
|---|--------|---------|
| 1 | 侧边栏 | 显示「收藏」「浏览历史」导航项，选中高亮 |
| 2 | 收藏页 | 显示收藏列表，可取消收藏，可点击阅读 |
| 3 | 历史页 | 显示浏览历史，按日分组，可点击阅读 |
| 4 | 收藏按钮 | 阅读模式顶部可切换收藏/取消 |
| 5 | 个人中心 | 显示用户信息 + 收藏/历史统计 + 退出按钮 |
| 6 | 认证 | API 请求携带 `Authorization: Bearer demo-user` |
| 7 | 构建 | `npm run build` 无报错 |

---

*文档版本 v1.0 | 后端已完成，纯前端任务*
