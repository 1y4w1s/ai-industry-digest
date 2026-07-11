-- 迁移脚本：留存埋点事件表（改造计划 §1.5）
-- 创建时间：2026-07-10
-- 适用版本：所有环境（Supabase SQL Editor 执行）
-- 说明：
--   - open_events    : 邮件打开追踪（仅 token 维度聚合，绝不写 IP/UA，隐私合规）
--   - newsletter_sends: 发送事件（打开率的分母；同一 issue 幂等，不重复计）
-- 复用 §1.3 的 newsletter_subscribers 表做退订统计，不新增冲突的退订表。

-- 1) 打开事件表：token（=退订令牌，非邮箱）+ article（=简报日期 YYYY-MM-DD）
--    刻意不存 IP / User-Agent / 设备指纹 —— 只做"聚合打开"统计，不定位个人。
CREATE TABLE IF NOT EXISTS open_events (
  id BIGSERIAL PRIMARY KEY,
  token TEXT NOT NULL,                 -- 订阅者退订 token（与 newsletter_subscribers 一致）
  article TEXT NOT NULL,               -- 文章/期标识；本期用简报日期 YYYY-MM-DD
  opened_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_open_events_token_article
  ON open_events (token, article, opened_at);

COMMENT ON TABLE open_events IS '邮件打开追踪；仅 token+article 维度，不存 IP/UA（隐私合规）';
COMMENT ON COLUMN open_events.token IS '订阅者退订令牌，复用 newsletter_subscribers.token';
COMMENT ON COLUMN open_events.article IS '期标识，本期=简报日期 YYYY-MM-DD';

-- 2) 发送事件表：每条成功发出的简报记一行，作为打开率分母
CREATE TABLE IF NOT EXISTS newsletter_sends (
  id BIGSERIAL PRIMARY KEY,
  token TEXT NOT NULL,                 -- 订阅者退订 token
  issue_date TEXT NOT NULL,            -- 简报日期 YYYY-MM-DD（幂等键一部分）
  sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- (token, issue_date) 唯一：重跑同一期简报不会重复计入分母
CREATE UNIQUE INDEX IF NOT EXISTS uq_newsletter_sends_token_issue
  ON newsletter_sends (token, issue_date);

CREATE INDEX IF NOT EXISTS idx_newsletter_sends_sent_at
  ON newsletter_sends (sent_at);

COMMENT ON TABLE newsletter_sends IS '简报发送事件；打开率分母；同 (token,issue_date) 幂等';
COMMENT ON COLUMN newsletter_sends.issue_date IS '简报日期 YYYY-MM-DD';

-- 3) 验证迁移结果：
-- SELECT table_name FROM information_schema.tables
-- WHERE table_name IN ('open_events','newsletter_sends');
