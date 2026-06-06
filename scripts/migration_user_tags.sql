-- =============================================
-- Signal - 迁移脚本: user_tags 表
-- 在 Supabase SQL Editor 中执行此文件
-- 执行时间: 2026-06-06
-- =============================================

-- 用户标签画像表
-- 记录用户兴趣标签及其权重，用于个性化推荐
-- tag 值对齐 articles.tags 中的标签
CREATE TABLE IF NOT EXISTS user_tags (
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tag VARCHAR(50) NOT NULL,
    weight INTEGER DEFAULT 1,
    source VARCHAR(20) DEFAULT 'chat',  -- 'chat' | 'reading' | 'bookmark'
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, tag, source)
);

-- 按用户查询的索引
CREATE INDEX IF NOT EXISTS idx_user_tags_user ON user_tags(user_id);

-- 验证表已创建
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_name = 'user_tags';

-- 验证索引已创建
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'user_tags';
