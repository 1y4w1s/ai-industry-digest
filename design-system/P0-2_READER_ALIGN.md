# Signal — P0-2 阅读模式改造执行计划

> 任务 ID: P0-2
> 当前版本: ArticleReader v3.0（早期）
> 目标版本: v3.1（对齐首页设计系统）
> 预估工时: 25 分钟

---

## 一、改动总览

| # | 改动 | 类型 | 难度 | 工时 | 影响范围 |
|---|------|------|------|------|---------|
| 1 | Top bar 返回按钮：灰色按钮 → 蓝色链接 | 视觉 | ★☆☆ | 2 min | ~5 行 |
| 2 | Top bar 加日期：网址旁显示发布时间 | 功能 | ★☆☆ | 2 min | ~2 行 |
| 3 | 加载态：纯文字 → bounce dots | 视觉 | ★☆☆ | 3 min | ~12 行 |
| 4 | 失败态：纯文字 → 图标 + 重试按钮 | 功能 | ★☆☆ | 5 min | ~20 行 |
| 5 | 原文区底色：`#fff` → `#FBFCFD` | 视觉 | ★☆☆ | 1 min | 1 行 |
| 6 | AI 面板标题色统一 `#686C72` → `#8C9096` | 视觉 | ★☆☆ | 1 min | 1 行 |
| 7 | AI 精读从右侧面板移到原文上方 | 布局 | ★★☆ | 10 min | ~40 行 |
| 8 | 右侧面板只保留「深入对话」 | 布局 | ★★☆ | 包含在 #7 | 0 行 |
| 9 | 构建验证 | — | — | 2 min | — |
| | **合计** | | | **~25 min** | |

---

## 二、详细设计

### 改动 1 — Top bar 返回按钮

**文件：** `ArticleReader.jsx`

**当前：**
```jsx
<button onClick={onBack} className="flex items-center gap-1 px-2.5 py-1 text-xs rounded transition-all"
  style={{ background: '#F0F1F2', color: '#686C72' }}>
  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
  </svg>
  返回
</button>
```

**目标：**
```jsx
<button onClick={onBack}
  style={{ fontSize: '12px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', padding: 0 }}>
  ← 返回
</button>
```

**对齐对象：** 搜索结果页 `← 返回首页` 按钮样式。

---

### 改动 2 — Top bar 增加日期

**当前：** Top bar 右侧只显示 `{article?.source_name}`

**目标：** Top bar 右侧显示 `{article?.source_name} · {article?.published_at}`

```jsx
<span className="text-xs flex-shrink-0" style={{ color: '#8C9096' }}>
  {article?.source_name}{article?.published_at ? ` · ${article.published_at.slice(0, 10)}` : ''}
</span>
```

**理由：** 用户在 Top bar 一眼看到来源 + 日期，不需要滚动到正文去找。

---

### 改动 3 — 加载态

**当前：**
```jsx
<div className="flex-1 flex items-center justify-center text-sm" style={{ color: '#8C9096' }}>
  加载中...
</div>
```

**目标：**
```jsx
<div className="flex-1 flex items-center justify-center">
  <div className="text-center">
    <div className="flex gap-1.5 justify-center mb-3">
      <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '0ms' }} />
      <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '150ms' }} />
      <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '300ms' }} />
    </div>
    <span style={{ fontSize: '13px', color: '#686C72' }}>加载中...</span>
  </div>
</div>
```

**对齐对象：** 首页加载态。

---

### 改动 4 — 失败态

**当前：**
```jsx
<div className="flex-1 flex items-center justify-center text-sm" style={{ color: '#8C9096' }}>
  加载失败
</div>
```

**目标：**
```jsx
<div className="flex-1 flex items-center justify-center">
  <div className="text-center">
    <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: '#F0F1F2', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8C9096" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
      </svg>
    </div>
    <p style={{ fontSize: '14px', color: '#1A1C1E', marginBottom: '8px' }}>文章加载失败</p>
    <div className="flex gap-2 justify-center">
      <button onClick={() => window.location.reload()} style={{ fontSize: '12px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer' }}>
        重试
      </button>
      <button onClick={onBack} style={{ fontSize: '12px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer' }}>
        返回
      </button>
    </div>
  </div>
</div>
```

**理由：** 用户需要从失败态中恢复，而不是看到一句冷冰冰的「加载失败」。

---

### 改动 5 — 原文区底色

