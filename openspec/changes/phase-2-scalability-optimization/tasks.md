# Phase 2 实施任务清单

## 1. 环境准备

- [ ] 1.1 服务器安装 Redis
  ```bash
  ssh ubuntu@43.139.133.245
  sudo apt update && sudo apt install redis-server
  redis-cli ping  # 验证安装
  ```

- [ ] 1.2 添加 Python 依赖到 requirements.txt
  ```
  redis>=5.0.0
  pytest>=8.0.0
  pytest-asyncio>=0.23.0
  pytest-cov>=4.0.0
  ```

- [ ] 1.3 添加前端依赖到 package.json
  ```bash
  cd frontend && npm install echarts
  ```

- [ ] 1.4 配置服务器环境变量
  ```
  REDIS_URL=redis://localhost:6379
  ```

## 2. Redis 缓存层实现

- [ ] 2.1 创建缓存服务模块 `api/services/cache.py`
  - 实现 `CacheService` 类
  - 实现 `get`, `set`, `delete`, `get_stats` 方法
  - 实现缓存降级逻辑（Redis 不可用时直查数据库）

- [ ] 2.2 修改 `api/models/database.py` 集成缓存
  - `get_articles` 方法添加缓存逻辑
  - `get_or_create_profile` 方法添加缓存逻辑
  - 文章更新时清除相关缓存

- [ ] 2.3 创建缓存工具函数
  - 实现 `cache_key` 生成函数
  - 实现 `with_cache` 装饰器

- [ ] 2.4 添加缓存 API 端点
  - `GET /api/admin/cache/stats` - 获取缓存统计

- [ ] 2.5 编写缓存测试
  - 测试缓存命中/未命中
  - 测试缓存失效
  - 测试降级逻辑

## 3. 单元测试体系

- [ ] 3.1 配置 pytest
  - 更新 `pytest.ini`
  - 配置测试数据库 fixture

- [ ] 3.2 编写 JWT 验证测试 `tests/test_jwt_verify.py`
  - 测试有效 token
  - 测试无效 token
  - 测试过期 token
  - 测试 demo 用户

- [ ] 3.3 编写数据库测试 `tests/test_database.py`
  - 测试 `save_articles`
  - 测试 `get_articles` 分页
  - 测试 `get_articles` 搜索

- [ ] 3.4 编写 API 测试 `tests/test_api.py`
  - 测试 `/api/articles` 端点
  - 测试 `/api/auth/bookmarks` 端点
  - 测试 `/api/auth/history` 端点

- [ ] 3.5 配置测试覆盖率报告
  - 添加 `--cov=api` 参数
  - 配置覆盖率阈值 70%

## 4. CI/CD 流水线

- [ ] 4.1 创建 GitHub Actions 目录
  ```bash
  mkdir -p .github/workflows
  ```

- [ ] 4.2 创建 CI 流程 `.github/workflows/ci.yml`
  - Python 环境配置
  - 安装依赖
  - 运行 pytest
  - 运行 ESLint（前端）

- [ ] 4.3 创建 CD 流程 `.github/workflows/deploy.yml`
  - 触发条件：master 分支推送
  - 部署步骤：
    - SSH 到服务器
    - git pull
    - 安装依赖
    - 构建前端
    - 重启后端服务
    - 健康检查

- [ ] 4.4 配置 GitHub Secrets
  - `SERVER_HOST`: 服务器 IP
  - `SERVER_USER`: 用户名
  - `DEPLOY_KEY`: SSH 私钥

- [ ] 4.5 添加回滚脚本 `scripts/rollback.sh`
  - 回滚到上一个版本
  - 重启服务
  - 验证健康状态

## 5. WebSocket 实时通信

- [ ] 5.1 创建 WebSocket 管理器 `api/services/websocket_manager.py`
  - 实现连接管理（连接/断开/心跳）
  - 实现消息广播
  - 实现用户隔离（只推送给自己）

- [ ] 5.2 添加 WebSocket 路由 `api/routes/websocket.py`
  - `WS /ws` 端点
  - Token 验证
  - 心跳处理

- [ ] 5.3 修改收藏功能集成 WebSocket
  - 收藏/取消收藏时推送通知

- [ ] 5.4 修改浏览历史功能集成 WebSocket
  - 阅读记录更新时推送通知

- [ ] 5.5 前端 WebSocket 客户端 `frontend/src/lib/websocket.js`
  - 连接管理
  - 自动重连
  - 消息处理

- [ ] 5.6 前端 Notification 组件
  - 显示实时通知
  - 通知列表管理

## 6. 管理员数据看板

- [ ] 6.1 添加管理员 API 路由 `api/routes/admin.py`
  - `GET /api/admin/stats/overview` - 系统概览
  - `GET /api/admin/stats/users` - 用户统计
  - `GET /api/admin/stats/articles` - 文章统计
  - `GET /api/admin/stats/ai` - AI 处理统计

- [ ] 6.2 实现管理员权限控制
  - 在 `user_profiles` 表添加 `role` 字段
  - 添加 `require_admin` 装饰器
  - 在 Supabase RLS 中配置管理员策略

- [ ] 6.3 创建管理后台页面 `frontend/src/pages/AdminDashboard.jsx`
  - 系统概览卡片
  - 用户增长趋势图（ECharts 折线图）
  - 来源分布图（ECharts 饼图）
  - 热门文章列表

- [ ] 6.4 集成 ECharts
  - 安装 echarts
  - 创建 `components/LineChart.jsx`
  - 创建 `components/PieChart.jsx`
  - 创建 `components/StatsCard.jsx`

- [ ] 6.5 添加管理后台路由和权限控制
  - `/admin` 路由（仅管理员可访问）
  - 未登录重定向到登录页

## 7. 集成测试与部署

- [ ] 7.1 端到端测试
  - 测试完整用户流程
  - 测试管理员功能

- [ ] 7.2 性能测试
  - 缓存命中率测试
  - WebSocket 连接数压力测试

- [ ] 7.3 生产环境部署
  - 启动 Redis 服务
  - 配置 Redis 开机自启
  - 更新 Nginx 配置（支持 WebSocket）
  - 执行数据库迁移（添加 role 字段）

- [ ] 7.4 文档更新
  - 更新部署文档
  - 添加新功能使用说明
