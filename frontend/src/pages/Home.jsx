import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../api/client';
import ArticleReader from '../components/ArticleReader';
import SidePanel from '../components/SidePanel';

export default function Home({ onReadArticle, readerArticle }) {
  const [searchParams] = useSearchParams();
  const [reports, setReports] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [sidePanelOpen, setSidePanelOpen] = useState(true);

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
    setImportance(''); setSource(''); setTag('');
    setSearching(false); setSearchResults(null);
  };

  const handleQuickFilter = (imp, src, tg) => {
    if (imp || src || tg) doSearch('', imp, src, tg, 1);
    else { setSearching(false); setSearchResults(null); }
  };

  const activeFilterCount = [importance, source, tag].filter(Boolean).length;
  const isFilterActive = searching || activeFilterCount > 0;

  const handleAskAI = (question) => {
    window.dispatchEvent(new CustomEvent('ai-ask', { detail: { question } }));
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

  const highArticles = articles.filter((a) => a._imp === 'high');
  const heroArticle = highArticles[0];
  const displayReporting = !searching && report;

  return (
    <div className="h-full flex flex-col overflow-hidden" style={{ background: '#FBFCFD' }}>
      {/* ═══ Filter Bar ═══ */}
      <div className="flex-shrink-0" style={{ background: '#F6F7F8', borderBottom: '1px solid #E8EAED', padding: '6px 16px' }}>
        <div className="flex items-center gap-2 flex-wrap">
          {/* Importance pills — gray scale */}
          <div className="flex items-center gap-1">
            {[
              { key: 'high', label: '高', color: '#D4322E' },
              { key: 'medium', label: '中', color: '#C8960A' },
              { key: 'low', label: '低', color: '#8C9096' },
            ].map((opt) => (
              <button key={opt.key} onClick={() => {
                const next = importance === opt.key ? '' : opt.key;
                setImportance(next);
                if (next || source || tag) doSearch('', next, source, tag, 1);
                else { setSearching(false); setSearchResults(null); }
              }} className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] rounded transition-all"
                style={{ background: importance === opt.key ? '#D8DCE0' : 'transparent', color: importance === opt.key ? '#1A1C1E' : '#686C72' }}>
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: opt.color }} />
                {opt.label}
              </button>
            ))}
          </div>

          {/* Source/Tag dropdowns */}
          <select value={source} onChange={(e) => { setSource(e.target.value); handleQuickFilter(importance, e.target.value, tag); }}
            className="text-[11px] px-2 py-1 rounded cursor-pointer" style={{ background: '#EDEEF0', border: '1px solid #E8EAED', color: source ? '#1A1C1E' : '#8C9096' }}>
            <option value="">来源</option>
            {sources.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={tag} onChange={(e) => { setTag(e.target.value); handleQuickFilter(importance, source, e.target.value); }}
            className="text-[11px] px-2 py-1 rounded cursor-pointer" style={{ background: '#EDEEF0', border: '1px solid #E8EAED', color: tag ? '#1A1C1E' : '#8C9096' }}>
            <option value="">标签</option>
            {tags.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>

          {/* Filter status */}
          {isFilterActive && (
            <div className="flex items-center gap-2 ml-1">
              <span className="text-[11px]" style={{ color: '#686C72' }}>
                {searching ? `${searchResults?.total || 0} 条结果` : `${activeFilterCount} 个筛选中`}
              </span>
              <button onClick={handleClearSearch} className="text-[11px]" style={{ color: '#8C9096' }}>清除</button>
            </div>
          )}

          {/* Side panel toggle */}
          <button onClick={() => setSidePanelOpen(!sidePanelOpen)}
            className="hidden lg:flex xl:hidden ml-auto items-center gap-1 px-2 py-1 text-[11px] rounded cursor-pointer" style={{ background: '#EDEEF0', border: '1px solid #E8EAED', color: '#686C72' }}>
            <span className={sidePanelOpen ? 'rotate-180' : ''} style={{ display: 'inline-block', transition: 'transform 0.2s' }}>◀</span>
          </button>
        </div>
      </div>

      {/* ═══ Three-column Content ═══ */}
      <div className="flex-1 flex overflow-hidden">
        {/* Main content */}
        <div className="flex-1 min-w-0 overflow-y-auto">
          <div className="px-5 lg:px-6" style={{ paddingTop: '20px', paddingBottom: '32px' }}>
            {/* Date nav + inline stats */}
            {!searching && reports.length > 0 && (
              <div className="flex items-center gap-4 mb-5 flex-wrap">
                <h1 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '20px', fontWeight: 700, color: '#1A1C1E' }}>
                  每日简报
                </h1>
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {reports.map((r) => (
                    <button key={r.report_date} onClick={() => { setSelectedDate(r.report_date); setPage(1); }}
                      className="flex-shrink-0 px-3 py-1 text-xs font-medium rounded transition-all"
                      style={{ background: selectedDate === r.report_date ? '#D8DCE0' : '#F0F1F2', color: selectedDate === r.report_date ? '#1A1C1E' : '#686C72' }}>
                      {formatDateShort(r.report_date)} <span className="font-semibold">{r.report_date}</span>
                    </button>
                  ))}
                </div>
                {/* Inline stats */}
                {displayReporting && (
                  <div className="flex items-center gap-3 text-xs ml-auto" style={{ color: '#686C72' }}>
                    <span>📰 {articles.length} 篇</span>
                    <span>📡 {Object.keys(groups).length} 个来源</span>
                    <span>🔥 {highArticles.length} 篇高重要性</span>
                  </div>
                )}
              </div>
            )}

            {searching && (
              <div className="text-xs mb-4" style={{ color: '#686C72' }}>
                {searchResults ? `搜索到 ${searchResults.total} 条结果` : '搜索中...'}
                <span className="mx-2">·</span>
                <button onClick={handleClearSearch} style={{ color: '#2864A8' }}>返回日报</button>
              </div>
            )}

            {detailLoading ? (
              <div className="text-center py-16 text-sm" style={{ color: '#8C9096' }}>加载中...</div>
            ) : displayReporting ? (
              <>
                {/* Overview */}
                {report.summary_insight && (
                  <div className="mb-5 p-4" style={{ background: '#F6F7F8', borderRadius: '4px' }}>
                    <div className="text-sm leading-relaxed" style={{ color: '#2C2E32', borderLeft: '3px solid #1A1C1E', paddingLeft: '14px' }}>
                      {report.summary_insight}
                    </div>
                    {report.trending_keywords?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {report.trending_keywords.map((k) => (
                          <span key={k} className="px-2 py-0.5 text-xs rounded" style={{ background: '#E8EAED', color: '#686C72' }}>{k}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Hero article */}
                {heroArticle && (
                  <div className="hero-card mb-5" onClick={() => onReadArticle(heroArticle.id)}>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: '#D4322E' }}>头条</span>
                      <span className="text-[10px]" style={{ color: '#8C9096' }}>{heroArticle.source_name} · {heroArticle.published_at?.slice(0, 10)}</span>
                    </div>
                    <h2 style={{ fontFamily: "'Source Serif 4', Georgia, serif", fontSize: '18px', fontWeight: 700, color: '#1A1C1E', lineHeight: 1.35, marginBottom: '8px' }}>
                      {heroArticle.title}
                    </h2>
                    {heroArticle.summary && (
                      <p className="text-sm leading-relaxed line-clamp-2" style={{ color: '#2C2E32' }}>{heroArticle.summary}</p>
                    )}
                    {heroArticle.tags?.length > 0 && (
                      <div className="flex gap-1.5 mt-2">
                        {heroArticle.tags.map((t) => (
                          <span key={t} className="px-2 py-0.5 text-[10px] rounded" style={{ background: '#E8EAED', color: '#686C72' }}>{t}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Source groups */}
                {Object.entries(groups).sort(([,a],[,b]) => b.filter(x=>x._imp==='high').length - a.filter(x=>x._imp==='high').length).map(([src, arts]) => (
                  <div key={src} style={{ marginTop: '24px' }}>
                    <div className="flex items-center pb-1.5 mb-1" style={{ borderBottom: '1px solid #E8EAED' }}>
                      <span style={{ fontSize: '13px', fontWeight: 600, color: '#1A1C1E' }}>{src}</span>
                      <span className="text-xs ml-auto" style={{ color: '#8C9096' }}>{arts.length} 篇</span>
                    </div>
                    {arts.sort((a, b) => ({high:0,medium:1,low:2}[a._imp]||2) - ({high:0,medium:1,low:2}[b._imp]||2)).map((a) => (
                      <div key={a.id || a.url} onClick={() => onReadArticle(a.id)}
                        className="article-item flex items-start gap-2" style={{ padding: '6px 0' }}>
                        <div className={`flex-1 min-w-0 ${a._imp === 'high' ? 'imp-high' : a._imp === 'medium' ? 'imp-medium' : 'imp-low'}`}>
                          <span className="text-sm leading-relaxed" style={{ color: '#1A1C1E', fontWeight: a._imp === 'high' ? 500 : 400 }}>
                            {a.title}
                          </span>
                          <div className="flex items-center gap-2 mt-0.5" style={{ color: '#8C9096', fontSize: '11px' }}>
                            <span>{a.source_name}</span>
                            {a.published_at && <span>· {a.published_at.slice(0, 10)}</span>}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ))}
                {articles.length === 0 && <div className="text-center py-16 text-sm" style={{ color: '#8C9096' }}>暂无内容</div>}
              </>
            ) : searching && searchResults ? (
              <div className="space-y-1">
                {searchResults.items.map((a) => (
                  <div key={a.id || a.url} onClick={() => onReadArticle(a.id)}
                    className="article-item" style={{ padding: '6px 0' }}>
                    <div className={`${a.importance === 'high' ? 'imp-high' : a.importance === 'medium' ? 'imp-medium' : 'imp-low'}`}>
                      <span className="text-sm" style={{ color: '#1A1C1E' }}>{a.title}</span>
                      <div className="flex items-center gap-2 mt-0.5 text-xs" style={{ color: '#8C9096' }}>
                        <span>{a.source_name}</span>
                        {a.published_at && <span>· {a.published_at.slice(0, 10)}</span>}
                      </div>
                      {a.summary && <p className="text-xs mt-1 line-clamp-2" style={{ color: '#686C72' }}>{a.summary}</p>}
                    </div>
                  </div>
                ))}
                {searchResults.items.length === 0 && <div className="text-center py-16 text-sm" style={{ color: '#8C9096' }}>未找到相关文章</div>}
              </div>
            ) : (
              <div className="text-center py-16 text-sm" style={{ color: '#8C9096' }}>暂无数据</div>
            )}

            {/* Pagination */}
            {searching && searchResults?.pages > 1 && (
              <div className="flex justify-center gap-1 mt-6">
                <button disabled={page <= 1} onClick={() => doSearch('', importance, source, tag, page - 1)}
                  className="px-2.5 py-1 text-xs rounded disabled:opacity-40" style={{ background: '#F0F1F2', color: '#686C72' }}>←</button>
                {Array.from({ length: Math.min(searchResults.pages, 5) }, (_, i) => {
                  const p = Math.max(1, page - 2) + i;
                  if (p > searchResults.pages) return null;
                  return <button key={p} onClick={() => doSearch('', importance, source, tag, p)}
                    className="px-2.5 py-1 text-xs rounded" style={p === page ? { background: '#1A1C1E', color: '#fff' } : { background: '#F0F1F2', color: '#686C72' }}>{p}</button>;
                })}
                <button disabled={page >= searchResults.pages} onClick={() => doSearch('', importance, source, tag, page + 1)}
                  className="px-2.5 py-1 text-xs rounded disabled:opacity-40" style={{ background: '#F0F1F2', color: '#686C72' }}>→</button>
              </div>
            )}
          </div>
        </div>

        {/* ═══ Right Side Panel ═══ */}
        <div className={`flex-shrink-0 overflow-y-auto transition-all duration-300 ${sidePanelOpen ? 'w-[280px] opacity-100' : 'w-0 opacity-0 overflow-hidden'} ${searching ? 'hidden' : ''}`}
          style={{ borderLeft: '1px solid #E8EAED', padding: '20px 16px', background: '#FBFCFD' }}>
          <SidePanel
            keywords={report?.trending_keywords || []}
            insight={report?.summary_insight || ''}
            topArticles={highArticles}
            onArticleClick={(id) => onReadArticle(id)}
            onAskAI={handleAskAI}
          />
        </div>
      </div>
    </div>
  );
}

function formatDateShort(dateStr) {
  const d = new Date(dateStr);
  const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
  return `${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getDate().toString().padStart(2, '0')} 周${weekdays[d.getDay()]}`;
}
