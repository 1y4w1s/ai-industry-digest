# Phase 2: 可扩展性与性能优化提案

## Why

当前项目已具备基本的全栈功能（用户认证、文章管理、AI 摘要），但存在以下限制：
1. **性能瓶颈**：每次请求直接查询数据库，无缓存机制，高并发下响应慢
2. **工程化不足**：缺少单元测试、CI/CD 流水线，代码质量依赖人工 review
3. **实时性缺失**：用户操作（如收藏）需要手动刷新页面，无法实时感知变更

这些限制使得项目难以应对更大规模的数据和用户，也无法展示"工程化能力"。

## What Changes

**Phase 2 目标：将项目从"功能可用"提升到"工程规范"**

### 1. 性能优化
- 引入 Redis 缓存热点数据（文章列表、用户会话）
- 实现缓存失效策略（TTL + 主动更新）

### 2. 工程化建设
- 添加 pytest 单元测试覆盖核心功能
- 配置 GitHub Actions CI/CD 流水线（测试 → 构建 → 部署）

### 3. 实时能力
- 引入 WebSocket 支持实时推送（收藏、历史变更通知）
- 添加管理员数据看板（用户量、访问趋势）

### 4. 异步任务
- 使用 Celery 异步处理 AI 摘要生成
- 解决同步调用导致的响应延迟问题

## Capabilities

### New Capabilities

- `redis-cache`: Redis 缓存层实现，包括缓存策略、失效机制、测试
- `unit-testing`: 单元测试体系建设，包括后端 API 测试、数据库操作测试
- `cicd-pipeline`: GitHub Actions CI/CD 流水线，包括自动化测试和部署
- `websocket-realtime`: WebSocket 实时通信，用于推送通知
- `admin-dashboard`: 管理员数据看板，展示系统关键指标

### Modified Capabilities

- 无（Phase 2 不修改现有功能的行为，只是增强性能和工程化）

## Impact

### 影响的代码
- `api/routes/` - API 路由需适配缓存层
- `api/models/database.py` - 数据库操作需添加缓存逻辑
- `frontend/` - 前端需添加 WebSocket 连接和数据看板页面

### 影响的依赖
- 新增：`redis`、`celery`、`flower`
- 新增：`pytest`、`pytest-asyncio`
- 新增：`websockets`

### 基础设施变更
- 需在服务器安装 Redis
- 需配置 Celery + Redis 作为消息队列
- GitHub Secrets 需添加服务器部署密钥

### API 变更
- 新增：`GET /api/admin/stats` - 管理员统计接口
- 新增：`WS /ws` - WebSocket 连接端点
