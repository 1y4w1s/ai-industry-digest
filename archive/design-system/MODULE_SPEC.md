# Signal — 模块详细规格书

> 本文档按实施顺序列出每个模块的完整设计规格
> 你确认一个，我实现一个

---

## Step 1 — `utils/date.js`

### 文件路径

`frontend/src/utils/date.js`

### 职责

提供全站公用的日期格式化函数。

### 导出接口

```js
export function getDateLabel(dateStr: string): string
```

### 逻辑

| 相对今天 | 返回 |
|---------|------|
| 0 天前（当天） | `"今天"` |
| 1 天前 | `"昨天"` |
| 2 天前 | `"前天"` |
| 3 天前及以上 | `"06/01 周一"` |

### 代码

```js
export function getDateLabel(dateStr) {
  const d = new Date(dateStr);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(d);
  target.setHours(0, 0, 0, 0);
  const diff = (today - target) / (1000 * 60 * 60 * 24);

  if (diff === 0) return '今天';
  if (diff === 1) return '昨天';
  if (diff === 2) return '前天';

  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  return `${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')} 周${weekdays[d.getDay()]}`;
}
```

### 测试用例

| 输入 | 今天 | 预期输出 |
|------|------|---------|
| `2026-06-04` | 2026-06-04 | `"今天"` |
| `2026-06-03` | 2026-06-04 | `"昨天"` |
| `2026-06-02` | 2026-06-04 | `"前天"` |
| `2026-06-01` | 2026-06-04 | `"06/01 周日"` |

### 改动范围

- **新建:** `frontend/src/utils/date.js`
- **修改:** `frontend/src/pages/Home.jsx` — 替换内联函数为 import

---

## Step 2 — `components/ArticleCard.jsx`

### 文件路径

`frontend/src/components/ArticleCard.jsx`

### 职责

展示单篇文章。支持两种模式：`compact`（列表用）和 `detailed`（搜索用）。

### Props

| 属性 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `article` | `object` | 必填 | `{ id, title, source_name, published_at, _imp, summary?, tags? }` |
| `onSelect` | `(id) => void` | 必填 | 点击触发 |
| `variant` | `'compact' \| 'detailed'` | `'compact'` | 展示模式 |

### 渲染规格

**compact 模式（默认）：**

```
┌─────────────────────────────────────────────┐
│ █ 标题文字（重要性竖线：红/金/灰）            │  ← 14px, #1A1C1E
│   来源 · 日期                                 │  ← 11px, #8C9096
└─────────────────────────────────────────────┘
```

- 内边距：上下 6px，左右 0 → hover 时左右 12px（margin 补偿 -12px）
- hover 背景：`#F6F7F8`
- 重要性竖线：高 `#D4322E` 3px / 中 `#C8960A` 3px / 低 无
- 圆角：4px
- 标题行高：1.4
- CSS class: `.article-item`

**detailed 模式（搜索用）：**

```
┌─────────────────────────────────────────────┐
│ █ 标题文字                                    │  ← 14px, #1A1C1E
│   来源 · 日期                                 │  ← 11px, #8C9096
│   摘要文字 2 行                                 │  ← 12px, #686C72, line-clamp-2
└─────────────────────────────────────────────┘
```

- 与 compact 区别：增加摘要展示（`line-clamp-2`）

### 状态

| 状态 | 背景 | 边框 |
|------|------|------|
| 默认 | 透明 | 无 |
| hover | `#F6F7F8` | 无 |
| 已选阅读 | 不变 | 无 |

### 代码骨架

```jsx
export default function ArticleCard({ article, onSelect, variant = 'compact' }) {
  const impClass = article._imp === 'high' ? 'imp-high' 
    : article._imp === 'medium' ? 'imp-medium' : 'imp-low';

  return (
    <div className="article-item" onClick={() => onSelect(article.id)}>
      <div className={impClass}>
        <span className="text-sm" style={{ color: '#1A1C1E', fontWeight: article._imp === 'high' ? 500 : 400 }}>
          {article.title}
        </span>
        <div className="flex items-center gap-2 mt-0.5" style={{ color: '#8C9096', fontSize: '11px' }}>
          <span>{article.source_name}</span>
          {article.published_at && <span>· {article.published_at.slice(0, 10)}</span>}
        </div>
        {variant === 'detailed' && article.summary && (
          <p className="text-xs mt-1 line-clamp-2" style={{ color: '#686C72' }}>{article.summary}</p>
        )}
      </div>
    </div>
  );
}
```

