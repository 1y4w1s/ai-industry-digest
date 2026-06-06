# Signal — 自动化部署指南

> 最后更新: 2026-06-04

---

## 两种部署方式

| 方式 | 适用场景 | 需要什么 |
|------|---------|---------|
| **一键脚本** | SSH 登录服务器后手动部署 | 服务器终端 |
| **自动部署** | 推送代码到 GitHub 后自动部署 | 配置 1 次 SSH 密钥 |

---

## 方式一：一键脚本部署

### 前置配置：确保使用 SSH URL

**首次部署前，请确保仓库使用 SSH 协议**（GitHub 不再支持 HTTPS 密码认证）：

```bash
# 查看当前远程配置
cd /opt/ai-industry-digest && git remote -v

# 如果显示 https://...，需要改为 SSH URL
git remote set-url origin git@github.com:1y4w1s/ai-industry-digest.git

# 验证 SSH 连接
ssh -T git@github.com
# 成功会显示: Hi 1y4w1s! You've successfully authenticated...
```

### 一键部署命令

在服务器上执行一条命令即可完成整套部署流程：

```bash
cd /opt/ai-industry-digest && git pull origin master && bash scripts/deploy.sh
```

脚本会自动执行：
1. `git pull origin master` — 拉取最新代码
2. `pip install -r requirements.txt` — 更新 Python 依赖
3. `cd frontend && npm run build` — 构建前端
4. 重启后端 uvicorn 服务
5. 验证服务是否启动成功

### 查看部署日志

```bash
# 查看实时部署输出
bash scripts/deploy.sh

# 查看后端运行日志
tail -f /opt/ai-industry-digest/backend.log

# 查看上次部署时间
ls -l /opt/ai-industry-digest/backend.log
```

---

## 方式二：GitHub Actions 自动部署

配置一次后，**每次推送代码到 master 分支**，服务器会自动更新。

### 前置条件：配置 SSH 密钥（仅需 1 次）

> 如果服务器上运行 `git pull` 不需要密码（当前远程 URL 已内嵌 token），则第 1 步可跳过。

#### 第 1 步：在服务器生成 SSH 密钥（可选）

```bash
# 在服务器上执行
ssh-keygen -t ed25519 -f ~/.ssh/github_actions -N ""
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
```

#### 第 2 步：查看私钥内容

```bash
cat ~/.ssh/github_actions
```

会输出类似：

```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAA...
-----END OPENSSH PRIVATE KEY-----
```

**完整复制**包括开头和结尾的 `-----BEGIN` 和 `-----END` 行。

#### 第 3 步：添加到 GitHub Secrets

