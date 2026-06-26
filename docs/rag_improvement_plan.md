# RAG 系统改造计划 PRD

> 版本: v1.0  
> 日期: 2026-06-26  
> 状态: 待评审  
> 负责人: 产品经理

---

## 一、需求背景

### 1.1 现状概述

当前 RAG 系统已实现以下基础能力：

- 文档上传与解析（TXT/MD/PDF/DOCX）
- 固定长度切片（chunk_size=500, overlap=50）
- Embedding 向量化（阿里云 text-embedding-v3, 1024维）
- 混合检索（向量 + 关键词 + RRF 融合）
- Query 改写
- 知识图谱（实体识别 + 关系抽取）
- 知识库对话

### 1.2 现存问题

通过全面审查，识别出以下关键问题：

| 问题 | 严重程度 | 影响范围 |
|------|----------|----------|
| 三套独立检索逻辑能力不一致，kb/chat 接口检索质量差 | P0 | 用户体验 |
| Embedding 逐片串行生成，大文档处理极慢 | P0 | 系统性能 |
| `search_kb_by_embedding` 数据库函数定义缺失 | P0 | 运维风险 |
| 切片策略无语义感知，纯固定长度+标点回溯 | P1 | 检索精度 |
| 无查询结果重排序（Re-ranking） | P1 | 检索精度 |
| 无上下文压缩（Context Compression） | P1 | LLM 成本 |
| 无检索质量监控与回测机制 | P1 | 系统可观测性 |
| 无文档增量更新机制 | P1 | 用户体验 |
| 知识图谱未被检索利用 | P2 | 检索精度 |
| 切片元数据薄弱 | P2 | 可扩展性 |
| 缺少搜索结果 Query Suggestion | P2 | 用户体验 |
| 多模态内容（PDF/DOCX 图片）被丢弃 | P2 | 信息完整性 |

### 1.3 改造目标

1. **提升检索精度**：解决切片策略和检索排序的根本问题
2. **降低系统成本**：通过上下文压缩减少 LLM token 消耗
3. **增强可观测性**：建立检索质量监控体系
4. **统一系统架构**：消除多套检索逻辑的不一致性
5. **保障运维安全**：补充缺失的数据库函数定义

---

## 二、用户故事

| ID | 用户故事 | 优先级 |
|----|----------|--------|
| US-01 | 作为知识库用户，我希望搜索任何文档都能获得一致的高质量结果，无论我在哪个对话入口提问 | P0 |
| US-02 | 作为知识库用户，我希望上传大文档（100页以上）后能较快完成处理，而不是等待几分钟 | P0 |
| US-03 | 作为系统管理员，我希望确认所有数据库函数有完整的版本控制记录，避免迁移丢失 | P0 |
| US-04 | 作为知识库用户，我希望文档切片能按语义段落自然分割，不会出现一句话被切成两段的情况 | P1 |
| US-05 | 作为知识库用户，我希望搜索结果的排序更准确，最相关的内容排在最前面 | P1 |
| US-06 | 作为日常使用用户，我希望 AI 的回答能精准引用文档中最相关的部分，而不是大段无关内容 | P1 |
| US-07 | 作为系统管理员，我希望能够监控检索系统的运行质量，及时发现并定位问题 | P1 |
| US-08 | 作为知识库用户，我希望修改文档后只需更新变更的部分，不需要重新处理整个文档 | P1 |
| US-09 | 作为知识库用户，当我搜索不准确时，系统能给出相关的搜索建议 | P2 |
| US-10 | 作为知识库用户，我希望包含图表的 PDF 文档也能被检索到其中的关键信息 | P2 |

---

## 三、功能清单

### Phase 1 — 打好地基（P0 必须做）

| ID | 功能 | 优先级 | 预估工时 |
|----|------|--------|----------|
| F-01 | **统一检索入口**：消除三套检索逻辑差异，全部统一使用 AdvancedRetrievalService | P0 | 4h |
| F-02 | **补充 search_kb_by_embedding 函数定义文档**：在 /scripts 目录创建 SQL 定义文件，加入 CI 检查 | P0 | 1h |
| F-03 | **Embedding 生成改为批量并行**：process_document 中改用 get_embeddings() 批量处理 | P0 | 3h |
| F-04 | **文档处理接入异步任务**：将 process_document 改为后台任务执行，不阻塞 API 响应 | P0 | 4h |
| F-05 | **新增检索质量日志**：记录每个查询的检索结果、分数、耗时 | P0 | 3h |

