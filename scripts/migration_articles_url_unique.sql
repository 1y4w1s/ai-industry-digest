-- Signal · 为 articles.url 添加唯一约束
-- 用途：支持批量 upsert 去重，替代逐条 select+insert 模式
-- 前置条件：需确保当前数据无重复 url（若有重复需先清理）
--
-- 注意：Supabase SQL Editor 或 psql 均可执行

-- 1. 先清理重复的 url（保留最新的一条）
DELETE FROM articles a1 USING (
  SELECT url, MIN(id) as min_id
  FROM articles
  GROUP BY url
  HAVING COUNT(*) > 1
) a2
WHERE a1.url = a2.url AND a1.id != a2.min_id;

-- 2. 添加唯一约束
ALTER TABLE articles ADD CONSTRAINT articles_url_key UNIQUE (url);
