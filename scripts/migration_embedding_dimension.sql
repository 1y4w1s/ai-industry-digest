-- 修改 kb_chunks 表的 embedding 字段维度为 1024（阿里云 text-embedding-v3 返回的维度）

-- 1. 首先删除旧的索引（如果存在）
DROP INDEX IF EXISTS idx_kb_chunks_embedding;

-- 2. 修改向量维度
ALTER TABLE kb_chunks ALTER COLUMN embedding TYPE vector(1024);

-- 3. 重新创建索引
CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding 
ON kb_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 4. 验证修改
SELECT typname, typlen FROM pg_type WHERE typname = 'vector';
SELECT attname, atttypmod FROM pg_attribute WHERE attrelid = 'kb_chunks'::regclass AND attname = 'embedding';

-- 输出示例:
--  vector | 1024
--  embedding | 1024
