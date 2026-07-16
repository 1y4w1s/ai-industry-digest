-- Signal · 前置迁移：创建 exec_sql RPC 函数
-- 此函数允许 migration runner (run_migrations.py) 通过 Supabase REST API 执行任意 SQL
-- 手动在 Supabase SQL Editor 执行一次即可

CREATE OR REPLACE FUNCTION exec_sql(sql_text text)
RETURNS void
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
    EXECUTE sql_text;
END;
$$;
