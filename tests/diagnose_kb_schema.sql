-- =============================================
-- 知识库上传 500 错误 · 数据库 Schema 诊断
-- 在 Supabase 控制台 → SQL Editor 中运行
-- =============================================

-- 1. 检查 kb_documents 表有哪些字段
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'kb_documents'
ORDER BY ordinal_position;

-- 2. 检查 is_public 字段是否存在
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'kb_documents' AND column_name = 'is_public'
        ) THEN '✅ is_public 存在'
        ELSE '❌ is_public 缺失！需执行 migration_kb_public.sql'
    END AS is_public_check;

-- 3. 检查 content_hash 和 version 字段是否存在
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'kb_documents' AND column_name = 'content_hash'
        ) THEN '✅ content_hash 存在'
        ELSE '❌ content_hash 缺失！需执行 migration_incremental_update.sql'
    END AS content_hash_check,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'kb_documents' AND column_name = 'version'
        ) THEN '✅ version 存在'
        ELSE '❌ version 缺失！需执行 migration_incremental_update.sql'
    END AS version_check;

-- 4. 检查 kb_documents 的外键约束
SELECT
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON tc.constraint_name = ccu.constraint_name
WHERE tc.table_name = 'kb_documents'
    AND tc.constraint_type = 'FOREIGN KEY';

-- 5. 检查 RLS 策略
SELECT
    schemaname,
    tablename,
    policyname,
    cmd AS operation
FROM pg_policies
WHERE tablename = 'kb_documents'
ORDER BY policyname;

-- 6. 检查 RLS 是否启用
SELECT
    relname AS table_name,
    relrowsecurity AS rls_enabled
FROM pg_class
WHERE relname = 'kb_documents';

-- 7. 模拟插入测试（只会插入后回滚，不留下数据）
BEGIN;
    -- 尝试插入一条带 is_public 的测试记录
    INSERT INTO kb_documents (id, name, file_type, file_size, status, source, tags, is_public, created_at, updated_at)
    VALUES (
        '00000000-0000-0000-0000-000000000000',
        '_test_diagnostic.txt',
        'text',
        10,
        'pending',
        'user',
        '{}'::text[],
        TRUE,
        NOW(),
        NOW()
    );
    
    -- 如果插入成功，尝试更新 content_hash 和 version
    UPDATE kb_documents 
    SET content_hash = 'test_hash_diagnostic',
        version = 1
    WHERE id = '00000000-0000-0000-0000-000000000000';
    
    -- 删除测试数据
    DELETE FROM kb_documents WHERE id = '00000000-0000-0000-0000-000000000000';
    
    -- 如果执行到这里，说明一切正常
    RAISE NOTICE '✅ 所有操作成功！';
ROLLBACK;

-- =============================================
-- 如果诊断出问题，运行以下修复脚本：
-- =============================================
-- 
-- 修复 1: 添加 is_public 字段
-- ALTER TABLE IF EXISTS kb_documents 
-- ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT TRUE;
-- 
-- 修复 2: 添加 content_hash 和 version 字段
-- ALTER TABLE IF EXISTS kb_documents 
-- ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
-- ALTER TABLE IF EXISTS kb_documents 
-- ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64) DEFAULT '';