---

## Step 3 — `components/DateNav.jsx`

### 文件路径

`frontend/src/components/DateNav.jsx`

### 职责

日期导航栏。展示自然语言标签（今天/昨天/前天），默认折叠超过 3 个。

### Props

| 属性 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `reports` | `array` | 必填 | `[{ report_date: '2026-06-03' }, ...]` |
| `selectedDate` | `string` | 必填 | 当前选中日期 |
| `onSelect` | `(date) => void` | 必填 | 点击日期触发 |

### 内部状态

| 状态 | 类型 | 初始值 |
|------|------|--------|
| `expanded` | `boolean` | `false` |

### 渲染规格

```
今天                    昨天                  06/01 周日          展开所有日期 ▾
```

- 每个日期按钮：`padding: 6px 14px`，`font-size: 12px`
- 选中态：`border-bottom: 2px solid #1A1C1E`，颜色 `#1A1C1E`
- 未选中：`border-bottom: 2px solid transparent`，颜色 `#686C72`
- 折叠按钮：`font-size: 11px`，颜色 `#686C72`，无背景
- 默认显示前 3 个，超过 3 个显示「展开所有日期 ▾」
- 展开后显示全部，按钮变为「收起 ▴」
- 日期是「今天」「昨天」「前天」时，右侧小字灰色显示 `MM-DD`

### 边界情况

| 情况 | 行为 |
|------|------|
| 1 期日报 | 只显示一个日期，无折叠按钮 |
| 3 期日报 | 全部展示，无折叠按钮 |
| 5 期日报 | 默认展示 3 个，点击展开显示全部 5 个 |
| 日期跨月 | `06/01 周一` 正常展示 |
| 选择「展开」后点日期 | 保持展开状态 |

---

## Step 4 — `components/FilterBar.jsx`

### 文件路径

`frontend/src/components/FilterBar.jsx`

### 职责

筛选栏：重要性 pill + 来源下拉 + 标签下拉 + 状态提示 + 清除按钮。

### Props

| 属性 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `importance` | `string` | `''` | `'high' \| 'medium' \| 'low' \| ''` |
| `source` | `string` | `''` | 选中的来源 |
| `tag` | `string` | `''` | 选中的标签 |
| `sources` | `string[]` | `[]` | 可选来源列表 |
| `tags` | `string[]` | `[]` | 可选标签列表 |
| `activeFilterCount` | `number` | `0` | 当前激活的筛选数 |
| `onImportanceChange` | `(val) => void` | 必填 | |
| `onSourceChange` | `(val) => void` | 必填 | |
| `onTagChange` | `(val) => void` | 必填 | |
| `onClear` | `() => void` | 必填 | 清除所有筛选 |

### 渲染规格

```
[🔴 高] [🟡 中] [⚪ 低]   [arXiv ▾] [标签 ▾]   2 个筛选中 · 清除
```

- 底色：`#F6F7F8`，全宽，`padding: 6px 16px`
- 重要性 pill：`11px`，选中 `background: #D8DCE0 + color: #1A1C1E`，未选中 `transparent + #686C72`
- 来源/标签下拉：`background: #EDEEF0`，`border: 1px solid #E8EAED`，`11px`
- 下拉文字：选中时 `#1A1C1E`，未选中时 `#8C9096`
- 状态提示和清除：仅在 `activeFilterCount > 0` 时显示

### 筛选触发逻辑

```
用户点击 pill / 改变下拉
  ↓
调用 onImportanceChange / onSourceChange / onTagChange
  ↓
父组件重新计算 filteredArticles（前端过滤）
  ↓
FilterBar 重新接收新的 activeFilterCount
```

---

## Step 5a — `components/DataStats.jsx`

### 文件路径

`frontend/src/components/DataStats.jsx`

### 职责

展示数据统计行。纯文字，无 emoji。

### Props

| 属性 | 类型 | 默认 |
|------|------|------|
| `totalArticles` | `number` | `0` |
| `sourceCount` | `number` | `0` |
| `highCount` | `number` | `0` |

### 渲染规格

```
23 篇文章 · 4 个来源 · 7 篇高重要性
```

- `font-size: 12px`，`color: #686C72`
- `margin-top: 8px`，`padding-top: 8px`，`border-top: 1px solid #E8EAED`
- 使用 `·`（中点）作为分隔符

---

## Step 5b — `components/Pagination.jsx`

### 文件路径

