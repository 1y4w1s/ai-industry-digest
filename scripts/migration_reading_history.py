#!/usr/bin/env python3
"""
迁移脚本：为 reading_history 表添加缺失的列
"""

import os
from supabase import create_client

def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("错误：请设置环境变量 SUPABASE_URL 和 SUPABASE_KEY")
        return
    
    supabase = create_client(url, key)
    
    # 添加 read_percent 列
    print("尝试添加 read_percent 列...")
    try:
        result = supabase.client.execute(
            "ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS read_percent double precision"
        )
        print("✅ read_percent 列添加成功")
    except Exception as e:
        print(f"❌ 添加 read_percent 列失败: {e}")
    
    # 添加 duration_sec 列
    print("尝试添加 duration_sec 列...")
    try:
        result = supabase.client.execute(
            "ALTER TABLE reading_history ADD COLUMN IF NOT EXISTS duration_sec integer"
        )
        print("✅ duration_sec 列添加成功")
    except Exception as e:
        print(f"❌ 添加 duration_sec 列失败: {e}")
    
    print("\n迁移完成！")

if __name__ == "__main__":
    main()
