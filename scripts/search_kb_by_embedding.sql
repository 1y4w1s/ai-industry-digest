-- search_kb_by_embedding: 向量相似度搜索函数
--
-- 用途: 根据查询向量在知识库中检索语义相似的文档切片
-- 使用 cosine 距离（<=>）计算相似度，结果按相似度降序排列
--
-- 参数:
--   query_embedding: vector(1024) - 查询文本的向量表示（阿里云 text-embedding-v3）
--   user_id: UUID - 当前用户 ID，用于权限过滤（公开文档 OR 自己拥有的文档）
--   limit_count: INTEGER - 返回结果数量上限（默认 10）
--
-- 返回:
--   id: UUID - kb_chunks 切片 ID
--   content: TEXT - 切片文本内容
--   document_id: UUID - 所属文档 ID
--   document_name: VARCHAR(255) - 文档名称
--   file_type: VARCHAR(20) - 文档类型（text/markdown/pdf/docx）
--   is_public: BOOLEAN - 文档是否公开
--   doc_user_id: UUID - 文档所有者 ID
--   similarity: FLOAT - 相似度分数（0~1，越大越相关）
--
-- 使用示例:
--   SELECT * FROM search_kb_by_embedding(
--     '[0.1, 0.2, ...]'::vector(1024),
--     '00000000-0000-0000-0000-000000000000'::uuid,
--     5
--   );

CREATE OR REPLACE FUNCTION search_kb_by_embedding(
    query_embedding vector(1024),
    user_id UUID,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE(
    id UUID,
    content TEXT,
    document_id UUID,
    document_name VARCHAR(255),
    file_type VARCHAR(20),
    is_public BOOLEAN,
    doc_user_id UUID,
    similarity FLOAT
)
LANGUAGE plpgsql STABLE
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.content,
        c.document_id,
        d.name AS document_name,
        d.file_type,
        d.is_public,
        d.user_id AS doc_user_id,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM kb_chunks c
    JOIN kb_documents d ON c.document_id = d.id
    WHERE (d.is_public = true OR d.user_id = user_id)
      AND c.embedding IS NOT NULL
    ORDER BY c.embedding <=> query_embedding
    LIMIT limit_count;
END;
$$;
