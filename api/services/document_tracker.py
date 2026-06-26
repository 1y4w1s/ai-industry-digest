"""
文档版本追踪与增量更新服务

核心能力：
  1. 内容变更检测：通过 content_hash 判断文档是否被修改
  2. 版本管理：每次变更自动递增版本号
  3. 跳过无变更文档：避免不必要的全量重处理

使用方式：
  tracker = get_document_tracker()
  
  # 上传新文档时
  tracker.init_document(doc_id, content)
  
  # 重新处理文档时
  change = tracker.detect_change(doc_id, content)
  if change["changed"]:
      tracker.bump_version(doc_id)
      # ... 执行全量重处理
  else:
      # 跳过处理
"""

import hashlib
from typing import Dict, Any, Optional
from api.models.database import get_db


class DocumentTracker:
    """文档版本追踪器"""

    def compute_hash(self, content: str) -> str:
        """计算文档内容的 MD5 哈希值"""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def init_document(self, document_id: str, content: str) -> bool:
        """
        初始化文档追踪信息（新文档上传时调用）
        
        返回:
            True 表示成功
        """
        content_hash = self.compute_hash(content)
        db = get_db()
        db.client.table("kb_documents") \
            .update({
                "content_hash": content_hash,
                "version": 1,
            }) \
            .eq("id", document_id) \
            .execute()
        return True

    def detect_change(self, document_id: str, new_content: str) -> Dict[str, Any]:
        """
        检测文档是否有变更
        
        返回:
            {
                "changed": bool,       # 是否有变更
                "old_hash": str,       # 旧哈希
                "new_hash": str,       # 新哈希
                "current_version": int, # 当前版本号
                "skip_reason": str,    # 跳过原因（仅 changed=False 时有意义）
            }
        """
        db = get_db()
        result = db.client.table("kb_documents") \
            .select("content_hash, version") \
            .eq("id", document_id) \
            .execute()

        if not result.data:
            return {
                "changed": True,
                "old_hash": "",
                "new_hash": "",
                "current_version": 0,
                "skip_reason": "document_not_found",
            }

        doc = result.data[0]
        old_hash = doc.get("content_hash") or ""
        current_version = doc.get("version") or 0
        new_hash = self.compute_hash(new_content)

        if old_hash == new_hash:
            return {
                "changed": False,
                "old_hash": old_hash,
                "new_hash": new_hash,
                "current_version": current_version,
                "skip_reason": "内容无变更，跳过处理",
            }

        return {
            "changed": True,
            "old_hash": old_hash,
            "new_hash": new_hash,
            "current_version": current_version,
            "skip_reason": "",
        }

    def bump_version(self, document_id: str, content: str) -> int:
        """
        递增文档版本号并更新哈希
        
        返回:
            新的版本号
        """
        db = get_db()
        new_hash = self.compute_hash(content)

        # 读取当前版本号
        result = db.client.table("kb_documents") \
            .select("version") \
            .eq("id", document_id) \
            .execute()

        current_version = result.data[0].get("version", 0) if result.data else 0
        new_version = current_version + 1

        db.client.table("kb_documents") \
            .update({
                "version": new_version,
                "content_hash": new_hash,
            }) \
            .eq("id", document_id) \
            .execute()

        return new_version

    def get_document_info(self, document_id: str) -> Optional[Dict[str, Any]]:
        """获取文档的追踪信息"""
        db = get_db()
        result = db.client.table("kb_documents") \
            .select("id, name, version, content_hash, status, chunks_count") \
            .eq("id", document_id) \
            .execute()

        if not result.data:
            return None
        return result.data[0]


# 单例
_tracker = None


def get_document_tracker() -> DocumentTracker:
    """获取文档追踪器单例"""
    global _tracker
    if _tracker is None:
        _tracker = DocumentTracker()
    return _tracker
