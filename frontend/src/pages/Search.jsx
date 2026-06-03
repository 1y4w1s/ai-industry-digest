import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';

export default function Search({ onArticleClick }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [keyword, setKeyword] = useState(searchParams.get('q') || '');
  const [importance, setImportance] = useState('');
  const [source, setSource] = useState('');
  const [tag, setTag] = useState('');
  const [results, setResults] = useState({ items: [], total: 0, pages: 0 });
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [sources, setSources] = useState([]);
  const [tags, setTags] = useState([]);

  useEffect(() => {
    api.getSources().then((d) => setSources(d.sources || [])).catch(() => {});
    api.getTags().then((d) => setTags(d.tags || [])).catch(() => {});
  }, []);

  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setKeyword(q);
      doSearch(q, '', '', '', 1);
    }
  }, [searchParams]);

  const doSearch = async (kw, imp, src, tg, pg) => {
    setLoading(true);
    try {
      const data = await api.getArticles({
        page: pg,
        page_size: 20,
        keyword: kw || undefined,
        importance: imp || undefined,
        source: src || undefined,
        tag: tg || undefined,
      });
      setResults(data);
      setPage(pg);
    } catch {
      setResults({ items: [], total: 0, pages: 0 });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setSearchParams(keyword ? { q: keyword } : {});
    doSearch(keyword, importance, source, tag, 1);
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="font-heading text-xl font-bold text-text-primary">全文检索</h1>
        <p className="text-sm text-text-secondary mt-1">搜索全站文章，支持关键词、标签、来源过滤</p>
      </div>

      {/* Filters */}
      <form onSubmit={handleSearch} className="bg-bg-surface border border-border-primary rounded-2xl p-4 mb-6">
        <div className="flex flex-wrap gap-3">
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="搜索关键词..."
            className="flex-1 min-w-[200px] px-4 py-2 bg-bg-base border border-border-primary rounded-xl text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/30"
          />
          <select value={importance} onChange={(e) => setImportance(e.target.value)} className="px-3 py-2 bg-bg-base border border-border-primary rounded-xl text-sm text-text-secondary focus:outline-none focus:border-accent">
            <option value="">全部重要性</option>
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
          </select>
          <select value={source} onChange={(e) => setSource(e.target.value)} className="px-3 py-2 bg-bg-base border border-border-primary rounded-xl text-sm text-text-secondary focus:outline-none focus:border-accent">
            <option value="">全部来源</option>
            {sources.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={tag} onChange={(e) => setTag(e.target.value)} className="px-3 py-2 bg-bg-base border border-border-primary rounded-xl text-sm text-text-secondary focus:outline-none focus:border-accent">
            <option value="">全部标签</option>
            {tags.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
          <button type="submit" className="px-5 py-2 bg-accent text-white text-sm rounded-xl hover:bg-accent-subtle transition-all">
            搜索
          </button>
        </div>
      </form>

      {/* Results */}
      {loading ? (
        <div className="text-center text-text-tertiary py-12 text-sm">搜索中...</div>
      ) : (
        <>
          {results.total > 0 && (
            <div className="text-xs text-text-tertiary mb-4">共 {results.total} 条结果</div>
          )}
          <div className="space-y-2">
            {results.items.map((a) => (
              <div
                key={a.id}
                onClick={() => onArticleClick(a.id)}
                className="bg-bg-surface border border-border-primary rounded-xl p-4 cursor-pointer hover:border-accent/30 hover:bg-bg-raised transition-all group"
              >
                <h3 className="font-medium text-sm text-text-primary group-hover:text-accent transition-colors">{a.title}</h3>
                <div className="flex items-center gap-3 mt-1.5 text-xs text-text-tertiary">
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    a.importance === 'high' ? 'bg-high-imp/10 text-high-imp' :
                    a.importance === 'medium' ? 'bg-medium-imp/10 text-medium-imp' :
                    'bg-low-imp/10 text-low-imp'
                  }`}>{a.importance || 'low'}</span>
                  <span>{a.source_name}</span>
                  {a.published_at && <span>· {a.published_at.slice(0, 10)}</span>}
                </div>
                {a.summary && <p className="text-xs text-text-secondary mt-2 line-clamp-2">{a.summary}</p>}
                {a.tags?.length > 0 && (
                  <div className="flex gap-1.5 mt-2">
                    {a.tags.map((t) => <span key={t} className="px-2 py-0.5 bg-accent/10 text-accent text-xs rounded">{t}</span>)}
                  </div>
                )}
              </div>
            ))}
            {results.items.length === 0 && keyword && (
              <div className="text-center text-text-tertiary py-12 text-sm">未找到相关文章</div>
            )}
          </div>

          {/* Pagination */}
          {results.pages > 1 && (
            <div className="flex justify-center gap-2 mt-6">
              <button disabled={page <= 1} onClick={() => doSearch(keyword, importance, source, tag, page - 1)} className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary disabled:opacity-40">
                ←
              </button>
              {Array.from({ length: Math.min(results.pages, 5) }, (_, i) => {
                const start = Math.max(1, page - 2);
                const p = start + i;
                if (p > results.pages) return null;
                return (
                  <button key={p} onClick={() => doSearch(keyword, importance, source, tag, p)}
                    className={`px-3 py-1.5 rounded-lg text-xs ${p === page ? 'bg-accent text-white' : 'bg-bg-raised border border-border-primary text-text-secondary hover:text-text-primary'}`}>
                    {p}
                  </button>
                );
              })}
              <button disabled={page >= results.pages} onClick={() => doSearch(keyword, importance, source, tag, page + 1)} className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary disabled:opacity-40">
                →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
