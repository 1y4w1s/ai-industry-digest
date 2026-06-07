# WebSocket 实时通信规格

## ADDED Requirements

### Requirement: WebSocket 连接管理

系统 SHALL 提供 WebSocket 连接端点，支持客户端实时接收通知。

#### Scenario: 客户端连接
- **WHEN** 客户端发送 WebSocket 连接请求到 `ws://host/ws?token={jwt}`
- **THEN** 服务器验证 token 有效后，建立连接，返回成功

#### Scenario: 连接认证失败
- **WHEN** 客户端使用无效 token 连接
- **THEN** 服务器关闭连接，返回 401 错误

#### Scenario: 心跳保活
- **WHEN** 连接建立后 30 秒无消息
- **THEN** 服务器发送心跳 ping，客户端需响应 pong

#### Scenario: 断线重连
- **WHEN** 客户端连接断开
- **THEN** 客户端自动在 5 秒后尝试重连，最多重试 3 次

### Requirement: 收藏变更通知

当用户收藏/取消收藏文章时，系统 SHALL 通过 WebSocket 推送通知。

#### Scenario: 收藏文章通知
- **WHEN** 用户成功收藏文章
- **THEN** 服务器向该用户推送 `{"type": "bookmark_added", "article_id": "...", "timestamp": "..."}`

#### Scenario: 取消收藏通知
- **WHEN** 用户成功取消收藏
- **THEN** 服务器向该用户推送 `{"type": "bookmark_removed", "bookmark_id": "...", "timestamp": "..."}`

### Requirement: 浏览历史同步

当用户阅读新文章时，系统 SHALL 实时更新用户的浏览历史视图。

#### Scenario: 新阅读记录通知
- **WHEN** 用户阅读文章并记录浏览历史
- **THEN** 服务器向该用户推送 `{"type": "history_updated", "article_id": "...", "read_at": "..."}`

### Requirement: 后台任务状态通知

当 AI 摘要生成等后台任务完成时，系统 SHALL 推送任务状态。

#### Scenario: 摘要生成完成
- **WHEN** AI 摘要生成任务完成
- **THEN** 服务器向请求用户推送 `{"type": "task_completed", "task_id": "...", "result": {...}}`

### Requirement: 系统公告

管理员可以向所有在线用户发送系统公告。

#### Scenario: 发送系统公告
- **WHEN** 管理员调用管理接口发送公告
- **THEN** 所有在线用户收到 `{"type": "announcement", "title": "...", "content": "..."}`