`frontend/src/components/Pagination.jsx`

### 职责

分页组件。显示上下页 + 最多 5 个页码。

### Props

| 属性 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | `number` | `1` | 当前页码 |
| `totalPages` | `number` | `1` | 总页数 |
| `onPageChange` | `(pg) => void` | 必填 | |

### 渲染规格

```
← 1 2 3 4 5 →
```

- 按钮：`padding: 6px 10px`，`font-size: 12px`，圆角 4px
- 默认：`background: #F0F1F2`，`color: #686C72`
- 当前页：`background: #1A1C1E`，`color: #fff`
- 禁用：`opacity: 0.4`
- 页码最多显示 5 个，`page` 居中（如 `1 2 [3] 4 5`）

### 边界情况

| 情况 | 行为 |
|------|------|
| 1 页 | 不渲染 |
| 2 页 | 显示 `← 1 2 →` |
| 6 页，当前第 3 页 | `← 1 2 3 4 5 →` |
| 6 页，当前第 5 页 | `← 2 3 4 5 6 →` |

---

## Step 6a — `components/HeroArticle.jsx`

### 文件路径

`frontend/src/components/HeroArticle.jsx`

### 职责

头条大卡片。展示最高重要性的文章，突出显示。

### Props

| 属性 | 类型 | 默认 |
|------|------|------|
| `article` | `object` | 必填 |
| `onSelect` | `(id) => void` | 必填 |

### 渲染规格

```
┌────────────────────────────────────────────────────┐
│ 头条                                      arXiv · 06/03 │  ← 10px 红色「头条」标签
│                                                        │
│ DeepSeek 发布新一代推理模型，推理效率提升 3 倍         │  ← 18px, 700w, Source Serif 4
│                                                        │
│ DeepSeek 团队今日发布最新推理模型...（摘要 2 行）      │  ← 14px, #2C2E32, line-clamp-2
│                                                        │
│ [标签 1] [标签 2]                                       │  ← 10px, bg #E8EAED
└────────────────────────────────────────────────────────┘
```

- 卡片底色：`#F6F7F8`，圆角 4px
- hover 底色：`#F0F1F2`
- 内边距：`20px 24px`
- 下边距：`20px`

---

## Step 6b — `components/ArticleGroup.jsx`

### 文件路径

`frontend/src/components/ArticleGroup.jsx`

### 职责

来源分组 + 文章列表。

### Props

| 属性 | 类型 | 默认 |
|------|------|------|
| `sourceName` | `string` | 必填 |
| `articles` | `array` | 必填 |
| `onSelectArticle` | `(id) => void` | 必填 |

### 渲染规格

```
arXiv ───────────────────────────────── 20 篇       ← 13px, 600w, #1A1C1E
                                                   ← 分割线 #E8EAED
  █ DeepSeek 发布新一代推理模型      arXiv · 06/03   ← 高重要性：红色竖线
  █ 快手 Taiji 框架部署至广告系统    arXiv · 06/03   ← 中重要性：黄色竖线
  █ 一种新的损失函数优化方法         arXiv · 06/03   ← 低重要性：无竖线
```

- 组标题：`font-size: 13px`，`font-weight: 600`，`color: #1A1C1E`
- 分组线：`border-bottom: 1px solid #E8EAED`
- 组上边距：`24px`
- 文章通过 `<ArticleCard variant="compact" />` 渲染
- 文章按重要性排序：high → medium → low

---

## Step 7 — `components/ReportOverview.jsx`

### 文件路径

`frontend/src/components/ReportOverview.jsx`

### 职责

概览区：今日概览文字 + 关键词标签。

### Props

| 属性 | 类型 | 默认 |
|------|------|------|
| `insight` | `string` | `''` |
| `keywords` | `string[]` | `[]` |

### 渲染规格

```
┌────────────────────────────────────────────────────┐
│ │ 今日AI行业聚焦于效率革命与工业落地并行...         │  ← 14px, border-left: 3px #1A1C1E
│ │                                                   │  ← padding-left: 14px
│   [学术论文] [技术突破] [融资]                      │  ← 12px, bg #E8EAED, #686C72
└────────────────────────────────────────────────────┘
```

- 卡片底色：`#F6F7F8`
- 内边距：`16px`
- 下边距：`20px`
- 关键词标签：`border-radius: 4px`，`padding: 4px 8px`
- 如果 `insight` 为空，不渲染
- 如果 `keywords` 为空，关键词行不渲染

