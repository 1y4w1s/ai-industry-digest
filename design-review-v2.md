# 捞乾 · 全站布局重设计审查报告 V2（代码级审查）

> 由于无法获取实时截图（Chrome MCP session 卡死），本次审查基于代码逐行分析。

---

## 一、对比度与可访问性（A11y）

### 1. 金色 `#C8922A` 在白底上的对比度
- **WCAG AA 要求**：正常文本 ≥ 4.5:1，大文本 ≥ 3:1
- `#C8922A`（金）在 `#FFFFFF`（侧栏白底）上：约 2.8:1 ❌
- `#C8922A`（金）在 `#F8F0DC`（brass-bg）上：约 3.2:1 ❌
- **问题范围**：导航 active 文字、徽章文字、金色指示条
- **修复**：active 文字改用 `#A67B1E`（深金），徽章 bg 加深

### 2. 琥珀色 `#D46520` 在仿古纸 `#F5F0E8` 上
- 约 3.5:1，接近达标但略低
- 但琥珀只用于点缀（coral/CTA），非核心文字，可接受

---

## 二、文章列表区

### 3. 每篇文章底部分割线过密（ArticleCard:56）
- 每个卡片 `borderBottom: '1px solid var(--color-border-light)'`
- 假设一个 source 有 5 篇文章 → 5 条分割线 → "斑马线"视觉效果
- **建议**：分割线颜色改为更淡（`opacity: 0.5` 或 `var(--color-border-light)` 混合），或只在每组之间添加

### 4. Hover 效果使用 opacity（ArticleCard:64-65）
- `opacity: 0.75` 会让文字颜色整体变淡，包括黑色标题→变灰
- 更好的 hover：`translateX(4px)` 或 `background` 变化，而非透明度
- **建议**：改为 `background: 'var(--color-bg-hover)'` 或 `paddingLeft` 微移

### 5. 重要性圆点对齐（ArticleCard:56-67）
- 圆点 `marginTop: 8`、`flexShrink: 0`，与 14px 文字首行对齐
- 如果文章标题换行到第二行，圆点保持在第一行中间，视觉上脱节
- **建议**：使用 `alignSelf: 'flex-start'` + `marginTop: 6` 精确控制

---

## 三、信息架构

### 6. DailyBriefing vs MainThreadPanel 功能重复
- 两者都用了 `api.getMainThread(date)` 同一份数据
- DailyBriefing 显示故事详情，MainThreadPanel 只显示标题标签
- 用户看到两个"今日"区块，可能困惑为什么内容不同
- **建议**：MainThreadPanel 前面加一个更轻的前缀（如金色小圆点而非"今日主线"标题）

### 7. "全部信号" 与 "今日速览" 的主次关系
- 现在视觉上：今日速览(18px + 标签行) vs 全部信号(14px + 金色线)
- 差距缩小了，但"全部信号"后面紧跟的 `共 N 篇` 计数器反而强化了"归档"感
- **建议**：去掉 `共 N 篇` 或改为更轻的展示

---

## 四、布局完整性

### 8. 移除版本号后顶部多余的 `mt-2`
- 版本号移除前：`py-2 mt-2` 在 `border-t` 下方留出空间
- 移除后：`RecentItems` 直接从 `border-t` 开始，没有顶部边距
- **修复**：给 `RecentItems` 加 `paddingTop: 12` 或在外层 div 保留 `pt-2`

### 9. 移动端侧栏与底部导航冲突
- 侧栏 `z-index: 50`，底部导航 `z-index: 50`
- 当侧栏打开时，底部导航会显示在侧栏之上
- **修复**：侧栏打开时隐藏底部导航，或侧栏 z-index 提升至 60

### 10. 平板端 768-1024px 的适配
- 内容区 `max-width: 800px`，在 800px 以下视口 = 0 padding
- 侧栏在 lg 断点（1024px）以上才显示，800-1024px 之间内容区无侧栏但 padding 可能不足
- **建议**：添加 `@media (max-width: 860px)` 减少 padding

### 11. SkeletonCard 动画依赖
- `animation: pulse 1.5s ease-in-out infinite` 依赖 `@keyframes pulse`
- 已在 index.css 中定义 ✅
- 但 SkeletonCard 组件没有检查 CSS 是否加载，如果 CSS 加载失败骨架屏会静止

---

## 五、移动端细节

### 12. MobileNav safe-area-inset-bottom
- 使用了 `paddingBottom: 'env(safe-area-inset-bottom, 0)'` ✅
- 但没有 `paddingBottom: 'constant(safe-area-inset-bottom, 0)'` 用于旧 iOS
- **建议**：添加 `constant()` 回退

### 13. 登录按钮 padding 统一
- 未登录状态按钮 `py-2.5`，登录状态也 `py-2.5` ✅
- 头像 w-8 h-8 ✅
- 退出登录按钮仍用 `padding: 4` — 触控点太小
- **建议**：退出按钮提升到 `padding: 8`

---

## 总结

| 类别 | 通过 | 需改进 |
|------|------|--------|
| A11y 对比度 | 0 | 2 🔴 |
| 文章列表 | 0 | 3 🟡 |
| 信息架构 | 0 | 2 🟡 |
| 布局完整性 | 1 | 3 🟡 |
| 移动端 | 1 | 2 🟢 |

**新增发现（未在第一版报告中）**：
1. 侧栏移除版本号后顶部间距丢失
2. 侧栏 z-index 与底部导航冲突
3. 平板端 800-1024px padding 不足
4. 退出登录按钮触控点太小
