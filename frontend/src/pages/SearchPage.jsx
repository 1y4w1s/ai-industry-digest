import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import ArticleCard from '../components/ArticleCard';
import Pagination from '../components/Pagination';
import AIRecommendPanel from '../components/AIRecommendPanel';

export default function SearchPage() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const navigate = useNavigate();
  const goToArticle = (id) => navigate(`/?article=${encodeURIComponent(id)}`);

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);

  useEffect(() => {
    setPage(1);
  }, [query]);

  useEffect(() => {
    if (!query) return;
    setLoading(true);
    api.getArticles({ page, page_size: 50, keyword: query })
      .then((data) => {
        const items = (data.items || []).map((a) => ({ ...a, _imp: a.importance }));
        setResults({ ...data, items });
      })
      .catch(() => setResults({ items: [], total: 0, pages: 0 }))
      .finally(() => setLoading(false));
  }, [query, page]);

  const handlePageChange = (pg) => {
    setPage(pg);
    setLoading(true);
    api.getArticles({ page: pg, page_size: 50, keyword: query })
      .then((data) => {
        const items = (data.items || []).map((a) => ({ ...a, _imp: a.importance }));
        setResults({ ...data, items });
      })
      .catch(() => setResults({ items: [], total: 0, pages: 0 }))
      .finally(() => setLoading(false));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="flex-1 flex flex-col min-h-0" style={{ background: 'var(--color-bg-white)' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6 py-5" style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div className="mb-5">
            <button onClick={() => navigate('/')} style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-blue-link)', background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              ← 返回首页
            </button>
          </div>

          <div className="mb-6" style={{ borderBottom: '1px solid var(--color-border-light)', paddingBottom: '16px' }}>
            <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: 'var(--fs-xl)', fontWeight: 700, color: 'var(--color-text-title)', marginBottom: '4px' }}>
              搜索结果
            </h1>
            {query && !loading && results && (
              <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>
                关键词 "<span style={{ color: 'var(--color-text-title)', fontWeight: 500 }}>{query}</span>" · 共 {results.total} 条结果
              </div>
            )}
          </div>

          <div className="flex gap-6" style={{ position: 'relative' }}>
            <div className="flex-1 min-w-0">
              {loading && (
                <div className="text-center py-16">
                  <div className="flex gap-1.5 justify-center mb-3">
                    <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '0ms' }} />
                    <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '150ms' }} />
                    <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-text-label)', animationDelay: '300ms' }} />
                  </div>
                  <span style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>搜索中...</span>
                </div>
              )}

              {!loading && results && results.items.length > 0 && (
                <div className="space-y-1">
                  {results.items.map((a) => (
                    <ArticleCard key={a.id || a.url} article={a} onSelect={goToArticle} variant="detailed" keyword={query} />
                  ))}
                </div>
              )}

              {!loading && results && results.items.length === 0 && (
                <div className="text-center py-20">
                  <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: 'var(--color-bg-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-label)" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <p style={{ fontSize: '14px', color: 'var(--color-text-title)', marginBottom: '4px' }}>未找到相关文章</p>
                  <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)', marginBottom: '12px' }}>试试其他关键词，或询问 AI 助手获取推荐</p>
                  <a href="/" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--color-blue-link)', textDecoration: 'none' }}>
                    去看看今日日报 →
                  </a>
                </div>
              )}

              {!query && !loading && (
                <div className="text-center py-20">
                  <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: 'var(--color-bg-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-label)" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <p style={{ fontSize: '14px', color: 'var(--color-text-title)', marginBottom: '4px' }}>搜索 AI 行业文章</p>
                  <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-muted)' }}>点击右上角搜索图标，输入关键词</p>
                </div>
              )}

              {results?.pages > 1 && (
                <Pagination page={page} totalPages={results.pages} onPageChange={handlePageChange} />
              )}
            </div>

            <div className="hidden lg:block w-80 flex-shrink-0" style={{ position: 'sticky', top: '20px', alignSelf: 'flex-start', maxHeight: 'calc(100vh - 100px)', overflowY: 'auto' }}>
              <AIRecommendPanel keyword={query} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