### Phase 2 — 提升精度（P1 重要做）

| ID | 功能 | 优先级 | 预估工时 |
|----|------|--------|----------|
| F-06 | **替换为语义感知的切片策略**：使用 RecursiveCharacterTextSplitter 多层分隔符 | P1 | 4h |
| F-07 | **引入 Re-ranker（Cross-encoder）**：对 RRF 结果做二次精排 | P1 | 8h |
| F-08 | **引入 Context Compression**：检索结果送入 LLM 前做相关性压缩 | P1 | 6h |
| F-09 | **检索策略按意图自动路由**：根据查询类型选择最佳检索组合 | P1 | 6h |
| F-10 | **元数据增强**：丰富切片 metadata 信息（章节标题、实体列表、页码等） | P1 | 3h |
| F-11 | **文档增量更新**：支持文档版本管理，只更新变更的切片 | P1 | 8h |

### Phase 3 — 扩展能力（P2 可选做）

| ID | 功能 | 优先级 | 预估工时 |
|----|------|--------|----------|
| F-12 | **知识图谱融入检索**：Graph Score 作为第三路检索信号 | P2 | 10h |
| F-13 | **多模态支持**：PDF/DOCX 图片 OCR 提取文字或生成描述 | P2 | 8h |
| F-14 | **Query Suggestion**：搜索结果为空的拼写纠正和相近推荐 | P2 | 5h |
| F-15 | **监控仪表盘**：Embedding 覆盖率、检索延迟、精度趋势可视化 | P2 | 6h |

---

## 四、验收标准

### Phase 1 验收标准

| 验收项 | 验证方法 | 通过条件 |
|--------|----------|----------|
| AC-01 | 分别从 /api/chat、/api/kb/chat、/api/agent-chat 搜索"什么是大语言模型" | 三个接口返回的 Top3 结果一致 |
| AC-02 | 在 Supabase SQL Editor 执行 search_kb_by_embedding 的 SQL 定义 | 函数创建成功，无报错 |
| AC-03 | 上传一个500页 PDF 文档 | 处理完成时间 < 改造前的 1/5 |
| AC-04 | 调用 /api/kb/documents/{id}/process 后立即返回 | 响应时间 < 2秒（异步处理） |
| AC-05 | 查看 chat.log 或新增的检索日志 API | 每条查询有完整的检索记录 |

### Phase 2 验收标准

| 验收项 | 验证方法 | 通过条件 |
|--------|----------|----------|
| AC-06 | 对一个带 Markdown 标题的文档做切片 | 切片边界与文档章节标题对齐，不切断段落 |
| AC-07 | 用模糊查询测试对比改造前后的 Top5 相关性 | 用户盲测认为改造后更相关 |
| AC-08 | 查询"大模型训练方法"，检查注入 LLM 的上下文 | 上下文长度减少 > 40%（对比原始切片拼接） |
| AC-09 | 输入"最近有什么文档推荐" | 路由到推荐模式，返回最新文档 |
| AC-10 | 修改文档中的部分内容后调用增量更新 | 只更新变更涉及的切片，time 比全量处理少 80% |

### Phase 3 验收标准

| 验收项 | 验证方法 | 通过条件 |
|--------|----------|----------|
| AC-11 | 查询"OpenAI 有哪些产品" | 结果中包含从知识图谱获取的关联实体信息 |
| AC-12 | 上传带图表的 PDF，搜索图表中的文字 | 能够检索到图表中的关键信息 |
| AC-13 | 搜索"transformer 架构"（故意错拼） | 系统返回"您是不是在找：Transformer 架构？" |
| AC-14 | 查看监控仪表盘页面 | 展示 Embedding 覆盖率、检索延迟、精度趋势 |

---

## 五、异常流程说明

