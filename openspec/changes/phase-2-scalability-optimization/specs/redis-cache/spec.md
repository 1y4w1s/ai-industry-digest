# Redis 缓存层规格

## ADDED Requirements

### Requirement: 文章列表缓存

系统 SHALL 实现文章列表的 Redis 缓存，缓存 key 格式为 `articles:page:{page}:{filters_hash}`，TTL 为 5 分钟。

#### Scenario: 首次请求无缓存
- **WHEN** 用户请求文章列表，缓存不存在
- **THEN** 系统从数据库查询，存入 Redis，返回数据

#### Scenario: 缓存命中
- **WHEN** 用户请求文章列表，缓存存在且未过期
- **THEN** 系统直接从 Redis 返回，不查询数据库

#### Scenario: 缓存过期
- **WHEN** 缓存已过期（超过 5 分钟）
- **THEN** 系统重新从数据库查询，更新缓存，返回数据

#### Scenario: 数据写入后缓存失效
- **WHEN** 新文章采集完成或文章更新
- **THEN** 系统主动删除所有 `articles:*` 缓存 key

### Requirement: 会话缓存

系统 SHALL 实现用户会话信息的 Redis 缓存，缓存 key 格式为 `session:{user_id}`，TTL 为 1 小时。

#### Scenario: 获取用户会话
- **WHEN** 验证用户 token 时
- **THEN** 系统优先从 Redis 获取会话信息，未命中则查数据库并缓存

### Requirement: 缓存降级策略

当 Redis 不可用时，系统 SHALL 自动降级到直接查询数据库，不影响核心功能。

#### Scenario: Redis 连接失败
- **WHEN** Redis 服务不可用或连接超时
- **THEN** 系统捕获异常，直接查询数据库，记录错误日志

### Requirement: 缓存统计

系统 SHALL 提供缓存命中率统计接口，用于监控缓存效果。

#### Scenario: 获取缓存统计
- **WHEN** 调用 `GET /api/admin/cache/stats`
- **THEN** 返回缓存命中次数、未命中次数、命中率
