# Signal 拆分 — 云服务器部署清单

> 2026-07-03：Signal 已下线知识库 API 与前端入口，仅保留日报能力。  
> 知识库后续在 `rag-knowledge-platform` 单独部署。

## 部署状态

### 阶段 C（路由/入口下线）— 已完成

- [x] push `master`（commit `22500ff`）
- [x] GitHub Actions 部署绿
- [x] `/api/kb/documents` 返回 404
- [x] 侧栏无「知识库」入口
- [x] 访问 `/knowledge` 重定向首页
- [ ] 服务器 cron 清理 `KB_IMPORT` / `import_to_kb`（需 SSH 确认，见 §3）

### 阶段 D（物理删除孤儿文件）

- [x] 本地删除 KB/RAG 孤儿文件
- [x] 61 项 pytest 通过
- [ ] push + GitHub Actions 部署绿（本 commit）

## 1. 推送代码

```bash
git add .
git commit -m "split: remove KB routes from Signal digest platform"
git push origin master
```

GitHub Actions 会自动部署到 `43.139.133.245`（与平时相同）。

## 2. 部署后验证（在服务器或本机 curl）

```bash
# 健康检查
curl -s http://43.139.133.245:8080/health

# 日报 API 应正常
curl -s "http://43.139.133.245:8080/api/reports?page=1&page_size=1"

# 知识库 API 应返回 404
curl -s -o /dev/null -w "%{http_code}" http://43.139.133.245:8080/api/kb/documents
# 期望: 404
```

浏览器检查：

- 首页日报、搜索、收藏、归档正常
- 侧栏 **无「知识库」** 入口
- 访问 `/knowledge` 会回到首页（无独立 KB 页）

## 3. 修改服务器 cron（重要）

SSH 登录服务器后，编辑 crontab：

```bash
crontab -e
```

**删除或修改**以下与知识库相关的行（若存在）：

```cron
# 删除 KB_IMPORT（已不再支持）
0 3 * * * cd /opt/ai-industry-digest && KB_IMPORT=true python3 run.py ...

# 删除独立 KB 导入任务
0 4 * * * cd /opt/ai-industry-digest && python3 scripts/import_to_kb.py ...
```

**保留**日报采集任务，例如：

```cron
0 3 * * * cd /opt/ai-industry-digest && python3 run.py >> /opt/ai-industry-digest/daily.log 2>&1
```

（不要带 `KB_IMPORT=true`）

## 4. 环境变量

服务器 `/opt/ai-industry-digest/.env` 中的 `KB_IMPORT` 可删除，留空也不影响。

## 5. 回滚（若出问题）

```bash
cd /opt/ai-industry-digest
git log -5 --oneline
git checkout <拆分前的 commit>
pm2 restart signal-backend
```

## 6. 本地仓库清理（阶段 D 已完成）

Signal 仓库内 KB/RAG 孤儿文件已物理删除（2026-07-03）。  
RAG 相关能力请在 `rag-knowledge-platform` 单独部署。
