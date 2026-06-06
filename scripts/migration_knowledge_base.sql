-- 知识库文档表
CREATE TABLE IF NOT EXISTS kb_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_size INTEGER,
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 文档切片表
CREATE TABLE IF NOT EXISTS kb_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES kb_documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 实体表（用于知识图谱）
CREATE TABLE IF NOT EXISTS kb_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES kb_documents(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- concept, person, organization, technology
    created_at TIMESTAMP DEFAULT NOW()
);

-- 关系表（用于知识图谱）
CREATE TABLE IF NOT EXISTS kb_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES kb_documents(id) ON DELETE CASCADE,
    source_entity_id UUID REFERENCES kb_entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES kb_entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(100), -- is_a, part_of, related_to, based_on
    label VARCHAR(100), -- 中文标签
    created_at TIMESTAMP DEFAULT NOW()
);

-- 关系表索引
CREATE INDEX IF NOT EXISTS idx_kb_relations_document_id ON kb_relations(document_id);

-- 实体-切片关联表
CREATE TABLE IF NOT EXISTS kb_entity_chunks (
    entity_id UUID REFERENCES kb_entities(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES kb_chunks(id) ON DELETE CASCADE,
    PRIMARY KEY (entity_id, chunk_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_kb_documents_user_id ON kb_documents(user_id);
CREATE INDEX IF NOT EXISTS idx_kb_chunks_document_id ON kb_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_kb_entities_document_id ON kb_entities(document_id);
CREATE INDEX IF NOT EXISTS idx_kb_relations_source ON kb_relations(source_entity_id);
CREATE INDEX IF NOT EXISTS idx_kb_relations_target ON kb_relations(target_entity_id);
