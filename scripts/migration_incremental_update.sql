-- F-11 增量更新所需的数据库字段
-- 在 kb_documents 表中添加 version 和 content_hash 字段

ALTER TABLE IF EXISTS kb_documents 
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;

ALTER TABLE IF EXISTS kb_documents 
ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64) DEFAULT '';
