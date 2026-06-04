import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import ArticleCard from '../components/ArticleCard';
import Pagination from '../components/Pagination';

export default function HistoryPage({ onReadArticle }) {
  const { isLoggedIn, login } = useAuth();
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    api.getHistory(page)
      .then((data) => setHistory(data))
      .catch(() => setHistory({ items: [], total: 0, pages: 0 }))
      .finally(() => setLoading(false));
  }, [page]);

  const grouped = [];
  if (history?.items) {
    const map = {};
    const today = new Date(); today.setHours(0, 0, 0, 0);
    for (const h of history.items) {
      const d = new Date(h.read_at); d.setHours(0, 0, 0, 0);
      const diff = (today - d) / (1000 * 60 * 60 * 24);
      let label;
      if (diff === 0) label = '今天';
      else if (diff === 1) label = '昨天';
      else { const w = ['日','一','二','三','四','五','六']; label = `${(d.getMonth()+1).toString().padStart(2,'0')}/${d.getDate().toString().padStart(2,'0')} 周${w[d.getDay()]}`; }
      if (!map[label]) { map[label] = { label, items: [] }; grouped.push(map[label]); }
      map[label].items.push(h);
    }
  }

  return (
    <div className="h-full flex flex-col" style={{ background: 'var(--color-bg-white)' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '20px', paddingBottom: '32px', maxWidth: '800px' }}>
          <div className="mb-5">
            <button onClick={() => navigate('/')} style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-blue-link)', background: 'none', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', padding: 0 }}>
              ← 返回首页
            </button>
          </div>

          {!isLoggedIn ? (
            <div className="text-center py-20">
              <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: 'var(--color-bg-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-label)" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <p style={{ fontSize: '14px', color: 'var(--color-text-title)', marginBottom: '8px' }}>当前页面需要登录才能浏览</p>
              <button onClick={() => { login(); }}
                style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-blue-link)', background: 'none', border: 'none', cursor: 'pointer' }}>
                登录 / 注册
              </button>
            </div>
          ) : (<>
          <div className="mb-6" style={{ borderBottom: '1px solid var(--color-border-light)', paddingBottom: '16px' }}>
            <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: 'var(--fs-xl)', fontWeight: 700, color: 'var(--color-text-title)' }}>
              浏览历史
            </h1>
            {history && (
              <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                共 {history.total} 条记录
              </div>
            )}
          </div>

          {loading ? (
            <div className="text-center py-16">
              <div className="flex gap-1.5 justify-center mb-3">
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
              </div>
              <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>加载中...</span>
            </div>
          ) : grouped.length > 0 ? (
            <div className="space-y-6">
              {grouped.map((g) => (
                <div key={g.label}>
                  <div style={{ fontSize: 'var(--fs-sm)', fontWeight: 500, color: 'var(--color-text-title)', marginBottom: '4px', paddingBottom: '8px', borderBottom: '1px solid var(--color-border-light)' }}>
                    {g.label}
                  </div>
                  <div className="space-y-1">
                    {g.items.map((h) => (
                      <ArticleCard key={h.id || h.article_id} article={{ ...h.articles, _imp: h.articles?.importance || '' }} onSelect={onReadArticle} variant="detailed" />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-20">
              <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: 'var(--color-bg-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-label)" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p style={{ fontSize: '14px', color: 'var(--color-text-title)', marginBottom: '4px' }}>还没有浏览记录</p>
              <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>阅读文章后会自动记录在这里</p>
            </div>
          )}
          </>)}

          {history?.pages > 1 && (
            <Pagination page={page} totalPages={history.pages} onPageChange={(pg) => setPage(pg)} />
          )}
        </div>
      </div>
    </div>
  );
}
