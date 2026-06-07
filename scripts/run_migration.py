#!/usr/bin/env python3
"""
执行数据库迁移：为 reading_history 表添加缺失的列
"""

import os
from supabase import create_client

def main():
    print("=== 执行数据库迁移 ===")
    print()
    
    url = "https://vobpkdrujixghvttgkuq.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZvYnBrZHJ1aml4Z2h2dHRna3VxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDQ4Mjg3MiwiZXhwIjoyMDk2MDU4ODcyfQ.fHqbH-1qytRby_hF_YfNqhIEvWQxkLXCNKVmB2U5F5A"
    
    supabase = create_client(url, key)
    
    # 添加 read_percent 列
    print("1. 添加 read_percent 列...")
    try:
        supabase.sql("ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS read_percent double precision").execute()
        print("   ✅ 成功")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    # 添加 duration_sec 列
    print("2. 添加 duration_sec 列...")
    try:
        supabase.sql("ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS duration_sec integer").execute()
        print("   ✅ 成功")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
    
    print()
    print("=== 验证表结构 ===")
    try:
        result = supabase.table("reading_history").select("*").limit(1).execute()
        if result.data:
            print("当前 reading_history 表列:")
            for col in result.data[0].keys():
                print(f"  - {col}")
        else:
            print("表为空，但列已创建")
    except Exception as e:
        print(f"❌ 验证失败: {e}")
    
    print()
    print("=== 迁移完成 ===")

if __name__ == "__main__":
    main()
