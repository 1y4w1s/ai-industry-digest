# Signal — AI 个性化与安全增强架构设计

> 版本: v1.0  
> 创建日期: 2026-06-06  
> 状态: 待实施  
> 来源: grill-me 决策记录（2026-06-06）

---

## 一、架构总览

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户浏览器（前端）                             │
│  ┌──────────┐  ┌───────────────┐  ┌────────────┐  ┌─────────────┐ │
│  │AIChatBub │  │ ArticleReader │  │KnowledgeBae│  │ Recommend-  │ │
│  │ ble      │  │ + 滚动追踪      │  │ Page       │  │ ationWidget │ │
│  └────┬─────┘  └───────┬───────┘  └─────┬──────┘  └──────┬──────┘ │
│       │                │                │                │         │
│       └────────────────┼────────────────┼────────────────┘         │
│                        │                │                          │
│                   ┌────▼────────────────▼────┐                     │
│                   │     API Client (client.js) │                     │
│                   └────┬───────────────────────┘                     │
│                        │ HTTPS                                      │
└────────────────────────┼────────────────────────────────────────────┘
                         │
┌────────────────────────┼────────────────────────────────────────────┐
│              FastAPI 后端 (api/)                                    │
│                        │                                            │
│  ┌─────────────────────┴─────────────────────────────────────┐     │
│  │                     API 路由层                              │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │     │
│  │  │ /api/chat │ │ /api/auth │ │ /api/kb  │ │/api/recommend│ │     │
│  │  │ 对话+画像  │ │ 历史+画像  │ │ 知识库    │ │ 推荐接口(新) │ │     │
│  │  └─────┬────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘ │     │
│  └────────┼───────────┼────────────┼──────────────┼─────────┘     │
│           │           │            │              │               │
│  ┌────────▼───────────▼────────────▼──────────────▼─────────┐     │
│  │               DatabaseManager (database.py)               │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │     │
│  │  │ articles │ │ user_*   │ │ kb_*     │ │ user_tags(新)│ │     │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │     │
│  └────────────────────────────────────────────────────────────┘     │
│           │                                                        │
│  ┌────────▼──────────────────────────────────────────────────┐     │
│  │            AI 服务层                                        │     │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐   │     │
│  │  │ DeepSeek Chat    │  │ Tag Extractor（新增,零成本）   │   │     │
│  │  │ (对话 + 推荐)     │  │ ← 仅匹配已有标签，不调 API    │   │     │
│  │  └──────────────────┘  └──────────────────────────────┘   │     │
│  └────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、数据流

### 2.1 阅读深度追踪数据流

```
用户打开文章
    │
    ▼
ArticleReader 组件挂载
    │
    ├── 启动 IntersectionObserver 追踪"可见内容的百分比"
    │   （基于文档总高度 vs 用户已滚动到的位置）
    │
    ├── 用户阅读过程中，滚动位置变化 → 记录当前 read_percent
    │
    ├── 用户离开阅读器（unmount/返回）
    │   │
    │   ├── read_percent < 15% → 丢弃，不上报（视为误触）
    │   │
    │   └── read_percent >= 15% → POST /auth/history
    │           { article_id, read_percent, duration_sec }
    │
    ▼
后端 add_reading_history()
    │
    ├── 同天同篇已存在？
    │   ├── 是 → 取 max(现有 read_percent, 新 read_percent) UPSERT
    │   └── 否 → INSERT
    │
    ▼
reading_history 表
    (新增 read_percent FLOAT 列)
```

**关键阈值：** 可见区域滚动比例 >= 15% 才算有效阅读

### 2.2 用户画像（标签提取）数据流

```
用户发送聊天消息
    │
    ▼
POST /api/chat { message: "GPT-5 和 Claude 4 哪个更强？" }
    │
    ├── (主线) 正常调用 DeepSeek → 回复 → 返回给用户
    │
    └── (支线·异步，不阻塞回复)
        │
        ▼
        TagExtractor.extract(message)
            │
            ├── 将消息分词、去停用词
            ├── 与 articles 表中所有已有标签做模糊匹配
            │   (如 "GPT" 匹配到已有标签 "GPT", "GPT-4o" 等)
            │
            ├── 匹配到了？
            │   ├── 是 → UPSERT user_tags(user_id, tag, weight+1)
            │   └── 否 → 丢弃，不写入
            │
            ▼
        user_tags 表
            (user_id, tag, weight, source='chat', updated_at)
```

