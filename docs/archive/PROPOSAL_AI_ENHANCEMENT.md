# Signal — AI 功能深度拓展提案

> **版本**: v4.0  
> **创建日期**: 2026-06-06  
> **状态**: 待评审  
> **作者**: AI 助手

---

## 一、项目背景

### 1.1 当前状态
Signal 平台已具备基础 AI 对话能力，支持：
- 文章级对话（基于文章内容提问）
- 全局对话（注入今日日报上下文）
- 对话历史保持

### 1.2 新增需求
用户希望增加以下功能：

| 功能模块 | 描述 | 优先级 |
|---------|------|--------|
| **知识库管理** | 用户可上传文档、切片、标签化、生成知识图谱 | 🔴 核心 |
| **语义搜索** | 全文内容搜索，响应时间 < 3秒 | 🔴 核心 |
| **自然语言操作** | 支持内容操作、筛选操作、导航操作 | 🟡 重要 |
| **个性化推荐** | 基于阅读偏好推荐文章 | 🟡 重要 |
| **多模态理解** | 图片内容分析 | 🟢 加分 |

### 1.3 成本约束
- 预算：0元（使用免费方案），备用预算100元
- 服务器：无GPU
- 用户量：少量用户

---

## 二、技术选型

### 2.1 最终技术栈

| 功能 | 技术方案 | 成本 | 依赖 |
|------|---------|------|------|
| **知识库** | 用户上传 + 切片 + 向量化 + 实体识别 + 知识图谱 | 0元 | DeepSeek, React Flow |
| 语义搜索 | pgvector (Supabase内置) + DeepSeek API | 0元 | DeepSeek |
| 自然语言操作 | 意图识别 + 动态上下文 | 0元 | DeepSeek |
| 个性化推荐 | 简单加权算法 + 用户画像 | 0元 | 无 |
| 多模态理解 | 阿里百炼 Qwen-VL API | 0元（免费额度） | 阿里云 |
| 代码理解 | DeepSeek API | 0元 | DeepSeek |
| 图谱可视化 | React Flow | 0元 | npm包 |

### 2.2 核心技术说明

#### React Flow（知识图谱可视化）
- **优点**：React 原生、性能好、交互丰富
- **替代方案**：D3.js（太复杂）、Cytoscape.js（老牌但集成不便）
- **版本**：v11+

#### Supabase pgvector（向量存储）
- **优点**：已有基础设施，无需额外部署
- **启用方式**：`CREATE EXTENSION vector`

#### Groq API（多模态）
- **免费额度**：充足，适合少量用户
- **注册地址**：https://console.groq.com/

---

## 三、知识库模块（核心功能）

### 3.1 功能概述

用户可上传个人文档（PDF、TXT、MD、DOCX），系统自动：
1. 解析文档内容
2. 切片处理（按段落/句子）
3. 向量化存储
4. 实体识别 + 关系抽取
5. 生成知识图谱

### 3.2 用户场景

| 角色 | 场景 |
|------|------|
| 普通用户 | 上传个人笔记、论文，建立个人知识库 |
| 管理员 | 管理全局知识库、审核共享文档 |

### 3.3 支持的文档格式

| 格式 | 处理方式 | 难度 |
|------|---------|------|
| TXT | 直接读取 | ⭐ |
| MD | 解析 Markdown | ⭐ |
| PDF | pdfminer/PyMuPDF 提取文本 | ⭐⭐⭐ |
| DOCX | python-docx 解析 | ⭐⭐ |

---

## 四、UI/UX 设计

### 4.1 设计原则

**遵循项目现有风格**：
- Tailwind CSS + CSS 变量
- 简洁现代的卡片式设计
- 支持深色模式
- 统一的颜色变量（`--color-*`）

### 4.2 页面结构

