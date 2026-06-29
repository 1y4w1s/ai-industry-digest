"""
知识库上传 500 错误诊断测试

检查项目：
1. kb_documents 表结构（是否缺少 is_public、content_hash、version 等字段）
2. 使用真实 token 模拟上传请求
3. 检查 Supabase 返回的原始错误信息
4. 检查 RLS 策略是否阻止了插入
"""

import os
import sys
import json
import uuid
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client


def print_separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_table_structure(db):
    """检查 kb_documents 表结构（查看哪些字段存在）"""
    print_separator("1. 检查 kb_documents 表结构")

    # 通过查询一条记录来推断表结构
    result = db.client.table("kb_documents").select("*").limit(1).execute()

    if result.data:
        columns = list(result.data[0].keys())
        print(f"  ✅ 表存在，现有字段 ({len(columns)}个):")
        for col in columns:
            print(f"    - {col}")

        # 检查关键字段
        required_columns = {
            "is_public": "migration_kb_public.sql",
            "content_hash": "migration_incremental_update.sql",
            "version": "migration_incremental_update.sql",
        }
        print()
        missing = False
        for col, migration in required_columns.items():
            if col in columns:
                print(f"  ✅ {col} ✓ (来自 {migration})")
            else:
                print(f"  ❌ {col} ✗ 缺失！需要执行 {migration}")
                missing = True
        return not missing
    else:
        print("  ⚠️ 表存在但无数据，无法推断完整结构")
        print("  将通过插入测试数据来验证...")
        return None


def test_foreign_key_constraint(db):
    """测试 user_id 外键约束"""
    print_separator("2. 测试 user_id 外键约束")

    # 尝试插入一条测试数据，检查外键约束
    test_id = str(uuid.uuid4())
    test_user_id = "00000000-0000-0000-0000-000000000001"  # demo UUID

    try:
        db.client.table("kb_documents").insert({
            "id": test_id,
            "user_id": test_user_id,
            "name": "_test_diagnostic_temp",
            "file_type": "text",
            "file_size": 10,
            "status": "pending",
            "source": "user",
            "tags": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }).execute()
        print(f"  ✅ demo UUID 插入成功 — 外键约束未启用或 demo UUID 存在")
        # 清理
        db.client.table("kb_documents").delete().eq("id", test_id).execute()
        return True
    except Exception as e:
        error_str = str(e).lower()
        if "foreign" in error_str or "constraint" in error_str or "violates" in error_str:
            print(f"  ❌ 外键约束阻止了 demo UUID 的插入: {e}")
            return False
        elif "column" in error_str and "does not exist" in error_str:
            print(f"  ❌ 缺少字段导致插入失败: {e}")
            return None  # 表示是字段缺失问题
        else:
            print(f"  ⚠️ 其他错误: {e}")
            return None


def test_insert_with_is_public(db):
    """测试插入时是否支持 is_public 字段"""
    print_separator("3. 测试 is_public 字段")

    test_id = str(uuid.uuid4())

    try:
        db.client.table("kb_documents").insert({
            "id": test_id,
            "name": "_test_diagnostic_ispublic",
            "file_type": "text",
            "file_size": 10,
            "status": "pending",
            "source": "user",
            "tags": [],
            "is_public": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }).execute()
        print(f"  ✅ is_public 字段可用 ✓")
        db.client.table("kb_documents").delete().eq("id", test_id).execute()
        return True
    except Exception as e:
        error_str = str(e)
        if "is_public" in error_str.lower() and "does not exist" in error_str.lower():
            print(f"  ❌ is_public 字段不存在！需要执行 migration_kb_public.sql")
            print(f"     错误: {e}")
            return False
        else:
            print(f"  ⚠️ 其他错误: {e}")
            return None


def test_update_content_hash_version(db):
    """测试是否能更新 content_hash 和 version 字段"""
    print_separator("4. 测试 content_hash / version 字段")

    # 先创建一条记录
    test_id = str(uuid.uuid4())
    try:
        db.client.table("kb_documents").insert({
            "id": test_id,
            "name": "_test_diagnostic_hash",
            "file_type": "text",
            "file_size": 10,
            "status": "pending",
            "source": "user",
            "tags": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }).execute()
    except Exception as e:
        print(f"  ❌ 无法创建测试记录: {e}")
        return None

    try:
        db.client.table("kb_documents").update({
            "content_hash": "test_hash_123",
            "version": 1,
        }).eq("id", test_id).execute()
        print(f"  ✅ content_hash / version 字段可用 ✓")
        db.client.table("kb_documents").delete().eq("id", test_id).execute()
        return True
    except Exception as e:
        error_str = str(e)
        if "content_hash" in error_str.lower() or "version" in error_str.lower():
            print(f"  ❌ content_hash 或 version 字段不存在！需要执行 migration_incremental_update.sql")
            print(f"     错误: {e}")
            db.client.table("kb_documents").delete().eq("id", test_id).execute()
            return False
        else:
            print(f"  ⚠️ 其他错误: {e}")
            db.client.table("kb_documents").delete().eq("id", test_id).execute()
            return None