**设计原则：**
- 零额外 API 成本（不调用 DeepSeek 做提取）
- 标签天然对齐 `articles.tags`，推荐时可直接 JOIN
- 异步执行，不增加对话响应延迟

### 2.3 标签权重聚合来源

```
用户画像（user_tags）权重来源分布：

┌──────────────────────────────────────────────────┐
│  来源              权重    采集方式              │
├──────────────────────────────────────────────────┤
│  AI 对话提示词      20%    实时提取匹配          │
│  阅读历史标签       40%    JOIN reading_history  │
│                             → articles.tags      │
│  收藏标签           30%    JOIN bookmarks         │
│                             → articles.tags      │
│  阅读深度 >15%      10%    加权系数              │
│                             (低于15%不计入)       │
│  文章反馈 👎         -     排除对应的标签        │
└──────────────────────────────────────────────────┘
```

### 2.4 个性化推荐数据流

```
用户打开首页 / 刷新
    │
    ▼
GET /api/recommend?user_id=xxx&limit=5
    │
    ▼
后端 recommend()
    │
    ├── 1. 读取 user_tags 获取用户标签权重向量
    │       { "LLM": 15, "多模态": 8, "RAG": 5, ... }
    │
    ├── 2. 获取今日日报文章列表（候选池）
    │       + 历史高赞文章（hot pool）
    │
    ├── 3. 对每篇文章计算匹配度得分：
    │       score = Σ(tag_weight × article_importance_weight)
    │       其中 tag_weight 来自用户画像
    │           article_importance_weight = {high:3, medium:2, low:1}
    │
    ├── 4. 多样性调节：
    │       如果 top-5 标签过于集中（如全是 "LLM"），
    │       从次优标签中插入 1 篇
    │
    └── 5. 返回排序后的文章列表
    │
    ▼
前端渲染 → 首页"为你推荐"区域
```

### 2.5 AI 对话 + 安全隔离数据流

```
用户右下角气泡提问
    │
    ▼
POST /api/chat { message, session_id }
    │
    ▼
chat.py 构建 system prompt
    │
    ├── ✅ 今日日报上下文（保持不变）
    │
    ├── ❌ 不再注入知识库文档内容（安全隔离）
    │
    ├── ❌ 不再注入用户个人信息（隐私保护）
    │
    ├── ✅ 新的：异步提取关键词写 user_tags（非阻塞）
    │
    └── 调用 DeepSeek → 返回纯文本回复
    │
    ▼
前端收到回复
    │
    ├── 1. DOMPurify.sanitize(reply)  ← 新增安全层
    │
    ├── 2. renderMd()  ← 渲染 markdown
    │
    └── 3. 渲染到气泡中显示
```

### 2.6 操作执行（白名单指令）数据流

```
AI 回复文本中嵌入 Markdown 链接
    │
    ▼
示例：AI 回复
    "我找到了相关文章，[点击查看搜索结果](/search?q=GPT-5)"
    "需要我[取消收藏这篇](/unbookmark?article_id=xxx)吗？"
    │
    ▼
前端渲染
    ├── 显示为可点击的普通链接
    ├── 用户自己决定是否点击
    └── 不需要前端解析 action 指令（最简方案）
    │
    ▼
用户点击链接
    ├── /search?q=...   → 前端路由跳转（无安全风险）
    └── /unbookmark?xx  → POST API 执行取消收藏（需登录态）
```

**操作白名单（当前阶段）：**

| 操作 | URL 格式 | 安全级别 | 是否需要确认 |
|------|---------|---------|------------|
| 导航到搜索 | `/search?q=xxx` | 🟢 安全 | 否 |
| 导航到文章 | `/?article=xxx` | 🟢 安全 | 否 |
| 导航到归档 | `/archive` | 🟢 安全 | 否 |
| 取消收藏 | 链接引导用户手动点，不自动执行 | 🟡 安全 | 用户点击才触发 |

**当前阶段不执行：** `bookmark`（收藏）、`clear_history`（清历史）、`delete`（删除）

---

## 三、安全架构（分层防御）

