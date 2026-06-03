-- =============================================
-- AI Industry Digest - 建表语句
-- 在 Supabase SQL Editor 中执行
-- =============================================

-- 核心内容表
-- =============================================

-- 表 1: articles（文章主表）
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source_name TEXT NOT NULL,
    raw_content TEXT,
    summary TEXT,
    tags TEXT[],
    importance TEXT CHECK (importance IN ('high', 'medium', 'low')),
    importance_reason TEXT,
    source_refs TEXT[],
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_importance ON articles(importance);
CREATE INDEX IF NOT EXISTS idx_articles_tags ON articles USING GIN(tags);

-- 表 2: daily_reports（日报索引）
CREATE TABLE IF NOT EXISTS daily_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_date DATE UNIQUE NOT NULL,
    article_ids UUID[],
    summary_insight TEXT,
    trending_keywords TEXT[],
    trend_analysis TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_reports_date ON daily_reports(report_date DESC);
