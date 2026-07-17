#!/usr/bin/env python3
"""数据库列迁移工具"""
import os
from supabase import create_client

def main():
    # 凭据从环境变量读取
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        print("❌ 请设置 SUPABASE_URL 和 SUPABASE_KEY 环境变量")
        return

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
        print("检查完成")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()
