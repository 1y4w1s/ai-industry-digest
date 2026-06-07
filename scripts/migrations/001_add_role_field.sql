-- Signal - 添加管理员角色字段
-- 执行方式: 在 Supabase SQL Editor 中运行

-- 1. 添加 role 字段到 user_profiles 表
ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'user' NOT NULL;

-- 2. 添加检查约束，确保 role 只能是有效值
ALTER TABLE user_profiles 
DROP CONSTRAINT IF EXISTS valid_role;

ALTER TABLE user_profiles 
ADD CONSTRAINT valid_role CHECK (role IN ('user', 'admin'));

-- 3. 创建索引加速角色查询
CREATE INDEX IF NOT EXISTS idx_user_profiles_role ON user_profiles(role);

-- 4. 为现有用户设置默认角色（如果需要）
UPDATE user_profiles SET role = 'user' WHERE role IS NULL;

-- 5. 设置第一个管理员（替换为实际的用户 ID）
-- UPDATE user_profiles SET role = 'admin' WHERE id = 'your-user-id';

-- 查看结果
SELECT id, nickname, role FROM user_profiles LIMIT 10;
