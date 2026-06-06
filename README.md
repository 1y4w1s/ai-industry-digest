# Signal — AI 行业日报聚合平台

> **线上地址**: [http://43.139.133.245:8080](http://43.139.133.245:8080)  
> **技术栈**: [docs/TECH_STACK.md](./docs/TECH_STACK.md) | **设计规范**: [docs/design/DESIGN_SPEC.md](./docs/design/DESIGN_SPEC.md)  
> **部署指南**: [docs/ops/DEPLOY_GUIDE.md](./docs/ops/DEPLOY_GUIDE.md) | **归档索引**: [archive/INDEX.md](./archive/INDEX.md)

自动采集 → AI 处理 → 日报生成 → 知识库 → 个性化推荐，全链路自动化。

---

## 快速上手

```bash
# 后端
pip install -r requirements.txt
python -m uvicorn api.main:app --reload

# 前端
cd frontend && npm install && npm run dev

# 测试
python -m pytest tests/ -v     # 42 项（41 passed, 1 skipped）
```

## 核心功能

| 模块 | 说明 |
|------|------|
| **日报首页** | 按日期浏览 AI 行业日报，来源分组 + 重要性标记 |
| **文章阅读器** | AI 精读摘要 + 原文 + AI 对话 + TTS 朗读 + PDF 导出 |
| **全文搜索** | 搜索文章 + 知识库文档，标题/摘要关键词高亮 |
| **知识库** | 上传/预览/下载 PDF/DOCX/TXT/MD，知识图谱可视化 |
| **AI 对话** | 文章级 + 全局对话，标签画像个性化提示词 |
| **个性化推荐** | 基于阅读/对话/收藏兴趣标签的推荐 Widget |
| **用户系统** | 邮箱注册 + GitHub OAuth + 收藏/历史/统计/趋势 |

## 自动化

| 工作流 | 触发 | 动作 |
|--------|------|------|
| `daily.yml` | 每天 6:00/12:00/18:00 | 采集 → AI 处理 → 日报入库 |
| `deploy.yml` | git push master | 服务器代码同步 → 构建 → 重启 |
| `cron` | 每天 3:00 | 日报采集 + 知识库自动导入 |
| `scripts/migrate.py` | 部署时自动 | 数据库 schema migration |

## 项目结构速览

```
api/              FastAPI 后端（5 路由 + 2 服务 + 单例 DB）
frontend/         React + Vite 前端（代码分割，9 页面，15+ 组件）
collector/        多源采集器（arXiv/RSS/HF）
processor/        AI 处理 + 日报生成
scripts/          部署/迁移/备份
docs/             技术栈/设计/运维文档
tests/            42 项单元测试
```

## 文档索引

| 文档 | 位置 |
|------|------|
| 技术栈详情 | [docs/TECH_STACK.md](./docs/TECH_STACK.md) |
| 设计规范 | [docs/design/DESIGN_SPEC.md](./docs/design/DESIGN_SPEC.md) |
| 部署指南 | [docs/ops/DEPLOY_GUIDE.md](./docs/ops/DEPLOY_GUIDE.md) |
| 排障记录 | [docs/ops/部署与排障记录.md](./docs/ops/部署与排障记录.md) |
| 知识库前端设计 | [docs/design/KB_FRONTEND_DESIGN.md](./docs/design/KB_FRONTEND_DESIGN.md) |
| 项目归档 | [archive/INDEX.md](./archive/INDEX.md) |
| 整改任务书 | [任务书.md](./任务书.md) |
