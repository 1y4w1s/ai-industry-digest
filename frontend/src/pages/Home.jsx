import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import ArticleReader from '../components/ArticleReader';

export default function Home({ onReadArticle, readerArticle }) {
  const [searchParams] = useSearchParams();
  const [reports, setReports] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  // Search/filter state
  const [keyword, setKeyword] = useState(searchParams.get('q') || '');
  const [importance, setImportance] = useState('');
  const [source, setSource] = useState('');
  const [tag, setTag] = useState('');
  const [sources, setSources] = useState([]);
  const [tags, setTags] = useState([]);
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);

  // Load sources/tags
  useEffect(() => {
    api.getSources().then((d) => setSources(d.sources || [])).catch(() => {});
    api.getTags().then((d) => setTags(d.tags || [])).catch(() => {});
  }, []);

  // If there's a search query from header
  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setKeyword(q);
      doSearch(q, '', '', '', 1);
    }
  }, [searchParams]);

  // Load reports
  useEffect(() => {
    if (searching) return;
    setLoading(true);
    api.getReports(page).then((data) => {
      setReports(data.items || []);
      setTotal(data.total || 0);
      if (!selectedDate && data.items?.length > 0) {
        setSelectedDate(data.items[0].report_date);
      }
    }).finally(() => setLoading(false));
  }, [page, searching]);

  // Load report detail
  useEffect(() => {
    if (!selectedDate || searching) return;
    setDetailLoading(true);
    api.getReport(selectedDate).then((data) => {
      setReport(data);
    }).finally(() => setDetailLoading(false));
  }, [selectedDate, searching]);

  // Search function
  const doSearch = async (kw, imp, src, tg, pg) => {
    setSearching(true);
    setDetailLoading(true);
    try {
      const data = await api.getArticles({
        page: pg, page_size: 50,
        keyword: kw || undefined, importance: imp || undefined,
        source: src || undefined, tag: tg || undefined,
      });
      setSearchResults(data);
      setPage(pg);
    } catch {
      setSearchResults({ items: [], total: 0, pages: 0 });
    } finally {
      setDetailLoading(false);
    }
  };

  const handleFilterSearch = (e) => {
    e.preventDefault();
    if (keyword || importance || source || tag) {
      doSearch(keyword, importance, source, tag, 1);
    } else {
      setSearching(false);
      setSearchResults(null);
    }
  };

  const handleClearSearch = () => {
    setKeyword('');
    setImportance('');
    setSource('');
    setTag('');
    setSearching(false);
    setSearchResults(null);
  };

  // Quick filter: auto-search when dropdown changes
  const handleQuickFilter = (imp, src, tg) => {
    if (imp || src || tg) {
      doSearch(keyword || '', imp, src, tg, 1);
    } else {
      setSearching(false);
      setSearchResults(null);
    }
  };

  // If reading an article
  if (readerArticle) {
    return <ArticleReader articleId={readerArticle} onBack={() => onReadArticle(null)} />;
  }

  // ── Render article list ──
  const articles = [];
  if (report && !searching) {
    for (const level of ['high', 'medium', 'low']) {
      for (const a of (report.articles?.[level] || [])) {
        articles.push({ ...a, _imp: level });
      }
    }
  }

  const groups = {};
  for (const a of (searchResults?.items || articles)) {
    const src = a.source_name || '其他';
    if (!groups[src]) groups[src] = [];
    groups[src].push(a);
  }

  const displayArticles = searchResults?.items || articles;
  const displayTotal = searchResults?.total || articles.length;

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* ── Global Filter Bar ── */}
      <div className="flex-shrink-0 flex items-center gap-2 px-4 lg:px-6 py-2.5 border-b border-border-subtle bg-bg-surface/60">
        <select value={importance} onChange={(e) => { setImportance(e.target.value); handleQuickFilter(e.target.value, source, tag); }} className="px-2.5 py-1.5 bg-bg-base border border-border-primary rounded-lg text-xs text-text-secondary focus:outline-none focus:border-accent/50">
          <option value="">全部重要度</option>
          <option value="high">高</option><option value="medium">中</option><option value="low">低</option>
        </select>
        <select value={source} onChange={(e) => { setSource(e.target.value); handleQuickFilter(importance, e.target.value, tag); }} className="px-2.5 py-1.5 bg-bg-base border border-border-primary rounded-lg text-xs text-text-secondary focus:outline-none focus:border-accent/50">
          <option value="">全部来源</option>
          {sources.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={tag} onChange={(e) => { setTag(e.target.value); handleQuickFilter(importance, source, e.target.value); }} className="px-2.5 py-1.5 bg-bg-base border border-border-primary rounded-lg text-xs text-text-secondary focus:outline-none focus:border-accent/50">
          <option value="">全部标签</option>
          {tags.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        {searching && (
          <button type="button" onClick={handleClearSearch} className="px-3 py-1.5 text-xs text-text-tertiary hover:text-text-primary transition-colors ml-2">清除筛选</button>
        )}
      </div>

      {/* ── Content ── */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 lg:p-6">
          {/* Date nav (only when not searching) */}
          {!searching && reports.length > 0 && (
            <div className="flex gap-2 mb-5 overflow-x-auto pb-2">
              {reports.map((r) => (
                <button key={r.report_date} onClick={() => { setSelectedDate(r.report_date); setPage(1); }}
                  className={`flex-shrink-0 px-3.5 py-2 rounded-xl text-xs font-medium transition-all ${
                    selectedDate === r.report_date
                      ? 'bg-accent/10 border border-accent/30 text-accent'
                      : 'bg-bg-surface border border-border-primary text-text-secondary hover:text-text-primary hover:border-accent/30'
                  }`}>
                  <div className="opacity-60">{formatDateShort(r.report_date)}</div>
                  <div className="font-semibold">{r.report_date}</div>
                </button>
              ))}
            </div>
          )}

          {/* Search results header */}
          {searching && (
            <div className="text-xs text-text-tertiary mb-4">
              {searchResults ? `搜索到 ${searchResults.total} 条结果` : '搜索中...'}
              <span className="mx-2">·</span>
              <button onClick={handleClearSearch} className="text-accent hover:underline">返回日报</button>
            </div>
          )}

          {/* Loading */}
          {detailLoading ? (
            <div className="text-center text-text-tertiary py-16 text-sm">加载中...</div>
          ) : !searching && report ? (
            <>
              {/* Overview */}
              {report.summary_insight && (
                <div className="bg-bg-surface border border-border-subtle rounded-2xl p-5 mb-5">
                  <div className="flex items-center gap-3 text-xs text-text-tertiary mb-3">
                    <span>📰 {articles.length} 篇文章</span>
                    <span>📡 {Object.keys(groups).length} 个来源</span>
                  </div>
                  <div className="bg-bg-raised rounded-xl p-4 text-sm text-text-primary leading-relaxed border-l-2 border-accent mb-3">
                    {report.summary_insight}
                  </div>
                  {report.trending_keywords?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {report.trending_keywords.map((k) => (
                        <span key={k} className="px-2.5 py-1 bg-accent/10 text-accent text-xs rounded-full border border-accent/20">{k}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Grouped articles */}
              {Object.entries(groups).sort(([,a],[,b]) => b.filter(x=>x._imp==='high').length - a.filter(x=>x._imp==='high').length).map(([src, arts]) => (
                <div key={src} className="mb-5">
                  <div className="flex items-center gap-2 mb-2.5 pb-2 border-b border-border-subtle">
                    <span className="font-heading font-semibold text-sm text-text-primary">{src}</span>
                    <span className="text-xs text-text-tertiary ml-auto">{arts.length} 篇</span>
                  </div>
                  <div className="space-y-1.5">
                    {arts.map((a) => (
                      <div key={a.id || a.url} onClick={() => onReadArticle(a.id)}
                        className="bg-bg-surface border border-border-subtle rounded-xl p-3.5 cursor-pointer hover:border-accent/30 hover:bg-bg-raised transition-all group">
                        <div className="flex items-start gap-3">
                          <div className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${a._imp === 'high' ? 'bg-high-imp' : a._imp === 'medium' ? 'bg-medium-imp' : 'bg-low-imp'}`} />
                          <div className="flex-1 min-w-0">
                            <h3 className="text-sm font-medium text-text-primary group-hover:text-accent transition-colors leading-relaxed">{a.title}</h3>
                            <div className="flex items-center gap-2 mt-1 text-xs text-text-tertiary">
                              <span>{a.source_name}</span>
                              {a.published_at && <span>· {a.published_at.slice(0, 10)}</span>}
                              {a.tags?.length > 0 && <span>· {a.tags.slice(0, 2).join(', ')}{a.tags.length > 2 ? '...' : ''}</span>}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              {articles.length === 0 && <div className="text-center text-text-tertiary py-16 text-sm">暂无内容</div>}
            </>
          ) : searching && searchResults ? (
            /* Search results */
            <div className="space-y-1.5">
              {searchResults.items.map((a) => (
                <div key={a.id || a.url} onClick={() => onReadArticle(a.id)}
                  className="bg-bg-surface border border-border-subtle rounded-xl p-3.5 cursor-pointer hover:border-accent/30 hover:bg-bg-raised transition-all group">
                  <div className="flex items-start gap-3">
                    <div className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${a.importance === 'high' ? 'bg-high-imp' : a.importance === 'medium' ? 'bg-medium-imp' : 'bg-low-imp'}`} />
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-text-primary group-hover:text-accent transition-colors">{a.title}</h3>
                      <div className="flex items-center gap-2 mt-1 text-xs text-text-tertiary">
                        <span>{a.source_name}</span>
                        {a.published_at && <span>· {a.published_at.slice(0, 10)}</span>}
                      </div>
                      {a.summary && <p className="text-xs text-text-secondary mt-1.5 line-clamp-2">{a.summary}</p>}
                    </div>
                  </div>
                </div>
              ))}
              {searchResults.items.length === 0 && <div className="text-center text-text-tertiary py-16 text-sm">未找到相关文章</div>}
            </div>
          ) : (
            <div className="text-center text-text-tertiary py-16 text-sm">暂无数据</div>
          )}

          {/* Pagination for search */}
          {searching && searchResults?.pages > 1 && (
            <div className="flex justify-center gap-2 mt-6">
              <button disabled={page <= 1} onClick={() => doSearch(keyword, importance, source, tag, page-1)}
                className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary disabled:opacity-40">←</button>
              {Array.from({ length: Math.min(searchResults.pages, 5) }, (_, i) => {
                const p = Math.max(1, page - 2) + i;
                if (p > searchResults.pages) return null;
                return <button key={p} onClick={() => doSearch(keyword, importance, source, tag, p)}
                  className={`px-3 py-1.5 rounded-lg text-xs ${p === page ? 'bg-accent text-white' : 'bg-bg-raised border border-border-primary text-text-secondary hover:text-text-primary'}`}>{p}</button>;
              })}
              <button disabled={page >= searchResults.pages} onClick={() => doSearch(keyword, importance, source, tag, page+1)}
                className="px-3 py-1.5 bg-bg-raised border border-border-primary rounded-lg text-xs text-text-secondary hover:text-text-primary disabled:opacity-40">→</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function formatDateShort(dateStr) {
  const d = new Date(dateStr);
  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  return `${(d.getMonth()+1).toString().padStart(2,'0')}/${d.getDate().toString().padStart(2,'0')} 周${weekdays[d.getDay()]}`;
}
