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

  const [keyword, setKeyword] = useState(searchParams.get('q') || '');
  const [importance, setImportance] = useState('');
  const [source, setSource] = useState('');
  const [tag, setTag] = useState('');
  const [sources, setSources] = useState([]);
  const [tags, setTags] = useState([]);
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    api.getSources().then((d) => setSources(d.sources || [])).catch(() => {});
    api.getTags().then((d) => setTags(d.tags || [])).catch(() => {});
  }, []);

  useEffect(() => {
    const q = searchParams.get('q');
    if (q) { setKeyword(q); doSearch(q, '', '', '', 1); }
  }, [searchParams]);

  useEffect(() => {
    if (searching) return;
    setLoading(true);
    api.getReports(page).then((data) => {
      setReports(data.items || []);
      setTotal(data.total || 0);
      if (!selectedDate && data.items?.length > 0) setSelectedDate(data.items[0].report_date);
    }).finally(() => setLoading(false));
  }, [page, searching]);

  useEffect(() => {
    if (!selectedDate || searching) return;
    setDetailLoading(true);
    api.getReport(selectedDate).then((data) => setReport(data)).finally(() => setDetailLoading(false));
  }, [selectedDate, searching]);

  const doSearch = async (kw, imp, src, tg, pg) => {
    setSearching(true); setDetailLoading(true);
    try {
      const data = await api.getArticles({ page: pg, page_size: 50, keyword: kw || undefined, importance: imp || undefined, source: src || undefined, tag: tg || undefined });
      setSearchResults(data); setPage(pg);
    } catch { setSearchResults({ items: [], total: 0, pages: 0 }); }
    finally { setDetailLoading(false); }
  };

  const handleClearSearch = () => {
    setKeyword(''); setImportance(''); setSource(''); setTag('');
    setSearching(false); setSearchResults(null);
  };

  const handleQuickFilter = (imp, src, tg) => {
    if (imp || src || tg) doSearch(keyword || '', imp, src, tg, 1);
    else { setSearching(false); setSearchResults(null); }
  };

  if (readerArticle) return <ArticleReader articleId={readerArticle} onBack={() => onReadArticle(null)} />;

  const articles = [];
  if (report && !searching) {
    for (const level of ['high', 'medium', 'low'])
      for (const a of (report.articles?.[level] || [])) articles.push({ ...a, _imp: level });
  }

  const groups = {};
  for (const a of (searchResults?.items || articles)) {
    const src = a.source_name || '其他';
    if (!groups[src]) groups[src] = [];
    groups[src].push(a);
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* ═══ Filter Row — 3 dropdowns, h-[36px], gap-3, centered ═══ */}
      <div className="flex-shrink-0 flex items-center justify-start gap-3 px-5 py-2.5 border-b border-border-muted bg-bg-surface/70">
        <select value={importance} onChange={(e) => { setImportance(e.target.value); handleQuickFilter(e.target.value, source, tag); }}
          className="h-9 px-3 text-xs text-text-secondary rounded-md focus:outline-none transition-all cursor-pointer"
          style={{ background: '#23233B', border: '1px solid #333355' }}>
          <option value="">全部重要度</option>
          <option value="high">高</option><option value="medium">中</option><option value="low">低</option>
        </select>
        <select value={source} onChange={(e) => { setSource(e.target.value); handleQuickFilter(importance, e.target.value, tag); }}
          className="h-9 px-3 text-xs text-text-secondary rounded-md focus:outline-none transition-all cursor-pointer"
          style={{ background: '#23233B', border: '1px solid #333355' }}>
          <option value="">全部来源</option>
          {sources.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={tag} onChange={(e) => { setTag(e.target.value); handleQuickFilter(importance, source, e.target.value); }}
          className="h-9 px-3 text-xs text-text-secondary rounded-md focus:outline-none transition-all cursor-pointer"
          style={{ background: '#23233B', border: '1px solid #333355' }}>
          <option value="">全部标签</option>
          {tags.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        {searching && (
          <button onClick={handleClearSearch} className="h-9 px-3.5 text-xs text-text-secondary rounded-md hover:text-text-primary transition-all cursor-pointer"
            style={{ background: '#23233B', border: '1px solid #333355' }}>
            清除筛选
          </button>
        )}
      </div>

      {/* ═══ Main Content ═══ */}
      <div className="flex-1 overflow-y-auto px-5" style={{ paddingTop: '20px', paddingBottom: '32px' }}>
        {/* Date chips */}
        {!searching && reports.length > 0 && (
          <div className="flex gap-[10px] mb-5 overflow-x-auto pb-1">
            {reports.map((r) => (
              <button key={r.report_date} onClick={() => { setSelectedDate(r.report_date); setPage(1); }}
                className="flex-shrink-0 px-4 py-[6px] rounded-md text-xs font-medium transition-all"
                style={{
                  background: selectedDate === r.report_date ? '#253060' : '#222236',
                  color: selectedDate === r.report_date ? '#E2E5FF' : '#9499C2',
                }}>
                <span className="opacity-70">{formatDateShort(r.report_date)}</span>
                <span className="ml-1.5 font-semibold">{r.report_date}</span>
              </button>
            ))}
          </div>
        )}

        {searching && (
          <div className="text-xs text-text-secondary mb-4" style={{ color: '#9499C2' }}>
            {searchResults ? `搜索到 ${searchResults.total} 条结果` : '搜索中...'}
            <span className="mx-2">·</span>
            <button onClick={handleClearSearch} className="hover:underline" style={{ color: '#5886FF' }}>返回日报</button>
          </div>
        )}

        {detailLoading ? (
          <div className="text-center py-16 text-sm" style={{ color: '#6B70A0' }}>加载中...</div>
        ) : !searching && report ? (
          <>
            {/* Bento Stats — 3 cards, gap-4, equal width */}
            <div className="grid grid-cols-3 gap-4 mb-5">
              {[
                { label: '文章总数', value: articles.length, icon: '📰', color: '#5886FF' },
                { label: '信息源', value: Object.keys(groups).length, icon: '📡', color: '#36D399' },
                { label: '高重要性', value: articles.filter((a) => a._imp === 'high').length, icon: '🔥', color: '#F87272' },
              ].map((s) => (
                <div key={s.label} className="text-center" style={{ background: '#1F1F35', borderRadius: '10px', padding: '20px' }}>
                  <div className="text-lg mb-1">{s.icon}</div>
                  <div className="font-heading font-bold" style={{ fontSize: '28px', color: s.color, lineHeight: 1.2 }}>{s.value}</div>
                  <div className="text-xs mt-1" style={{ color: '#9499C2' }}>{s.label}</div>
                </div>
              ))}
            </div>

            {/* Overview */}
            {report.summary_insight && (
              <div className="mb-5 p-4 rounded-xl" style={{ background: '#1B1B32', border: '1px solid #30304C' }}>
                <div className="text-sm leading-relaxed" style={{ color: '#E2E5FF', borderLeft: '3px solid #5886FF', paddingLeft: '14px' }}>
                  {report.summary_insight}
                </div>
                {report.trending_keywords?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {report.trending_keywords.map((k) => (
                      <span key={k} className="px-2.5 py-0.5 text-xs rounded-full" style={{ background: 'rgba(88,134,255,0.1)', color: '#5886FF', border: '1px solid rgba(88,134,255,0.2)' }}>{k}</span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Source groups */}
            {Object.entries(groups).sort(([,a],[,b]) => b.filter(x=>x._imp==='high').length - a.filter(x=>x._imp==='high').length).map(([src, arts]) => (
              <div key={src} className="mb-5">
                <div className="flex items-center pb-3 mb-3" style={{ borderBottom: '1px solid #30304C' }}>
                  <span className="font-heading font-semibold text-sm" style={{ color: '#C5C8E6' }}>{src}</span>
                  <span className="text-xs ml-auto" style={{ color: '#6B70A0' }}>{arts.length} 篇</span>
                </div>
                <div className="space-y-2">
                  {arts.sort((a, b) => ({ high: 0, medium: 1, low: 2 }[a._imp] || 2) - ({ high: 0, medium: 1, low: 2 }[b._imp] || 2)).map((a) => (
                    <div key={a.id || a.url} onClick={() => onReadArticle(a.id)}
                      className={`article-card ${a._imp === 'high' ? 'article-card-high' : a._imp === 'medium' ? 'article-card-medium' : 'article-card-low'}`}>
                      <div className="title">{a.title}</div>
                      <div className="flex items-center gap-2 mt-1 text-xs" style={{ color: '#888AA8' }}>
                        <span>{a.source_name}</span>
                        {a.published_at && <span>· {a.published_at.slice(0, 10)}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {articles.length === 0 && <div className="text-center py-16 text-sm" style={{ color: '#6B70A0' }}>暂无内容</div>}
          </>
        ) : searching && searchResults ? (
          <div className="space-y-2">
            {searchResults.items.map((a) => (
              <div key={a.id || a.url} onClick={() => onReadArticle(a.id)}
                className="article-card" style={{ borderLeft: '3px solid ' + (a.importance === 'high' ? '#F87272' : a.importance === 'medium' ? 'rgba(245,158,11,0.5)' : 'transparent') }}>
                <div className="title">{a.title}</div>
                <div className="flex items-center gap-2 mt-1 text-xs" style={{ color: '#888AA8' }}>
                  <span>{a.source_name}</span>
                  {a.published_at && <span>· {a.published_at.slice(0, 10)}</span>}
                </div>
                {a.summary && <p className="text-xs mt-1.5 line-clamp-2" style={{ color: '#6B70A0' }}>{a.summary}</p>}
              </div>
            ))}
            {searchResults.items.length === 0 && <div className="text-center py-16 text-sm" style={{ color: '#6B70A0' }}>未找到相关文章</div>}
          </div>
        ) : (
          <div className="text-center py-16 text-sm" style={{ color: '#6B70A0' }}>暂无数据</div>
        )}

        {/* Pagination */}
        {searching && searchResults?.pages > 1 && (
          <div className="flex justify-center gap-2 mt-6">
            <button disabled={page <= 1} onClick={() => doSearch(keyword, importance, source, tag, page - 1)}
              className="px-3 py-1.5 rounded-lg text-xs transition-all disabled:opacity-40" style={{ background: '#22223D', border: '1px solid #333355', color: '#9499C2' }}>←</button>
            {Array.from({ length: Math.min(searchResults.pages, 5) }, (_, i) => {
              const p = Math.max(1, page - 2) + i;
              if (p > searchResults.pages) return null;
              return <button key={p} onClick={() => doSearch(keyword, importance, source, tag, p)}
                className="px-3 py-1.5 rounded-lg text-xs transition-all"
                style={p === page ? { background: '#5886FF', color: '#fff' } : { background: '#22223D', border: '1px solid #333355', color: '#9499C2' }}>{p}</button>;
            })}
            <button disabled={page >= searchResults.pages} onClick={() => doSearch(keyword, importance, source, tag, page + 1)}
              className="px-3 py-1.5 rounded-lg text-xs transition-all disabled:opacity-40" style={{ background: '#22223D', border: '1px solid #333355', color: '#9499C2' }}>→</button>
          </div>
        )}
      </div>
    </div>
  );
}

function formatDateShort(dateStr) {
  const d = new Date(dateStr);
  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  return `${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')} 周${weekdays[d.getDay()]}`;
}
