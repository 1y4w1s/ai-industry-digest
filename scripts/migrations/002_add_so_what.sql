-- 迁移脚本：为 articles 表添加 so_what 观点层字段
-- 创建时间：2026-07-10
-- 适用版本：所有环境（Supabase SQL Editor 执行）
-- 说明：so_what 可空。旧文无该字段值，查询默认 NULL，完全兼容历史数据。
--       对应改造计划 §1.2「So What / 对你意味着什么」观点层。

ALTER TABLE IF EXISTS articles
ADD COLUMN IF NOT EXISTS so_what TEXT;

COMMENT ON COLUMN articles.so_what IS '「So What / 对你意味着什么」观点层，由 AI 独立步骤生成，可空，与 summary 事实底解耦';

-- 验证迁移结果（确认列已存在且可空）：
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'articles' AND column_name = 'so_what';
