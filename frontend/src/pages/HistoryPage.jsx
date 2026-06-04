import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import ArticleCard from '../components/ArticleCard';
import Pagination from '../components/Pagination';

export default function HistoryPage({ onReadArticle }) {
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

  // Group by date (today / yesterday / date)
  const grouped = useMemo(() => {
    if (!history?.items) return [];
    const groups = [];
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    for (const h of history.items) {
      const d = new Date(h.read_at);
      d.setHours(0, 0, 0, 0);
      const diff = (today - d) / (1000 * 60 * 60 * 24);
      let label;
      if (diff === 0) label = '今天';
      else if (diff === 1) label = '昨天';
      else {
        const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
        label = `${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')} 周${weekdays[d.getDay()]}`;
      }
      let group = groups.find((g) => g.label === label);
      if (!group) { group = { label, items: [] }; groups.push(group); }
      group.items.push(h);
    }
    return groups;
  }, [history]);

  return (
    <div className="h-full flex flex-col" style={{ background: '#FBFCFD' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '20px', paddingBottom: '32px', maxWidth: '800px' }}>
          {/* Back link */}
          <div className="mb-5">
            <button onClick={() => navigate('/')} style={{ fontSize: '12px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', padding: 0 }}>
              ← 返回首页
            </button>
          </div>

          {/* Header */}
          <div className="mb-6" style={{ borderBottom: '1px solid #E8EAED', paddingBottom: '16px' }}>
            <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '20px', fontWeight: 700, color: '#1A1C1E' }}>
              浏览历史
            </h1>
            {history && (
              <div style={{ fontSize: '12px', color: '#686C72', marginTop: '4px' }}>
                共 {history.total} 条记录
              </div>
            )}
          </div>

          {/* List */}
          {loading ? (
            <div className="text-center py-16">
              <div className="flex gap-1.5 justify-center mb-3">
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '300ms' }} />
              </div>
              <span style={{ fontSize: '13px', color: '#686C72' }}>加载中...</span>
            </div>
          ) : grouped.length > 0 ? (
            <div className="space-y-6">
              {grouped.map((g) => (
                <div key={g.label}>
                  <div style={{ fontSize: '12px', fontWeight: 500, color: '#1A1C1E', marginBottom: '4px', paddingBottom: '8px', borderBottom: '1px solid #E8EAED' }}>
                    {g.label}
                  </div>
                  <div className="space-y-1">
                    {g.items.map((h) => (
                      <ArticleCard
                        key={h.id || h.article_id}
                        article={{ ...h.article, _imp: h.article?.importance || '' }}
                        onSelect={onReadArticle}
                        variant="detailed"
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-20">
              <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: '#F0F1F2', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8C9096" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p style={{ fontSize: '14px', color: '#1A1C1E', marginBottom: '4px' }}>还没有浏览记录</p>
              <p style={{ fontSize: '12px', color: '#686C72' }}>阅读文章后会自动记录在这里</p>
            </div>
          )}

          {history?.pages > 1 && (
            <Pagination page={page} totalPages={history.pages} onPageChange={(pg) => setPage(pg)} />
          )}
        </div>
      </div>
    </div>
  );
}
