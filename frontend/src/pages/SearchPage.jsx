import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import ArticleCard from '../components/ArticleCard';
import Pagination from '../components/Pagination';

export default function SearchPage({ onReadArticle }) {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const navigate = useNavigate();
  const inputRef = useRef(null);

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [inputValue, setInputValue] = useState('');

  // Sync input with URL query on mount
  useEffect(() => {
    setInputValue(query);
  }, [query]);

  // Fetch on query or page change
  useEffect(() => {
    if (!query) return;
    setLoading(true);
    api.getArticles({ page, page_size: 50, keyword: query })
      .then((data) => setResults(data))
      .catch(() => setResults({ items: [], total: 0, pages: 0 }))
      .finally(() => setLoading(false));
  }, [query, page]);

  const handleSearch = (e) => {
    e.preventDefault();
    const trimmed = inputValue.trim();
    if (trimmed) {
      navigate(`/search?q=${encodeURIComponent(trimmed)}`);
      setPage(1);
    }
  };

  const handlePageChange = (pg) => {
    setPage(pg);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="h-full flex flex-col" style={{ background: '#FBFCFD' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6" style={{ paddingTop: '20px', paddingBottom: '32px', maxWidth: '800px' }}>
          {/* Back link */}
          <div className="mb-4">
            <button onClick={() => navigate('/')} style={{ fontSize: '12px', color: '#2864A8', background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              ← 返回首页
            </button>
          </div>

          {/* Search bar */}
          <form onSubmit={handleSearch} className="mb-6">
            <div className="relative">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: '#8C9096' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="搜索文章..."
                style={{
                  width: '100%',
                  padding: '10px 14px 10px 38px',
                  fontSize: '14px',
                  background: '#FFFFFF',
                  border: '1px solid #D8DCE0',
                  borderRadius: '6px',
                  color: '#2C2E32',
                  outline: 'none',
                  transition: 'border-color 0.15s',
                }}
                onFocus={(e) => e.target.style.borderColor = '#1A1C1E'}
                onBlur={(e) => e.target.style.borderColor = '#D8DCE0'}
              />
              {inputValue && (
                <button type="button" onClick={() => { setInputValue(''); inputRef.current?.focus(); }}
                  style={{ position: 'absolute', right: '40px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', padding: '4px', color: '#8C9096' }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5}><path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" /></svg>
                </button>
              )}
              <button type="submit"
                style={{ position: 'absolute', right: '8px', top: '50%', transform: 'translateY(-50%)', padding: '4px 10px', fontSize: '12px', background: '#1A1C1E', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                搜索
              </button>
            </div>
          </form>

          {/* Results header */}
          {query && !loading && results && (
            <div style={{ fontSize: '12px', color: '#686C72', marginBottom: '20px', paddingBottom: '12px', borderBottom: '1px solid #E8EAED' }}>
              关键词 "<span style={{ color: '#1A1C1E', fontWeight: 500 }}>{query}</span>" · 共 {results.total} 条结果
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div className="text-center py-16">
              <div className="flex gap-1.5 justify-center mb-3">
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '0ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '150ms' }} />
                <span className="w-2 h-2 rounded-full animate-bounce" style={{ background: '#8C9096', animationDelay: '300ms' }} />
              </div>
              <span style={{ fontSize: '13px', color: '#686C72' }}>搜索中...</span>
            </div>
          )}

          {/* Results list */}
          {!loading && results && results.items.length > 0 && (
            <div className="space-y-1">
              {results.items.map((a) => (
                <ArticleCard
                  key={a.id || a.url}
                  article={{ ...a, _imp: a.importance }}
                  onSelect={onReadArticle}
                  variant="detailed"
                />
              ))}
            </div>
          )}

          {/* Empty: no results found */}
          {!loading && results && results.items.length === 0 && (
            <div className="text-center py-20">
              <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: '#F0F1F2', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8C9096" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <p style={{ fontSize: '14px', color: '#1A1C1E', marginBottom: '4px' }}>未找到相关文章</p>
              <p style={{ fontSize: '12px', color: '#686C72' }}>
                关键词 "<span style={{ color: '#1A1C1E' }}>{query}</span>" 没有匹配结果，试试其他关键词
              </p>
            </div>
          )}

          {/* Empty: no query entered */}
          {!query && !loading && (
            <div className="text-center py-20">
              <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: '#F0F1F2', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8C9096" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <p style={{ fontSize: '14px', color: '#1A1C1E', marginBottom: '4px' }}>搜索 AI 行业文章</p>
              <p style={{ fontSize: '12px', color: '#686C72' }}>输入关键词搜索全站文章</p>
            </div>
          )}

          {/* Pagination */}
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
