# 单元测试规格

## ADDED Requirements

### Requirement: JWT 验证测试

`api/services/jwt_verify.py` 中的 token 验证逻辑 SHALL 覆盖以下测试场景。

#### Scenario: 有效 token 验证
- **WHEN** 传入有效的 Supabase JWT token
- **THEN** 返回用户 UUID

#### Scenario: 无效 token 验证
- **WHEN** 传入格式错误的 token（如空字符串、损坏的 JWT）
- **THEN** 返回 None

#### Scenario: 过期 token 验证
- **WHEN** 传入已过期的 Supabase JWT token
- **THEN** 返回 None

#### Scenario: Demo 用户 token
- **WHEN** 传入 "demo_user" 字符串
- **THEN** 返回 DEMO_USER_UUID

### Requirement: 数据库操作测试

`api/models/database.py` 中的核心操作 SHALL 覆盖以下测试场景。

#### Scenario: 保存文章（正常）
- **WHEN** 调用 `save_articles` 保存新文章
- **THEN** 返回 inserted=1, skipped=0, errors=0

#### Scenario: 保存文章（重复）
- **WHEN** 调用 `save_articles` 保存已存在的文章
- **THEN** 返回 inserted=0, skipped=1, errors=0

#### Scenario: 分页查询
- **WHEN** 调用 `get_articles(page=1, page_size=10)`
- **THEN** 返回 items 长度 ≤ 10，包含 total 和 pages 字段

#### Scenario: 关键词搜索
- **WHEN** 调用 `get_articles(keyword="AI")`
- **THEN** 返回的文章标题或摘要包含 "AI"

### Requirement: API 路由测试

关键 API 路由 SHALL 覆盖以下测试场景。

#### Scenario: 获取文章列表
- **WHEN** GET `/api/articles?page=1`
- **THEN** 返回 200 状态码，包含 items 数组

#### Scenario: 获取单篇文章
- **WHEN** GET `/api/articles/{valid_id}`
- **THEN** 返回 200 状态码，包含文章详情

#### Scenario: 获取不存在的文章
- **WHEN** GET `/api/articles/{invalid_id}`
- **THEN** 返回 404 状态码

#### Scenario: 收藏文章（已登录）
- **WHEN** POST `/api/auth/bookmarks` 带有效 token
- **THEN** 返回 200 状态码，收藏创建成功

### Requirement: 测试覆盖率

核心模块（jwt_verify, database.py, 主要 API 路由）SHALL 达到 70% 以上的代码覆盖率。

#### Scenario: 覆盖率检查
- **WHEN** 运行 `pytest --cov=api --cov-report=term-missing`
- **THEN** 报告显示覆盖率 ≥ 70%
