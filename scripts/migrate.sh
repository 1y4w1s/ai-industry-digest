#!/bin/bash
# 数据库迁移脚本
# 用法: SUPABASE_URL=your_url SUPABASE_KEY=your_key ./scripts/migrate.sh

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
  echo "❌ 请设置 SUPABASE_URL 和 SUPABASE_KEY 环境变量"
  echo "用法: SUPABASE_URL=... SUPABASE_KEY=... $0"
  exit 1
fi

curl -X POST "$SUPABASE_URL/rest/v1/rpc/execute_sql" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"sql": "ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS read_percent double precision"}'

echo ""
echo "---"

curl -X POST "$SUPABASE_URL/rest/v1/rpc/execute_sql" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"sql": "ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS duration_sec integer"}'

echo ""
echo "迁移完成！"
