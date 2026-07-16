-- Signal · 中文分词支持
-- 新增 search_text 列（预分词后的搜索文本）
-- 更新 trigger 使用 search_text
-- 历史数据回填

-- 1. 新增 search_text 列
ALTER TABLE articles ADD COLUMN IF NOT EXISTS search_text TEXT;

-- 2. 更新 trigger 函数，优先使用 search_text
CREATE OR REPLACE FUNCTION articles_search_update()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('simple',
        COALESCE(NEW.search_text, '') || ' ' ||
        COALESCE(NEW.title, '') || ' ' ||
        COALESCE(NEW.summary, '') || ' ' ||
        COALESCE(NEW.source_name, '') || ' ' ||
        COALESCE(array_to_string(NEW.tags, ' '), '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 3. 更新 RPC 函数，加入 search_text 搜索
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
        OR COALESCE(a.search_text, '') ILIKE '%' || search_query || '%'
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

-- 4. 更新计数函数
CREATE OR REPLACE FUNCTION search_articles_count(search_query text)
RETURNS integer
LANGUAGE plpgsql STABLE
AS $$
DECLARE total integer;
BEGIN
    SELECT COUNT(*) INTO total
    FROM articles a
    WHERE
        a.search_vector @@ plainto_tsquery('simple', search_query)
        OR a.title ILIKE '%' || search_query || '%'
        OR a.source_name ILIKE '%' || search_query || '%'
        OR COALESCE(a.search_text, '') ILIKE '%' || search_query || '%';
    RETURN total;
END;
$$;
