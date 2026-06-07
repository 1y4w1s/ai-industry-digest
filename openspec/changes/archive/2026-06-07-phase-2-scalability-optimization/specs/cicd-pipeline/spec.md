# CI/CD 流水线规格

## ADDED Requirements

### Requirement: PR 检查流水线

每当创建或更新 Pull Request，流水线 SHALL 自动运行以下检查。

#### Scenario: PR 创建触发检查
- **WHEN** 开发者创建 PR 或 push 新提交
- **THEN** GitHub Actions 自动触发 CI 检查

#### Scenario: Python 测试
- **WHEN** CI 流水线运行
- **THEN** 执行 `pytest tests/ --tb=short`，失败则阻止合并

#### Scenario: 前端构建
- **WHEN** 前端代码变更（frontend/** 或 package.json）
- **THEN** 执行 `cd frontend && npm install && npm run build`，失败则阻止合并

#### Scenario: 代码格式检查
- **WHEN** CI 流水线运行
- **THEN** 执行 ESLint 检查，失败则阻止合并

### Requirement: 主分支部署流水线

当代码合并到 master 分支时，流水线 SHALL 自动部署到生产服务器。

#### Scenario: Master 分支推送触发部署
- **WHEN** 代码合并到 master
- **THEN** GitHub Actions 自动执行部署流程

#### Scenario: 自动拉取代码
- **WHEN** 部署流程开始
- **THEN** SSH 到服务器执行 `git pull origin master`

#### Scenario: 依赖更新
- **WHEN** requirements.txt 或 package.json 变更
- **THEN** 自动执行 `pip install -r requirements.txt` 和 `npm install`

#### Scenario: 前端构建
- **WHEN** 前端代码变更
- **THEN** 执行 `cd frontend && npm run build`

#### Scenario: 后端服务重启
- **WHEN** 后端代码变更
- **THEN** 重启 uvicorn 进程

#### Scenario: 部署验证
- **WHEN** 部署完成后
- **THEN** 发送 HTTP 请求到 `/health` 端点验证服务可用

### Requirement: 部署通知

部署完成后，系统 SHALL 发送通知。

#### Scenario: 部署成功通知
- **WHEN** 部署验证通过
- **THEN** 在 GitHub PR 中添加部署成功评论，包含部署时间和版本

#### Scenario: 部署失败通知
- **WHEN** 部署验证失败
- **THEN** 发送 Slack/飞书通知，包含错误日志摘要

### Requirement: 回滚机制

当部署失败时，流水线 SHALL 支持快速回滚。

#### Scenario: 手动回滚触发
- **WHEN** 开发者添加 `deploy: rollback` 标签到 commit
- **THEN** 流水线回滚到上一个稳定版本

#### Scenario: 自动回滚条件
- **WHEN** 健康检查连续 3 次失败
- **THEN** 流水线自动回滚到上一个版本
