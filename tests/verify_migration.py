"""
验证数据库迁移是否已成功执行
用 supabase Python 客户端直连检查，无需 psql
"""

import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client


def main():
    print("=" * 60)
    print("  数据库迁移验证")
    print("=" * 60)

    # 连接数据库
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("\n❌ 未设置 SUPABASE_URL 或 SUPABASE_KEY")
        print("   请确保 .env 文件中包含这两项")
        sys.exit(1)
    
    client = create_client(url, key)
    print(f"\n✅ 数据库连接成功")
    print(f"   URL: {url}")

    # 获取表结构
    try:
        result = client.table("kb_documents").select("*").limit(1).execute()
        if result.data:
            columns = list(result.data[0].keys())
            print(f"\n📋 kb_documents 现有字段 ({len(columns)}个):")
            for col in columns:
                print(f"   - {col}")
        else:
            print("\n⚠️ 表存在但无数据")
            columns = []
    except Exception as e:
        print(f"\n❌ 查询失败: {e}")
        sys.exit(1)

    # 检查关键字段
    print("\n📌 迁移验证:")
    checks = {
        "is_public": "❌ 缺失（需执行 migration_kb_public.sql）",
        "content_hash": "❌ 缺失（需执行 migration_incremental_update.sql）",
        "version": "❌ 缺失（需执行 migration_incremental_update.sql）",
    }
    all_ok = True
    for field in ["is_public", "content_hash", "version"]:
        if field in columns:
            print(f"   ✅ {field} ✓")
        else:
            print(f"   ❌ {field} 缺失！")
            all_ok = False

    # 如果字段全在，模拟一次完整上传流程
    if all_ok:
        print("\n🧪 字段齐全，模拟上传流程...")
        
        test_id = str(uuid.uuid4())
        
        # 步骤 1: INSERT（带 is_public）
        try:
            client.table("kb_documents").insert({
                "id": test_id,
                "name": "_test_verify_upload.txt",
                "file_type": "text",
                "file_size": 10,
                "status": "pending",
                "source": "user",
                "tags": [],
                "is_public": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }).execute()
            print("   ✅ 步骤1: INSERT 成功（含 is_public）")
        except Exception as e:
            print(f"   ❌ 步骤1: INSERT 失败: {e}")
            sys.exit(1)

        # 步骤 2: UPDATE content_hash + version
        try:
            client.table("kb_documents").update({
                "content_hash": "test_hash_verify",
                "version": 1,
            }).eq("id", test_id).execute()
            print("   ✅ 步骤2: UPDATE content_hash + version 成功")
        except Exception as e:
            print(f"   ❌ 步骤2: UPDATE 失败: {e}")
            sys.exit(1)

        # 清理
        client.table("kb_documents").delete().eq("id", test_id).execute()
        print("   🧹 清理测试数据完成")

        print("\n" + "=" * 60)
        print("  ✅ 全部通过！知识库上传 500 问题已修复")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("  ❌ 仍有字段缺失，请执行对应 SQL 迁移")
        print("=" * 60)


if __name__ == "__main__":
    main()
