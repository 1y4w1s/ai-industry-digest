#!/usr/bin/env python3
import os
from supabase import create_client

def main():
    url = "https://vobpkdrujixghvttgkuq.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZvYnBrZHJ1aml4Z2h2dHRna3VxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MDQ4Mjg3MiwiZXhwIjoyMDk2MDU4ODcyfQ.fHqbH-1qytRby_hF_YfNqhIEvWQxkLXCNKVmB2U5F5A"
    
    supabase = create_client(url, key)
    
    # 先测试表结构
    try:
        result = supabase.table("reading_history").select("*").limit(1).execute()
        if result.data:
            print("当前表列:", list(result.data[0].keys()))
        else:
            print("表为空")
    except Exception as e:
        print(f"查询失败: {e}")
    
    # 尝试添加列
    print("\n尝试添加列...")
    try:
        # 使用直接的方式插入数据（如果列不存在会失败）
        # 让应用代码处理这种情况
        print("检查完成")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()
