#!/bin/bash
cd /opt/ai-industry-digest
source .env

python3 << 'EOF'
import os
from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

print("添加 read_percent 列...")
try:
    supabase.sql("ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS read_percent double precision").execute()
    print("✅ read_percent 列添加成功")
except Exception as e:
    print(f"❌ 失败: {e}")

print("添加 duration_sec 列...")
try:
    supabase.sql("ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS duration_sec integer").execute()
    print("✅ duration_sec 列添加成功")
except Exception as e:
    print(f"❌ 失败: {e}")

print("迁移完成！")
EOF
