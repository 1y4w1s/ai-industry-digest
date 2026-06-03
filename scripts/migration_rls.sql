-- =============================================
-- AI Industry Digest - Supabase RLS 策略
-- 在 Supabase SQL Editor 中执行
-- =============================================

-- 启用 RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE reading_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE article_feedback ENABLE ROW LEVEL SECURITY;

-- user_profiles：用户只能看/改自己的
CREATE POLICY "user_profiles_select_own" ON user_profiles
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "user_profiles_insert_own" ON user_profiles
    FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "user_profiles_update_own" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- bookmarks：用户只能看/改自己的
CREATE POLICY "bookmarks_select_own" ON bookmarks
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "bookmarks_insert_own" ON bookmarks
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "bookmarks_delete_own" ON bookmarks
    FOR DELETE USING (auth.uid() = user_id);

-- reading_history：用户只能看/改自己的
CREATE POLICY "reading_history_select_own" ON reading_history
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "reading_history_insert_own" ON reading_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- article_feedback：用户只能看/改自己的
CREATE POLICY "feedback_select_own" ON article_feedback
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "feedback_insert_own" ON article_feedback
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "feedback_update_own" ON article_feedback
    FOR UPDATE USING (auth.uid() = user_id);

-- articles / daily_reports：公开可读
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "articles_select_public" ON articles
    FOR SELECT USING (true);
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;
CREATE POLICY "daily_reports_select_public" ON daily_reports
    FOR SELECT USING (true);
