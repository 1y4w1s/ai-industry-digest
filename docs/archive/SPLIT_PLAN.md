# Signal ↔ RAG 项目拆分计划（历史归档）

> 创建日期: 2026-07-03  
> 状态: **已完成**（阶段 A–D，2026-07-03）  
> 说明: 拆分已结束，Signal 现为独立日报产品。本文仅供追溯，**非当前开发依据**。

---

## 原则

1. **先复制、跑通，再删除** —— 不在 Signal 未验证前删 KB 代码  
2. **Signal 冻结 KB 新功能** —— 只修 P0 Bug，新能力只在 RAG 项目开发  
3. **同一 Supabase 可先共用** —— Signal 用 `articles*`，RAG 用 `kb_*`

---

## 本地端口约定

| 项目 | 后端 | 前端 |
|------|------|------|
| Signal | 8000 | 5173 |
| RAG | **8001** | **5174** |

---

## 迁出清单（Signal → RAG）

### 后端 — 整包迁移

```
api/routes/kb.py
api/routes/agent_router.py
api/routes/monitor.py
api/services/retrieval.py
api/services/reranker.py
api/services/compression.py
api/services/router.py
api/services/graph_retrieval.py
api/services/query_suggestion.py
api/services/metadata.py
api/services/document_tracker.py
api/services/image_extractor.py
api/services/image_caption.py
api/services/data_cleaner.py
api/services/embedding.py
api/services/intent_classifier.py
api/services/agent.py
api/services/monitor/
tasks.py
processor/ai_processor.py          # KB 实体抽取；后续拆为 kb_processor.py
scripts/import_to_kb.py
scripts/reprocess_documents.py
scripts/migration_knowledge_base.sql
scripts/migration_kb_public.sql
scripts/migration_embedding_dimension.sql
scripts/migration_incremental_update.sql
scripts/migration_metrics.sql
scripts/search_kb_by_embedding.sql
```

### 后端 — 复制共用

```
api/services/jwt_verify.py
api/services/cache.py
api/models/database.py             # 首版整包复制，后续 RAG 只保留 kb 方法
collector/base.py                  # database.py 依赖 Article 类型
```

### 测试 — 迁移

```
tests/test_kb.py
tests/test_f07_f08_reranker_compression.py
tests/test_f09_router.py
tests/test_f10_metadata.py
tests/test_f11_document_tracker.py
tests/test_f12_graph.py
tests/test_f13_multimodal.py
tests/test_f14_query_suggestion.py
tests/test_f15_monitor.py
tests/test_retrieval_integration.py
tests/benchmark_rag_metrics.py
tests/e2e_kb_upload.py
tests/test_jwt_verify.py
tests/test_cache.py
```

### 前端 — 迁移

```
frontend/src/pages/KnowledgeBasePage.jsx
frontend/src/pages/LoginPage.jsx
frontend/src/components/UploadProgressPanel.jsx
frontend/src/components/KnowledgePreviewDrawer.jsx
frontend/src/components/KnowledgeGraphDrawer.jsx
frontend/src/components/Toast.jsx
frontend/src/context/*
frontend/src/lib/*
frontend/src/api/client.js           # RAG 版只保留 kb + auth
```

---

## 留在 Signal

```
collector/
processor/          # dedup, reporter, ai_processor（日报用）
run.py
api/routes/content.py, auth.py, chat.py, recommend.py, admin.py
api/services/tag_extractor.py, jwt_verify.py, cache.py
frontend: Home, Archive, Search, Bookmarks, History, Profile, Settings, Admin（日报部分）
```

---

## 耦合点与剪断方式

| 耦合 | 位置 | 剪断方式 | 阶段 |
|------|------|----------|------|
| 全局对话注入 KB | `api/routes/chat.py` | 删除 `search_kb_chunks` 注入 | C |
| 采集后灌 KB | `run.py` `KB_IMPORT` | 改 HTTP ingest 或关闭 | C |
| AIProcessor 共用 | `kb.py` → `processor/` | RAG 内独立 `kb_processor.py` | D |
| 导航入口 | `Layout.jsx` | 「知识库」改外链 RAG | C |
| 路由注册 | `api/main.py` | 移除 kb/agent/monitor router | C |

---

## 执行阶段

### 阶段 A — 准备 ✅

- [x] `docs/PRODUCT_CORE.md`
- [x] `docs/SPLIT_PLAN.md`
- [x] RAG 项目 `docs/PRODUCT_CORE.md` + `docs/ARCHIVE_JAVA.md`
- [x] 两边 `AGENTS.md`

### 阶段 B — RAG bootstrap（进行中）

- [x] 清空旧 Java 栈，复制 KB 代码
- [x] `api/main.py` 仅 KB 路由
- [x] 前端 KB 页 + 5174/8001 配置
- [ ] 本地 8001 / 5174 跑通上传与搜索（需你配 `.env` 后验证）
- [ ] RAG 测试跑绿

### 阶段 C — 剪 Signal ✅

- [x] `chat.py` 去 KB 注入
- [x] 前端移除 `/knowledge` 与侧栏「知识库」
- [x] `main.py` 下线 kb / agent / monitor 路由
- [x] `run.py` 移除 `KB_IMPORT`
- [x] 搜索 / 管理后台去掉 KB 与 F-15 监控
- [x] 云服务器 push + 部署验收（commit `22500ff`，见 `docs/ops/SIGNAL_SPLIT_DEPLOY.md`）
- [ ] 服务器 cron 清理 `KB_IMPORT` / `import_to_kb`（需 SSH）

### 阶段 D — 清理

- [x] Signal 物理删除已迁文件（2026-07-03，61 项日报测试通过）
- [x] 更新 Signal README
- [ ] 更新 RAG 项目 README

---

## 未来集成契约（草案）

```
POST /api/v1/ingest
Content-Type: application/json
Authorization: Bearer <service-token 或用户 JWT>

{
  "title": "string",
  "url": "string",
  "content": "string",
  "source_name": "string",
  "published_at": "ISO8601",
  "tags": ["string"]
}

→ 202 { "document_id": "uuid", "status": "processing" }
```

由 RAG 项目实现；Signal `run.py` 在阶段 C 改为调用此接口。
