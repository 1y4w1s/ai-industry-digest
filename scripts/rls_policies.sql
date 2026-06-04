-- ============================================================
-- Signal - Supabase RLS 策略配置
-- 执行方式：Supabase 控制台 → SQL Editor → 粘贴执行
-- 日期：2026-06-04
-- ============================================================

-- 1. bookmarks 表：用户只能管理自己的收藏
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "用户查看自己的收藏" ON bookmarks
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "用户添加自己的收藏" ON bookmarks
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "用户删除自己的收藏" ON bookmarks
  FOR DELETE
  USING (auth.uid() = user_id);

-- 2. reading_history 表：用户只能管理自己的历史
ALTER TABLE reading_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "用户查看自己的历史" ON reading_history
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "用户添加自己的历史" ON reading_history
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "用户删除自己的历史" ON reading_history
  FOR DELETE
  USING (auth.uid() = user_id);

-- 3. article_feedback 表：用户只能管理自己的反馈
ALTER TABLE article_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "用户查看自己的反馈" ON article_feedback
  FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "用户提交/更新自己的反馈" ON article_feedback
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "用户更新自己的反馈" ON article_feedback
  FOR UPDATE
  USING (auth.uid() = user_id);

-- 4. user_profiles 表：用户只能查看和更新自己的资料
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "用户查看自己的资料" ON user_profiles
  FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "用户更新自己的资料" ON user_profiles
  FOR UPDATE
  USING (auth.uid() = id);

-- 5. articles 表：不开放给前端（仅后端 service_role 访问）
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
-- 不创建任何策略 = 默认拒绝所有 from anon key

-- 6. daily_reports 表：不开放给前端（仅后端 service_role 访问）
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;
-- 不创建任何策略 = 默认拒绝所有 from anon key

-- ============================================================
-- 验证：查看已启用的 RLS 策略
-- ============================================================
SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual
FROM pg_policies
WHERE tablename IN ('bookmarks', 'reading_history', 'article_feedback', 'user_profiles', 'articles', 'daily_reports')
ORDER BY tablename, policyname;
