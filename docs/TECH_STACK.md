# Signal — 技术栈

> 单一真相源。所有技术选型、版本、用途在此集中记录。
> 最后更新: 2026-06-06

---

## 前端

| 技术 | 版本 | 用途 | 说明 |
|------|------|------|------|
| **React** | 18 | UI 框架 | Hooks + Context + 函数式组件，无 class component |
| **Vite** | 8 | 构建工具 | 秒级 HMR，生产构建代码分割（`React.lazy`） |
| **Tailwind CSS** | v4 | 样式框架 | 原子化 CSS + CSS 变量主题系统（亮/暗/跟随系统） |
| **React Router** | v6 | 客户端路由 | 嵌套路由 + searchParams 参数传参，10+ 路由页面 |
| **html2canvas + jsPDF** | - | PDF 导出 | 客户端渲染截图 → 自动分页 PDF |
| **SpeechSynthesis API** | 浏览器原生 | TTS 朗读 | 中文语音分段朗读，支持暂停/继续/停止 |
| **Supabase JS SDK** | v2 | 数据库 + Auth | 客户端直接连接 Supabase Auth + REST 查询 |

## 后端

| 技术 | 版本 | 用途 | 说明 |
|------|------|------|------|
| **Python** | 3.9+ | 运行时 | - |
| **FastAPI** | - | API 框架 | 异步路由 + 依赖注入 + 中间件（限流/CORS） |
| **Supabase (PostgREST)** | - | 数据库 + Auth | PostgreSQL 12+，RLS 策略，JWT 认证 |
| **Supabase JS SDK** | v2 | 服务端客户端 | `create_client()` 单例模式管理 |
| **httpx** | - | 异步 HTTP | 信息源采集 + API 代理请求 |
| **feedparser** | - | RSS 解析 | 多源标准化采集 |
| **BeautifulSoup** | - | HTML 清洗 | 提取正文内容 |
| **PyMuPDF (fitz)** | 1.24.0 | PDF 解析 | 预览前 10 页文本 |
| **python-docx** | 1.1.2 | DOCX 解析 | 提取前 50 段文本 |
| **PyJWT + cryptography** | - | JWT 验证 | JWKS 公钥 RS256 签名验证 |

## AI

| 技术 | 用途 | 说明 |
|------|------|------|
| **DeepSeek API** | 摘要生成 | 每篇文章自动生成摘要 |
| **DeepSeek API** | 标签分类 | 从预定义 11 个标签中匹配 |
| **DeepSeek API** | 重要性评分 | high / medium / low 三级 |
| **DeepSeek API** | 实体识别 + 关系抽取 | 知识库知识图谱构建 |
| **TagExtractor** | 本地标签匹配 | 字符串匹配，零 API 成本 |

## DevOps

| 技术 | 用途 | 说明 |
|------|------|------|
| **GitHub Actions** | CI/CD | `deploy.yml`（推送到 master 自动部署）+ `daily.yml`（定时采集 6:00/12:00/18:00） |
| **Nginx** | 反向代理 | 监听 8080 端口，转发 `/api/` 到 uvicorn:8000 |
| **Uvicorn** | ASGI 服务器 | 单进程部署，后台持久运行 |
| **Linux (Ubuntu)** | 生产环境 | 轻量云服务器 |
| **cron** | 定时任务 | 每天 3:00 全流程采集 + KB 导入 |
| **Supabase SQL Editor** | 数据库迁移 | 手动执行 `scripts/migration_*.sql` |
| **scripts/migrate.py** | 自动 migration | 自动发现并执行未运行的 SQL migration |

## 数据流

```
信息源 (arXiv / RSS / HF Daily)
    ↓ collector/*   (httpx + feedparser + BeautifulSoup)
原始文章
    ↓ processor/dedup.py   (URL 去重)
    ↓ processor/ai_processor.py   (DeepSeek: 摘要+标签+重要性)
    ↓ processor/reporter.py   (按重要性分组 → 日报)
Supabase DB (articles → daily_reports)
    ↓ API  →  api/routes/content.py   (FastAPI)
    ↓ client → 前端展示
         ↓
知识库自动导入:  import_to_kb.py → kb_documents → kb_chunks → kb_entities/relations
         ↓
AI 个性化推荐:   chat.py → TagExtractor → user_tags → recommend.py → RecommendationWidget
```

## 安全体系

| 层 | 措施 | 状态 |
|----|------|------|
| 认证 | Supabase Auth (JWT) + GitHub OAuth | ✅ |
| JWT 验证 | JWKS 公钥 RS256 签名验证（`jwt_verify.py`） | ✅ |
| UUID 直通防御 | 裸 UUID 不再通过认证，仅接受 JWT 签名验证或 demo-user | ✅ 新增 |
| Token 自动刷新 | 前端 401 拦截 → `refreshSession()` → 重试 → 失败跳登录 | ✅ 新增 |
| Token 过期预判 | `isTokenExpiringSoon()` 提前 5 分钟主动刷新 | ✅ 新增 |
| CORS | 白名单域名（非通配符 `*`） | ✅ |
| 限流 | 双层内存限流：`/api/` 120 req/min，`/api/auth/` 30 req/min | ✅ 增强 |
| XSS | DOMPurify 清洗 AI 回复 HTML | ✅ |
| 路径穿越 | 服务端确定扩展名（`EXTENSION_MAP`） | ✅ |
| 认证一致性 | 统一 `verify_token()` 支持 Header + Query token | ✅ |
| 数据库连接 | 单例 `get_db()` 防连接池耗尽 | ✅ |

## 文件结构

```
ai-industry-digest/
├── api/                    # 后端
│   ├── main.py            # FastAPI 入口（路由注册 + 中间件 + 健康检查）
│   ├── models/database.py # DatabaseManager 单例 + Tables 常量
│   ├── routes/            # API 路由
│   │   ├── content.py     # 文章/日报/搜索/代理
│   │   ├── auth.py        # 用户/收藏/历史/画像/统计
│   │   ├── chat.py        # AI 对话 + 标签提取
│   │   ├── kb.py          # 知识库 CRUD + 预览/下载/图谱
│   │   └── recommend.py   # 个性化推荐
│   └── services/          # 服务层
│       ├── jwt_verify.py  # JWT 验证工具
│       └── tag_extractor.py # 标签匹配
├── frontend/src/           # 前端
│   ├── App.jsx            # 路由 + 代码分割
│   ├── api/client.js      # API 客户端
│   ├── components/        # 15+ 通用组件
│   ├── pages/             # 9 个页面
│   ├── context/           # Auth + Theme
│   ├── hooks/             # useReport + useFilter
│   ├── lib/               # supabase.js + token.js
│   └── utils/             # cache.js + date.js + markdown.js
├── collector/              # 信息源采集
├── processor/              # AI 处理 + 日报生成
├── scripts/                # 部署/迁移/备份
├── docs/                   # 文档
│   ├── TECH_STACK.md      # ← 你现在在这
│   ├── ops/               # 部署与运维
│   └── design/            # 设计文档
├── tests/                  # 42 项测试（41 passed, 1 skipped）
└── 任务书.md              # 整改任务跟踪
```