```
┌──────────────────────────────────────────────────────────────┐
│  L5 - AI 层: 指令白名单                                      │
│  ├── 回复中仅含 Markdown 链接格式                            │
│  ├── 无隐藏 JSON action 指令                                │
│  ├── 无自动执行的 function call                              │
│  └── 知识库内容不注入全局 chat system prompt                  │
├──────────────────────────────────────────────────────────────┤
│  L4 - 输出层: DOMPurify sanitize (新增)                     │
│  ├── AI 回复渲染前必过 DOMPurify.sanitize()                 │
│  ├── 覆盖文件:                                              │
│  │   ├── AIChatBubble.jsx  L207                             │
│  │   ├── AIRecommendPanel.jsx L116                          │
│  │   └── ArticleReader.jsx L319                             │
│  └── 保留文章内容渲染（受控的 raw_content）                 │
├──────────────────────────────────────────────────────────────┤
│  L3 - 存储层: Supabase RLS                                  │
│  ├── kb_documents.user_id = auth.uid()                      │
│  ├── reading_history.user_id = auth.uid()                    │
│  └── bookmarks.user_id = auth.uid()                          │
├──────────────────────────────────────────────────────────────┤
│  L2 - 内容层: 知识库隔离 (新增)                             │
│  ├── 全局 AI 助手看不到知识库内容                           │
│  ├── 知识库对话仅在 /knowledge 页面独立上下文进行            │
│  └── 防 prompt injection 扩散                               │
├──────────────────────────────────────────────────────────────┤
│  L1 - 输入层: 文件校验 (已有)                               │
│  ├── 文件格式白名单: .txt .md .pdf .docx                    │
│  └── 大小限制: 10MB                                         │
└──────────────────────────────────────────────────────────────┘
```

---

## 四、数据库变更

### 4.1 新增表: user_tags

```sql
-- 用户标签画像表
-- 记录用户的兴趣标签及其权重
CREATE TABLE IF NOT EXISTS user_tags (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tag VARCHAR(50) NOT NULL,           -- 标签名，对齐 articles.tags
    weight INTEGER DEFAULT 1,           -- 累计权重（出现次数）
    source VARCHAR(20) DEFAULT 'chat',  -- 来源: 'chat' | 'reading' | 'bookmark'
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, tag, source)
);

CREATE INDEX IF NOT EXISTS idx_user_tags_user ON user_tags(user_id);
```

### 4.2 修改表: reading_history

```sql
-- 新增阅读深度列
ALTER TABLE reading_history 
ADD COLUMN IF NOT EXISTS read_percent FLOAT DEFAULT NULL;

ALTER TABLE reading_history 
ADD COLUMN IF NOT EXISTS duration_sec INT DEFAULT NULL;
```

### 4.3 不新建 chat_logs 表

**决策：** 不建 `chat_logs` 表。用户的提示词内容仅用于实时提取标签，不持久化存储。理由：
- 节省数据库空间
- 减轻隐私合规负担
- 提取出的标签已足够形成画像

---

## 五、前端组件变更

### 5.1 ArticleReader.jsx — 新增滚动追踪

```
┌──────────────────────────────────────┐
│  ← 返回  文章标题             收藏 📑 │
├──────────────────────────────────────┤
│  AI 精读                             │
│  ┌────────────────────────────────┐ │
│  │ 摘要内容...                    │ │
│  └────────────────────────────────┘ │
│                                      │
│  文章正文区域                          │
│  ┌────────────────────────────────┐ │
│  │                                │ │
│  │  ← 用户滚动这里 →              │ │
│  │                                │ │
│  │                                │ │
│  │                                │ │
│  │                                │ │
│  │  ═══════════════════════       │ │
│  │  当前可见区域（viewport）       │ │
│  │  ═══════════════════════       │ │
│  │                                │ │
│  │                                │ │
│  │                                │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌──────────── 右侧对话面板 ───────┐ │
│  │  深入对话                       │ │
│  │  ┌──────────────────────────┐  │ │
│  │  │ 用户: 总结一下            │  │ │
│  │  │ AI: 这篇文章主要...      │  │ │
│  │  └──────────────────────────┘  │ │
│  │  [输入...] [发送]              │ │
│  └──────────────────────────────┘ │
└──────────────────────────────────────┘
```

**新增逻辑：**
- `useEffect` 监听 `scroll` 事件（带 200ms 节流）
- 计算 `readPercent = scrollTop / (scrollHeight - clientHeight) * 100`
- 组件 unmount 时，如果 `readPercent >= 15`，上报
- 如果用户通过对话面板提问，顺便上报当前阅读进度

### 5.2 AIChatBubble.jsx — 新增安全层

**变更：**
- 引入 `DOMPurify`
- `renderMd(msg.content)` → `renderMd(DOMPurify.sanitize(msg.content))`
- 其他逻辑不变

