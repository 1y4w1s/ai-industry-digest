-- Signal · 搜索引擎优化 Phase 1
-- 1. 启用 pg_trgm 扩展，加速 ILIKE 模糊搜索
-- 2. 添加 trigram GIN 索引
-- 3. 创建全文搜索 RPC 函数，支持 ts_rank 相关性排序
-- 4. 更新 search_vector 包含 source_name

-- 在 Supabase SQL Editor 中执行

-- ============================================================
-- Part 1: pg_trgm 扩展 + GIN 索引
-- ============================================================
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 为 title 和 source_name 创建 trigram 索引（加速 ILIKE %keyword%）
CREATE INDEX IF NOT EXISTS idx_articles_title_trgm ON articles USING GIN (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_articles_source_trgm ON articles USING GIN (source_name gin_trgm_ops);

-- ============================================================
-- Part 2: 全文搜索 RPC 函数
-- ============================================================
-- 返回按 ts_rank 排序的搜索结果（Supabase REST API 不支持 ts_rank，
-- 通过 RPC 绕开此限制）
CREATE OR REPLACE FUNCTION search_articles_ranked(
    search_query text,
    result_limit int DEFAULT 50,
    result_offset int DEFAULT 0
)
RETURNS TABLE(
    id uuid,
    title text,
    url text,
    source_name text,
    summary text,
    tags jsonb,
    importance text,
    importance_reason text,
    so_what text,
    source_refs jsonb,
    published_at timestamptz,
    raw_content text,
    created_at timestamptz,
    search_vector tsvector,
    rank real
)
LANGUAGE plpgsql STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id, a.title, a.url, a.source_name, a.summary,
        a.tags, a.importance, a.importance_reason, a.so_what,
        a.source_refs, a.published_at, a.raw_content, a.created_at,
        a.search_vector,
        ts_rank(a.search_vector, plainto_tsquery('simple', search_query)) AS rank
    FROM articles a
    WHERE
        a.search_vector @@ plainto_tsquery('simple', search_query)
        OR a.title ILIKE '%' || search_query || '%'
        OR a.source_name ILIKE '%' || search_query || '%'
    ORDER BY
        CASE WHEN a.search_vector @@ plainto_tsquery('simple', search_query)
             THEN ts_rank(a.search_vector, plainto_tsquery('simple', search_query))
             ELSE 0.1
        END * CASE a.importance
            WHEN 'high' THEN 3.0
            WHEN 'medium' THEN 2.0
            ELSE 1.0
        END DESC,
        a.published_at DESC
    LIMIT result_limit
    OFFSET result_offset;
END;
$$;

-- 计数函数（分页用）
CREATE OR REPLACE FUNCTION search_articles_count(
    search_query text
)
RETURNS integer
LANGUAGE plpgsql STABLE
AS $$
DECLARE
    total integer;
BEGIN
    SELECT COUNT(*) INTO total
    FROM articles a
    WHERE
        a.search_vector @@ plainto_tsquery('simple', search_query)
        OR a.title ILIKE '%' || search_query || '%'
        OR a.source_name ILIKE '%' || search_query || '%';
    RETURN total;
END;
$$;

-- ============================================================
-- Part 3: 更新 search_vector 触发器，加入 source_name
-- ============================================================
CREATE OR REPLACE FUNCTION articles_search_update()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('simple',
        COALESCE(NEW.title, '') || ' ' ||
        COALESCE(NEW.summary, '') || ' ' ||
        COALESCE(NEW.source_name, '') || ' ' ||
        COALESCE(array_to_string(NEW.tags, ' '), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 回填历史数据的 search_vector（包含 source_name）
UPDATE articles SET search_vector =
    to_tsvector('simple',
        COALESCE(title, '') || ' ' ||
        COALESCE(summary, '') || ' ' ||
        COALESCE(source_name, '') || ' ' ||
        COALESCE(array_to_string(tags, ' '), '')
    );