**1 行变更：**
```
background: '#fff' → background: '#FBFCFD'
```

---

### 改动 6 — AI 面板标题色

**1 行变更：**
```
color: '#686C72' → color: '#8C9096'
```
仅「AI 精读」标题。右侧「深入对话」标题已经是 `#8C9096`，不需要改。

---

### 改动 7+8 — AI 精读移到原文上方（核心改动）

**当前布局：**
```
┌──────────────────┬─────────────────────┐
│  原文 (白色)      │  AI 精读 (灰色底)    │
│                   │  摘要               │
│  标题             │  标签               │
│  元数据           ├─────────────────────┤
│  原文内容         │  深入对话            │
│                   │  聊天记录            │
│                   │  输入框              │
└──────────────────┴─────────────────────┘
```

**目标布局：**
```
┌──────────────────┬─────────────────────┐
│  ← 返回           │  深入对话            │
│                   │  聊天记录            │
│  ┌─ AI 精读 ──┐  │                      │
│  │  摘要       │  │                      │
│  │  标签       │  │                      │
│  └────────────┘  │                      │
│                   │                      │
│  标题             │                      │
│  来源 · 日期     │                      │
│  [在新窗口阅读 ↗]│                      │
│                   │                      │
│  原文内容...      │                      │
│                   │                      │
└──────────────────┴─────────────────────┘
```

**改动内容：**

1. 右栏删除 AI 精读 + 标签区块
2. 左栏在标题上方插入 AI 精读卡片
3. AI 精读卡片样式与首页 HeroArticle 一致（`#F6F7F8`底色，16px padding）

**代码变化（右栏）：**
```jsx
// 当前右栏结构
<div className="w-[380px] ...">      ← 不删，保留整个面板
  <div className="flex-[3] ...">      ← 删掉这个区块（AI 精读）
    <h3>AI 精读</h3>                 ← 删
    <div>摘要</div>                   ← 删
    <标签>                            ← 删
  </div>
  <div className="flex-[2] ...">     ← 保留（深入对话）
    ...
  </div>
</div>
```

右栏删除 flex-[3] 后，「深入对话」占满整个右侧面板，不再分上下两部分。

**代码变化（左栏 — 在标题上方插入）：**
```jsx
{article.summary && (
  <div style={{ background: '#F6F7F8', borderRadius: '4px', padding: '16px', marginBottom: '24px' }}>
    <div className="text-sm leading-relaxed" style={{ color: '#2C2E32' }}>
      {article.summary}
    </div>
    {article.tags?.length > 0 && (
      <div className="flex flex-wrap gap-1.5 mt-3">
        {article.tags.map((t) => (
          <span key={t} className="px-2 py-0.5 text-xs rounded" style={{ background: '#E8EAED', color: '#686C72' }}>{t}</span>
        ))}
      </div>
    )}
    {article.importance_reason && (
      <div className="mt-2 text-xs italic" style={{ color: '#8C9096' }}>{article.importance_reason}</div>
    )}
  </div>
)}
```

---

## 三、不改的

| 功能 | 不改的理由 |
|------|-----------|
| 右侧「深入对话」功能逻辑 | 正常运行，不动 |
| `stripHtml` 处理逻辑 | 正确，不动 |
| 原文内容区域样式 | 字体/行高/字号已对齐 |
| 左右分栏总布局 | 去掉 AI 精读后，右栏只剩对话，更清爽 |
| 响应式断点 | 阅读模式桌面优先，移动端后续 P1-2 |

---

## 四、验收标准

| # | 验收项 | 通过条件 |
|---|--------|---------|
| 1 | 返回按钮 | 蓝色链接 `← 返回`，无背景色块 |
| 2 | Top bar 日期 | 显示 `来源 · 2026-06-03` 格式 |
| 3 | 加载态 | 三圆点 bounce +「加载中...」文字 |
| 4 | 失败态 | 图标 + 文字 +「重试」「返回」按钮 |
| 5 | 左栏底色 | `#FBFCFD`，不是 `#fff` |
| 6 | AI 精读标题色 | `#8C9096`，不是 `#686C72` |
| 7 | AI 精读位置 | 在原文上方，灰色卡片底色 |
| 8 | 右栏内容 | 只包含「深入对话」+ 聊天框，无 AI 精读 |
| 9 | 构建 | `npm run build` 无报错 |

---

*文档版本 v1.1 | 含 AI 精读迁移方案 | 预估 25 min*