```
┌─────────────────────────────────────────────────────────────────────────┐
│  知识库                                                    [+ 上传文档] │
├─────────────────────────────────────────────────────────────────────────┤
│  🔍 搜索...  [标签▼] [来源▼] [状态▼]                    共 23 条记录    │
├─────────────────────────────────────────────────────────────────────────┤
│  ☐ │ 文档名称          │ 标签               │ 切片数 │ 更新时间 │图谱│ │
├───┼──────────────────┼────────────────────┼────────┼──────────┼────┤   │
│ ☐ │ 大模型综述.pdf     │ [LLM] [GPT]      │ 15    │ 2024-01-15│🔗│   │
│ ☐ │ RAG技术总结.md     │ [RAG] [检索]     │ 12    │ 2024-01-14│🔗│   │
│ ☐ │ 多模态论文.txt     │ [多模态] [VLM]   │ 8     │ 2024-01-13│🔗│   │
├─────────────────────────────────────────────────────────────────────────┤
│  显示 1-10 / 23 条  │ ◀ 1 2 3 ▶ │ 每页 [20▼] 条                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.3 组件样式规范

**遵循项目 CSS 变量**：

```css
/* 表格容器 */
.knowledge-table {
  background: var(--color-bg-white);
  border: 1px solid var(--color-border-light);
  border-radius: 6px;
}

/* 表格行悬停 */
.knowledge-table tr:hover {
  background: var(--color-bg-hover);
}

/* 标签样式 */
.tag {
  display: inline-block;
  padding: 2px 8px;
  font-size: var(--fs-xs);
  background: var(--color-bg-off);
  color: var(--color-text-muted);
  border-radius: 4px;
}

