-- 迁移脚本：邮件简报订阅者表（改造计划 §1.3 退订机制落库）
-- 创建时间：2026-07-10
-- 适用版本：所有环境（Supabase SQL Editor 执行）
-- 说明：退订状态落库；退订链接携带 token，指向 API 的 /unsubscribe 落地页。
--       对应改造计划 §1.3「邮件简报 = 产品核心」的退订机制要求。

CREATE TABLE IF NOT EXISTS newsletter_subscribers (
  id BIGSERIAL PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'active',        -- active | unsubscribed
  token TEXT NOT NULL UNIQUE,
  source TEXT NOT NULL DEFAULT 'seed',          -- seed | env | cli | web
  subscribed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  unsubscribed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_newsletter_subscribers_status
  ON newsletter_subscribers (status);

COMMENT ON TABLE newsletter_subscribers IS '邮件简报订阅者；退订状态落库，退订链接带 token';
COMMENT ON COLUMN newsletter_subscribers.token IS '退订令牌，写入退订链接 ?token=';
COMMENT ON COLUMN newsletter_subscribers.status IS 'active=在订, unsubscribed=已退订';
COMMENT ON COLUMN newsletter_subscribers.source IS '订阅来源：seed=手动播种, env=CI 环境变量, cli=命令行, web=网页';

-- 验证迁移结果：
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'newsletter_subscribers';
