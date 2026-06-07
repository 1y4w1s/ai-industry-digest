-- 迁移脚本：为 reading_history 表添加缺失的列
-- 创建时间：2026-06-07
-- 适用版本：所有环境

-- 添加 read_percent 列（阅读进度百分比）
ALTER TABLE IF EXISTS reading_history
ADD COLUMN IF NOT EXISTS read_percent double precision;

-- 添加 duration_sec 列（阅读时长，单位：秒）
ALTER TABLE IF EXISTS reading_history
ADD COLUMN IF NOT EXISTS duration_sec integer;

-- 为 read_percent 创建索引（可选，根据查询需求）
-- CREATE INDEX IF NOT EXISTS idx_reading_history_read_percent ON reading_history(read_percent);

-- 更新迁移记录
-- INSERT INTO migrations (version, name, executed_at) VALUES ('20260607', 'Add read_percent and duration_sec columns', NOW());

-- 验证迁移结果
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'reading_history';