/* 图谱链接按钮 */
.graph-link {
  color: var(--color-blue-link);
  cursor: pointer;
  font-size: var(--fs-sm);
}
.graph-link:hover {
  text-decoration: underline;
}
```

### 4.4 抽屉组件（知识图谱）

**样式与现有 AI 助手弹窗一致**：

```jsx
// 抽屉样式
const drawerStyle = {
  background: 'var(--color-bg-white)',
  border: '1px solid var(--color-border)',
  borderRadius: '6px',
  boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
};
```

**抽屉布局**：

```
┌──────────────────────────────────────────────┐
│  📊 知识图谱：大模型综述.pdf            [×]   │
├──────────────────────────────────────────────┤
│  🔍 搜索节点...                              │
├──────────────────────────────────────────────┤
│                                              │
│         [LLM] ─── [GPT-4]                  │
│            │                                │
│      [Transformer]                          │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │ 节点详情（选中时显示）                   │ │
│  │ 名称: LLM                             │ │
│  │ 类型: 概念                             │ │
│  │ 出现次数: 5 次                         │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  [力导向] [层级] [网格]                       │
├──────────────────────────────────────────────┤
│  [导出图片] [全屏] [折叠]                     │
└──────────────────────────────────────────────┘
```

### 4.5 上传文档弹窗

**样式与项目风格一致**：

```
┌──────────────────────────────────────────────────┐
│  上传文档                                    [×]   │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │                                            │ │
│  │     📄                                     │ │
│  │     拖拽文件到此处，或                     │ │
│  │     <u>点击上传</u>                       │ │
│  │                                            │ │
│  │     支持: PDF, DOCX, TXT, MD              │ │
│  │     最大: 10MB                            │ │
│  │                                            │ │
│  └────────────────────────────────────────────┘ │
│                                                  │
│  标签: [输入标签，用逗号分隔...]                │
│                                                  │
├──────────────────────────────────────────────────┤
│                         [取消]  [上传并处理]      │
└──────────────────────────────────────────────────┘
```

### 4.6 节点详情卡片

```
┌─────────────────────────────────────────┐
│  📌 节点详情                       [×] │
├─────────────────────────────────────────┤
│  名称: LLM (大语言模型)                 │
│  类型: 概念                             │
│  出现次数: 5 次                         │
│                                         │
│  📍 出现位置:                          │
│  ├─ Chunk #2: "LLM是指..."             │
│  ├─ Chunk #5: "GPT是一个LLM"           │
│  └─ Chunk #8: "LLM的参数..."           │
│                                         │
│  🔗 关联节点 (3):                      │
│  ├─ GPT-4 (是...的一种)                │
│  ├─ Transformer (基于)                 │
│  └─ 参数微调 (应用于)                  │
│                                         │
│  [查看切片] [高亮关联] [复制]           │
└─────────────────────────────────────────┘
```

---

## 五、数据模型

### 5.1 数据库表设计

```sql
-- 知识库文档表
CREATE TABLE kb_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size INTEGER,
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 文档切片表
CREATE TABLE kb_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES kb_documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER,
    vector_id VARCHAR(255), -- pgvector 中的 ID
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 实体表（用于知识图谱）
CREATE TABLE kb_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES kb_documents(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- concept, person, organization, technology, etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- 关系表（用于知识图谱）
CREATE TABLE kb_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID REFERENCES kb_entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES kb_entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(100), -- is_a, part_of, related_to, based_on, etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- 实体-切片关联表
CREATE TABLE kb_entity_chunks (
    entity_id UUID REFERENCES kb_entities(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES kb_chunks(id) ON DELETE CASCADE,
    PRIMARY KEY (entity_id, chunk_id)
);
```

### 5.2 向量存储（pgvector）

```sql
-- 创建向量存储扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建向量表
CREATE TABLE kb_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID REFERENCES kb_chunks(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536), -- DeepSeek embedding 维度
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引以加速搜索
CREATE INDEX idx_embeddings_embedding ON kb_embeddings USING ivfflat (embedding vector_cosine_ops);
```

---

## 六、API 设计

### 6.1 文档管理 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/kb/documents | 获取文档列表 |
| POST | /api/kb/documents | 上传文档 |
| GET | /api/kb/documents/:id | 获取文档详情 |
| DELETE | /api/kb/documents/:id | 删除文档 |
| PATCH | /api/kb/documents/:id | 更新文档（标签等） |

### 6.2 切片 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/kb/documents/:id/chunks | 获取文档切片 |
| GET | /api/kb/chunks/:id | 获取切片详情 |
| DELETE | /api/kb/chunks/:id | 删除切片 |

### 6.3 知识图谱 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/kb/documents/:id/graph | 获取文档知识图谱数据 |
| GET | /api/kb/entities/:id | 获取实体详情 |
| GET | /api/kb/search | 语义搜索切片 |

### 6.4 API 请求/响应示例

**POST /api/kb/documents（上传文档）**

```json
// Request (multipart/form-data)
{
  "file": <binary>,
  "tags": ["LLM", "GPT"]
}

// Response
{
  "id": "uuid",
  "name": "大模型综述.pdf",
  "file_type": "pdf",
  "status": "processing",
  "tags": ["LLM", "GPT"],
  "created_at": "2024-01-15T10:30:00Z"
}
```

**GET /api/kb/documents/:id/graph（获取知识图谱）**

```json
// Response
{
  "nodes": [
    {
      "id": "entity-1",
      "name": "LLM",
      "type": "concept",
      "chunkCount": 5
    },
    {
      "id": "entity-2",
      "name": "GPT-4",
      "type": "technology",
      "chunkCount": 3
    }
  ],
  "edges": [
    {
      "source": "entity-1",
      "target": "entity-2",
      "relation": "is_a",
      "label": "是一种"
    }
  ]
}
```

---

## 七、知识图谱实现

### 7.1 实体识别（NER）

使用 DeepSeek API 进行实体识别：

```python
# 实体识别 Prompt
NER_PROMPT = """
从以下文本中识别出实体，并分类。

文本：
{text}

实体类型：
- concept: 概念（如：大语言模型、机器学习）
- technology: 技术（如：Transformer、GPT）
- person: 人名（如：Sam Altman）
- organization: 机构（如：OpenAI、Google）
- product: 产品（如：GPT-4、Claude）

请以 JSON 格式返回：
[
  {{"name": "实体名", "type": "类型"}},
  ...
]

只返回 JSON，不要其他内容。
"""
```

### 7.2 关系抽取（RE）

```python
# 关系抽取 Prompt
RE_PROMPT = """
从以下文本中抽取实体之间的关系。

文本：
{text}

已识别实体：
{entities}

关系类型：
- is_a: A 是一种 B（如：大语言模型 is_a 机器学习）
- part_of: A 是 B 的一部分
- based_on: A 基于 B
- related_to: A 与 B 相关
- author_of: A 是 B 的作者
- published_by: A 由 B 发布

请以 JSON 格式返回：
[
  {{"source": "实体A", "target": "实体B", "relation": "关系类型", "label": "中文标签"}},
  ...
]

只返回 JSON，不要其他内容。
"""
```

### 7.3 图谱数据结构

```javascript
// React Flow 图谱节点
const nodes = [
  {
    id: 'entity-1',
    type: 'custom',
    position: { x: 100, y: 100 },
    data: {
      label: 'LLM',
      type: 'concept',
      chunkCount: 5,
      details: {
        occurrences: ['Chunk #2', 'Chunk #5'],
        relations: ['GPT-4', 'Transformer']
      }
    },
    style: {
      background: '#E8F4FD',
      border: '1px solid #2864A8',
      borderRadius: '8px',
      padding: '8px 12px'
    }
  }
];

// 图谱边
const edges = [
  {
    id: 'e1-2',
    source: 'entity-1',
    target: 'entity-2',
    label: '是一种',
    type: 'smoothstep',
    animated: false,
    style: { stroke: '#686C72' }
  }
];
```

---

## 八、实施计划

### 8.1 阶段划分

| 阶段 | 名称 | 周期 | 核心任务 |
|------|------|------|---------|
| **Phase 0** | 文档上传基础 | 1周 | 上传接口、文档解析、基础存储 |
| **Phase 1** | 切片 + 向量化 | 1周 | 切片处理、向量存储、语义搜索 |
| **Phase 2** | 知识库 UI | 1周 | 表格页面、上传弹窗、抽屉组件 |
| **Phase 3** | 知识图谱 | 2周 | 实体识别、关系抽取、图谱可视化 |
| **Phase 4** | 自然语言操作 | 1周 | 意图识别、操作映射 |
| **Phase 5** | 个性化推荐 | 1周 | 用户画像、推荐算法 |
| **Phase 6** | 多模态理解 | 1周 | Groq API 集成、图片分析 |

### 8.2 Phase 0 详细任务

| 任务 | 预估工时 | 说明 |
|------|----------|------|
| 数据库表创建 | 2h | 创建 kb_documents 等表 |
| 文件上传接口 | 4h | 支持 PDF/DOCX/TXT/MD |
| 文档解析 | 8h | 提取文本内容 |
| 基础 CRUD | 4h | 文档管理接口 |

### 8.3 Phase 1 详细任务

| 任务 | 预估工时 | 说明 |
|------|----------|------|
| 切片处理 | 8h | RecursiveCharacterTextSplitter |
| 向量化 | 4h | DeepSeek Embedding API |
| pgvector 存储 | 4h | 向量存储和检索 |
| 语义搜索 API | 8h | 搜索接口 |

### 8.4 Phase 2 详细任务

| 任务 | 预估工时 | 说明 |
|------|----------|------|
| 表格页面 | 8h | 文档列表、分页、筛选 |
| 上传弹窗 | 8h | 拖拽上传、进度显示 |
| 图谱抽屉 | 4h | 抽屉容器 |
| React Flow 集成 | 8h | 图谱渲染 |

### 8.5 Phase 3 详细任务

| 任务 | 预估工时 | 说明 |
|------|----------|------|
| 实体识别服务 | 8h | DeepSeek NER |
| 关系抽取服务 | 8h | DeepSeek RE |
| 图谱数据接口 | 4h | 图谱查询 API |
| 图谱交互 | 8h | 节点点击、详情卡片 |

---

## 九、验收标准

### 9.1 知识库管理

- [ ] 用户可上传 PDF/DOCX/TXT/MD 文档
- [ ] 文档自动切片处理
- [ ] 文档列表支持分页、筛选、搜索
- [ ] 支持标签管理
- [ ] 支持文档删除

### 9.2 知识图谱

- [ ] 自动识别文档中的实体
- [ ] 自动抽取实体间关系
- [ ] 图谱可视化展示（React Flow）
- [ ] 节点详情展示
- [ ] 图谱布局切换（力导向/层级/网格）

### 9.3 语义搜索

- [ ] 支持全文语义搜索
- [ ] 搜索响应时间 < 3秒
- [ ] 可按标签、来源筛选

### 9.4 自然语言操作

- [ ] 意图识别准确率 > 90%
- [ ] 支持收藏/筛选/导航等操作

### 9.5 个性化推荐

- [ ] 推荐点击率提升 > 20%

### 9.6 多模态理解

- [ ] Groq API 集成成功
- [ ] 图片内容描述准确

---

## 十、风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 文档解析失败 | 中 | 用户上传无效文件 | 前端格式校验 + 后端异常处理 |
| 实体识别不准 | 中 | 图谱质量差 | 提供手动编辑入口 |
| 向量搜索慢 | 低 | 搜索体验差 | 创建索引、限制返回数量 |
| 图谱渲染卡顿 | 中 | 大量节点时性能差 | 虚拟化、限制显示数量 |

---

## 十一、成本汇总

| 项目 | 月均成本 | 年均成本 |
|------|----------|----------|
| Supabase | 0元 | 0元 |
| DeepSeek API | 0元 | 0元（免费额度内） |
| Groq API | 0元 | 0元（备用100元可用6-12月） |
| React Flow | 0元 | npm 免费包 |
| **总计** | **0元** | **0元** |

---

## 附录

### A. 密钥管理配置指南

#### A.1 .env 文件完整配置

```env
# ============================================
# API 密钥配置
# ============================================

# DeepSeek API（核心服务）
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_API_BASE_URL=https://api.deepseek.com/v1

# 阿里百炼 Qwen-VL（多模态服务）
ALIYUN_BAILIAN_API_KEY=sk-xxx
ALIYUN_BAILIAN_API_URL=https://dashscope.aliyuncs.com/api/text/image/text_to_image

# ============================================
# 数据库配置（已在 Supabase 中配置）
# ============================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# ============================================
# 应用配置
# ============================================
APP_ENV=development
PORT=8000
```

#### A.2 阿里百炼 Qwen-VL 注册步骤

1. 访问：https://bailian.aliyun.com/
2. 使用阿里云账号登录（没有的话注册一个）
3. 进入「模型服务」→「Qwen-VL」
4. 领取免费额度（新用户通常有 10,000 次免费调用）
5. 创建 API Key：
   - 进入「API 管理」→「创建密钥」
   - 设置密钥名称（如：Signal-Qwen-VL）
   - 复制生成的 API Key
6. 配置到项目 `.env`：`ALIYUN_BAILIAN_API_KEY=sk-xxx`

#### A.3 密钥轮换与安全最佳实践

**密钥轮换策略**：

| 密钥类型 | 建议轮换周期 | 到期提醒 |
|----------|--------------|----------|
| DeepSeek API Key | 3个月 | 到期前7天提醒 |
| 阿里百炼 API Key | 3个月 | 到期前7天提醒 |
| Supabase Service Key | 6个月 | 到期前14天提醒 |

**安全注意事项**：

1. ✅ **切勿硬编码密钥**：始终使用环境变量
2. ✅ **定期轮换密钥**：避免密钥泄露风险
3. ✅ **限制密钥权限**：仅授予必要的最小权限
4. ✅ **加密存储**：敏感环境使用密钥管理服务
5. ⚠️ **禁止公开分享**：不在代码仓库、聊天记录中暴露密钥
6. ⚠️ **及时撤销泄露密钥**：发现泄露立即禁用并轮换

**密钥到期处理流程**：

```
到期提醒 → 创建新密钥 → 更新环境变量 → 测试新密钥 → 禁用旧密钥
```

#### A.4 免费额度说明

| 服务 | 免费额度 | 额度用尽处理 |
|------|----------|--------------|
| DeepSeek API | 每月有免费额度 | 超出后按调用量计费 |
| 阿里百炼 Qwen-VL | 新用户 10,000 次 | 超出后按调用量计费 |
| Supabase | 免费层级够用 | 超出后升级付费方案 |

### B. 参考资料

- **React Flow**: https://reactflow.dev/
- **Supabase pgvector**: https://supabase.com/docs/guides/database/向量
- **阿里百炼**: https://bailian.aliyun.com/
- **DeepSeek API**: https://platform.deepseek.com/