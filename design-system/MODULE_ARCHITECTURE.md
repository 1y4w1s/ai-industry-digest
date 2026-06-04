# Signal — 模块化架构设计

> 基于当前代码分析，拆解模块边界，规划实现顺序
> 目标：Home.jsx 从 330 行 → 80 行（仅编排层）

---

## 一、为什么需要模块化

### 当前问题

```
Home.jsx (330 行)                      ← 一个文件管所有
├── 数据请求（reports/articles/sources/tags）
├── 搜索逻辑（doSearch/handleClearSearch）
├── 筛选逻辑（handleQuickFilter）
├── 日期导航渲染（60 行内联 JSX）
├── 筛选栏渲染（50 行内联 JSX）
├── 概览区渲染（20 行）
├── 头条卡片渲染（25 行）
├── 文章列表渲染（40 行）
├── 搜索列表渲染（30 行）
├── 分页渲染（20 行）
├── 右侧面板（引用 SidePanel）
└── getDateLabel 工具函数
```

**问题清单：**
1. 一个组件做了 5 件事（数据获取 + 搜索 + 筛选 + 渲染 + 分页）
2. 状态变量 18 个，散落各处
3. JSX 和内联 style 混在一起，无法单独测试
4. 搜索模式和日报模式共用同一套 state，逻辑交织
5. 筛选逻辑走了 API（`/api/articles`），但数据已经在本地了（`report.articles`）

### 理想状态

```
Home.jsx (~80 行)                     ← 只做编排
├── 决定当前模式（日报列表 / 阅读模式）
├── 数据请求（仅需要的数据）
├── 状态提升（selectedDate / filters）
└── 渲染子组件
    ├── <FilterBar />
    ├── <DateNav />
    ├── <DataStats />
    ├── <ReportOverview />
    ├── <HeroArticle />
    ├── <ArticleGroup />
    ├── <SidePanel />
    └── <SearchResults />
```

---

## 二、模块清单

### 2.1 按依赖层次排序

```
Level 0: 工具函数 / 纯展示
  ├── utils/date.js          → getDateLabel()
  └── components/icons/      → SVG 图标组件

Level 1: 原子组件（无业务逻辑，纯 UI）
  ├── components/ArticleCard → 单篇文章展示
  ├── components/DateNav     → 日期导航（自然语言+折叠）
  ├── components/FilterBar   → 筛选栏（重要性+来源+标签）
  ├── components/DataStats   → 数据统计行
  ├── components/Pagination  → 分页组件

Level 2: 组合组件（有业务逻辑，组合原子组件）
  ├── components/HeroArticle → 头条卡片（带数据）
  ├── components/ArticleGroup→ 来源分组 + 文章列表
  ├── components/ReportOverview → 概览区
  ├── components/SearchResults  → 搜索列表 + 分页

Level 3: 页面组件（编排层）
  ├── pages/Home             → 日报首页
  ├── pages/SearchPage       → 搜索结果页 (future)
  └── components/ArticleReader → 阅读模式 (已有)

Level 4: 全局框架
  ├── components/Layout      → 侧边栏 + Header
  ├── components/AIChatBubble → AI 对话 (已有)
  └── components/SidePanel   → 右侧面板 (已有)
```

### 2.2 完整模块表

| ID | 模块 | 类型 | 职责 | 现有代码量 | 拆后代码量 | 依赖 |
|----|------|------|------|-----------|-----------|------|
| D01 | `utils/date.js` | 工具函数 | `getDateLabel()` 自然语言日期转换 | 散落在 Home | 15 行 | 无 |
| D02 | `utils/cache.js` | 工具函数 | localStorage 读写 + 过期判断 | 不存在 | 20 行 | 无 |
| C01 | `ArticleCard` | 原子组件 | 单篇文章展示（标题+来源+日期+重要性竖线） | 重复 3 处 | 30 行 | 无 |
| C02 | `DateNav` | 原子组件 | 日期导航栏（自然语言标签 + 展开/收起） | 50 行内联 | 40 行 | D01 |
| C03 | `FilterBar` | 原子组件 | 筛选栏（重要性 pill + 来源/标签下拉） | 40 行内联 | 45 行 | 无 |
| C04 | `DataStats` | 原子组件 | "N 篇文章 · N 个来源 · N 篇高重要性" | 10 行内联 | 15 行 | 无 |
| C05 | `Pagination` | 原子组件 | 分页按钮（上下页 + 页码） | 20 行内联 | 30 行 | 无 |
| C06 | `HeroArticle` | 组合组件 | 头条卡片（标题+摘要+标签+来源+日期） | 25 行内联 | 30 行 | C01 |
| C07 | `ArticleGroup` | 组合组件 | 来源分组标题 + 文章列表 | 40 行内联 | 35 行 | C01 |
| C08 | `ReportOverview` | 组合组件 | 概览 + 关键词标签 | 20 行内联 | 25 行 | 无 |
| C09 | `SearchResults` | 组合组件 | 搜索结果列表 + 分页 + 返回按钮 | 50 行内联 | 45 行 | C01, C05 |
| P01 | `Home` | 页面组件 | 编排层：数据请求 + 模式切换 + 子组件组合 | 330 行 | **~80 行** | C02-C09 |
| — | `Layout` | 全局 | (已有) 不需改动 | — | — | — |
| — | `SidePanel` | 全局 | (已有) 不需改动 | — | — | — |
| — | `ArticleReader` | 全局 | (已有) 不需改动 | — | — | — |
| — | `AIChatBubble` | 全局 | (已有) 不需改动 | — | — | — |

