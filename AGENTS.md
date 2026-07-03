# AGENTS.md — Signal

## 产品边界

- **Signal 只做 AI 行业日报**，不做知识库/RAG 新功能。
- 知识库已迁至 `rag-knowledge-platform`，见 `docs/SPLIT_PLAN.md`。

## 协作规则

1. 一个对话只做一个极小任务。
2. 动手前先看 `docs/PRODUCT_CORE.md`，不擅自扩展范围。
3. 改功能逻辑必须同步更新相关文档。
4. 不动 `rag-knowledge-platform` 里的代码（除非任务 explicitly 涉及集成）。

## 当前状态

- **Signal（本仓库）**：阶段 D 物理清理已完成（KB/RAG 孤儿文件已删，61 项测试通过）；阶段 C 云部署已验收（commit 22500ff）
- **RAG 项目**：bootstrap 已完成，完善与部署留待下一阶段
