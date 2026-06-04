import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import ArticleCard from '../components/ArticleCard';
import Pagination from '../components/Pagination';

export default function SearchPage({ onReadArticle }) {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const navigate = useNavigate();

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (!query) return;
    setLoading(true);
    setPage(1);
    api.getArticles({ page: 1, page_size: 50, keyword: query })
      .then((data) => setResults(data))
      .catch(() => setResults({ items: [], total: 0, pages: 0 }))
      .finally(() => setLoading(false));
  }, [query]);

  const handlePageChange = (pg) => {
    setPage(pg);
    setLoading(true);
    api.getArticles({ page: pg, page_size: 50, keyword: query })
      .then((data) => setResults(data))
      .catch(() => setResults({ items: [], total: 0, pages: 0 }))
      .finally(() => setLoading(false));
  };

  return (
    <div className="h-full flex flex-col" style={{ background: '#FBFCFD' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '20px', paddingBottom: '32px' }}>
          {/* Search header */}
          <div className="mb-5">
            <div className="flex items-center gap-3 mb-2">
              <button onClick={() => navigate('/')} style={{ fontSize: '12px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                ← 返回首页
              </button>
            </div>
            <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '20px', fontWeight: 700, color: '#1A1C1E', marginBottom: '8px' }}>
              搜索结果
            </h1>
            {query && !loading && results && (
              <div style={{ fontSize: '12px', color: '#686C72' }}>
                关键词 "<span style={{ color: '#1A1C1E', fontWeight: 500 }}>{query}</span>" · 共 {results.total} 条结果
              </div>
            )}
          </div>

          {loading ? (
            <div className="text-center py-16">
              <div className="flex gap-1.5 justify-center mb-3">
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '300ms' }} />
              </div>
              <span style={{ fontSize: '13px', color: '#686C72' }}>搜索中...</span>
            </div>
          ) : results ? (
            <div className="space-y-1">
              {results.items.map((a) => (
                <ArticleCard
                  key={a.id || a.url}
                  article={{ ...a, _imp: a.importance }}
                  onSelect={onReadArticle}
                  variant="detailed"
                />
              ))}
              {results.items.length === 0 && (
                <div className="text-center py-16 text-sm" style={{ color: '#8C9096' }}>
                  未找到与 "<span style={{ color: '#1A1C1E' }}>{query}</span>" 相关的文章
                </div>
              )}
            </div>
          ) : query ? null : (
            <div className="text-center py-16 text-sm" style={{ color: '#8C9096' }}>
              输入关键词搜索文章
            </div>
          )}

          {results?.pages > 1 && (
            <Pagination
              page={page}
              totalPages={results.pages}
              onPageChange={handlePageChange}
            />
          )}
        </div>
      </div>
    </div>
  );
}