---

## 三、组件接口设计

### C01 — ArticleCard

```jsx
<ArticleCard
  article={{ id, title, source_name, published_at, _imp, summary, tags }}
  onSelect={(id) => void}        // 点击文章
  variant="compact"|"detailed"   // compact: 列表模式, detailed: 搜索模式
/>
```

### C02 — DateNav

```jsx
<DateNav
  reports={[ {report_date: '2026-06-03'}, ... ]}
  selectedDate="2026-06-03"
  onSelect={(date) => void}
/>
// 内部管理 expanded 状态
```

### C03 — FilterBar

```jsx
<FilterBar
  importance="high"|"medium"|"low"|""
  source=""|string
  tag=""|string
  sources={["arXiv", ...]}
  tags={["学术", ...]}
  activeFilterCount={0|1|2|3}
  isFilterActive={boolean}
  onImportanceChange={(val) => void}
  onSourceChange={(val) => void}
  onTagChange={(val) => void}
  onClear={() => void}
/>
```

### C04 — DataStats

```jsx
<DataStats
  totalArticles={23}
  sourceCount={4}
  highCount={7}
/>
```

### C05 — Pagination

```jsx
<Pagination
  page={1}
  totalPages={5}
  onPageChange={(pg) => void}
/>
```

### C06 — HeroArticle

```jsx
<HeroArticle
  article={article}
  onSelect={(id) => void}
/>
```

### C07 — ArticleGroup

```jsx
<ArticleGroup
  sourceName="arXiv"
  articles={[ ... ]}
  onSelectArticle={(id) => void}
/>
```

### C08 — ReportOverview

```jsx
<ReportOverview
  insight="今日AI行业聚焦于..."
  keywords={["学术", "融资", ...]}
/>
```

### C09 — SearchResults

```jsx
<SearchResults
  results={{ items: [...], total: 30, pages: 3 }}
  page={1}
  onPageChange={(pg) => void}
  onSelectArticle={(id) => void}
  onClear={() => void}
/>
```

---

## 四、数据流

### 4.1 当前（混乱）

```
App
 ├─ readerArticle (state) → 传给 Layout → isReading
 │                          传给 Home → 判断是否显示 ArticleReader
 │
 Home
  ├─ reports / report (state)         ← 两个 fetch
  ├─ searching / searchResults (state) ← 另一个 fetch
  ├─ importance / source / tag (state) ← 筛选
  ├─ page / total (state)              ← 分页
  ├─ sidePanelOpen / dateExpanded      ← UI 状态
  └─ sources / tags (state)            ← 元数据
```

### 4.2 目标

```
App
 └─ readerArticle (state)
      │
      └─ Home (orchestrator)
           │
           ├─ useReportData()     ← 自定义 hook: fetch reports + report detail
           │    ├─ reports, report, loading
           │    └─ selectedDate, setSelectedDate
           │
           ├─ useFilter()         ← 自定义 hook: 前端过滤逻辑
           │    ├─ filters (重要性/来源/标签)
           │    ├─ filteredArticles
           │    └─ setFilter, clearFilters
           │
           ├─ <DateNav />         ← 纯展示
           ├─ <FilterBar />       ← 纯展示
           ├─ <DataStats />       ← 纯展示
           ├─ <ReportOverview />  ← 纯展示
           ├─ <HeroArticle />     ← 纯展示
           ├─ <ArticleGroup />    ← 纯展示
           └─ <SidePanel />       ← 纯展示
```

关键变化：
- **筛选改为前端过滤**（filter `report.articles`），不再调 API
- **搜索和首页分离**（搜索走独立页面，不走 Home）
- **自定义 hooks** 抽离数据获取逻辑
- **所有子组件都是纯展示**（无 useEffect，无数据请求）

