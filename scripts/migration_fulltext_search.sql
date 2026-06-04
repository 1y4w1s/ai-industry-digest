-- =============================================
-- Signal - 全文搜索迁移
-- 在 Supabase SQL Editor 中执行
-- =============================================

-- 为 articles 表添加 tsvector 列
ALTER TABLE articles ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- 创建全文搜索索引（支持中文 + 英文）
CREATE INDEX IF NOT EXISTS idx_articles_search ON articles USING GIN(search_vector);

-- 创建触发器函数：自动更新 search_vector
CREATE OR REPLACE FUNCTION articles_search_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector := to_tsvector('simple', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.summary, '') || ' ' || COALESCE(array_to_string(NEW.tags, ' '), ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 创建触发器
DROP TRIGGER IF EXISTS trg_articles_search ON articles;
CREATE TRIGGER trg_articles_search
  BEFORE INSERT OR UPDATE ON articles
  FOR EACH ROW EXECUTE FUNCTION articles_search_update();

-- 为已有数据建立索引
UPDATE articles SET search_vector = to_tsvector('simple', COALESCE(title, '') || ' ' || COALESCE(summary, '') || ' ' || COALESCE(array_to_string(tags, ' '), ''));
