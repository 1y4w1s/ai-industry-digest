# 管理员数据看板规格

## ADDED Requirements

### Requirement: 系统概览统计

管理员 SHALL 能够查看系统整体运行数据。

#### Scenario: 查看系统概览
- **WHEN** 管理员访问 `GET /api/admin/stats/overview`
- **THEN** 返回包含以下数据的 JSON：
  - `total_users`: 用户总数
  - `total_articles`: 文章总数
  - `total_bookmarks`: 收藏总数
  - `total_reads`: 浏览记录总数
  - `daily_active_users`: 今日活跃用户数
  - `articles_this_week`: 本周新增文章数

### Requirement: 用户增长趋势

管理员 SHALL 能够查看用户增长趋势数据。

#### Scenario: 查看用户趋势
- **WHEN** 管理员访问 `GET /api/admin/stats/users?period=30d`
- **THEN** 返回包含每日新增用户数的数组 `[{"date": "2024-01-01", "count": 5}, ...]`

#### Scenario: 用户分布统计
- **WHEN** 管理员访问 `GET /api/admin/stats/users/distribution`
- **THEN** 返回用户注册来源分布（邮箱域名统计）

### Requirement: 内容统计

管理员 SHALL 能够查看内容相关的统计数据。

#### Scenario: 来源文章统计
- **WHEN** 管理员访问 `GET /api/admin/stats/articles/by-source`
- **THEN** 返回每个来源的文章数量分布

#### Scenario: 热门文章排行
- **WHEN** 管理员访问 `GET /api/admin/stats/articles/popular?limit=10`
- **THEN** 返回被阅读次数最多的 10 篇文章

#### Scenario: AI 处理统计
- **WHEN** 管理员访问 `GET /api/admin/stats/ai/processing`
- **THEN** 返回 AI 处理统计：
  - `total_processed`: 总处理文章数
  - `avg_processing_time`: 平均处理时长（秒）
  - `success_rate`: 成功率百分比

### Requirement: 管理员界面

系统 SHALL 提供管理员 Web 界面展示数据看板。

#### Scenario: 访问管理员页面
- **WHEN** 管理员用户访问 `/admin`
- **THEN** 显示包含以下模块的数据看板：
  - 系统概览卡片（用户、文章、收藏数量）
  - 用户增长趋势折线图
  - 来源分布饼图
  - 热门文章排行列表

#### Scenario: 实时数据更新
- **WHEN** 数据看板页面打开
- **THEN** 每 60 秒自动刷新数据

### Requirement: 管理员权限控制

普通用户 SHALL 无法访问管理员功能和界面。

#### Scenario: 非管理员用户访问
- **WHEN** 普通用户尝试访问 `/admin` 页面或 `/api/admin/*` 接口
- **THEN** 返回 403 Forbidden

#### Scenario: 未登录用户访问
- **WHEN** 未登录用户尝试访问管理员页面
- **THEN** 重定向到登录页面