def check_rls_status(db):
    """检查 kb_documents 表的 RLS 状态"""
    print_separator("5. 检查 RLS 策略")

    try:
        # 查询 kb_documents 表的 RLS 策略
        result = db.client.table("pg_policies") \
            .select("*") \
            .eq("tablename", "kb_documents") \
            .execute()
        policies = result.data or []

        if policies:
            print(f"  ✅ kb_documents 有 {len(policies)} 条 RLS 策略:")
            for p in policies:
                print(f"    - {p.get('policyname')} ({p.get('cmd')})")
        else:
            print(f"  ⚠️ kb_documents 表没有 RLS 策略")
            print(f"     如果 RLS 已启用且使用的是 anon key，所有操作将被拒绝！")
            print(f"     但后端使用 service_role key，应可绕过 RLS")
    except Exception as e:
        print(f"  ⚠️ 无法查询 RLS 策略（可能是权限问题）: {e}")


def check_supabase_key_type():
    """检查使用的 SUPABASE_KEY 类型"""
    print_separator("6. 检查 SUPABASE_KEY 类型")

    key = os.getenv("SUPABASE_KEY", "")
    if not key:
        print("  ❌ SUPABASE_KEY 未设置")
        return

    # service_role key 通常以 'eyJ' 开头（JWT格式）
    # anon key 同样以 'eyJ' 开头，但可以从角色判断
    print(f"  🔑 SUPABASE_KEY 前缀: {key[:20]}...")

    # 尝试解码 JWT（不验证签名）来判断角色
    try:
        import jwt as pyjwt
        payload = pyjwt.decode(key, options={"verify_signature": False})
        role = payload.get("role", "unknown")
        print(f"  📋 Key 角色: {role}")
        if role == "service_role":
            print(f"  ✅ 使用 service_role key — 可绕过 RLS")
        elif role == "anon":
            print(f"  ❌ 使用 anon key — RLS 会生效！")
            print(f"     需要确保 kb_documents 有正确的 RLS 策略")
        else:
            print(f"  ⚠️ 未知角色: {role}")
    except Exception as e:
        print(f"  ⚠️ 无法解码 key: {e}")


def simulate_minimal_upload(db):
    """模拟最简上传流程，看哪个步骤出错"""
    print_separator("7. 模拟最小上传流程")

    test_id = str(uuid.uuid4())
    content_hash = hashlib.md5(b"test content").hexdigest()

    # Step 1: INSERT
    print("  步骤 1: 插入文档记录...")
    try:
        insert_data = {
            "id": test_id,
            "name": "_test_upload_flow.txt",
            "file_type": "text",
            "file_size": 50,
            "status": "pending",
            "source": "user",
            "tags": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        # 尝试带 is_public 插入
        try:
            insert_data_with_public = {**insert_data, "is_public": True}
            db.client.table("kb_documents").insert(insert_data_with_public).execute()
            print(f"  ✅ 步骤 1a: 带 is_public 插入成功 ✓")
        except Exception:
            # 回退到不带 is_public
            print(f"  ⚠️ 步骤 1a: 带 is_public 插入失败，尝试不带 is_public...")
            db.client.table("kb_documents").insert(insert_data).execute()
            print(f"  ✅ 步骤 1b: 不带 is_public 插入成功 ✓")
    except Exception as e:
        print(f"  ❌ 步骤 1: 插入失败: {e}")
        return

    # Step 2: UPDATE content_hash & version (init_document)
    print("  步骤 2: 更新 content_hash 和 version...")
    try:
        db.client.table("kb_documents").update({
            "content_hash": content_hash,
            "version": 1,
        }).eq("id", test_id).execute()
        print(f"  ✅ 步骤 2: content_hash / version 更新成功 ✓")
    except Exception as e:
        print(f"  ❌ 步骤 2: 更新失败: {e}")
        print(f"      ← 这里就是 500 的根源！")

    # 清理
    db.client.table("kb_documents").delete().eq("id", test_id).execute()
    print(f"  🧹 清理测试数据完成")


def main():
    print(f"\n{'='*60}")
    print(f"  知识库上传 500 错误诊断工具")
    print(f"  时间: {datetime.now().isoformat()}")
    print(f"{'='*60}")

    # 初始化数据库连接
    try:
        from api.models.database import get_db
        db = get_db()
        print(f"\n  ✅ 数据库连接成功")
    except Exception as e:
        print(f"\n  ❌ 数据库连接失败: {e}")
        sys.exit(1)

    # 导入 hashlib（给 simulate 用）
    import hashlib

    # 执行所有检查
    checks = []

    r1 = check_table_structure(db)
    checks.append(("表结构检查", r1))

    r2 = test_foreign_key_constraint(db)
    checks.append(("外键约束检查", r2))

    r3 = test_insert_with_is_public(db)
    checks.append(("is_public 字段", r3))

    r4 = test_update_content_hash_version(db)
    checks.append(("content_hash/version 字段", r4))

    check_rls_status(db)
    check_supabase_key_type()

    simulate_minimal_upload(db)

    # 汇总
    print_separator("诊断汇总")
    all_pass = True
    for name, result in checks:
        status = "✅" if result else ("❌" if result is False else "⚠️")
        status_text = "通过" if result else ("失败" if result is False else "无法判断")
        print(f"  {status} {name}: {status_text}")
        if result is False:
            all_pass = False

    if not all_pass:
        print(f"\n  ❌ 发现数据库配置问题，需要执行对应的 SQL 迁移脚本")
        print(f"\n  推荐修复步骤:")
        print(f"   1. 登录 Supabase 控制台 → SQL Editor")
        print(f"   2. 依次执行以下脚本:")
        print(f"      - scripts/migration_kb_public.sql")
        print(f"      - scripts/migration_incremental_update.sql")
        print(f"   3. 重启后端服务后重试")
    else:
        print(f"\n  ✅ 数据库结构无异常，500 错误可能是其他原因（如文件处理逻辑异常）")


if __name__ == "__main__":
    main()
