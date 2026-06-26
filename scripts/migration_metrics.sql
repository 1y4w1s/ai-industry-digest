-- F-15 监控指标表
-- 存储每次检索、重排序、压缩、路由的性能指标和质量数据
-- 单表设计，JSONB 字段支持灵活的指标结构

CREATE TABLE IF NOT EXISTS kb_metrics (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_type         VARCHAR(32)  NOT NULL,   -- search / rerank / compress / route / error / request
    user_id             VARCHAR(64)  DEFAULT '',
    query               TEXT         DEFAULT '',
    created_at          TIMESTAMP    DEFAULT NOW(),

    -- 时间指标（毫秒）
    latency_ms          INTEGER      DEFAULT 0,

    -- 检索指标
    vector_count        INTEGER      DEFAULT 0,
    keyword_count       INTEGER      DEFAULT 0,
    graph_count         INTEGER      DEFAULT 0,
    final_count         INTEGER      DEFAULT 0,
    top_scores          JSONB        DEFAULT '[]'::jsonb,
    route               VARCHAR(16)  DEFAULT '',
    mode                VARCHAR(16)  DEFAULT '',   -- hybrid / vector_only / keyword_only / graph_only / recommend

    -- 重排序指标
    pre_rerank_top1_score   REAL     DEFAULT 0,
    post_rerank_top1_score  REAL     DEFAULT 0,
    rerank_delta            REAL     DEFAULT 0,     -- post - pre

    -- 压缩指标
    original_chars      INTEGER      DEFAULT 0,
    compressed_chars    INTEGER      DEFAULT 0,
    compress_mode       VARCHAR(16)  DEFAULT '',

    -- 路由指标
    intent_type         VARCHAR(16)  DEFAULT '',
    limit_mult          REAL         DEFAULT 1.0,
    needs_time_filter   BOOLEAN      DEFAULT FALSE,

    -- 错误信息
    error_msg           TEXT         DEFAULT '',
    extra               JSONB        DEFAULT '{}'::jsonb
);

-- 按类型和时间查询
CREATE INDEX IF NOT EXISTS idx_metrics_type_ts ON kb_metrics (metric_type, created_at DESC);

-- 按用户查询
CREATE INDEX IF NOT EXISTS idx_metrics_user_ts ON kb_metrics (user_id, created_at DESC);

-- 按路由意图查询
CREATE INDEX IF NOT EXISTS idx_metrics_route_ts ON kb_metrics (route, created_at DESC);
