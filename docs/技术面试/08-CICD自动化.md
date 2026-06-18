# CI/CD 自动化

## 流水线架构

```
代码 Push 或 PR
    │
    ▼ GitHub Actions 触发
    │
    ├── test-backend (并行)
    │   ├── Set up Python 3.11
    │   ├── pip install -r requirements.txt
    │   ├── pytest tests/ -v --tb=short
    │   └── 57 passed ✓
    │
    ├── test-frontend (并行)
    │   ├── Set up Node.js 20
    │   ├── npm install
    │   ├── npm run build
    │   └── 构建成功 ✓
    │
    └── deploy (测试通过后)
        ├── SSH 到腾讯云服务器
        ├── git pull
        ├── pip install -r requirements.txt
        ├── cd frontend && npm install && npm run build
        ├── pm2 restart backend
        └── sudo nginx -s reload
```

## 关键配置

### CI 配置

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [master]
  pull_request:
    branches: [master]

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: python -m pytest tests/ -v --tb=short

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }

      - name: Build
        working-directory: frontend
        run: |
          npm install
          npm run build
```

### 部署配置

```yaml
# .github/workflows/deploy.yml
deploy:
  needs: [test-backend, test-frontend]
  runs-on: ubuntu-latest
  steps:
    - name: Deploy via SSH
      uses: appleboy/ssh-action@v1
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SSH_PRIVATE_KEY }}
        script: |
          cd /opt/ai-industry-digest
          git pull origin master
          pip install -r requirements.txt
          cd frontend && npm install && npm run build
          cd ..
          pm2 restart backend
          sudo nginx -s reload
```

## 定时采集配置

```yaml
# .github/workflows/daily.yml
name: Daily Collection

on:
  schedule:
    - cron: '0 22,4,10 * * *'   # UTC 22/4/10 = 北京 6/12/18
  workflow_dispatch:             # 支持手动触发
```

## 环境变量管理

敏感信息不写入代码，通过 GitHub Secrets 注入：

| Secret | 用途 |
|--------|------|
| `SUPABASE_URL` | 数据库地址 |
| `SUPABASE_KEY` | 数据库密钥 |
| `DEEPSEEK_API_KEY` | AI API 密钥 |
| `SERVER_HOST` | 服务器 IP |
| `SSH_PRIVATE_KEY` | SSH 登录密钥 |

## 面试话术

> "CI/CD 用 GitHub Actions 实现，零成本、配置简单。测试阶段前后端并行——pytest + npm build，全部通过才部署。部署时 SSH 到腾讯云，git pull → pip install → npm build → pm2 restart，约 2 分钟完成无人值守发布。定时采集每天 6/12/18 点自动运行，GitHub Secrets 管理所有敏感信息。"

## 常见问题

| 问题 | 原因 | 修复 |
|------|------|------|
| `npm ci` 失败 | lock 文件不同步 | 改用 `npm install` |
| `requirements.txt` 编码错误 | UTF-16 BOM | 重新生成 UTF-8 |
| Supabase Key 不存在 | Secrets 未配置 | 单元测试用 mock 数据 |