# -*- coding: utf-8 -*-
path = 'D:\\MyPrograms\\ai-industry-digest\\api\\models\\database.py'
text = open(path, 'r', encoding='utf8').read()

# Add repo attributes to __init__
old_init = '''    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError(
                "请设置环境变量 SUPABASE_URL 和 SUPABASE_KEY"
            )
        self.client = create_client(url, key)'''

new_init = '''    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError(
                "请设置环境变量 SUPABASE_URL 和 SUPABASE_KEY"
            )
        self.client = create_client(url, key)

        # 仓储层
        self.articles = ArticleRepository(self.client)
        self.users = UserRepository(self.client)
        self.bookmarks_obj = BookmarkRepository(self.client)
        self.chat_repo = ChatRepository(self.client)'''

if old_init in text:
    text = text.replace(old_init, new_init)
    open(path, 'w', encoding='utf8').write(text)
    print('OK: __init__ updated')
else:
    print('__init__ pattern not found')

# Now add delegation methods that route to repositories
# Add after the import section a delegation note
# Then update the save_articles method to delegate
old_save = '''    def save_articles(self, articles: List[Article]) -> dict:
        """批量写入文章到 Supabase（批量查重 + 批量 upsert）"""
        result = {"inserted": 0, "skipped": 0, "errors": 0}
        if not articles:
            return result

        # 收集所有 URL
        all_urls = [a.url for a in articles]
        existing_urls = set()

        # 分批查重（Supabase in_() 上限约 1000）
        BATCH_SIZE = 500
        for i in range(0, len(all_urls), BATCH_SIZE):
            batch = all_urls[i:i + BATCH_SIZE]
            try:
                resp = self.client.table("articles") \\
                    .select("url") \\
                    .in_("url", batch) \\
                    .execute()
                if resp.data:
                    existing_urls.update(item["url"] for item in resp.data)
            except Exception as e:
                print(f"    [DB ERROR] 批量查重失败: {e}")
                result["errors"] += 1
                # 降级：逐条处理
                return self._save_articles_fallback(articles)

        # 过滤出新文章
        new_articles = [a for a in articles if a.url not in existing_urls]
        result["skipped"] = len(articles) - len(new_articles)

        if not new_articles:
            return result

        # 分批批量插入（使用 upsert 防并发竞争）
        for i in range(0, len(new_articles), BATCH_SIZE):
            batch = new_articles[i:i + BATCH_SIZE]
            data_list = []
            for a in batch:
                data_list.append({
                    "title": a.title,
                    "url": a.url,
                    "source_name": a.source_name,
                    "raw_content": a.raw_content[:50000],
                    "summary": a.summary or "",
                    "tags": a.tags or [],
                    "importance": a.importance or "low",
                    "importance_reason": a.importance_reason or "",
                    "so_what": getattr(a, "so_what", None),
                    "source_refs": a.source_refs or [],
                    "published_at": a.published_at.isoformat() if a.published_at else None,
                })
            try:
                self.client.table("articles") \\
                    .upsert(data_list, on_conflict="url", ignore_duplicates=True) \\
                    .execute()
                result["inserted"] += len(data_list)
            except Exception as e:
                print(f"    [DB ERROR] 批量写入失败: {e}")
                result["errors"] += len(data_list)

        # 清除文章列表缓存
        if result["inserted"] > 0:
            invalidate_cache("articles:*")

        return result

    def _save_articles_fallback(self, articles: List[Article]) -> dict:
        """逐条插入（降级路径）"""
        result = {"inserted": 0, "skipped": 0, "errors": 0}
        for article in articles:
            try:
                existing = self.client.table("articles") \\
                    .select("id") \\
                    .eq("url", article.url) \\
                    .execute()
                if existing.data and len(existing.data) > 0:
                    result["skipped"] += 1
                    continue
                data = {
                    "title": article.title,
                    "url": article.url,
                    "source_name": article.source_name,
                    "raw_content": article.raw_content[:50000],
                    "summary": article.summary or "",
                    "tags": article.tags or [],
                    "importance": article.importance or "low",
                    "importance_reason": article.importance_reason or "",
                    "so_what": getattr(article, "so_what", None),
                    "source_refs": article.source_refs or [],
                    "published_at": article.published_at.isoformat() if article.published_at else None,
                }
                self.client.table("articles").insert(data).execute()
                result["inserted"] += 1
            except Exception as e:
                print(f"    [DB ERROR] 写入失败 [{article.url[:50]}...]: {e}")
                result["errors"] += 1
        if result["inserted"] > 0:
            invalidate_cache("articles:*")
        return result'''

new_save = '''    def save_articles(self, articles: List[Article]) -> dict:
        """批量写入文章（委托到 ArticleRepository）"""
        return self.articles.save_articles(articles)

    def _save_articles_fallback(self, articles: List[Article]) -> dict:
        """降级写入（委托到 ArticleRepository）"""
        return self.articles._save_articles_fallback(articles)'''

if old_save in text:
    text = text.replace(old_save, new_save)
    open(path, 'w', encoding='utf8').write(text)
    print('OK: save_articles delegated')
else:
    print('save_articles pattern not found - checking current state')
    if 'return self.articles.save_articles(articles)' in text:
        print('  already delegated')

# Add delegation for get_articles
text = text.replace(
    'def get_articles(',
    'def get_articles(self, *args, **kwargs):\n        return self.articles.get_articles(*args, **kwargs)\n\n    def _get_articles_impl('
)

open(path, 'w', encoding='utf8').write(text)
print('OK: get_articles delegated')
