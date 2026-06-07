#!/usr/bin/env python3
"""
执行数据库迁移：为 reading_history 表添加缺失的列
"""

import os
from supabase import create_client, Client

def main():
    print("=== 执行数据库迁移 ===")
    print()
    
    url = "https://vobpkdrujixghvttgkuq.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZvYnBrZHJ1aml4Z2h2dHRna3VxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDQ4Mjg3MiwiZXhwIjoyMDk2MDU4ODcyfQ.fHqbH-1qytRby_hF_YfNqhIEvWQxkLXCNKVmB2U5F5A"
    
    supabase: Client = create_client(url, key)
    
    # 查看当前列
    print("当前 reading_history 表列:")
    try:
        result = supabase.table("reading_history").select("*").limit(1).execute()
        if result.data:
            columns = list(result.data[0].keys())
            for col in columns:
                print(f"  - {col}")
        else:
            print("  (表为空)")
    except Exception as e:
        print(f"  ❌ 获取列失败: {e}")
    
    print()
    
    # 检查是否需要添加列
    columns = ['read_percent', 'duration_sec']
    for col in columns:
        if col not in result.data[0].keys():
            print(f"需要添加 {col} 列")
            
            # 使用 REST API 尝试更新（这种方式不支持 ALTER TABLE）
            # 我们需要使用其他方式
            print(f"  ⚠️ 需要手动在 Supabase 控制台执行 ALTER TABLE")
            print(f"    ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS {col} double precision;")
        else:
            print(f"{col} 列已存在")
    
    print()
    print("=== 迁移说明 ===")
    print("由于 Supabase Python SDK 的同步客户端不支持直接执行 SQL，")
    print("请在 Supabase 控制台手动执行以下 SQL：")
    print()
    print("ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS read_percent double precision;")
    print("ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS duration_sec integer;")
    print()
    print("操作步骤：")
    print("1. 登录 https://supabase.com/dashboard/project/vobpkdrujixghvttgkuq")
    print("2. 进入 SQL Editor")
    print("3. 执行上述 SQL")
    print("4. 验证：SELECT * FROM reading_history LIMIT 1;")

if __name__ == "__main__":
    main()
