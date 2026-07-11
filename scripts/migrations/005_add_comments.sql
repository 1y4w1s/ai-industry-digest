-- Signal - 文章评论区（改造计划 §3.2）
-- 仅开放，不主动运营。匿名/登录可选。
-- 基础审核/举报防垃圾：关键词过滤 + 举报标记。
--
-- 用法：在 Supabase SQL Editor 执行本文件。
-- 部署前已创建同结构表可安全重跑（含 IF NOT EXISTS）。

-- ── 评论表 ─────────────────────────────────────

CREATE TABLE IF NOT EXISTS article_comments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id      TEXT NOT NULL,  -- 应用层关联 articles(uuid)，不设 FK（类型不兼容）
    user_id         TEXT,               -- 登录用户 ID（可空，匿名评论时为空）
    author_name     TEXT DEFAULT '',    -- 匿名展示名（可选，登录用户可从 profile 自动获取）
    content         TEXT NOT NULL CHECK (char_length(content) BETWEEN 1 AND 2000),
    parent_id       UUID REFERENCES article_comments(id) ON DELETE CASCADE,  -- 回复的父评论
    is_reported     BOOLEAN NOT NULL DEFAULT FALSE,  -- 被举报标记
    is_approved     BOOLEAN NOT NULL DEFAULT TRUE,   -- 审核通过（默认通过，举报后标记为 FALSE 隐藏）
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 索引：按文章查评论（按时间倒序，先展示最新）
CREATE INDEX IF NOT EXISTS idx_comments_article_id
    ON article_comments (article_id, created_at DESC);

-- 索引：举报待审核列表
CREATE INDEX IF NOT EXISTS idx_comments_reported
    ON article_comments (is_reported, is_approved)
    WHERE is_reported = TRUE;

-- ── 评论举报表 ────────────────────────────────

CREATE TABLE IF NOT EXISTS comment_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comment_id      UUID NOT NULL REFERENCES article_comments(id) ON DELETE CASCADE,
    reason          TEXT NOT NULL CHECK (char_length(reason) BETWEEN 1 AND 500),
    reporter_token  TEXT NOT NULL DEFAULT '',       -- 匿名举报者标识（非敏感，仅防重复举报同一评论）
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (comment_id, reporter_token)             -- 同一人不得重复举报同一评论
);

CREATE INDEX IF NOT EXISTS idx_reports_comment_id
    ON comment_reports (comment_id);