### 4.3 自定义 Hooks

```js
// hooks/useReport.js
function useReport() {
  const [reports, setReports] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  // 加载日报列表
  // 加载选中日期详情
  // 缓存逻辑
  return { reports, selectedDate, setSelectedDate, report, loading };
}

// hooks/useFilter.js
function useFilter(articles) {
  const [filters, setFilters] = useState({ importance: '', source: '', tag: '' });

  const filteredArticles = useMemo(() => {
    return articles.filter(a => {
      if (filters.importance && a._imp !== filters.importance) return false;
      if (filters.source && a.source_name !== filters.source) return false;
      if (filters.tag && !(a.tags || []).includes(filters.tag)) return false;
      return true;
    });
  }, [articles, filters]);

  const activeCount = Object.values(filters).filter(Boolean).length;
  const clearFilters = () => setFilters({ importance: '', source: '', tag: '' });

  return { filters, setFilters, filteredArticles, activeCount, clearFilters };
}

// hooks/useCache.js
function useCache(key, fetcher, ttl = 30 * 60 * 1000) {
  // API 请求 + localStorage 缓存
  // 失败时返回缓存数据
}
```

---

## 五、重构后的 Home.jsx（预期效果）

```jsx
// pages/Home.jsx — ~80 行
export default function Home({ onReadArticle, readerArticle }) {
  const { reports, selectedDate, setSelectedDate, report, loading } = useReport();
  const { filters, setFilters, filteredArticles, activeCount, clearFilters } = useFilter(articles);

  if (readerArticle) return <ArticleReader ... />;
  if (loading) return <Loading />;

  const groups = groupBySource(filteredArticles);

  return (
    <Page>
      <FilterBar
        filters={filters}
        onFilterChange={setFilters}
        activeCount={activeCount}
        onClear={clearFilters}
      />
      <MainContent>
        <DateNav reports={reports} selected={selectedDate} onSelect={setSelectedDate} />
        <DataStats total={...} sources={...} high={...} />
        <ReportOverview insight={report.insight} keywords={report.keywords} />
        <HeroArticle article={heroArticle} onSelect={onReadArticle} />
        {groups.map(g => <ArticleGroup key={g.name} {...g} onSelect={onReadArticle} />)}
      </MainContent>
      <SidePanel keywords={...} insight={...} topArticles={topArticles} ... />
    </Page>
  );
}
```

相比当前 330 行：
- 逻辑拆分到 3 个 hooks
- UI 拆分到 7 个子组件
- 编排层只剩 ~80 行

---

## 六、实现顺序

依赖关系：基础组件 → 组合组件 → 页面重构

| 步骤 | 内容 | 文件数 | 预估 |
|------|------|--------|------|
| **Step 1** | 创建 `utils/date.js` — 迁移 `getDateLabel()` | 新建 1 | 5min |
| **Step 2** | 创建 `ArticleCard` — 从 Home 中提取单篇文章渲染 | 新建 1 | 10min |
| **Step 3** | 创建 `DateNav` — 日期导航（自然语言 + 折叠） | 新建 1 | 10min |
| **Step 4** | 创建 `FilterBar` — 筛选栏 | 新建 1 | 10min |
| **Step 5** | 创建 `Pagination` + `DataStats` — 分页 + 统计 | 新建 2 | 10min |
| **Step 6** | 创建 `HeroArticle` + `ArticleGroup` — 组合组件 | 新建 2 | 15min |
| **Step 7** | 创建 `ReportOverview` — 概览区 | 新建 1 | 5min |
| **Step 8** | 创建 `hooks/useReport.js` + `hooks/useFilter.js` | 新建 2 | 15min |
| **Step 9** | 重构 `Home.jsx` — 使用所有子组件 + hooks | 修改 1 | 15min |
| **Step 10** | 清理旧代码 + 构建验证 | 修改 2 | 10min |

**合计：约 1.5 小时**（每步可独立验证，风险低）

### 为什么不一步到位

每个子组件都是**从 Home.jsx 中复制现有代码 → 包装成独立文件**，不引入新功能，不改样式。步骤之间互不影响，可随时中断。

---

## 七、不做的事情

| 不做 | 原因 |
|------|------|
| 不引入新 UI 框架 | Tailwind v4 足够 |
| 不改现有视觉风格 | 只拆代码，不改颜色/间距/字体 |
| 不引入状态管理库 | React hooks 足够 |
| 不做服务端组件 | 纯前端 SPA |
| 不改 API 接口 | 后端不动 |

---

*文档版本 v1.0 | 基于当前代码（2026-06-04）分析*