1. 打开 [GitHub 仓库 Secrets 页面](https://github.com/1y4w1s/ai-industry-digest/settings/secrets/actions)
2. 点击 **New repository secret**
3. Name: `SSH_PRIVATE_KEY`
4. Secret: 粘贴上一步复制的私钥内容
5. 点击 **Add secret**

#### 第 4 步：验证

推送任意代码到 master 分支：

```bash
git push origin master
```

然后打开 [GitHub Actions 页面](https://github.com/1y4w1s/ai-industry-digest/actions)，应该能看到 **Auto Deploy** workflow 正在运行。点进去可以看到实时输出日志。

---

## 日常使用流程

### 开发 → 部署

```
本地: 修改代码 → git push origin master
                        ↓
GitHub Actions: 自动运行 Auto Deploy
                        ↓
服务器: 自动拉取 → 构建 → 重启
                        ↓
浏览器刷新 http://43.139.133.245:8080 即可看到更新
```

### 紧急回滚

如果部署后出了问题：

```bash
# 登录服务器
cd /opt/ai-industry-digest

# 回退到上一个版本
git log --oneline -5          # 查看最近 5 次提交
git reset --hard <上一版本SHA>  # 回退代码
bash scripts/deploy.sh         # 重新部署
```

---

## 服务器管理命令速查

```bash
# 部署
bash /opt/ai-industry-digest/scripts/deploy.sh

# 查看后端状态
ps aux | grep uvicorn | grep -v grep

# 查看后端日志
tail -f /opt/ai-industry-digest/backend.log

# 手动重启后端
pkill -f uvicorn
cd /opt/ai-industry-digest
nohup /home/ubuntu/.local/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# 手动运行采集
cd /opt/ai-industry-digest && python3 run.py

# 手动导入文章到知识库
cd /opt/ai-industry-digest && python3 scripts/import_to_kb.py --all

# 预览要导入的文章（不实际执行）
cd /opt/ai-industry-digest && python3 scripts/import_to_kb.py --dry-run --all

# 查看知识库导入统计
cd /opt/ai-industry-digest && python3 scripts/import_to_kb.py --stats

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 定时任务配置

### 一键配置（推荐）

在服务器上执行以下两条命令即可完成配置：

```bash
# 1. 配置定时任务（每天凌晨 3:00 全流程 + 自动导入知识库）
(crontab -l 2>/dev/null; echo "0 3 * * * cd /opt/ai-industry-digest && KB_IMPORT=true python3 run.py >> /opt/ai-industry-digest/daily.log 2>&1") | crontab -

# 2. 验证配置
crontab -l
```

### 手动编辑方式

```bash
# 编辑 crontab
crontab -e

# 在文件末尾添加以下行：
# ─────────────────────────────────
# Signal 自动采集 + 知识库导入 - 每天凌晨 3:00
0 3 * * * cd /opt/ai-industry-digest && KB_IMPORT=true python3 run.py >> /opt/ai-industry-digest/daily.log 2>&1

# 如果只需要知识库导入（不采集），每天 4:00 执行
0 4 * * * cd /opt/ai-industry-digest && python3 scripts/import_to_kb.py >> /opt/ai-industry-digest/kb_import.log 2>&1
```

### 流程说明

```
03:00  采集（RSS/Arxiv/HF）→ AI处理 → 日报生成 → 知识库导入
  ↓
03:15~03:20  全部完成
  ↓
你起床 → 打开页面 → 日报最新 ✅ + 知识库已更新 ✅
```

### 查看定时任务日志

```bash
# 查看每日采集+导入日志
tail -f /opt/ai-industry-digest/daily.log

# 查看最近一次运行情况
tail -20 /opt/ai-industry-digest/daily.log

# 知识库导入日志（单独）
tail -f /opt/ai-industry-digest/kb_import.log
```

### 管理定时任务

```bash
# 查看当前定时任务
crontab -l

# 编辑定时任务
crontab -e

# 清空定时任务
crontab -r
```

## 常见问题

### Q: 部署后页面空白 / API 502

A: 后端可能启动失败，查看日志：

```bash
tail -20 /opt/ai-industry-digest/backend.log
```

### Q: npm run build 失败

A: 检查前端依赖：

```bash
cd /opt/ai-industry-digest/frontend
npm install
npm run build
```

### Q: git pull 提示 Invalid username or token / Password authentication failed

A: GitHub 不再支持 HTTPS 密码认证，需要改用 SSH 协议：

```bash
# 查看当前远程配置
git remote -v

# 如果显示 https://...，改为 SSH URL
git remote set-url origin git@github.com:1y4w1s/ai-industry-digest.git

# 验证 SSH 连接
ssh -T git@github.com
# 成功会显示: Hi 1y4w1s! You've successfully authenticated...
```

### Q: SSH 连接失败 (Permission denied)

A: 检查 SSH 密钥是否正确配置：

```bash
# 检查是否有 SSH 密钥
ls -la ~/.ssh/

# 如果没有密钥，生成新的
ssh-keygen -t ed25519 -C "your_email@example.com"

# 将公钥添加到 GitHub
cat ~/.ssh/id_ed25519.pub
# 复制输出，粘贴到 GitHub → Settings → SSH and GPG keys
```

### Q: 自动部署没有触发

A: 检查：
1. `SSH_PRIVATE_KEY` Secret 是否已配置
2. GitHub Actions 页面是否有报错
3. 服务器是否开机

### Q: 部署后页面空白 / JS/CSS 404 (hash 文件名不匹配)

A: 每次 `npm run build` 生成的 JS/CSS 文件名 hash 不同。浏览器缓存了旧 `index.html`，引用了已经不存在的旧 hash 文件。

**解决方案 A — 浏览器端强制刷新：**
按 `Ctrl+Shift+R` (Windows) 或 `Cmd+Shift+R` (Mac) 强制刷新，跳过缓存。

**解决方案 B — 服务器端根治（推荐）：**
在 Nginx 配置中对 `index.html` 禁用缓存，这样每次部署后浏览器自动拉取新 HTML：

```nginx
location = /index.html {
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

添加到 `/etc/nginx/sites-available/default` 的 `server` 块内，然后运行 `sudo nginx -t && sudo systemctl restart nginx`。
