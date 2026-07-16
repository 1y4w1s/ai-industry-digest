import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import ArticleCard from '../components/ArticleCard';
import Pagination from '../components/Pagination';
import AIRecommendPanel from '../components/AIRecommendPanel';
import SkeletonCard from '../components/SkeletonCard';

const SUGGESTIONS = [
  'OpenAI', '大模型', '融资', 'AI 医疗', '自动驾驶', '量子计算',
  'GPT', 'Claude', 'Google', 'Meta', '腾讯', '百度',
];

const IMP_OPTIONS = [
  { value: '', label: '全部' },
  { value: 'high', label: '高' },
  { value: 'medium', label: '中' },
  { value: 'low', label: '低' },
];

export default function SearchPage() {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const navigate = useNavigate();
  const goToArticle = (id) => navigate(`/?article=${encodeURIComponent(id)}`);

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  // 筛选状态
  const [filterSource, setFilterSource] = useState('');
  const [filterTag, setFilterTag] = useState('');
  const [filterImportance, setFilterImportance] = useState('');
  const [sources, setSources] = useState([]);
  const [tags, setTags] = useState([]);

  // 加载来源/标签列表
  useEffect(() => {
    api.getSources().then(setSources).catch(() => {});
    api.getTags().then(setTags).catch(() => {});
  }, []);

  // 重置页码当筛选条件变化
  useEffect(() => { setPage(1); }, [query, filterSource, filterTag, filterImportance]);

  // 搜索
  useEffect(() => {
    if (!query) return;
    setLoading(true);
    const filters = {};
    if (filterSource) filters.source = filterSource;
    if (filterTag) filters.tag = filterTag;
    if (filterImportance) filters.importance = filterImportance;

    api.searchAll(query, page, 50, filters)
      .then((data) => {
        const items = (data.articles?.items || []).map((a) => ({ ...a, _imp: a.importance }));
        setResults({ ...data.articles, items });
      })
      .catch(() => setResults({ items: [], total: 0, pages: 0 }))
      .finally(() => setLoading(false));
  }, [query, page, filterSource, filterTag, filterImportance]);

  const handlePageChange = (pg) => {
    setPage(pg);
    setLoading(true);
    const filters = {};
    if (filterSource) filters.source = filterSource;
    if (filterTag) filters.tag = filterTag;
    if (filterImportance) filters.importance = filterImportance;
    api.searchAll(query, pg, 50, filters)
      .then((data) => {
        const items = (data.articles?.items || []).map((a) => ({ ...a, _imp: a.importance }));
        setResults({ ...data.articles, items });
      })
      .catch(() => setResults({ items: [], total: 0, pages: 0 }))
      .finally(() => setLoading(false));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const activeFilters = [filterSource, filterTag, filterImportance].filter(Boolean).length;

  return (
    <div className="flex-1 flex flex-col min-h-0" style={{ background: 'var(--color-bg-white)' }}>
      <div className="flex-1 overflow-y-auto">
        <div className="px-5 lg:px-6 py-5" style={{ maxWidth: '800px', margin: '0 auto' }}>
          <div className="mb-5">
            <button onClick={() => navigate('/')} style={{ fontSize: '12px', color: 'var(--color-text-muted)', background: 'none', border: 'none', cursor: 'pointer', padding: 0, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
              ← 返回首页
            </button>
          </div>

          <div className="mb-4" style={{ paddingBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
              <h1 style={{ fontFamily: "var(--font-display)", fontSize: '20px', fontWeight: 700, color: 'var(--color-text-title)' }}>
                搜索结果
              </h1>
              <span style={{ flex: 1, height: '1px', background: 'linear-gradient(90deg, var(--color-brass) 0%, var(--color-border-light) 100%)', minWidth: 40 }} />
            </div>
            {query && !loading && results && (
              <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: 2 }}>
                关键词 "<span style={{ color: 'var(--color-text-title)', fontWeight: 500 }}>{query}</span>" · {results.total}{activeFilters > 0 ? ` · ${activeFilters} 个筛选` : ''}
              </div>
            )}
          </div>

          {/* 筛选栏 */}
          {query && (
            <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
              <select value={filterSource} onChange={(e) => setFilterSource(e.target.value)}
                style={{ fontSize: '12px', padding: '6px 10px', borderRadius: 6, border: '1px solid var(--color-border)', background: 'var(--color-bg-white)', color: 'var(--color-text-body)', outline: 'none', maxWidth: 140 }}>
                <option value="">来源</option>
                {sources.slice(0, 20).map((s) => (<option key={s} value={s}>{s}</option>))}
              </select>

              <select value={filterTag} onChange={(e) => setFilterTag(e.target.value)}
                style={{ fontSize: '12px', padding: '6px 10px', borderRadius: 6, border: '1px solid var(--color-border)', background: 'var(--color-bg-white)', color: 'var(--color-text-body)', outline: 'none', maxWidth: 140 }}>
                <option value="">标签</option>
                {tags.slice(0, 20).map((t) => (<option key={t} value={t}>{t}</option>))}
              </select>

              <select value={filterImportance} onChange={(e) => setFilterImportance(e.target.value)}
                style={{ fontSize: '12px', padding: '6px 10px', borderRadius: 6, border: '1px solid var(--color-border)', background: 'var(--color-bg-white)', color: 'var(--color-text-body)', outline: 'none' }}>
                {IMP_OPTIONS.map((o) => (<option key={o.value} value={o.value}>{o.label}</option>))}
              </select>

              {activeFilters > 0 && (
                <button onClick={() => { setFilterSource(''); setFilterTag(''); setFilterImportance(''); }}
                  style={{ fontSize: '11px', color: 'var(--color-brass)', background: 'none', border: 'none', cursor: 'pointer', padding: '4px 8px' }}>
                  清除筛选
                </button>
              )}
            </div>
          )}

          <div className="flex gap-6" style={{ position: 'relative' }}>
            <div className="flex-1 min-w-0">
              {loading && (
                <div className="space-y-0">
                  <SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard />
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
                <div className="text-center py-16">
                  <div style={{ width: '48px', height: '48px', margin: '0 auto 16px', borderRadius: '50%', background: 'var(--color-bg-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-label)" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  </div>
                  <p style={{ fontSize: '14px', color: 'var(--color-text-title)', marginBottom: '4px' }}>未找到相关文章</p>
                  <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '16px' }}>试试其他关键词，或调整筛选条件</p>
                  <div style={{ marginTop: 4 }}>
                    <a href="/" style={{ fontSize: '12px', color: 'var(--color-brass)', textDecoration: 'none' }}>去看看今日日报 →</a>
                  </div>
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
                  <p style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>输入关键词搜索</p>
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
