# Phase 2 技术设计方案

## Context

当前项目 `ai-industry-digest` 已实现基本的全栈功能：
- React + FastAPI + Supabase 架构
- 用户认证、JWT 验证
- 文章管理、AI 摘要生成
- Nginx 静态文件服务

**现状问题**：
1. 性能：无缓存层，每次请求直接查询 Supabase
2. 工程化：无测试、无 CI/CD
3. 体验：无实时反馈，用户需手动刷新

**约束条件**：
- 单台服务器资源有限
- 预算有限（优先使用免费/低成本方案）
- 需要保持向后兼容，不破坏现有功能

## Goals / Non-Goals

**Goals:**
1. 实现 Redis 缓存层，提升 API 响应速度
2. 建立单元测试体系，保证代码质量
3. 配置 GitHub Actions CI/CD，实现自动化部署
4. 添加 WebSocket 实时通知能力
5. 开发管理员数据看板

**Non-Goals:**
1. 不做微服务拆分，保持单体架构
2. 不做数据库分库分表（当前数据量不需要）
3. 不做移动端原生应用
4. 不做高可用多活部署（单台服务器）

## Decisions

### Decision 1: Redis 作为缓存层

**选择**: Redis（而非 Memcached 或自建内存缓存）

**理由**:
- 功能丰富：支持 String、Hash、List、Set 等多种数据结构
- 持久化支持：可配置 RDB/AOF 持久化
- 生态成熟：Python (redis-py)、JavaScript (ioredis) 支持完善
- 运维简单：单节点部署足够支撑当前规模

**替代方案考虑**:
- Memcached：功能单一，不支持复杂数据结构
- 自建 LRU Cache：需要自己实现序列化、持久化、过期策略
- Supabase Edge Functions：成本较高，延迟大

### Decision 2: 使用 Celery 处理异步任务

**选择**: Celery + Redis（而非 Python threading 或 asyncio）

**理由**:
- 任务队列标准方案：支持任务分发、重试、优先级
- 与 Django/FastAPI 集成成熟
- Flower 提供 Web UI 监控任务执行
- 失败重试机制完善

**替代方案考虑**:
- asyncio + aiohttp：适合 IO 密集型，但任务管理能力弱
- RQ (Redis Queue)：功能类似，但社区和文档不如 Celery
- Supabase Edge Functions：成本高，冷启动慢

### Decision 3: 使用 FastAPI WebSocket

**选择**: FastAPI 原生 WebSocket 支持（而非 Socket.IO 或纯 WebSocket）

**理由**:
- FastAPI 原生支持，集成简单
- 与现有 FastAPI 项目无缝结合
- 支持依赖注入，易于添加认证逻辑

**替代方案考虑**:
- Socket.IO：功能强大但体积大，学习成本高
- 纯 WebSocket：需要自己实现心跳、重连

### Decision 4: ECharts 作为可视化库

**选择**: ECharts（而非 D3.js 或 Chart.js）

**理由**:
- 中文文档完善，上手快
- 配置式 API，适合快速开发
- 图表类型丰富，满足数据看板需求

**替代方案考虑**:
- D3.js：灵活但学习曲线陡峭
- Chart.js：简单但图表类型有限

## Risks / Trade-offs

| Risk | 描述 | Mitigation |
|------|------|------------|
| Redis 单点故障 | Redis 崩溃导致缓存不可用 | 实现降级策略，自动切换到直查数据库 |
| WebSocket 连接数限制 | 单服务器 WebSocket 连接数有限（Linux 默认 1024） | 配置 ulimit 和 nginx worker_connections |
| CI/CD 部署失败 | 自动化部署可能失败 | 添加健康检查和自动回滚机制 |
| 测试覆盖率不足 | 测试编写不及时 | 将测试覆盖率纳入 PR 检查项 |
| 服务器资源不足 | Redis + Celery 增加内存占用 | 监控内存使用，及时扩容或优化 |

## Migration Plan

### Phase 2.1: Redis 缓存（1 周）
1. 安装 Redis：`sudo apt install redis-server`
2. 添加依赖：`pip install redis`
3. 实现缓存服务层 `api/services/cache.py`
4. 修改 `database.py` 集成缓存
5. 添加缓存测试

### Phase 2.2: 单元测试（1 周）
1. 配置 pytest + pytest-cov
2. 编写 JWT 验证测试
3. 编写数据库操作测试
4. 编写 API 路由测试
5. 配置 GitHub Actions 测试流程

### Phase 2.3: CI/CD 流水线（3 天）
1. 创建 `.github/workflows/` 目录
2. 实现 CI 流程（测试 + 构建）
3. 实现 CD 流程（部署 + 验证）
4. 配置 GitHub Secrets

### Phase 2.4: WebSocket + 看板（2 周）
1. 实现 WebSocket 服务
2. 前端 WebSocket 客户端
3. 管理后台 API 路由
4. 管理后台前端页面
5. 集成 ECharts 可视化

### 回滚策略
- Redis 配置变更：保留旧配置，快速恢复
- CI/CD：使用蓝绿部署概念，新版本有问题可切回旧版本
- WebSocket：新功能开关控制，可独立关闭

## Open Questions

1. **Redis 持久化策略**: 使用 RDB 还是 AOF？考虑到数据可从数据库恢复，建议使用 RDB（每 5 分钟快照）。

2. **WebSocket 认证**: 使用 JWT token 在连接时验证，还是先匿名连接再升级？建议前者（更安全）。

3. **管理员权限**: 是否需要独立的 admin 表？建议扩展 user_profiles 表添加 role 字段。

4. **Celery Broker**: 使用 Redis 还是 RabbitMQ？建议 Redis（已安装，维护简单）。

5. **数据看板权限**: 普通管理员和超级管理员如何区分？建议先实现单一管理员角色。
