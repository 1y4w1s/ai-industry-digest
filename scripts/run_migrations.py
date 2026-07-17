#!/usr/bin/env python3
"""
Signal · 数据库迁移管理器

使用方法：
    python scripts/run_migrations.py                  # 执行所有待迁移
    python scripts/run_migrations.py --dry-run        # 仅预览不动手
    python scripts/run_migrations.py --rollback NAME  # 回滚（暂不支持）

检测 logic：
    1. 从 scripts/migration_*.sql 读取所有迁移文件
    2. 按文件名排序（前缀数字决定执行顺序）
    3. 查询 _migrations 表已执行的迁移
    4. 执行未执行的迁移并记录
"""

import os
import sys
import hashlib
import time
import argparse
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIGRATIONS_DIR = os.path.join(PROJECT_ROOT, "scripts")

# Supabase 连接配置
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ 请设置 SUPABASE_URL 和 SUPABASE_KEY 环境变量")
    sys.exit(1)

from supabase import create_client


def get_migration_files() -> list:
    """获取所有 migration 文件，按文件名排序"""
    files = []
    files = []
    # Main dir: scripts/migration_*.sql
    for f in sorted(os.listdir(MIGRATIONS_DIR)):
        if f.startswith("migration_") and f.endswith(".sql"):
            path = os.path.join(MIGRATIONS_DIR, f)
            files.append(path)
    # Subdir: scripts/migrations/*.sql
    sub_dir = os.path.join(MIGRATIONS_DIR, "migrations")
    if os.path.isdir(sub_dir):
        for f in sorted(os.listdir(sub_dir)):
            if f.endswith(".sql"):
                path = os.path.join(sub_dir, f)
                files.append(path)
    for path in files:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
            files.append({
                "filename": f,
                "path": path,
                "content": content,
                "checksum": hashlib.sha256(content.encode()).hexdigest()[:16],
            })
    return files


def ensure_tracking_table(db):
    """确保 _migrations 表存在"""
    try:
        db.table("_migrations").select("id").limit(1).execute()
    except Exception:
        # 表不存在，运行初始化迁移
        init_file = os.path.join(MIGRATIONS_DIR, "migration_000_init_tracking.sql")
        if os.path.exists(init_file):
            with open(init_file, "r") as f:
                sql = f.read()
            # 通过 raw SQL 执行（需要 Supabase SQL endpoint）
            db.rpc("exec_sql", {"sql_text": sql}).execute()


def get_executed_migrations(db) -> set:
    """获取已执行的迁移文件名集合"""
    try:
        result = db.table("_migrations").select("filename").execute()
        return {row["filename"] for row in (result.data or [])}
    except Exception:
        return set()


def execute_migration(db, migration: dict, dry_run: bool = False) -> bool:
    """执行单个迁移文件"""
    filename = migration["filename"]
    print(f"\n{'='*60}")
    print(f"📦 {filename}")
    print(f"   checksum: {migration['checksum']}")
    print(f"   size: {len(migration['content'])} bytes")
    print(f"{'='*60}")

    if dry_run:
        print("   ⏸️  dry-run 模式，跳过执行")
        return True

    # 执行 SQL
    start = time.time()
    try:
        # 尝试通过 RPC 执行（需要预先创建 exec_sql 函数）
        db.rpc("exec_sql", {"sql_text": migration["content"]}).execute()
    except Exception:
        # 降级：逐条执行（按 ; 分割）
        statements = [s.strip() for s in migration["content"].split(";") if s.strip()]
        for stmt in statements:
            try:
                db.rpc("exec_sql", {"sql_text": stmt + ";"}).execute()
            except Exception as e:
                print(f"   ⚠️  语句执行警告（可能已存在）: {e}")

    elapsed = int((time.time() - start) * 1000)
    print(f"   ✅ 完成 ({elapsed}ms)")

    # 记录到 _migrations 表
    try:
        db.table("_migrations").insert({
            "filename": filename,
            "description": filename.replace("migration_", "").replace(".sql", "").replace("_", " "),
            "checksum": migration["checksum"],
            "execution_ms": elapsed,
        }).execute()
    except Exception as e:
        print(f"   ⚠️  记录迁移日志失败: {e}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Signal 数据库迁移管理器")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不执行")
    args = parser.parse_args()

    print("🔧 Signal 数据库迁移管理器")
    print(f"   迁移目录: {MIGRATIONS_DIR}")
    print(f"   {'DRY-RUN 模式' if args.dry_run else '执行模式'}")

    # 连接数据库
    print("\n📡 连接数据库...")
    db = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("   连接成功")

    # 获取迁移文件
    migrations = get_migration_files()
    print(f"\n📋 发现 {len(migrations)} 个迁移文件")

    # 获取已执行记录
    executed = get_executed_migrations(db)
    print(f"✅ 已执行 {len(executed)} 个")
    print(f"⏳ 待执行 {len(migrations) - len([m for m in migrations if m['filename'] not in executed])} 个")

    # 执行未执行的迁移
    executed_count = 0
    for m in migrations:
        if m["filename"] not in executed:
            ok = execute_migration(db, m, dry_run=args.dry_run)
            if ok:
                executed_count += 1

    print(f"\n{'='*60}")
    if args.dry_run:
        print(f"⏸️  预览完成，{executed_count} 个迁移可执行")
    else:
        print(f"✅ 完成，{executed_count} 个迁移已执行")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
