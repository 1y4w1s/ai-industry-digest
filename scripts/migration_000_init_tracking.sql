-- Signal · 数据库迁移版本管理
-- 创建 _migrations 表用于追踪已执行的迁移
-- 每次执行迁移前检查该表，避免重复执行

CREATE TABLE IF NOT EXISTS _migrations (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    description TEXT,
    checksum TEXT NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    execution_ms INTEGER NOT NULL DEFAULT 0
);

-- 记录已存在的迁移（避免旧迁移重复执行）
-- 后续迁移通过 scripts/run_migrations.py 运行