| 场景 | 预期行为 |
|------|----------|
| Embedding API 临时不可用 | 降级为关键词检索，记录错误日志，不阻塞用户查询 |
| 文档切片后部分 Embedding 生成失败 | 保存切片但不记录 embedding，由 Celery 定时任务重试 |
| Re-ranker 服务超时（> 2秒） | 跳过精排，直接返回 RRF 融合结果 |
| Context Compression 调用失败 | 不压缩，直接拼接原始切片内容 |
| 增量更新时原文档已被删除 | 返回 404，告知用户文档不存在 |
| 知识图谱查询无结果 | 不影响正常检索流程，仅跳过 Graph Score |
| OCR 处理超时（> 30秒/页） | 跳过该页图片处理，只返回已提取文本 |

---

## 六、改造路线图

```
Phase 1（1周）
├── Day 1-2: F-01 统一检索入口
├── Day 1:   F-02 补充函数定义
├── Day 2-3: F-03 Embedding 批量并行
├── Day 3-4: F-04 异步任务改造
└── Day 5:   F-05 检索质量日志

Phase 2（2周）
├── Day 1-2: F-06 语义感知切片
├── Day 3-5: F-07 Re-ranker
├── Day 4-5: F-08 Context Compression
├── Day 6-7: F-09 检索策略路由
├── Day 6:   F-10 元数据增强
└── Day 8-10: F-11 文档增量更新

Phase 3（2周）
├── Day 1-3: F-12 知识图谱融入检索
├── Day 3-5: F-13 多模态支持
├── Day 4-5: F-14 Query Suggestion
└── Day 5-6: F-15 监控仪表盘
```

---

## 七、附录

### 7.1 相关文件索引

| 文件 | 说明 |
|------|------|
| [api/routes/kb.py#L654-L682](file:///d:/MyPrograms/ai-industry-digest/api/routes/kb.py#L654-L682) | 当前切片函数 `split_into_chunks` |
| [api/services/retrieval.py](file:///d:/MyPrograms/ai-industry-digest/api/services/retrieval.py) | 高级检索服务（含 Query 改写 + 混合检索 + RRF） |
| [api/services/embedding.py](file:///d:/MyPrograms/ai-industry-digest/api/services/embedding.py) | Embedding 服务（含批量接口） |
| [api/routes/kb.py#L449-L531](file:///d:/MyPrograms/ai-industry-digest/api/routes/kb.py#L449-L531) | 文档处理流程 `process_document` |
| [api/routes/kb.py#L711-L764](file:///d:/MyPrograms/ai-industry-digest/api/routes/kb.py#L711-L764) | kb/chat 的独立检索逻辑（待统一） |
| [api/routes/chat.py#L48-L93](file:///d:/MyPrograms/ai-industry-digest/api/routes/chat.py#L48-L93) | chat 的检索逻辑 |
| [scripts/migration_knowledge_base.sql](file:///d:/MyPrograms/ai-industry-digest/scripts/migration_knowledge_base.sql) | 知识库数据库表定义 |
| [scripts/migration_embedding_dimension.sql](file:///d:/MyPrograms/ai-industry-digest/scripts/migration_embedding_dimension.sql) | pgvector 维度修改 SQL |
| [tasks.py](file:///d:/MyPrograms/ai-industry-digest/tasks.py) | Celery 定时任务（Embedding 补全） |

### 7.2 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 统一检索入口导致现有接口行为改变 | 中 | 前端可能不兼容 | 保持旧接口兼容，内部路由到新逻辑 |
| 异步处理增加系统复杂度 | 中 | 调试困难 | 保持同步/异步双模式，可通过参数切换 |
| Re-ranker 增加检索延迟 | 低 | 用户体验下降 | 设置超时兜底，超时后降级为 RRF 直接返回 |
| 增量更新引起数据不一致 | 低 | 切片与文档不同步 | 实现前先做版本号对照，处理完后校验 |

### 7.3 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 检索 P99 延迟 < 3秒（含 Re-ranker） |
| 性能 | 大文档（500页 PDF）处理时间 < 改造前的 1/5 |
| 可用性 | 任何第三方服务（Embedding/LLM）不可用时，系统降级可用 |
| 可维护性 | 所有数据库函数定义纳入版本控制 |
| 可观测性 | 每条查询可追溯检索链路和耗时 |
