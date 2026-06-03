import { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function Bookmarks({ onArticleClick }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchBookmarks = (pg) => {
    setLoading(true);
    api.getBookmarks(pg).then((data) => {
      setItems(data.items || []);
      setTotal(data.total || 0);
      setPage(pg);
    }).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => { fetchBookmarks(1); }, []);

  const handleRemove = async (id, e) => {
    e.stopPropagation();
    try {
      await api.removeBookmark(id);
      fetchBookmarks(page);
    } catch {}
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="font-heading text-xl font-bold text-text-primary">我的收藏</h1>
        <p className="text-sm text-text-secondary mt-1">收藏的文章列表</p>
      </div>

      {loading ? (
        <div className="text-center text-text-tertiary py-12 text-sm">加载中...</div>
      ) : items.length === 0 ? (
        <div className="text-center text-text-tertiary py-12 text-sm">暂无收藏</div>
      ) : (
        <>
          <div className="space-y-2">
            {items.map((b) => (
              <div key={b.id} onClick={() => onArticleClick(b.article_id)} className="bg-bg-surface border border-border-primary rounded-xl p-4 cursor-pointer hover:border-accent/30 hover:bg-bg-raised transition-all group">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm text-text-primary group-hover:text-accent transition-colors">{b.articles?.title || '未知'}</h3>
                    <div className="text-xs text-text-tertiary mt-1">
                      {b.articles?.source_name} · {b.articles?.published_at?.slice(0, 10)}
                    </div>
                    {b.articles?.summary && <p className="text-xs text-text-secondary mt-2 line-clamp-2">{b.articles.summary}</p>}
                  </div>
                  <button onClick={(e) => handleRemove(b.id, e)} className="ml-3 p-1.5 text-text-tertiary hover:text-error transition-colors flex-shrink-0">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>

          {total > 20 && (
            <div className="flex justify-center gap-2 mt-6">
              <button disabled={page <= 1} onClick={() => fetchBookmarks(page - 1)} className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary disabled:opacity-40">←</button>
              <span className="px-3 py-1.5 text-xs text-text-tertiary">{page}</span>
              <button disabled={page * 20 >= total} onClick={() => fetchBookmarks(page + 1)} className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary disabled:opacity-40">→</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