---

## Step 8 — Hooks

### `hooks/useReport.js`

```js
export function useReport() {
  const [reports, setReports] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 加载日报列表（首次 + page 变化时）
  // 加载选中日报详情（selectedDate 变化时）
  // 成功时缓存到 localStorage
  // 失败时从缓存读取

  return { reports, selectedDate, setSelectedDate, report, loading, error };
}
```

### `hooks/useFilter.js`

```js
export function useFilter(articles) {
  const [filters, setFilters] = useState({ importance: '', source: '', tag: '' });

  const filteredArticles = useMemo(() => {
    return articles.filter(a => {
      if (filters.importance && a._imp !== filters.importance) return false;
      if (filters.source && a.source_name !== filters.source) return false;
      if (filters.tag && !(a.tags || []).includes(filters.tag)) return false;
      return true;
    });
  }, [articles, filters]);

  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  const clearFilters = useCallback(() => {
    setFilters({ importance: '', source: '', tag: '' });
  }, []);

  return { filters, setFilters, filteredArticles, activeFilterCount, clearFilters };
}
```

### `hooks/useCache.js`

```js
export function useCache(key, fetcher, ttl = 30 * 60 * 1000) {
  const [data, setData] = useState(null);
  const [fromCache, setFromCache] = useState(false);
  const [age, setAge] = useState(null);

  // 尝试 API 请求
  // 成功 → 更新 localStorage + 返回
  // 失败 → 读取 localStorage
}
```

---

## Step 9 — 重构后的 Home.jsx

### 预期结构

```jsx
export default function Home({ onReadArticle, readerArticle }) {
  const { reports, selectedDate, setSelectedDate, report, loading } = useReport();
  const [sidePanelOpen, setSidePanelOpen] = useState(true);

  // 如果已切换到阅读模式
  if (readerArticle) return <ArticleReader articleId={readerArticle} onBack={() => onReadArticle(null)} />;

  // 构建数据
  const articles = buildArticles(report);
  const groups = groupBySource(articles);
  const { filters, setFilters, filteredArticles, activeFilterCount, clearFilters } = useFilter(articles);
  const highArticles = articles.filter(a => a._imp === 'high');
  const heroArticle = highArticles[0];

  if (loading) return <LoadingState />Token;

  return (
    <PageLayout>
      <FilterBar
        filters={filters} ...
      />
      <MainContent>
        <DateNav reports={reports} selected={selectedDate} onSelect={setSelectedDate} />
        <DataStats total={articles.length} sourceCount={Object.keys(groups).length} highCount={highArticles.length} />
        <ReportOverview insight={report.summary_insight} keywords={report.trending_keywords} />
        <HeroArticle article={heroArticle} onSelect={onReadArticle} />
        {groups.map(g => <ArticleGroup sourceName={g.name} articles={g.articles} onSelectArticle={onReadArticle} />)}
      </MainContent>
      <SidePanel keywords={report?.trending_keywords} insight={report?.summary_insight} topArticles={highArticles} ... />
    </PageLayout>
  );
}
```

**目标行数: ~90 行（当前 330 行）**

---

## 实现顺序

```
Step 1  →  utils/date.js           (5 min)   ← 无依赖
Step 2  →  ArticleCard             (10 min)  ← 无依赖
Step 3  →  DateNav                 (10 min)  ← 依赖 Step 1
Step 4  →  FilterBar               (10 min)  ← 无依赖
Step 5  →  DataStats + Pagination  (10 min)  ← 无依赖
Step 6  →  HeroArticle + ArticleGroup (15 min) ← 依赖 Step 2
Step 7  →  ReportOverview          (5 min)   ← 无依赖
Step 8  →  Hooks (useReport/useFilter/useCache) (15 min)
Step 9  →  重构 Home.jsx          (15 min)  ← 依赖所有以上
Step 10 →  构建验证                (10 min)
─────────────────────────────────────────
总计: ~1.5 小时
```

---

## 约定

1. 每个组件一个文件，文件名为组件名
2. 所有组件默认导出
3. 内联 style 优先（与现有代码一致）
4. 不引入 Tailwind class 之外的样式
5. 每个组件都是纯展示组件（无 useEffect）
6. hooks 放在 `frontend/src/hooks/` 目录
7. 工具函数放在 `frontend/src/utils/` 目录
8. 组件放在 `frontend/src/components/` 目录

---

*文档版本 v1.1 | 按实施顺序排列，每个模块独立可审*
