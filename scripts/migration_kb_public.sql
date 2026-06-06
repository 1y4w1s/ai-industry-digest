-- =============================================
-- Signal - 迁移: kb_documents 加 is_public 字段
-- 在 Supabase SQL Editor 中执行
-- 执行时间: 2026-06-06
-- =============================================

-- 新增公开/私有标记，默认公开
ALTER TABLE IF EXISTS kb_documents 
ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT TRUE;

-- 现有文档全部设为公开
UPDATE kb_documents SET is_public = TRUE WHERE is_public IS NULL;

-- 验证
SELECT is_public, COUNT(*) FROM kb_documents GROUP BY is_public;