### 5.3 新增推荐区域 — RecommendationWidget

```
在首页日报列表上方新增：

┌──────────────────────────────────────────┐
│  🔥 为你推荐                        [×] │
├──────────────────────────────────────────┤
│  ┌──────────────────────────────────────┐│
│  │ [高] 文章标题 1  ← 基于你的阅读偏好  ││
│  │    摘要...                           ││
│  ├──────────────────────────────────────┤│
│  │ [高] 文章标题 2                      ││
│  │    摘要...                           ││
│  ├──────────────────────────────────────┤│
│  │ [中] 文章标题 3                      ││
│  │    摘要...                           ││
│  └──────────────────────────────────────┘│
│  基于你的阅读记录和收藏推荐              │
└──────────────────────────────────────────┘
```

**交互：**
- 仅登录用户可见
- 首次加载时调用 `GET /api/recommend`
- 可关闭（localStorage 记住"已关闭"状态）
- 每天刷新一次（推荐池随日报更新）

---

## 六、API 变更

### 6.1 新增: GET /api/recommend

```json
// Request
GET /api/recommend?limit=5

// Response
{
  "items": [
    {
      "id": "uuid",
      "title": "文章标题",
      "summary": "摘要...",
      "tags": ["LLM", "GPT"],
      "importance": "high",
      "source_name": "量子位",
      "score": 18.5,
      "reason": "基于你对 LLM 和 Agent 话题的关注"
    }
  ],
  "strategy": "tag_weighted"
}
```

### 6.2 修改: POST /api/chat

```json
// Request（不变）
{
  "message": "GPT-5 和 Claude 4 哪个更强？",
  "article_id": null,
  "session_id": "xxx"
}

// Response（不变）
{
  "reply": "根据最新的文章...",
  "session_id": "xxx"
}

// 新增副作用（调用端无感知）：
// → 异步提取关键词 → UPSERT user_tags
```

### 6.3 修改: POST /api/auth/history

```json
// Request（新增字段）
{
  "article_id": "uuid",
  "read_percent": 72.5,
  "duration_sec": 340
}

// Response
{
  "success": true
}
```

---

## 七、实施路线（4 步）

### 第 1 步：安全底裤

| 任务 | 文件 | 工时 |
|------|------|------|
| 1.1 `npm install dompurify` | 前端依赖 | 5min |
| 1.2 3 处加 DOMPurify sanitize | `AIChatBubble.jsx`, `AIRecommendPanel.jsx`, `ArticleReader.jsx` | 1h |
| 1.3 知识库隔离 — 修改 system prompt 逻辑 | `chat.py` | 1h |

### 第 2 步：用户画像基础

| 任务 | 文件 | 工时 |
|------|------|------|
| 2.1 在 Supabase 执行建表 SQL | `init_schema.sql` 追加 | 10min |
| 2.2 在 database.py 新增 `upsert_user_tag()` 方法 | `database.py` | 1h |
| 2.3 在 chat.py 回复后异步调用 TagExtractor | `chat.py` + 新文件 `tag_extractor.py` | 2h |

### 第 3 步：阅读深度追踪

| 任务 | 文件 | 工时 |
|------|------|------|
| 3.1 前端 ArticleReader 加滚动追踪逻辑 | `ArticleReader.jsx` | 3h |
| 3.2 后端 HistoryRequest 加 `read_percent`, `duration_sec` | `auth.py` | 1h |
| 3.3 database.py 加 UPSERT 逻辑（取 max） | `database.py` | 1h |

### 第 4 步：推荐 + 操作执行

| 任务 | 文件 | 工时 |
|------|------|------|
| 4.1 推荐接口 `GET /api/recommend` | 新文件 `routes/recommend.py` | 3h |
| 4.2 前端推荐组件 `RecommendationWidget` | 新文件 + `Home.jsx` | 2h |
| 4.3 AI Markdown 链接跳转（已天然支持，几乎零改动） | — | 0h |

---

## 八、技术债务约束

| 约束 | 规则 |
|------|------|
| 文件大小警戒线 | 任何源文件超过 800 行 → 自动拆分为多个模块 |
| 代码审查 | 每步实施完成后，AI 自动 review → 人工判断是否修改 |
| 架构文档更新 | 本次文档在实施过程中同步更新 |

---

> 本设计文档由 2026-06-06 grill-me 讨论产出
> 所有决策已与项目负责人确认
> 下一步：开始第 1 步实施 — 安全底裤
