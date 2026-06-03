import { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function History({ onArticleClick }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    setLoading(true);
    api.getHistory(page).then((data) => {
      setItems(data.items || []);
      setTotal(data.total || 0);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [page]);

  return (
    <div>
      <div className="mb-6">
        <h1 className="font-heading text-xl font-bold text-text-primary">浏览历史</h1>
        <p className="text-sm text-text-secondary mt-1">你阅读过的文章</p>
      </div>

      {loading ? (
        <div className="text-center text-text-tertiary py-12 text-sm">加载中...</div>
      ) : items.length === 0 ? (
        <div className="text-center text-text-tertiary py-12 text-sm">暂无浏览记录</div>
      ) : (
        <>
          <div className="space-y-2">
            {items.map((h) => (
              <div key={h.id} onClick={() => onArticleClick(h.article_id)} className="bg-bg-surface border border-border-primary rounded-xl p-4 cursor-pointer hover:border-accent/30 hover:bg-bg-raised transition-all group">
                <h3 className="font-medium text-sm text-text-primary group-hover:text-accent transition-colors">{h.articles?.title || '未知'}</h3>
                <div className="flex items-center gap-3 mt-1.5 text-xs text-text-tertiary">
                  <span>{h.articles?.source_name}</span>
                  <span>· 浏览于 {h.read_at?.slice(0, 16).replace('T', ' ')}</span>
                </div>
                {h.articles?.summary && <p className="text-xs text-text-secondary mt-2 line-clamp-2">{h.articles.summary}</p>}
              </div>
            ))}
          </div>

          {total > 20 && (
            <div className="flex justify-center gap-2 mt-6">
              <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary disabled:opacity-40">←</button>
              <span className="px-3 py-1.5 text-xs text-text-tertiary">{page}</span>
              <button disabled={page * 20 >= total} onClick={() => setPage(page + 1)} className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary disabled:opacity-40">→</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
